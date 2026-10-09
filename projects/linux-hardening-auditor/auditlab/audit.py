"""Offline snapshot-based Linux configuration review.

Every finding is evidence-scoped. Missing/ambiguous data are NOT_CHECKED, not PASS.
No commands, remote connections, secrets, log uploads or system changes.
"""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

SCHEMA = "linux-audit-snapshot-v1"
MAX_SECTION_CHARS = 24_000
FIELDS = ("ssh_effective", "ufw_status", "passwd_text", "group_text", "tcp_listening")
STATUS = ("pass", "review", "fail", "not_checked")


def _finding(
    identifier: str,
    status: str,
    finding: str,
    evidence: str,
    next_step: str,
) -> dict[str, str]:
    assert status in STATUS
    return {
        "check_id": identifier,
        "status": status,
        "finding": finding,
        "evidence_summary": evidence,
        "next_step": next_step,
    }


def _ssh_values(text: str | None) -> dict[str, str]:
    if text is None:
        return {}
    values: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        pieces = line.split(None, 1)
        if len(pieces) != 2:
            continue
        key, value = pieces[0].lower(), pieces[1].strip().lower()
        # Ambiguous duplicate key: do not claim an effective value.
        if key in values:
            values[key] = ""
        else:
            values[key] = value
    return values


def _ssh_check(key: str, name: str, value: str | None, rule: dict[str, str], guidance: str) -> dict[str, str]:
    if value is None or value == "":
        return _finding(key, "not_checked", name, "Missing or ambiguous effective SSH value.", guidance)
    result = rule.get(value, "not_checked")
    message = f"Effective SSH setting {key} was classified as {result.upper()}."
    if result == "not_checked":
        message = "Effective SSH value is not recognized by this educational check."
    return _finding(key, result, name, message, guidance)


def _ufw_state(text: str | None) -> str | None:
    if text is None:
        return None
    match = re.search(r"(?im)^\s*Status:\s*(active|inactive)\s*$", text)
    return match.group(1).lower() if match else None


def _ufw_incoming(text: str | None) -> str | None:
    if text is None:
        return None
    match = re.search(r"(?im)^\s*Default:\s*(allow|deny|reject)\s*\(incoming\)", text)
    return match.group(1).lower() if match else None


def _uid_zero_check(text: str | None) -> dict[str, str]:
    guidance = "Review UID 0 ownership locally; do not publish account lists or identifiers."
    if not text or not text.strip():
        return _finding("uid_zero", "not_checked", "Privileged UID 0 accounts", "No account snapshot supplied.", guidance)
    uid0_accounts: list[str] = []
    invalid = False
    for record in text.splitlines():
        if not record.strip() or record.startswith("#"):
            continue
        fields = record.split(":")
        if len(fields) != 7 or not fields[2].isdigit():
            invalid = True
            continue
        if int(fields[2]) == 0:
            uid0_accounts.append(fields[0])
    if invalid or not uid0_accounts:
        return _finding("uid_zero", "not_checked", "Privileged UID 0 accounts", "Account snapshot incomplete or malformed.", guidance)
    if uid0_accounts == ["root"]:
        return _finding("uid_zero", "pass", "Privileged UID 0 accounts", "Only root holds UID 0 in this snapshot.", guidance)
    return _finding("uid_zero", "fail", "Privileged UID 0 accounts", f"{len(uid0_accounts)} accounts hold UID 0, or root identity is inconsistent.", guidance)


def _sudo_group_check(text: str | None) -> dict[str, str]:
    guidance = "Review access through sudoers, nested groups and other privilege mechanisms in a separate exercise."
    if text is None:
        return _finding("sudo_group", "not_checked", "Explicit sudo-group members", "No group snapshot supplied.", guidance)
    matches = [row for row in text.splitlines() if row.split(":", 1)[0] == "sudo"]
    if len(matches) != 1:
        return _finding("sudo_group", "not_checked", "Explicit sudo-group members", "sudo group is missing or ambiguous.", guidance)
    parts = matches[0].split(":")
    if len(parts) != 4 or not parts[2].isdigit():
        return _finding("sudo_group", "not_checked", "Explicit sudo-group members", "Malformed sudo group entry.", guidance)
    members = [name.strip() for name in parts[3].split(",") if name.strip()]
    if members:
        return _finding("sudo_group", "review", "Explicit sudo-group members", f"{len(members)} explicitly listed sudo-group member(s); names omitted.", guidance)
    return _finding("sudo_group", "pass", "Explicit sudo-group members", "No direct sudo-group members listed; other privilege paths not checked.", guidance)


def _listeners_check(text: str | None) -> dict[str, str]:
    guidance = "Confirm each listening TCP service is needed, accessible only where intended, and governed by firewall policy."
    if text is None or not text.strip():
        return _finding("tcp_listeners", "not_checked", "TCP listening exposure", "No listening-socket snapshot supplied.", guidance)
    count = 0
    wildcard = 0
    malformed = 0
    for line in text.splitlines():
        parts = line.split()
        if not parts or (parts[0].lower() == "state"):
            continue
        if len(parts) < 5 or parts[0].upper() != "LISTEN":
            malformed += 1
            continue
        # ss -lntH columns: State Recv-Q Send-Q Local Peer; index 3 is Local.
        local = parts[3]
        if ":" not in local:
            malformed += 1
            continue
        host = local.rsplit(":", 1)[0]
        count += 1
        if host in ("*", "0.0.0.0", "[::]", "::"):
            wildcard += 1
    if malformed:
        return _finding("tcp_listeners", "not_checked", "TCP listening exposure", "One or more socket rows could not be interpreted.", guidance)
    if wildcard:
        return _finding("tcp_listeners", "review", "TCP listening exposure", f"{wildcard} of {count} TCP listener(s) bind all interfaces in the supplied snapshot.", guidance)
    if count:
        return _finding("tcp_listeners", "pass", "TCP listening exposure", f"{count} TCP listener(s) have no observed wildcard bindings; reachability not verified.", guidance)
    return _finding("tcp_listeners", "not_checked", "TCP listening exposure", "No parseable listener rows were provided.", guidance)


def audit_snapshot(snapshot: dict[str, Any]) -> dict[str, object]:
    """Assess *provided* data only. No filesystem reads or system subprocesses."""
    if not isinstance(snapshot, dict):
        raise TypeError("Snapshot must be a JSON object")
    if snapshot.get("schema") != SCHEMA:
        raise ValueError(f"Expected snapshot schema {SCHEMA}")
    if set(snapshot) - ({"schema"} | set(FIELDS)):
        raise ValueError("Unexpected snapshot fields")
    for key in FIELDS:
        field = snapshot.get(key)
        if field is not None and (not isinstance(field, str) or len(field) > MAX_SECTION_CHARS):
            raise ValueError(f"{key} must be a bounded text field or absent")

    ssh = _ssh_values(snapshot.get("ssh_effective"))
    ufw_raw = snapshot.get("ufw_status")
    state = _ufw_state(ufw_raw)
    incoming = _ufw_incoming(ufw_raw)
    checks = [
        _ssh_check(
            "permitrootlogin", "SSH root login",
            ssh.get("permitrootlogin"),
            {"no": "pass", "yes": "fail", "prohibit-password": "review", "forced-commands-only": "review"},
            "Check SSH access requirements; review effective Match-context behavior separately.",
        ),
        _ssh_check(
            "passwordauthentication", "SSH password authentication",
            ssh.get("passwordauthentication"),
            {"no": "pass", "yes": "review"},
            "Review authentication policy, keys and any MFA requirements before making changes.",
        ),
        _ssh_check(
            "permitemptypasswords", "SSH empty-password authentication",
            ssh.get("permitemptypasswords"),
            {"no": "pass", "yes": "fail"},
            "Confirm no empty-password authentication is permitted; validate SSH Match contexts.",
        ),
        _finding(
            "ufw_status",
            {"active": "pass", "inactive": "fail"}.get(state, "not_checked"),
            "UFW enforcement status",
            "UFW reported active." if state == "active" else
            ("UFW reported inactive." if state == "inactive" else "No recognizable UFW status supplied."),
            "Check whether UFW or another approved firewall enforces host access policies.",
        ),
        _finding(
            "ufw_incoming",
            ("pass" if incoming in {"deny", "reject"} else "fail" if incoming == "allow" else "not_checked")
            if state == "active" else "not_checked",
            "UFW default incoming policy",
            (
                "Active UFW incoming default is deny/reject." if incoming in {"deny", "reject"} else
                "Active UFW incoming default allows traffic."
            ) if state == "active" and incoming else "Incoming default is unavailable or UFW is not active.",
            "Review necessary application exceptions and active firewall policy.",
        ),
        _uid_zero_check(snapshot.get("passwd_text")),
        _sudo_group_check(snapshot.get("group_text")),
        _listeners_check(snapshot.get("tcp_listening")),
    ]
    counts = Counter(item["status"] for item in checks)
    return {
        "schema": "linux-hardening-report-v1",
        "mode": "OFFLINE_READ_ONLY_SNAPSHOT",
        "checks": checks,
        "summary": {key: counts[key] for key in STATUS},
        "coverage": {
            "checks_total": len(checks),
            "checks_evaluated": len(checks) - counts["not_checked"],
            "source_sections_provided": sum(snapshot.get(field) is not None for field in FIELDS),
            "source_sections_expected": len(FIELDS),
        },
        "limitations": [
            "This report evaluates supplied snapshots only; it does not establish current host state.",
            "Missing or ambiguous evidence is NOT_CHECKED, not PASS.",
            "SSH Match blocks, other firewalls, alternative privilege paths and non-TCP exposure are out of scope.",
            "No checks modify host configurations, remediate issues or verify network reachability.",
            "No raw configuration text, usernames, or IP addresses are included in the report.",
        ],
    }
