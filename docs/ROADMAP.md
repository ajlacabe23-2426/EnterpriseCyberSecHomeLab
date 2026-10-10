# Enterprise Cybersecurity Homelab roadmap

Updated: 2026-10-10
Stage: Apple Silicon Mac/UTM migration and defensive learning portfolio.

## Product truth

README preserves earlier Windows/VirtualBox work separately from the Mac migration. Do not treat historical V1 evidence as V2 verification. Mac-based role/resource/network validation requires host-local evidence.

## NOW (ordered)

1. **Mac UTM topology inventory** — verify actual VM roles, NAT/private network isolation, RAM limits, addresses (without posting secrets), and safe teardown. Record machine-verified versus planned status.
2. **Defensive prompt-injection guard lab** — synthetic prompts and safe documents, expected detections, benign false-positive fixtures, versioned rules and repeatable defensive tests.
3. **Purple-team detection evidence** — controlled test event -> ingest/log -> alert -> investigation -> remediation -> retest with redacted screenshots and timestamps.

## NEXT

- Windows/identity role continuity revalidated on Mac subject to actual resource performance.
- Small publishable resume demonstrations with ethical scope, clear expected vs observed evidence, and reproducible runbooks.
- Safe backup/recovery drills for lab configuration.

## LATER / PARKED

- Larger VM footprint and integrations only after host resources are measured; never attack external networks or real users.

## Release gates

Local authorization and isolation, reproducible fixtures, no secrets in logs, harmless test events, host-observed outcomes. Software-only changes can be reviewed remotely, but VM verification cannot be claimed without Mac execution evidence.
