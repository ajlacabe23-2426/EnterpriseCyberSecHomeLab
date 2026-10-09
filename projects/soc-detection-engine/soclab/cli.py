"""Local file/stdin command-line runner for the SOC detection learning lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .detect import analyze_lines
from .parser import MAX_INPUT_BYTES


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze owned lab UFW and SSH syslog, without external services")
    parser.add_argument("--file", type=Path, help="UTF-8 lab log file (defaults to standard input)")
    parser.add_argument("--year", type=int, help="Required year for legacy syslog lines without a year")
    parser.add_argument("--utc-offset-hours", type=int, default=0, help="UTC offset of legacy timestamps, default 0")
    args = parser.parse_args(argv)
    try:
        if args.file is not None:
            if args.file.stat().st_size > MAX_INPUT_BYTES:
                raise ValueError("File exceeds the 5 MB educational input limit")
            with args.file.open("r", encoding="utf-8") as handle:
                result = analyze_lines(handle, assumed_year=args.year, utc_offset_hours=args.utc_offset_hours)
        else:
            # Read one additional character to detect oversized piped content.
            raw = sys.stdin.read(MAX_INPUT_BYTES + 1)
            if len(raw.encode("utf-8")) > MAX_INPUT_BYTES:
                raise ValueError("Standard input exceeds the 5 MB educational input limit")
            result = analyze_lines(raw.splitlines(keepends=True), assumed_year=args.year, utc_offset_hours=args.utc_offset_hours)
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
