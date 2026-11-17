"""Deterministic, explainable detections over offline, timestamped lab telemetry."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from datetime import timedelta
from typing import Iterable

from .parser import Event, MAX_INPUT_BYTES, MAX_INPUT_LINES, parse_line


def _stamp(event: Event) -> str:
    return event.when.isoformat(timespec="seconds").replace("+00:00", "Z")


def _alert(
    rule_id: str,
    severity: str,
    observations: list[Event],
    *,
    explanation: str,
    recommendation: str,
    target_port: int | None = None,
) -> dict[str, object]:
    first, last = observations[0], observations[-1]
    result: dict[str, object] = {
        "rule_id": rule_id,
        "severity": severity,
        "source": last.source,
        "host": last.host,
        "destination": last.destination,
        "event_count": len(observations),
        "first_seen_utc": _stamp(first),
        "last_seen_utc": _stamp(last),
        "explanation": explanation,
        "investigation_step": recommendation,
    }
    if target_port is not None:
        result["destination_port"] = target_port
    return result


def detect_events(events: list[Event]) -> list[dict[str, object]]:
    """Check controlled thresholds and report the earliest qualifying window per key.

    Deliberately emits at most one alert per rule/key for an input batch. V1 is
    a teaching tool, not a streaming SIEM or risk scoring service.
    """
    firewall_by_port: dict[tuple[str, str, str, int], deque[Event]] = defaultdict(deque)
    firewall_by_source: dict[tuple[str, str, str], deque[Event]] = defaultdict(deque)
    failures_by_source: dict[tuple[str, str], deque[Event]] = defaultdict(deque)
    emitted: set[tuple[object, ...]] = set()
    alerts: list[dict[str, object]] = []

    ordered = sorted(events, key=lambda e: (e.when, e.host, e.source, e.kind, e.port or 0))
    for event in ordered:
        if event.kind == "firewall_block":
            assert event.port is not None
            key = (event.host, event.source, event.destination, event.port)
            recent = firewall_by_port[key]
            while recent and event.when - recent[0].when > timedelta(minutes=5):
                recent.popleft()
            recent.append(event)
            signature = ("repeated_firewall_blocks", *key)
            if len(recent) >= 3 and signature not in emitted:
                alerts.append(_alert(
                    "repeated_firewall_blocks", "medium", list(recent),
                    explanation="Three or more blocked connections to one destination port in five minutes.",
                    recommendation="Compare firewall policy and approved maintenance activity; inspect source context.",
                    target_port=event.port,
                ))
                emitted.add(signature)

            wide_key = (event.host, event.source, event.destination)
            recent_wide = firewall_by_source[wide_key]
            while recent_wide and event.when - recent_wide[0].when > timedelta(minutes=5):
                recent_wide.popleft()
            recent_wide.append(event)
            wide_signature = ("multiple_blocked_ports", *wide_key)
            if len({item.port for item in recent_wide}) >= 3 and wide_signature not in emitted:
                alerts.append(_alert(
                    "multiple_blocked_ports", "medium", list(recent_wide),
                    explanation="Blocked connections reached at least three distinct destination ports in five minutes.",
                    recommendation="Check whether authorized network troubleshooting explains the activity.",
                ))
                emitted.add(wide_signature)

        elif event.kind == "auth_failure":
            key = (event.host, event.source)
            recent = failures_by_source[key]
            while recent and event.when - recent[0].when > timedelta(minutes=10):
                recent.popleft()
            recent.append(event)
            signature = ("repeated_ssh_auth_failures", *key)
            if len(recent) >= 3 and signature not in emitted:
                alerts.append(_alert(
                    "repeated_ssh_auth_failures", "high", list(recent),
                    explanation="Three or more failed SSH password logins from one source in ten minutes.",
                    recommendation="Review authorized logins, account controls, and additional host telemetry.",
                ))
                emitted.add(signature)

        elif event.kind == "auth_success":
            key = (event.host, event.source)
            recent = failures_by_source[key]
            while recent and event.when - recent[0].when > timedelta(minutes=10):
                recent.popleft()
            signature = ("ssh_success_after_failures", *key)
            if len(recent) >= 3 and signature not in emitted:
                sequence = list(recent) + [event]
                alerts.append(_alert(
                    "ssh_success_after_failures", "high", sequence,
                    explanation="An SSH authentication succeeded after three or more recent failures from the same source.",
                    recommendation="Verify login authorization and correlate with change windows; success does not prove compromise.",
                ))
                emitted.add(signature)
    return sorted(alerts, key=lambda x: (str(x["first_seen_utc"]), str(x["rule_id"]), str(x["source"])))


def analyze_lines(
    lines: Iterable[str], *, assumed_year: int | None = None, utc_offset_hours: int = 0
) -> dict[str, object]:
    """Analyze a bounded batch. No source lines are copied into the report."""
    if assumed_year is not None and not 2000 <= assumed_year <= 2100:
        raise ValueError("Assumed year must be 2000–2100")
    if not -12 <= utc_offset_hours <= 14:
        raise ValueError("UTC offset must be -12 to +14 hours")
    observations: list[Event] = []
    line_count = 0
    byte_count = 0
    for line in lines:
        if not isinstance(line, str):
            raise TypeError("Log lines must be UTF-8 decoded strings")
        line_count += 1
        byte_count += len(line.encode("utf-8"))
        if line_count > MAX_INPUT_LINES or byte_count > MAX_INPUT_BYTES:
            raise ValueError("Log batch exceeds configured limits")
        event = parse_line(line, assumed_year=assumed_year, utc_offset_hours=utc_offset_hours)
        if event is not None:
            observations.append(event)
    counts = Counter(event.kind for event in observations)
    return {
        "schema": "soc-detection-lab-v1",
        "mode": "OFFLINE_EDUCATIONAL_TRIAGE",
        "source_lines": line_count,
        "recognized_events": len(observations),
        "skipped_lines": line_count - len(observations),
        "event_counts": {
            "firewall_block": counts["firewall_block"],
            "auth_failure": counts["auth_failure"],
            "auth_success": counts["auth_success"],
        },
        "alerts": detect_events(observations),
        "limitations": [
            "Heuristic thresholds are educational; alerts are not proof of malicious behavior.",
            "Unknown or unsupported lines are counted as skipped, not silently classified as safe.",
            "Review real logs locally and sanitize source IP addresses before sharing or committing any reports.",
            "A batch emits at most one alert per rule/source/target key; event duplicates may affect thresholds.",
            "For yearless legacy syslog, specify the correct year and UTC offset; otherwise those lines are skipped.",
        ],
    }
