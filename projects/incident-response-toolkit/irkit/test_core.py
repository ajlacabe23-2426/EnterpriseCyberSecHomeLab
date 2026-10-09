"""Pure offline tests. All evidence objects are synthetic exercise material."""

from __future__ import annotations

import copy
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import unittest

from irkit.core import build_case, to_markdown

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


def fixture(name: str = "synthetic-case.json") -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def find_source(report: dict, name: str) -> dict:
    return next(item for item in report["source_provenance"] if item["reference"] == name)


class CaseTests(unittest.TestCase):
    def test_report_builds_from_both_modules(self):
        result = build_case(fixture())
        self.assertEqual(result["schema"], "incident-case-report-v1")
        self.assertEqual(result["case_state"], "triage_unverified")
        self.assertEqual(result["case_id"], "LAB-CASE-001")
        self.assertEqual(len(result["source_provenance"]), 2)
        self.assertEqual(len(result["timeline"]), 5)
        self.assertEqual(len(result["undated_configuration_findings"]), 4)

    def test_timeline_is_sorted_by_utc_timestamp(self):
        result = build_case(fixture())
        stamps = [item["at_utc"] for item in result["timeline"]]
        self.assertEqual(stamps, sorted(stamps))
        self.assertEqual(stamps[0], "2026-09-04T13:01:00Z")
        self.assertEqual(stamps[-1], "2026-09-04T13:15:00Z")

    def test_alert_window_time_basis_is_explicit(self):
        report = build_case(fixture())
        event = next(item for item in report["timeline"] if item["kind"] == "soc_alert")
        self.assertEqual(event["time_basis"], "soc_alert_last_seen")
        self.assertIn("window_start_utc", event)
        self.assertIn("unverified", event["interpretation"])

    def test_audit_review_timestamp_is_not_capture_timestamp(self):
        report = build_case(fixture())
        event = next(item for item in report["timeline"] if item["kind"] == "audit_review")
        self.assertEqual(event["time_basis"], "analyst_supplied_review_time")
        self.assertIn("not a verified host capture", event["interpretation"])

    def test_audit_snapshot_without_review_date_stays_undated(self):
        case = fixture()
        del case["audit_reviewed_at_utc"]
        result = build_case(case)
        self.assertFalse(any(item["kind"] == "audit_review" for item in result["timeline"]))
        self.assertEqual(len(result["undated_configuration_findings"]), 4)

    def test_hardening_not_checked_preserved_not_passed(self):
        report = build_case(fixture())
        self.assertEqual(report["configuration_summary"], {
            "pass": 2, "review": 1, "fail": 0, "not_checked": 1
        })

    def test_unverified_hypotheses_and_followups(self):
        report = build_case(fixture())
        self.assertTrue(all(item["status"] == "unverified" for item in report["questions_to_investigate"]))
        self.assertIn("configuration_context", [item["rule_id"] for item in report["questions_to_investigate"]])

    def test_benign_case_does_not_claim_incident_or_raise_alert(self):
        report = build_case(fixture("benign-case.json"))
        self.assertEqual(report["case_state"], "triage_unverified")
        self.assertEqual(report["timeline"], [])
        self.assertTrue(report["questions_to_investigate"])
        self.assertEqual(report["configuration_summary"]["pass"], 1)

    def test_no_evidence_rejected(self):
        with self.assertRaises(ValueError):
            build_case({"schema": "incident-case-input-v1", "case_id": "LAB-EMPTY"})

    def test_unknown_schema_rejected(self):
        case = fixture()
        case["schema"] = "legacy-case"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_extra_top_level_input_rejected(self):
        case = fixture()
        case["secret"] = "should not be allowed"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_invalid_case_id_rejected(self):
        for cid in ("bad", "a" * 100, "LAB CASE", "#HEADING", "[system]", "LAB:INVALID"):
            with self.subTest(case_id=cid), self.assertRaises(ValueError):
                case = fixture()
                case["case_id"] = cid
                build_case(case)

    def test_invalid_soc_schema_rejected(self):
        case = fixture()
        case["soc_report"]["schema"] = "wrong"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_soc_count_disagreement_rejected(self):
        case = fixture()
        case["soc_report"]["skipped_lines"] = 3
        with self.assertRaises(ValueError):
            build_case(case)

    def test_unknown_soc_rule_rejected(self):
        case = fixture()
        case["soc_report"]["alerts"][0]["rule_id"] = "unrecognized_rule"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_zero_event_count_rejected(self):
        case = fixture()
        case["soc_report"]["alerts"][0]["event_count"] = 0
        with self.assertRaises(ValueError):
            build_case(case)

    def test_event_count_bool_rejected(self):
        case = fixture()
        case["soc_report"]["alerts"][0]["event_count"] = True
        with self.assertRaises(ValueError):
            build_case(case)

    def test_future_window_before_start_rejected(self):
        case = fixture()
        case["soc_report"]["alerts"][0]["first_seen_utc"] = "2026-09-04T13:09:00Z"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_naive_timestamp_rejected(self):
        case = fixture()
        case["soc_report"]["alerts"][0]["first_seen_utc"] = "2026-09-04T13:00:00"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_time_offset_converts_to_utc(self):
        case = fixture()
        case["analyst_events"][0]["timestamp_utc"] = "2026-09-04T08:10:00-05:00"
        report = build_case(case)
        entry = next(x for x in report["timeline"] if x["evidence_ref"] == "EVD-ANALYST-1")
        self.assertEqual(entry["at_utc"], "2026-09-04T13:10:00Z")

    def test_invalid_audit_check_rejected(self):
        case = fixture()
        case["audit_report"]["checks"][0]["status"] = "secured"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_duplicate_audit_check_rejected(self):
        case = fixture()
        case["audit_report"]["checks"].append(copy.deepcopy(case["audit_report"]["checks"][0]))
        with self.assertRaises(ValueError):
            build_case(case)

    def test_audit_summary_disagreement_rejected(self):
        case = fixture()
        case["audit_report"]["summary"]["pass"] = 3
        with self.assertRaises(ValueError):
            build_case(case)

    def test_duplicate_analyst_evidence_id_rejected(self):
        case = fixture()
        case["analyst_events"][1]["evidence_id"] = case["analyst_events"][0]["evidence_id"]
        with self.assertRaises(ValueError):
            build_case(case)

    def test_invalid_analyst_event_kind_rejected(self):
        case = fixture()
        case["analyst_events"][0]["kind"] = "incident_confirmed"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_free_text_in_analyst_events_rejected(self):
        case = fixture()
        case["analyst_events"][0]["summary"] = "not accepted"
        with self.assertRaises(ValueError):
            build_case(case)

    def test_audit_review_time_without_audit_rejected(self):
        case = fixture()
        del case["audit_report"]
        with self.assertRaises(ValueError):
            build_case(case)

    def test_limits_on_alerts(self):
        case = fixture()
        case["soc_report"]["alerts"] = case["soc_report"]["alerts"] * 101
        with self.assertRaises(ValueError):
            build_case(case)

    def test_limits_on_analyst_events(self):
        case = fixture()
        case["analyst_events"] = case["analyst_events"] * 26
        with self.assertRaises(ValueError):
            build_case(case)

    def test_fingerprints_deterministic(self):
        c = fixture()
        x, y = build_case(c), build_case(copy.deepcopy(c))
        self.assertEqual(x, y)
        self.assertEqual(len(find_source(x, "SOC")["sha256_of_supplied_report"]), 64)

    def test_digest_changes_with_evidence(self):
        a = fixture()
        b = copy.deepcopy(a)
        b["soc_report"]["alerts"][0]["event_count"] += 1
        self.assertNotEqual(
            find_source(build_case(a), "SOC")["sha256_of_supplied_report"],
            find_source(build_case(b), "SOC")["sha256_of_supplied_report"],
        )

    def test_sensitive_source_fields_not_echoed(self):
        c = fixture()
        c["soc_report"]["alerts"][0]["host"] = "PRIVATE_HOSTNAME_X"
        c["soc_report"]["alerts"][0]["source"] = "SECRET-IP-ADDRESS"
        c["soc_report"]["alerts"][0]["explanation"] = "RAW_EVIDENCE_PRIVATE"
        c["audit_report"]["checks"][0]["evidence_summary"] = "FAKE_USERNAME_012"
        report = build_case(c)
        output = json.dumps(report) + to_markdown(report)
        for marker in ("PRIVATE_HOSTNAME_X", "SECRET-IP-ADDRESS", "RAW_EVIDENCE_PRIVATE", "FAKE_USERNAME_012"):
            self.assertNotIn(marker, output)

    def test_markdown_has_traceable_evidence_ids_and_review_gates(self):
        result = to_markdown(build_case(fixture()))
        self.assertIn("# Incident case LAB-CASE-001", result)
        self.assertIn("SOC#001", result)
        self.assertIn("AUDIT#001", result)
        self.assertIn("Unverified", result.title())
        self.assertIn("- [ ] Confirm scope", result)

    def test_markdown_never_claims_compromise(self):
        report = to_markdown(build_case(fixture()))
        self.assertIn("No intrusion is confirmed", report)

    def test_no_report_with_just_analyst_event_is_allowed_as_unverified(self):
        c = {"schema": "incident-case-input-v1", "case_id": "LAB-NOTES-001",
             "analyst_events": [{"evidence_id": "EVD-001", "timestamp_utc": "2026-09-04T13:00:00Z", "kind": "analyst_review"}]}
        report = build_case(c)
        self.assertEqual(report["source_provenance"], [])
        self.assertEqual(report["case_state"], "triage_unverified")


class CommandLineTests(unittest.TestCase):
    def run_cli(self, name: str, format_name: str = "json"):
        return subprocess.run(
            [sys.executable, "-m", "irkit.cli", "--file", str(FIXTURES / name), "--format", format_name],
            capture_output=True, text=True, check=False,
        )

    def test_cli_json_from_fixture(self):
        result = self.run_cli("synthetic-case.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["case_state"], "triage_unverified")

    def test_cli_markdown_from_fixture(self):
        result = self.run_cli("synthetic-case.json", "markdown")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Timeline", result.stdout)

    def test_cli_benign_fixture(self):
        result = self.run_cli("benign-case.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["timeline"], [])

    def test_cli_stdin_reads_manifest(self):
        text = (FIXTURES / "synthetic-case.json").read_text(encoding="utf-8")
        p = subprocess.run([sys.executable, "-m", "irkit.cli"], input=text,
                           capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["case_id"], "LAB-CASE-001")

    def test_cli_invalid_json_does_not_repeat_secret(self):
        p = subprocess.run([sys.executable, "-m", "irkit.cli"], input='{"FAKE_SECRET_012": bad',
                           capture_output=True, text=True, check=False)
        self.assertEqual(p.returncode, 2)
        self.assertNotIn("FAKE_SECRET_012", p.stderr)


if __name__ == "__main__":
    unittest.main()
