<p align="center">
  <img src="./assets/project-banner.svg" alt="Enterprise Cyber Lab V2" width="100%" />
</p>

# Enterprise Cyber Lab V2

**MacBook migration in progress · Original VM roles and accomplishments preserved · First manual purple-team workflow verified**

Enterprise Cyber Lab V2 continues the original enterprise cybersecurity homelab on
an Apple Silicon MacBook using UTM. The goal is to retain the original Windows,
Linux, identity, networking and access-control work, then add repeatable purple-team
exercises with evidence of detection, remediation and retesting.

## Current direction

- **Host:** MacBook Air M3, ARM64, 8 GB unified memory, using UTM.
- **Scope:** retain the original four VM roles; add the SEC01 logging/detection role.
- **Network:** private `ATLASHOME-LAB` plus shared/NAT connectivity where needed.
- **Domain target:** preserve `atlasiqlab.local` and the original identity/access-control design.
- **Status:** migration and revalidation in progress. The Linux red/target/blue path is now operational and the first manual purple-team workflow has been verified. Original Windows/VirtualBox results remain V1 evidence; they are not proof that the same Windows/AD controls already work on the Mac.

## Dedicated machine responsibilities

| Machine | Assigned work |
| --- | --- |
| MacBook | Entire Enterprise Cyber Lab V2: original VM roles, SEC01 and purple-team practice |
| Lenovo | AtlasIQ, Projects 6 and 7, and eventually Project 5; original Windows lab VMs will be removed by AJ |

This is a complete lab move, not a lab split across two hosts. The purpose is to
reduce the RAM pressure experienced on the Lenovo and dedicate the Mac to hands-on
lab practice. VM removal is planned, not performed by this documentation update.
The Mac's actual available memory and workload performance will be measured during
practice; total installed RAM alone does not establish how many VMs run comfortably.

## VM continuity

| Original VM / role | V2 purpose | Mac migration status |
| --- | --- | --- |
| DC01 | Active Directory, domain identity and DNS | Preserve role and domain; Mac guest implementation and validation pending |
| Win11-Client01 | Windows domain workstation and access-control testing | Preserve role; rebuild/transfer and domain rejoin validation pending |
| UBUNTU01 | Linux administration, SSH and controlled lab target | Ubuntu ARM64 built; SSH, Internet/DNS, dual-NIC configuration, UFW enforcement and firewall-log generation verified |
| Kali01 / KALI01 | Security testing workstation for owned lab targets | Built and operational on `10.10.10.30`; scoped Nmap testing against UBUNTU01 verified |
| SEC01 | Centralized logging, detection and blue-team workstation/server | Built and operational on `10.10.10.50`; centralized rsyslog TCP/514 ingestion from UBUNTU01 and UFW event correlation verified |

V2 preserves the original VM roles and work. Any hostname changes will be recorded
explicitly rather than silently replacing the original inventory. The five-role
inventory remains the target; simultaneous runtime allocations will be checked
against the actual 8 GB host.

## Migration checkpoint — 2026-09-02

UBUNTU01 has shared/NAT address `192.168.64.2` and lab address `10.10.10.20/24`
on `enp0s2`, as reported during the Mac build. Kali reached its desktop and a
successful ping was reported after connectivity troubleshooting.

**V2 addressing:** use a fresh, unique address plan for the VMs on the Mac.
Retired Lenovo VM addresses are historical references, not a cross-host conflict.
The rebuilt Windows workstation and Ubuntu still need distinct addresses within
the Mac's shared lab subnet; old IP assignments do not have to be preserved.

[Migration and revalidation checklist](docs/ENTERPRISE_CYBER_LAB_V2.md)

## Purple team — operational V1 checkpoint

The purple team coordinates three roles within the owned, isolated lab:

| Role | Responsibility | Evidence |
| --- | --- | --- |
| Red team | Run a scoped, repeatable lab security test | Target, expected behavior and test timestamps |
| Blue team | Observe telemetry, investigate and improve controls | Logs, detection result and remediation |
| Verifier | Repeat the same test and check expected allowed/denied behavior | Before/after result, residual gaps and retest outcome |

Each exercise follows **test → detect → analyze → change → retest → restore → verify**.
A finding is closed only when its expected outcome is verified.

### Verified workflow — 2026-09-04

The first complete manual purple-team workflow is now verified across:

```text
KALI01 10.10.10.30
        ↓ scoped Nmap probes
UBUNTU01 10.10.10.20
        ↓ UFW block + log
SEC01 10.10.10.50
        ↓ centralized evidence
Verifier retest
```

The exercise proved the observable state transition for TCP/8080:

```text
FILTERED → CLOSED → OPEN → FILTERED
```

This was achieved by changing one control at a time: baseline UFW deny, temporary
firewall allow with no listener, temporary HTTP listener, then full restoration of
the original secure state. SEC01 received the matching UFW telemetry and the final
Kali retest confirmed that TCP/8080 returned to filtered.

[Full purple-team workflow validation — 2026-09-04](docs/purple-team-workflow-validation-2026-09-04.md)

## Preserved original work

- Windows Server, AD DS, DNS and the `atlasiqlab.local` domain.
- Users, groups, organizational units, RBAC and share-permission work.
- Dual-NIC networking, SSH and Linux administration.
- Multihomed domain-controller DNS troubleshooting and remediation.
- Existing scripts, configuration records, validation notes and evidence.

Previously open Windows/AD checks remain open: domain-user authentication and
effective SMB/NTFS access on the rebuilt V2 Windows roles. Centralized Linux
telemetry and one repeatable detection/remediation/retest exercise are now verified.

## Documentation and evidence

- [V2 migration, scope and purple-team plan](docs/ENTERPRISE_CYBER_LAB_V2.md)
- [Purple-team workflow validation — 2026-09-04](docs/purple-team-workflow-validation-2026-09-04.md)
- [Original V1 overview](docs/V1_OVERVIEW.md)
- [Portfolio case study and V1 accomplishments](docs/PORTFOLIO_CASE_STUDY.md)
- [Original core network validation — 2026-08-27](docs/core-network-validation-2026-08-27.md)
- [Evidence index](evidence/README.md)

The existing repository URL remains stable so earlier links and history continue
to work. The project display name and current documentation are Enterprise Cyber Lab V2.
