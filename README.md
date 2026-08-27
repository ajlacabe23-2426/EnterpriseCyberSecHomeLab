# EnterpriseCyberSecHomeLab

A hands-on enterprise cybersecurity homelab focused on Windows administration, Active Directory, networking, access control, troubleshooting, validation, and security operations.

## Current recovery objective

Restore and verify the network path between `CLIENT01` and the domain controller `DC01` before making any DNS or domain-join changes.

Known lab targets:
- Domain: `atlasiqlab.local`
- Domain controller: `DC01`
- DC01 lab IP: `10.10.10.10/24`
- VirtualBox internal network: `ATLASHOME-LAB`

## Recovery workflow

1. Inspect host-side VirtualBox network configuration.
2. Collect CLIENT01 network state.
3. Collect DC01 network/service state.
4. Isolate the failing layer.
5. Apply the smallest remediation.
6. Verify IP connectivity, DNS, AD ports, and domain discovery.
7. Save evidence and document the root cause.

## Repo layout

- `scripts/collect-client01.ps1` — read-only client diagnostics
- `scripts/collect-dc01.ps1` — read-only DC diagnostics
- `scripts/verify-domain-path.ps1` — end-to-end validation
- `docs/NETWORK_RECOVERY_RUNBOOK.md` — recovery procedure and decision tree
- `docs/CURRENT_STATE.md` — known state and completion criteria
- `evidence/` — local evidence destination; diagnostic text files are intentionally ignored by Git

> The diagnostic scripts do not change network settings. Remediation should only happen after the failed layer is identified.
