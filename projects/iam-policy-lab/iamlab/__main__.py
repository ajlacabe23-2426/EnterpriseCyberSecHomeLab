"""CLI demonstration using only the authored fictional requests."""
import json
from datetime import datetime
from pathlib import Path
from .policy import evaluate

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "synthetic-requests.json"


def main() -> None:
    sample = json.loads(FIXTURES.read_text(encoding="utf-8"))
    for case in sample["cases"]:
        decision = evaluate(case["request"], now=datetime.fromisoformat(sample["as_of"].replace("Z", "+00:00")))
        print(f"{case['id']}: {decision['decision']} / {decision['reason']}")


if __name__ == "__main__":
    main()
