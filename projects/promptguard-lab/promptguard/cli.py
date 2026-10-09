"""Read local text or standard input and print a privacy-conscious JSON report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .detector import MAX_CHARS, SOURCE_GUIDANCE, scan_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline PromptGuard defensive text screening")
    parser.add_argument("--file", type=Path, help="Local UTF-8 input file; otherwise read standard input")
    parser.add_argument("--source-type", choices=tuple(SOURCE_GUIDANCE), default="unknown", help="Analyst-supplied origin classification; never grants authority")
    args = parser.parse_args(argv)
    try:
        if args.file:
            # Reject large files before fully reading them.
            if args.file.stat().st_size > 4 * MAX_CHARS:
                raise ValueError("Input file is too large")
            text = args.file.read_text(encoding="utf-8")
        else:
            text = sys.stdin.read(MAX_CHARS + 1)
        report = scan_text(text, source_type=args.source_type)
    except (OSError, UnicodeError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
