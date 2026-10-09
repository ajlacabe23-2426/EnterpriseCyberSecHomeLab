"""Review an offline, user-provided lab snapshot; never collect live host data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .audit import audit_snapshot

MAX_JSON_BYTES = 150_000


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Linux configuration snapshot auditor for owned homelab training"
    )
    parser.add_argument("--file", type=Path, help="Owned local JSON snapshot (default: stdin)")
    args = parser.parse_args(argv)
    try:
        if args.file is not None:
            if args.file.stat().st_size > MAX_JSON_BYTES:
                raise ValueError("JSON snapshot is too large")
            raw = args.file.read_bytes()
        else:
            raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ValueError("JSON snapshot is too large")
        data = json.loads(raw.decode("utf-8"))
        report = audit_snapshot(data)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        # Never echo source content in errors.
        print(json.dumps({"error": "Cannot read or validate local JSON snapshot"}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
