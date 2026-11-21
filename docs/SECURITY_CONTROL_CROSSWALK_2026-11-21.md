# Homelab defensive security control crosswalk — 2026-11-21

**Purpose:** A bounded, evidence-first learning path from untrusted text to least-privilege authorization, identity review, telemetry, and incident analysis. No claim of live integration or production protection.

## Controls and their current evidence

| Control | GitHub evidence | Current trust claim | Missing manual verification |
| --- | --- | --- | --- |
| Prompt-injection indicators | `projects/promptguard-lab` (main); action-boundary draft PR #16 | Deterministic offline regression tests, fictional samples | Real-world generalization and actual agent tool enforcement **NOT VERIFIED** |
| Independent tool authorization | `projects/promptguard-lab/promptguard/action_boundary.py` (PR #16) | Simulation only: denied origins, scoped action, expiry; no dispatch | Authentication of backend origin, approval integrity, real authorization service **NOT RUN** |
| Least-privilege IAM decision | `projects/iam-policy-lab` (draft PR #14) | Fictional RBAC and privileged approval negative tests | AD/Entra bindings, actual user rights, session and token controls **NOT RUN** |
| Linux local identity assessment | `docs/IAM_000_LIVE_BASELINE_2026-11-17.md` and `docs/IAM_001_LINUX_ACCESS_REVIEW.md` (draft PR #15) | Read-only runbooks and shell-syntax guardrails | Fresh on-Mac UTM guest observations **NOT RUN** |
| Host hardening | `projects/linux-hardening-auditor` | Offline snapshot assessment with fictional fixtures | Current guest configuration and effective access **NOT VERIFIED** |
| Telemetry and triage | `projects/soc-detection-engine`; `docs/SOC_001_TELEMETRY_TRIAGE.md` | Offline detectors plus historical UTM observations; do not confuse them | Fresh tagged event lineage on UBUNTU01 to SEC01 **NOT RUN** |
| Incident reasoning | `projects/incident-response-toolkit` | Offline synthetic evidence report | Genuine logged prompt events or real IAM changes **NOT INTEGRATED** |
| Recovery | `docs/ROADMAP.md` | Recovery drill planned | Reproducible backup/restore acceptance **NOT RUN** |

Draft PRs are not merged into `main`; their tooling must not be described as live or integrated.

## Two-hour learning sequence (operator does the hands-on work)

**Session 1 — 25 minutes: PromptGuard.** Run the offline scanner and action-boundary demonstration on the correct branch. For four sample cases, predict the finding, policy decision, and why it is not a real tool call. Record one known false negative and one known false positive from the frozen toy dataset without modifying the holdout cases.

**Session 2 — 25 minutes: IAM.** Review PR #14's fictional permission matrix. Predict whether an auditor can change a role assignment, whether an identity administrator missing a reviewer can elevate, and whether an expired grant is valid. Run the policy unit tests and explain the requirement for *independently verified* identity and approval in any real system.

**Session 3 — 30 minutes: Read-only host inventory.** When the operator has the Mac/UTM guest available, use PR #15's IAM-000/IAM-001 instructions on the **owned VM only**. Do not create/disable accounts or change networking. Record redacted observations, actual dates, accessible resources, and NOT_CHECKED items; never commit raw `id`, `getent`, interface or log output to this public repo.

**Session 4 — 25 minutes: SOC telemetry.** Use the existing SOC-001 *benign* heartbeat and check corresponding SEC01 receipt as documented, only after identifying the actual configured destination. Record source timestamp, receiver timestamp, expected outcome, and whether event lineage succeeded. This is not evidence that prompt injection or IAM decisions were ingested by SOC.

**Session 5 — 15 minutes: Portfolio explanation.** Present a one-page case summary: threat model, boundary, expected/observed behavior, source revision, tests, missing gates, and an honest follow-up. Never substitute GitHub CI for real guest observations.

## Additional next engineering investments

1. **Verified approval provenance:** replace fictional IAM flags and request-origin labels with externally established subject, approver, role and scope checks if a real agent app is ever built.
2. **Event schema, not fabricated telemetry:** design a synthetic IAM denial event schema, then test offline ingestion/correlation with existing defensive parsers before any real integration.
3. **Backup and restore drill:** document which VM configuration snapshots are safe to preserve, produce a sanitized recovery checklist, and manually verify a disposable rollback before changing domain or identity services.
4. **Least-privilege evidence:** after the Mac guest baseline exists, select a disposable lab-owned identity and benign resource for an independently supervised positive/negative access test; do not risk the sole administrator.

**Completion rule:** Every PASS identifies the exact software revision or host measurement that proves it. Anything not observed is `NOT_RUN`, `NOT_VERIFIED`, `REVIEW`, or `BLOCKED`.
