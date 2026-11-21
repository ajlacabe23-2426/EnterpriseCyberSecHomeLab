"""Educational negative tests: deny unknown, stale, and elevated requests by default."""
import json
import unittest
from datetime import datetime
from pathlib import Path
from iamlab.policy import evaluate

CASES = json.loads((Path(__file__).parent / "fixtures" / "synthetic-requests.json").read_text())
NOW = datetime.fromisoformat(CASES["as_of"].replace("Z", "+00:00"))


class IamPolicyTests(unittest.TestCase):
    def test_all_versioned_scenarios(self):
        for case in CASES["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(evaluate(case["request"], now=NOW), case["expected"])

    def test_empty_missing_and_invalid_request_fail_closed(self):
        for request in ({}, {"role": "helpdesk", "action": "read"},
                        {"role": None, "resource": "user_profile", "action": "read"},
                        {"role": [], "resource": "user_profile", "action": "read"}):
            with self.subTest(request=request):
                self.assertEqual(evaluate(request, now=NOW)["decision"], "DENY")

    def test_privileged_flags_must_be_actual_booleans(self):
        base = {"role": "identity_admin", "resource": "role_assignment", "action": "change",
                "mfa_verified": "true", "approval_confirmed": True,
                "self_target": False, "actor_id": "fictional-operator", "approver_id": "fictional-reviewer",
                "expires_at": "2026-11-17T19:00:00Z"}
        self.assertEqual(evaluate(base, now=NOW)["reason"], "MFA_REQUIRED")
        base["mfa_verified"] = True
        base["approval_confirmed"] = 1
        self.assertEqual(evaluate(base, now=NOW)["reason"], "HUMAN_APPROVAL_REQUIRED")

    def test_expiration_strictness_and_utc_clock(self):
        base = {"role": "identity_admin", "resource": "role_assignment", "action": "change",
                "mfa_verified": True, "approval_confirmed": True,
                "self_target": False, "actor_id": "fictional-operator", "approver_id": "fictional-reviewer"}
        for invalid in ("2026-11-17T20:00:00", "not-a-date", 55, "2026-02-30T20:00:00Z"):
            with self.subTest(invalid=invalid):
                self.assertEqual(evaluate({**base, "expires_at": invalid}, now=NOW)["reason"], "INVALID_EXPIRY")
        with self.assertRaises(ValueError):
            evaluate(base, now=NOW.replace(tzinfo=None))
        self.assertEqual(evaluate({**base, "expires_at": "2026-11-17T22:00:00Z"}, now=NOW)["decision"], "ALLOW")
        self.assertEqual(evaluate({**base, "expires_at": "2026-11-17T22:00:01Z"}, now=NOW)["reason"], "ELEVATION_TOO_LONG")


    def test_privileged_request_requires_explicit_target_and_independent_approver(self):
        base = {"role": "identity_admin", "resource": "role_assignment", "action": "change",
                "self_target": False, "actor_id": "fictional-operator",
                "approver_id": "fictional-reviewer", "mfa_verified": True,
                "approval_confirmed": True, "expires_at": "2026-11-17T19:00:00Z"}
        self.assertEqual(evaluate(base, now=NOW)["decision"], "ALLOW")
        for target_status in (None, "false", 0, 1):
            with self.subTest(target_status=target_status):
                self.assertEqual(evaluate({**base, "self_target": target_status}, now=NOW)["reason"], "SELF_TARGET_STATUS_REQUIRED")
        self.assertEqual(evaluate({**base, "self_target": True}, now=NOW)["decision"], "DENY")
        for approver in (None, "", "   ", 7):
            with self.subTest(approver=approver):
                self.assertEqual(evaluate({**base, "approver_id": approver}, now=NOW)["reason"], "APPROVER_IDENTITIES_REQUIRED")
        self.assertEqual(evaluate({**base, "approver_id": "fictional-operator"}, now=NOW)["reason"], "SELF_APPROVAL_PROHIBITED")
        self.assertEqual(evaluate({**base, "approver_id": " fictional-operator "}, now=NOW)["reason"], "SELF_APPROVAL_PROHIBITED")

if __name__ == "__main__":
    unittest.main()
