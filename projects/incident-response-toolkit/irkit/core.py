"""Evidence-first incident casework over offline, synthetic lab report objects.

No raw log ingestion, network requests, host commands or remediation. The
generated case excludes report-supplied IPs, hostnames and arbitrary source text.
A digest identifies the exact *supplied report*, not independently verified evidence.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

SCHEMA = "incident-case-input-v1"
MAX_ALERTS = 200
MAX_AUDIT_CHECKS = 16
MAX_ANALYST_EVENTS = 50

_RULES = {
    "repeated_firewall_blocks": ("Repeated blocked connections", "Check whether the source was performing approved troubleshooting or maintenance."),
    "multiple_blocked_ports": ("Multiple blocked destination ports", "Compare the observed port pattern with authorized network testing."),
    "repeated_ssh_auth_failures": ("Repeated SSH authentication failures", "Review approved accounts, normal login activity, and corroborating host telemetry."),
    "ssh_success_after_failures": ("SSH authentication success following failures", "Independently establish whether the successful session was authorized."),
}
_CHECKS = {
    "permitrootlogin": "SSH root-login setting",
    "passwordauthentication": "SSH password-authentication setting",
    "permitemptypasswords": "SSH empty-password setting",
    "ufw_status": "Host firewall active state",
    "ufw_incoming": "Firewall default incoming policy",
    "uid_zero": "UID 0 account configuration",
    "sudo_group": "Sudo group membership",
    "tcp_listeners": "TCP listening configuration",
}
_EVENT_KINDS = {
    "analyst_review": "Analyst reviewed the fictional evidence",
    "approved_change": "Authorized change recorded in exercise",
    "retest": "Controlled verification exercise documented",
}
_STATUS = ("pass", "review", "fail", "not_checked")
_ALLOWED_SEVERITY = ("medium", "high")
_ID = re.compile(r"^[A-Z][A-Z0-9-]{2,39}$")
_EVIDENCE_ID = re.compile(r"^[A-Z][A-Z0-9_-]{2,39}$")


def _when(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Timestamp must be a bounded timezone-aware ISO 8601 string")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid timestamp") from error
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("Timestamp must contain an explicit UTC offset")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _digest(value: dict) -> str:
    canon = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def _nonnegative_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def _soc(report: Any) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not isinstance(report, dict) or report.get("schema") != "soc-detection-lab-v1":
        raise ValueError("Expected a SOC Detection Engine V1 report")
    raw = report.get("alerts")
    if not isinstance(raw, list) or len(raw) > MAX_ALERTS:
        raise ValueError("Invalid or excessive SOC alert entries")
    for name in ("source_lines", "recognized_events", "skipped_lines"):
        if not _nonnegative_int(report.get(name)):
            raise ValueError("Invalid SOC telemetry counts")
    if report["recognized_events"] + report["skipped_lines"] != report["source_lines"]:
        raise ValueError("SOC event counts are inconsistent")

    timeline: list[dict[str, object]] = []
    ids: Counter[str] = Counter()
    for i, alert in enumerate(raw, 1):
        if not isinstance(alert, dict):
            raise ValueError("Invalid SOC alert")
        rule = alert.get("rule_id")
        if rule not in _RULES or alert.get("severity") not in _ALLOWED_SEVERITY:
            raise ValueError("Unknown SOC alert rule or severity")
        if not _positive_int(alert.get("event_count")):
            raise ValueError("Invalid aggregated SOC event count")
        start = _when(alert.get("first_seen_utc"))
        end = _when(alert.get("last_seen_utc"))
        if start > end:
            raise ValueError("SOC window ends before it begins")
        ids[rule] += 1
        timeline.append({
            "at_utc": end,
            "window_start_utc": start,
            "time_basis": "soc_alert_last_seen",
            "evidence_ref": f"SOC#{i:03d}",
            "kind": "soc_alert",
            "label": _RULES[rule][0],
            "rule_id": rule,
            "severity": alert["severity"],
            "aggregated_event_count": alert["event_count"],
            "interpretation": "Observed indicator in supplied report; authorization and incident status unverified.",
        })
    provenance = {
        "reference": "SOC",
        "report_schema": "soc-detection-lab-v1",
        "sha256_of_supplied_report": _digest(report),
        "alerts": len(raw),
        "recognized_events": report["recognized_events"],
        "skipped_lines": report["skipped_lines"],
        "limitations": "A report digest is not independent chain-of-custody or a signed attestation.",
    }
    return timeline, provenance


def _audit(report: Any) -> tuple[list[dict[str, object]], dict[str, object]]:
    if not isinstance(report, dict) or report.get("schema") != "linux-hardening-report-v1":
        raise ValueError("Expected a Linux Hardening Auditor V1 report")
    raw = report.get("checks")
    if not isinstance(raw, list) or len(raw) > MAX_AUDIT_CHECKS:
        raise ValueError("Invalid hardening check collection")
    seen: set[str] = set()
    items: list[dict[str, object]] = []
    for i, check in enumerate(raw, 1):
        if not isinstance(check, dict):
            raise ValueError("Invalid hardening check")
        identifier, status = check.get("check_id"), check.get("status")
        if identifier not in _CHECKS or status not in _STATUS or identifier in seen:
            raise ValueError("Unknown, duplicated, or invalid hardening check")
        seen.add(identifier)
        items.append({
            "evidence_ref": f"AUDIT#{i:03d}",
            "check_id": identifier,
            "label": _CHECKS[identifier],
            "status": status,
            "interpretation": "Snapshot-level configuration check; current host state not independently verified.",
        })
    summary = Counter(item["status"] for item in items)
    declared = report.get("summary")
    if declared is not None:
        if not isinstance(declared, dict) or any(
            not _nonnegative_int(declared.get(key)) or declared[key] != summary[key]
            for key in _STATUS
        ):
            raise ValueError("Hardening summary disagrees with individual findings")
    provenance = {
        "reference": "AUDIT",
        "report_schema": "linux-hardening-report-v1",
        "sha256_of_supplied_report": _digest(report),
        "checks": len(items),
        "checks_not_checked": summary["not_checked"],
        "limitations": "Snapshot findings alone do not verify live host configuration or incident severity.",
    }
    return items, provenance


def build_case(payload: dict[str, Any]) -> dict[str, object]:
    """Construct an explanatory case without copying untrusted source text."""
    if not isinstance(payload, dict):
        raise TypeError("Case input must be a JSON object")
    allowed = {"schema", "case_id", "soc_report", "audit_report", "analyst_events", "audit_reviewed_at_utc"}
    if set(payload) - allowed or payload.get("schema") != SCHEMA:
        raise ValueError("Unexpected case fields or schema")
    case_id = payload.get("case_id")
    if not isinstance(case_id, str) or not _ID.fullmatch(case_id):
        raise ValueError("Case ID must be 3–40 uppercase letters, digits or hyphens")
    if "soc_report" not in payload and "audit_report" not in payload and not payload.get("analyst_events"):
        raise ValueError("At least one evidence input or analyst event is required")

    timeline: list[dict[str, object]] = []
    findings: list[dict[str, object]] = []
    provenance: list[dict[str, object]] = []
    if "soc_report" in payload:
        events, source = _soc(payload["soc_report"])
        timeline.extend(events)
        provenance.append(source)
    if "audit_report" in payload:
        audit, source = _audit(payload["audit_report"])
        findings.extend(audit)
        provenance.append(source)
    if "audit_reviewed_at_utc" in payload:
        if "audit_report" not in payload:
            raise ValueError("Audit review timestamp requires an audit report")
        # This records analyst-supplied review time, NOT when host settings existed.
        timeline.append({
            "at_utc": _when(payload["audit_reviewed_at_utc"]),
            "time_basis": "analyst_supplied_review_time",
            "evidence_ref": "AUDIT",
            "kind": "audit_review",
            "label": "Analyst reviewed hardening snapshot",
            "interpretation": "Review time is supplied by the analyst; not a verified host capture timestamp.",
        })
    raw_events = payload.get("analyst_events", [])
    if not isinstance(raw_events, list) or len(raw_events) > MAX_ANALYST_EVENTS:
        raise ValueError("Invalid analyst event collection")
    refs: set[str] = set()
    for item in raw_events:
        if not isinstance(item, dict) or set(item) != {"evidence_id", "timestamp_utc", "kind"}:
            raise ValueError("Each analyst event requires only evidence_id, timestamp_utc and kind")
        evidence = item["evidence_id"]
        kind = item["kind"]
        if not isinstance(evidence, str) or not _EVIDENCE_ID.fullmatch(evidence) or evidence in refs:
            raise ValueError("Invalid or duplicate evidence reference")
        if kind not in _EVENT_KINDS:
            raise ValueError("Unknown analyst event kind")
        refs.add(evidence)
        timeline.append({
            "at_utc": _when(item["timestamp_utc"]),
            "time_basis": "analyst_supplied_event_time",
            "evidence_ref": evidence,
            "kind": kind,
            "label": _EVENT_KINDS[kind],
            "interpretation": "Analyst-entered event; supporting evidence must be independently reviewed.",
        })

    timeline.sort(key=lambda event: (str(event["at_utc"]), str(event["evidence_ref"])))
    rules_found = sorted({str(e["rule_id"]) for e in timeline if e["kind"] == "soc_alert"})
    audit_review = sorted(
        (entry for entry in findings if entry["status"] in ("fail", "review")),
        key=lambda entry: (str(entry["status"]), str(entry["check_id"])),
    )
    # These are *questions for follow-up*, never conclusions about compromise.
    questions: list[dict[str, str]] = [
        {"rule_id": rule, "question": _RULES[rule][1], "status": "unverified"}
        for rule in rules_found
    ]
    if audit_review:
        questions.append({
            "rule_id": "configuration_context",
            "question": "Do the snapshot-level configuration findings affect this event's exposure, and are they still current?",
            "status": "unverified",
        })
    if not questions:
        questions.append({
            "rule_id": "general_context",
            "question": "What authorized baseline and independent evidence establish whether an incident occurred?",
            "status": "unverified",
        })
    status_counts = Counter(item["status"] for item in findings)
    return {
        "schema": "incident-case-report-v1",
        "case_id": case_id,
        "case_state": "triage_unverified",
        "source_provenance": provenance,
        "timeline": timeline,
        "undated_configuration_findings": findings,
        "configuration_summary": {key: status_counts[key] for key in _STATUS},
        "questions_to_investigate": questions,
        "review_gates": [
            "Confirm scope, authorization and relevance of every evidence source.",
            "Compare observed events with maintenance windows and benign explanations.",
            "Verify timestamps, event integrity, and system-specific telemetry.",
            "Keep hypotheses separate from verified observations.",
            "Document any approved containment, recovery and retest separately; this tool takes no actions.",
        ],
        "limitations": [
            "Only pre-existing, analyst-supplied inputs are considered; no hosts were contacted.",
            "SOC alert windows are aggregated observations, not reconstructed packet-level activity.",
            "Undated hardening checks remain undated unless a review time is supplied, which is not capture time.",
            "Report digests identify input bytes after JSON normalization, not forensic chain of custody.",
            "No labels in this report establish compromise, attacker identity or remediation success.",
            "Free-text source fields, private IP addresses, hostnames and user names are not echoed.",
        ],
    }


def to_markdown(report: dict[str, object]) -> str:
    """Human-readable, intentionally source-redacted case report."""
    if report.get("schema") != "incident-case-report-v1":
        raise ValueError("Expected incident-case-report-v1")
    rows = [
        f"# Incident case {report['case_id']} (fictional training exercise)",
        "",
        "**State:** triage / unverified. **No intrusion is confirmed.**",
        "",
        "## Evidence references",
    ]
    for source in report["source_provenance"]:
        rows.append(
            f"- {source['reference']} ({source['report_schema']}): SHA-256 {source['sha256_of_supplied_report']} "
            "(input fingerprint, not independent custody proof)"
        )
    if not report["source_provenance"]:
        rows.append("- No machine-generated report included.")
    rows.extend(["", "## Timeline (time basis recorded per item)"])
    if not report["timeline"]:
        rows.append("- No timestamped observations supplied.")
    for event in report["timeline"]:
        rows.append(
            f"- {event['at_utc']} · {event['evidence_ref']} · {event['label']} "
            f"({event['time_basis']}; {event['interpretation']})"
        )
    rows.extend(["", "## Configuration snapshot findings (undated)"])
    if not report["undated_configuration_findings"]:
        rows.append("- No hardening report supplied.")
    for item in report["undated_configuration_findings"]:
        rows.append(f"- {item['evidence_ref']}: {item['label']} — {item['status'].upper()} (snapshot only)")
    rows.extend(["", "## Open questions (unverified)"])
    for item in report["questions_to_investigate"]:
        rows.append(f"- {item['question']}")
    rows.extend(["", "## Analyst verification gates"])
    for gate in report["review_gates"]:
        rows.append(f"- [ ] {gate}")
    rows.extend(["", "## Limitations"])
    for item in report["limitations"]:
        rows.append(f"- {item}")
    return "\n".join(rows) + "\n"
