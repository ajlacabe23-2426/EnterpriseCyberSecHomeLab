# SOC Detection Engine V1 — Enterprise Cyber Lab V2

An **offline, defensively scoped security-operations training module** for owned lab telemetry. It turns sanitized sample UFW firewall-block and OpenSSH authentication logs into explainable triage alerts. It **does not** connect to SEC01 automatically, query a live host, block connections, or claim a real incident occurred.

## Why this project exists

- Understand firewall and login events from a Linux environment.
- Practice log normalization, time windows, source/target context, and detection engineering.
- Investigate possible false positives and gaps using evidence rather than assumptions.
- Demonstrate Python, tests, secure data-handling habits, and incident-report writing.

## Setup (MacBook or any Python 3.11+ machine)

No dependencies beyond the Python standard library. From the repository root:

~~~sh
cd projects/soc-detection-engine
python3 -m unittest discover -s soclab -p 'test_*.py' -v
python3 -m soclab.cli --file fixtures/synthetic-sec01.log
python3 -m soclab.cli --file fixtures/synthetic-benign.log
~~~

You may also pipe *sanitized, authorized* syslog lines to standard input:

~~~sh
python3 -m soclab.cli < fixtures/synthetic-sec01.log
~~~

Example output is JSON with event counts, skipped lines, and alerts. **Neither raw log text nor account names are echoed** by the report, but source/destination IPs and hostnames *are included*, so sanitize and review results before sharing any report.

## Rules (education-only thresholds)

| Rule ID | Trigger | Investigation focus |
| --- | --- | --- |
| repeated_firewall_blocks | ≥3 blocked UFW connections to one destination port, source, and host within 5 minutes | Legitimate troubleshooting vs unusual repeated connection patterns |
| multiple_blocked_ports | ≥3 distinct destination ports blocked from one source toward the same host/destination in 5 minutes | Authorized diagnostics vs unusual breadth |
| repeated_ssh_auth_failures | ≥3 failed SSH password authentications from one source to one host in 10 minutes | Account context and access controls |
| ssh_success_after_failures | SSH login succeeds following ≥3 recent failures from the same source and host within 10 minutes | Verify authorization and activity context; **not evidence by itself of compromise** |

All flags require human review and context. A batch emits only the earliest qualifying alert per rule/key; it is **not** a streaming intrusion-detection system, comprehensive intrusion coverage, or a production SIEM.

## Timestamp and file expectations

- Recommended: one syslog event per line beginning with a full timezone-aware ISO 8601 timestamp, e.g. `2026-09-04T13:00:00+00:00`.
- Legacy syslog timestamps without a year (e.g. `Sep  4 13:00:00`) require `--year 2026`. Use `--utc-offset-hours -5` only when that **correctly represents the log's own UTC offset**; daylight-saving differences across a period require separate batches.
- Unknown lines and unsupported formats are counted as **skipped**, never assumed benign.
- Batches are limited to **5 MB and 20,000 lines** to keep the learning workflow bounded.
- An event is parsed from its *text content*, not from a trusted transport envelope; future work should verify sender identity and central-log provenance before treating real evidence as authoritative.

## Your portfolio verification exercise

1. Run the two fictional fixtures locally; note which alerts appear and which do not.
2. Explain why the blocked-port exercise from the September 4 purple-team verification might trigger a benign detection.
3. Write a one-page case report containing: scope, assumptions, raw vs recognized event counts, alerts, root-cause hypotheses, alternate explanations, control recommendations, and limitations.
4. When at the MacBook, run the same engine **offline** against an exported and redacted copy of SEC01-owned log entries. Do not alter firewall rules or live services merely to generate an alert.
5. Compare timestamps and observed results with the [documented original purple-team exercise](../../docs/purple-team-workflow-validation-2026-09-04.md). Record differences, then add a regression test for any real defect.

**Do not commit** real user names, real IP addresses, tokens, raw private logs, screenshots containing sensitive data, or production system information. Keep private logs inside the ignored `private-logs/` directory and generated case reports inside ignored `reports/`; use sanitized, fictional summaries for GitHub evidence.

## Planned extensions

- Source and log-format coverage checks (including dropped-message awareness).
- An explicit evidence/timeline investigation workflow, with known-false-positive teaching cases.
- Rules tested against redacted SEC01 exports after local validation.
- Optional interface once command-line results are reliable.

This module is independent of PromptGuard and the software projects. No additional virtual machines, subscriptions, hosted security services, or production credentials are required.
