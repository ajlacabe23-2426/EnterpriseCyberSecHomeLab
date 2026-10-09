"""Offline test cases for conservative, evidence-based hardening checks."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from auditlab.audit import SCHEMA, audit_snapshot

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


def fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def by_id(report: dict) -> dict:
    return {finding["check_id"]: finding for finding in report["checks"]}


class SnapshotAuditTests(unittest.TestCase):
    def test_secure_fictional_snapshot_all_pass(self):
        report = audit_snapshot(fixture("secure-fictional.json"))
        self.assertEqual(report["summary"], {"pass": 8, "review": 0, "fail": 0, "not_checked": 0})
        self.assertEqual(report["coverage"]["checks_evaluated"], 8)
        self.assertEqual(report["mode"], "OFFLINE_READ_ONLY_SNAPSHOT")

    def test_review_snapshot_detects_issues_and_inactive_firewall_policy_is_not_checked(self):
        report = audit_snapshot(fixture("review-fictional.json"))
        outcomes = by_id(report)
        for key in ("permitrootlogin", "permitemptypasswords", "ufw_status", "uid_zero"):
            self.assertEqual(outcomes[key]["status"], "fail")
        for key in ("passwordauthentication", "sudo_group", "tcp_listeners"):
            self.assertEqual(outcomes[key]["status"], "review")
        self.assertEqual(outcomes["ufw_incoming"]["status"], "not_checked")
        self.assertEqual(report["summary"], {"pass": 0, "review": 3, "fail": 4, "not_checked": 1})

    def test_missing_data_never_generates_passes(self):
        report = audit_snapshot(fixture("incomplete-fictional.json"))
        self.assertEqual(report["summary"], {"pass": 0, "review": 0, "fail": 0, "not_checked": 8})
        self.assertEqual(report["coverage"]["source_sections_provided"], 0)

    def test_effective_root_login_prohibit_password_requires_review(self):
        report = audit_snapshot({"schema": SCHEMA, "ssh_effective": "permitrootlogin prohibit-password"})
        self.assertEqual(by_id(report)["permitrootlogin"]["status"], "review")

    def test_password_auth_yes_needs_review_not_automatic_fail(self):
        report = audit_snapshot({"schema": SCHEMA, "ssh_effective": "passwordauthentication yes"})
        self.assertEqual(by_id(report)["passwordauthentication"]["status"], "review")

    def test_duplicate_ssh_key_is_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "ssh_effective": "permitrootlogin yes\npermitrootlogin no\n"})
        self.assertEqual(by_id(report)["permitrootlogin"]["status"], "not_checked")

    def test_unknown_ssh_value_is_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "ssh_effective": "passwordauthentication sometimes"})
        self.assertEqual(by_id(report)["passwordauthentication"]["status"], "not_checked")

    def test_case_insensitive_effective_ssh_output(self):
        report = audit_snapshot({"schema": SCHEMA, "ssh_effective": "PermitRootLogin NO"})
        self.assertEqual(by_id(report)["permitrootlogin"]["status"], "pass")

    def test_active_firewall_with_default_allow_is_fail(self):
        report = audit_snapshot({"schema": SCHEMA, "ufw_status": "Status: active\nDefault: allow (incoming), allow (outgoing)"})
        self.assertEqual(by_id(report)["ufw_status"]["status"], "pass")
        self.assertEqual(by_id(report)["ufw_incoming"]["status"], "fail")

    def test_active_firewall_with_reject_default_passes(self):
        report = audit_snapshot({"schema": SCHEMA, "ufw_status": "Status: active\nDefault: reject (incoming), allow (outgoing)"})
        self.assertEqual(by_id(report)["ufw_incoming"]["status"], "pass")

    def test_no_firewall_default_means_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "ufw_status": "Status: active"})
        self.assertEqual(by_id(report)["ufw_incoming"]["status"], "not_checked")

    def test_firewall_inactive_never_passes_incoming_policy(self):
        report = audit_snapshot({"schema": SCHEMA, "ufw_status": "Status: inactive\nDefault: deny (incoming)"})
        self.assertEqual(by_id(report)["ufw_incoming"]["status"], "not_checked")

    def test_missing_root_uid_not_claimed_secure(self):
        report = audit_snapshot({"schema": SCHEMA, "passwd_text": "learner:x:1000:1000:Lab:/home/learner:/bin/bash"})
        self.assertEqual(by_id(report)["uid_zero"]["status"], "not_checked")

    def test_uid0_secondary_account_is_failure_without_usernames_in_report(self):
        report = audit_snapshot({
            "schema": SCHEMA,
            "passwd_text": "root:x:0:0:root:/root:/bin/bash\nFAKE_EXTRA_USER_782:x:0:0:Lab:/home/extra:/bin/bash",
        })
        self.assertEqual(by_id(report)["uid_zero"]["status"], "fail")
        self.assertNotIn("FAKE_EXTRA_USER_782", json.dumps(report))

    def test_malformed_account_list_is_not_checked(self):
        report = audit_snapshot({
            "schema": SCHEMA,
            "passwd_text": "root:x:0:0:root:/root:/bin/bash\nmalformed",
        })
        self.assertEqual(by_id(report)["uid_zero"]["status"], "not_checked")

    def test_missing_sudo_group_is_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "group_text": "staff:x:50:learner"})
        self.assertEqual(by_id(report)["sudo_group"]["status"], "not_checked")

    def test_sudo_group_members_are_counted_but_names_not_exposed(self):
        report = audit_snapshot({"schema": SCHEMA, "group_text": "sudo:x:27:FAKE_PRIV_USER_667,person2"})
        self.assertEqual(by_id(report)["sudo_group"]["status"], "review")
        self.assertNotIn("FAKE_PRIV_USER_667", json.dumps(report))
        self.assertIn("2 explicitly", by_id(report)["sudo_group"]["evidence_summary"])

    def test_duplicate_sudo_group_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "group_text": "sudo:x:27:\nsudo:x:27:user"})
        self.assertEqual(by_id(report)["sudo_group"]["status"], "not_checked")

    def test_wildcard_listener_review_not_automatic_failure(self):
        report = audit_snapshot({"schema": SCHEMA, "tcp_listening": "LISTEN 0 4096 [::]:22 [::]:*"})
        self.assertEqual(by_id(report)["tcp_listeners"]["status"], "review")

    def test_specific_lab_interface_listener_can_pass_scoped_check(self):
        report = audit_snapshot({"schema": SCHEMA, "tcp_listening": "LISTEN 0 256 10.10.10.20:22 0.0.0.0:*"})
        self.assertEqual(by_id(report)["tcp_listeners"]["status"], "pass")
        self.assertIn("reachability not verified", by_id(report)["tcp_listeners"]["evidence_summary"])

    def test_unparseable_listener_output_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA, "tcp_listening": "LISTEN bad"})
        self.assertEqual(by_id(report)["tcp_listeners"]["status"], "not_checked")

    def test_absent_listener_snapshot_not_checked(self):
        report = audit_snapshot({"schema": SCHEMA})
        self.assertEqual(by_id(report)["tcp_listeners"]["status"], "not_checked")

    def test_report_does_not_echo_raw_configuration_or_fake_markers(self):
        sample = fixture("secure-fictional.json")
        sample["group_text"] += "staff:x:50:FAKE_PRIVATE_MARKER_470\n"
        report = audit_snapshot(sample)
        payload = json.dumps(report)
        self.assertNotIn("FAKE_PRIVATE_MARKER_470", payload)
        self.assertNotIn("learner:x:", payload)
        self.assertNotIn("127.0.0.1:", payload)

    def test_unexpected_fields_rejected(self):
        with self.assertRaises(ValueError):
            audit_snapshot({"schema": SCHEMA, "secret": "not allowed"})

    def test_wrong_schema_rejected(self):
        with self.assertRaises(ValueError):
            audit_snapshot({"schema": "some-other-schema"})

    def test_non_object_input_rejected(self):
        with self.assertRaises(TypeError):
            audit_snapshot("unexpected")

    def test_non_string_section_rejected(self):
        with self.assertRaises(ValueError):
            audit_snapshot({"schema": SCHEMA, "passwd_text": ["root"]})

    def test_oversized_section_rejected(self):
        with self.assertRaises(ValueError):
            audit_snapshot({"schema": SCHEMA, "ssh_effective": "x" * 24001})

    def test_determinism(self):
        snapshot = fixture("review-fictional.json")
        self.assertEqual(audit_snapshot(snapshot), audit_snapshot(snapshot))


class CLITests(unittest.TestCase):
    def test_cli_secure_fixture(self):
        command = [sys.executable, "-m", "auditlab.cli", "--file", str(FIXTURES / "secure-fictional.json")]
        done = subprocess.run(command, check=False, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["summary"]["pass"], 8)

    def test_cli_stdin_incomplete_fixture(self):
        command = [sys.executable, "-m", "auditlab.cli"]
        done = subprocess.run(
            command, input=json.dumps(fixture("incomplete-fictional.json")),
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["summary"]["not_checked"], 8)

    def test_cli_invalid_json_does_not_echo_text(self):
        done = subprocess.run(
            [sys.executable, "-m", "auditlab.cli"],
            input='{"FAKE_SECRET_LITERAL_441": invalid',
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(done.returncode, 2)
        self.assertNotIn("FAKE_SECRET_LITERAL_441", done.stderr)


if __name__ == "__main__":
    unittest.main()
