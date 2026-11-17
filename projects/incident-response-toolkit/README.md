# Incident Response Toolkit V1 — evidence-first casework

A small **offline Python learning module** for the Enterprise Cyber Lab V2 portfolio.
It turns *fictional, sanitized* security findings into a timeline, provenance
references, configuration review, and a case report with explicit open questions.

Its purpose is hands-on familiarity with junior incident-response and SOC
analyst workflows. It does **not** claim a compromise, contact a host,
search live logs, execute remediation, or act as a production incident platform.

## Run locally (Python 3.11+)

From the repository root:

~~~bash
cd projects/incident-response-toolkit
python3 -m unittest discover -s irkit -p 'test_*.py' -v
python3 -m irkit.cli --file fixtures/synthetic-case.json
python3 -m irkit.cli --file fixtures/synthetic-case.json --format markdown
python3 -m irkit.cli --file fixtures/benign-case.json --format markdown
~~~

Only Python standard-library modules are used; no dependencies or accounts needed.

## What's in a case report?

- **Case state:** always `triage_unverified`, never "confirmed intrusion" just because a detector flagged a pattern.
- **Source provenance:** SHA-256 fingerprints of JSON-normalized source reports (not forensic chain-of-custody proof).
- **Timeline:** evidence references and timestamps from the SOC report or specifically labeled analyst inputs; no timestamps are invented.
- **Undated configuration findings:** Linux hardening results remain undated by default, avoiding false chronological claims.
- **Open questions:** rule-specific investigation tasks and configuration relevance checks, not conclusions.
- **Review gates:** check authorization, compare benign explanations, independently verify evidence, and record approved recovery/retests.

Outputs intentionally omit arbitrary report text, source/destination IPs,
hostnames and usernames. However, the original input manifests may contain
sensitive source data: **never commit raw exports or real incidents** to the
public GitHub repository.

## Input contract

The case manifest JSON uses schema `incident-case-input-v1` and fields:

| Field | Required | Description |
| --- | --- | --- |
| `schema` | yes | Must be `incident-case-input-v1` |
| `case_id` | yes | Uppercase alphanumeric/hyphen case ID, 3–40 chars |
| `soc_report` | no | Existing SOC Detection Engine V1 JSON report (`soc-detection-lab-v1`) |
| `audit_report` | no | Existing Linux Hardening Auditor V1 JSON report (`linux-hardening-report-v1`) |
| `audit_reviewed_at_utc` | no | Explicit analyst review time, if an audit report exists; *not* a claim about source capture time |
| `analyst_events` | no | Up to 50 labeled fictional events, each with `evidence_id`, timezone-aware `timestamp_utc`, and `kind` |

Supply at least one of `soc_report`, `audit_report` or one analyst event.
Supported analyst event kinds are `analyst_review`, `approved_change`
and `retest`. These are *analyst-supplied claims*; the program does
not independently confirm that anyone performed an action.

The SOC report must contain recognized/skipped-line counts and supported
alerts with bounded dates and event counts. The audit report's individual
check statuses must match any included summary. Unexpected case fields,
unknown rules or unsupported event kinds are rejected.

Input JSON size is limited to 256 KB; generated outputs are printed only to
standard output. Nothing is saved automatically.

## Why these are separate components

| Tool | Evidence created by that tool | What is *not* proven |
| --- | --- | --- |
| SOC Detection Engine V1 | Log-pattern alerts and observed time windows | That an attack occurred |
| Linux Hardening Auditor V1 | Configuration observations from supplied snapshots | That live settings remain the same |
| Incident Response Toolkit V1 | Case timeline, evidence cross-references and investigation questions | Compromise, remediation success or formal forensic custody |

The toolkit consumes the **existing JSON report schemas** without importing
either upstream tool or altering their feature branches. That allows remote
coding and CI checks even while their separate PRs await review.

## Portfolio exercise: reconstruct a fictional incident

1. Read `fixtures/synthetic-case.json` and inspect the alerts and the hardening check status.
2. Generate a Markdown case report and explain why an SSH-success event **may** be authorized despite earlier failures.
3. Identify which timeline times came from aggregated observations and which were added by an analyst.
4. Point out one NOT_CHECKED setting, propose evidence needed to investigate it, and explain why it is not automatically safe or unsafe.
5. Compare against the benign fixture to demonstrate a non-incident case.
6. Save only fictional reports and sanitized screenshots as public portfolio evidence.

**MacBook milestone:** Eventually run the standalone SOC engine and hardening
auditor against privately reviewed/redacted observations from your owned
KALI01 / UBUNTU01 / SEC01 lab. Import only sanitized JSON results into a
case manifest locally. Verify formats, timezones, and interpretations yourself
and keep source evidence private.

## Limits and safe handling

- No external services, model calls, paid APIs, shell execution, host scans, or remote connections.
- No automated containment, credential changes, firewall edits or remediation.
- Only typed categories and safe preset descriptions are emitted; raw evidence and arbitrary free text are not echoed.
- SHA-256 fingerprints make changes detectable in **supplied JSON objects**; they are not signed evidence or a legal chain-of-custody.
- Treat all results as educational triage pending independent evidence.
- Keep private working material outside this public repository or inside
  the ignored `private-cases/` and `reports/` directories.

Future iterations can add a controlled analyst review sheet, explicit
MITRE ATT&CK mapping for carefully evidenced behaviors, and a local
dashboard after this offline data model is verified against the lab.
