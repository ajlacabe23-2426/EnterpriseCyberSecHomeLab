"""Parse bounded UFW and OpenSSH syslog observations from owned lab systems.

Only recognized event fields are returned; raw log lines and account names
are never included in generated alerts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import ipaddress
import re
from typing import Literal

EventKind = Literal["firewall_block", "auth_failure", "auth_success"]
MAX_LINE_LENGTH = 8192
MAX_INPUT_LINES = 20_000
MAX_INPUT_BYTES = 5_000_000

_ISO_PREFIX = re.compile(
    r"^(?P<when>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))\s+"
    r"(?P<host>[a-zA-Z0-9_.-]{1,64})\s+(?P<record>.+)$"
)
_LEGACY_PREFIX = re.compile(
    r"^(?P<when>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>[a-zA-Z0-9_.-]{1,64})\s+(?P<record>.+)$"
)
_SRC = re.compile(r"(?:^|\s)SRC=(\S+)")
_DST = re.compile(r"(?:^|\s)DST=(\S+)")
_PORT = re.compile(r"(?:^|\s)DPT=(\d{1,5})(?:\s|$)")
_SSH_SOURCE = re.compile(r"\bfrom\s+([0-9a-fA-F:.]+)\b")
_AUTH_FAIL = re.compile(r"\bFailed password for\b")
_AUTH_SUCCESS = re.compile(r"\bAccepted (?:password|publickey) for\b")


@dataclass(frozen=True)
class Event:
    when: datetime
    host: str
    kind: EventKind
    source: str
    destination: str
    port: int | None = None

    def __post_init__(self) -> None:
        if self.when.utcoffset() is None:
            raise ValueError("Event timestamp must have an explicit timezone")


def _ip(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def _time(match: re.Match[str], assumed_year: int | None, utc_offset_hours: int) -> datetime | None:
    raw = match.group("when")
    if "T" in raw:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None
    if assumed_year is None:
        return None
    if not 2000 <= assumed_year <= 2100 or not -12 <= utc_offset_hours <= 14:
        raise ValueError("Year and UTC offset must be explicitly bounded")
    try:
        local = datetime.strptime(f"{assumed_year} {raw}", "%Y %b %d %H:%M:%S")
        return local.replace(tzinfo=timezone(timedelta(hours=utc_offset_hours))).astimezone(timezone.utc)
    except ValueError:
        return None


def parse_line(line: str, *, assumed_year: int | None = None, utc_offset_hours: int = 0) -> Event | None:
    """Normalize one syslog line. Legacy lines need an explicit year.

    utc_offset_hours applies only to yearless legacy syslog; RFC3339 offsets
    are retained by the timestamp itself.
    """
    if not isinstance(line, str) or len(line) > MAX_LINE_LENGTH:
        return None
    match = _ISO_PREFIX.match(line.strip()) or _LEGACY_PREFIX.match(line.strip())
    if not match:
        return None
    timestamp = _time(match, assumed_year, utc_offset_hours)
    if timestamp is None:
        return None
    host, record = match.group("host"), match.group("record")

    if "[UFW BLOCK]" in record:
        src = _SRC.search(record)
        dst = _DST.search(record)
        dpt = _PORT.search(record)
        source = _ip(src.group(1) if src else None)
        destination = _ip(dst.group(1) if dst else None)
        if source and destination and dpt:
            port = int(dpt.group(1))
            if 1 <= port <= 65535:
                return Event(timestamp, host, "firewall_block", source, destination, port)

    if "sshd[" in record or "sshd:" in record:
        source_match = _SSH_SOURCE.search(record)
        source = _ip(source_match.group(1) if source_match else None)
        if not source:
            return None
        if _AUTH_FAIL.search(record):
            return Event(timestamp, host, "auth_failure", source, host)
        if _AUTH_SUCCESS.search(record):
            return Event(timestamp, host, "auth_success", source, host)
    return None
