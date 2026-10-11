"""Local, read-only incident case generation; JSON to stdout or Markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .core import build_case, to_markdown

MAX_FILE_BYTES = 256_000


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a privacy-conscious fictional incident response case report offline"
    )
    parser.add_argument("--file", type=Path, help="Case manifest JSON; otherwise read stdin")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)
    try:
        if args.file:
            if args.file.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("Case manifest too large")
            raw = args.file.read_bytes()
        else:
            raw = sys.stdin.buffer.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("Case manifest too large")
        manifest = json.loads(raw.decode("utf-8"))
        report = build_case(manifest)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        # Do not reflect private input text or filesystem paths in errors.
        print(json.dumps({"error": "Invalid or unavailable local case manifest"}), file=sys.stderr)
        return 2
    if args.format == "markdown":
        sys.stdout.write(to_markdown(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
