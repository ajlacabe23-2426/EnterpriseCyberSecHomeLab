# Homelab — Evidence and learning map

Task ID: LAB-EVIDENCE-MAP-2026-10-12
Status: VERIFYING
Risk Tier: TIER_2 (loopback server and evidence-state presentation)
Base SHA: 563bc45d1592168ee3b2ac84a0ed1f2c68d62a6c
Base PR: #9 governance/current Mac handoff; other feature PRs remain independent.

## Objective
Apply the user-authorized 3D structure idea to the homelab: inspect VM/network topology, trace telemetry and offline code tools, and learn firewall/listener behavior through a harmless browser simulation.

## Scope
`projects/homelab-map/`, `.github/workflows/homelab-map.yml`, this task record, root README link. No existing VM scripts or tools modified.

## Acceptance
- Map preserves source dates and narrow observed/configured/review/pending/blocked/open-PR states. Current receipt is not a full detection/isolation PASS; historical V1/V2 evidence is not relabeled current.
- Read-only Python standard-library loopback server; no uploads, raw logs, credentials, scans, external API/model calls or persistence.
- Interactive 3D/flat views, node controls, evidence details, code/source links, telemetry tracing and synthetic port-state simulation work in actual Chromium and mobile-sized viewport.
- Unit, negative HTTP, manifest/provenance and browser acceptance checks pass on frozen candidate; exact-head GitHub CI.

## Non-goals
No merges, VM/network/firewall changes, exposure of a remote service, live detection integration, hosted deployment or spending. Windows roles remain absent/blocked. Open PR tools are not imported or described as integrated.

## Gates
Python unittest; JavaScript syntax and model tests; actual Chromium loopback acceptance using only the curated snapshot; manual source-status review; exact-candidate CI. Mac/UTM acceptance remains NOT_RUN by this implementation.
