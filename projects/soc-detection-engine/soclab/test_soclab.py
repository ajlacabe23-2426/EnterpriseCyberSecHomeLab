"""Synthetic offline verification: no live systems, network probes or secrets."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from soclab.detect import analyze_lines
from soclab.parser import MAX_INPUT_LINES, parse_line

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


def ufw(ts: str, source: str = "10.10.10.30", port: int = 8080, host: str = "UBUNTU01") -> str:
    return (
        f"2026-09-04T{ts}+00:00 {host} kernel: [UFW BLOCK] IN=enp0s2 "
        f"SRC={source} DST=10.10.10.20 PROTO=TCP SPT=50001 DPT={port}\n"
    )


def ssh(ts: str, source: str = "10.10.10.30", success: bool = False, host: str = "UBUNTU01") -> str:
    status = "Accepted publickey" if success else "Failed password"
    return f"2026-09-04T{ts}+00:00 {host} sshd[11]: {status} for learner from {source} port 39000 ssh2\n"


class ParserTests(unittest.TestCase):
    def test_parse_firewall_observation(self):
        event = parse_line(ufw("13:00:00"))
        self.assertIsNotNone(event)
        self.assertEqual(event.kind, "firewall_block")
        self.assertEqual(event.port, 8080)
        self.assertEqual(event.source, "10.10.10.30")

    def test_parse_ssh_failure_and_success(self):
        self.assertEqual(parse_line(ssh("13:00:00")).kind, "auth_failure")
        self.assertEqual(parse_line(ssh("13:01:00", success=True)).kind, "auth_success")

    def test_ignore_malformed_ip(self):
        self.assertIsNone(parse_line(ufw("13:00:00", "not_an_ip")))

    def test_ignore_invalid_port(self):
        self.assertIsNone(parse_line(ufw("13:00:00", port=0)))

    def test_iso_requires_explicit_timezone(self):
        self.assertIsNone(parse_line(ufw("13:00:00").replace("+00:00", "")))

    def test_normalizes_timezone_to_utc(self):
        e = parse_line(ufw("13:00:00").replace("+00:00", "+05:00"))
        self.assertEqual(e.when.isoformat(), "2026-09-04T08:00:00+00:00")

    def test_legacy_timestamp_requires_year(self):
        raw = "Sep  4 13:00:00 UBUNTU01 kernel: [UFW BLOCK] SRC=10.10.10.30 DST=10.10.10.20 DPT=8080"
        self.assertIsNone(parse_line(raw))
        e = parse_line(raw, assumed_year=2026, utc_offset_hours=-5)
        self.assertIsNotNone(e)
        self.assertEqual(e.when.isoformat(), "2026-09-04T18:00:00+00:00")

    def test_long_line_rejected(self):
        self.assertIsNone(parse_line(ufw("13:00:00") + "x" * 9000))

    def test_unknown_logs_skipped(self):
        self.assertIsNone(parse_line("2026-09-04T13:00:00+00:00 UBUNTU01 systemd[1]: Status OK"))


class DetectorTests(unittest.TestCase):
    def test_full_synthetic_fixture(self):
        lines = (FIXTURES / "synthetic-sec01.log").read_text().splitlines(True)
        report = analyze_lines(lines)
        self.assertEqual(report["source_lines"], 10)
        self.assertEqual(report["recognized_events"], 9)
        self.assertEqual(report["skipped_lines"], 1)
        self.assertEqual(report["event_counts"], {
            "firewall_block": 5, "auth_failure": 3, "auth_success": 1,
        })
        ids = {alert["rule_id"] for alert in report["alerts"]}
        self.assertEqual(ids, {
            "repeated_firewall_blocks",
            "multiple_blocked_ports",
            "repeated_ssh_auth_failures",
            "ssh_success_after_failures",
        })

    def test_benign_fixture_produces_no_alerts(self):
        lines = (FIXTURES / "synthetic-benign.log").read_text().splitlines(True)
        report = analyze_lines(lines)
        self.assertEqual(report["recognized_events"], 2)
        self.assertEqual(report["alerts"], [])

    def test_events_sorted_before_rule_matching(self):
        entries = [ufw("13:04:00"), ufw("13:00:00"), ufw("13:02:00")]
        report = analyze_lines(entries)
        self.assertEqual(
            [a["rule_id"] for a in report["alerts"]],
            ["repeated_firewall_blocks"],
        )

    def test_firewall_window_does_not_bridge_time_gap(self):
        report = analyze_lines([ufw("13:00:00"), ufw("13:02:00"), ufw("13:07:00")])
        self.assertEqual(report["alerts"], [])

    def test_firewall_source_and_host_are_isolated(self):
        report = analyze_lines([
            ufw("13:00:00", source="10.10.10.30"),
            ufw("13:01:00", source="10.10.10.31"),
            ufw("13:02:00", source="10.10.10.30", host="SEC01"),
        ])
        self.assertEqual(report["alerts"], [])

    def test_only_distinct_ports_qualify_for_multiple_port_indicator(self):
        report = analyze_lines([ufw("13:00:00"), ufw("13:00:01"), ufw("13:00:02")])
        self.assertEqual({a["rule_id"] for a in report["alerts"]}, {"repeated_firewall_blocks"})

    def test_ssh_failed_attempts_are_grouped_by_source_and_host(self):
        report = analyze_lines([
            ssh("13:00:00"),
            ssh("13:01:00", source="10.10.10.31"),
            ssh("13:02:00"),
        ])
        self.assertEqual(report["alerts"], [])

    def test_ssh_success_without_failures_produces_no_alert(self):
        self.assertEqual(analyze_lines([ssh("13:05:00", success=True)])["alerts"], [])

    def test_ssh_success_after_old_failures_not_flagged(self):
        report = analyze_lines([
            ssh("13:00:00"), ssh("13:01:00"), ssh("13:02:00"),
            ssh("13:15:00", success=True),
        ])
        ids = {a["rule_id"] for a in report["alerts"]}
        self.assertNotIn("ssh_success_after_failures", ids)
        self.assertIn("repeated_ssh_auth_failures", ids)

    def test_report_never_contains_raw_log_or_usernames(self):
        report = analyze_lines([
            ssh("13:00:00").replace("learner", "FAKE_USERNAME_1930"),
            ssh("13:01:00").replace("learner", "FAKE_USERNAME_1930"),
            ssh("13:02:00").replace("learner", "FAKE_USERNAME_1930"),
        ])
        self.assertNotIn("FAKE_USERNAME_1930", json.dumps(report))
        self.assertNotIn("sshd[", json.dumps(report))

    def test_reports_skipped_not_safe(self):
        report = analyze_lines(["not a syslog line\n"])
        self.assertEqual(report["recognized_events"], 0)
        self.assertEqual(report["skipped_lines"], 1)
        self.assertIn("not silently classified as safe", " ".join(report["limitations"]))

    def test_upper_bound_on_lines(self):
        with self.assertRaises(ValueError):
            analyze_lines(["\n"] * (MAX_INPUT_LINES + 1))

    def test_bad_timestamp_parameters_rejected(self):
        with self.assertRaises(ValueError):
            analyze_lines([], assumed_year=1800)
        with self.assertRaises(ValueError):
            analyze_lines([], utc_offset_hours=19)

    def test_deterministic_report(self):
        fixture = (FIXTURES / "synthetic-sec01.log").read_text().splitlines(True)
        self.assertEqual(analyze_lines(fixture), analyze_lines(fixture))

    def test_cli_can_analyze_fixture_as_file(self):
        cmd = [
            sys.executable, "-m", "soclab.cli",
            "--file", str(FIXTURES / "synthetic-sec01.log"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["recognized_events"], 9)

    def test_cli_can_read_stdin(self):
        cmd = [sys.executable, "-m", "soclab.cli"]
        result = subprocess.run(cmd, input=ssh("13:04:00"), capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["recognized_events"], 1)


if __name__ == "__main__":
    unittest.main()
