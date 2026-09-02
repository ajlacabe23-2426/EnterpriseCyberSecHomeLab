<p align="center">
  <img src="./assets/project-banner.svg" alt="Enterprise Cyber Lab V2" width="100%" />
</p>

# Enterprise Cyber Lab V2

**MacBook migration in progress · Original VM roles and accomplishments preserved · Purple team planned**

Enterprise Cyber Lab V2 continues the original enterprise cybersecurity homelab on
an Apple Silicon MacBook using UTM. The goal is to retain the original Windows,
Linux, identity, networking and access-control work, then add repeatable purple-team
exercises with evidence of detection, remediation and retesting.

## Current direction

- **Host:** MacBook Air M3, ARM64, 8 GB unified memory, using UTM.
- **Scope:** retain the original four VM roles; add the planned SEC01 logging/detection role.
- **Network:** private `ATLASHOME-LAB` plus shared/NAT connectivity where needed.
- **Domain target:** preserve `atlasiqlab.local` and the original identity/access-control design.
- **Status:** migration and revalidation in progress. Original Windows/VirtualBox results
  remain V1 evidence; they are not proof that the same controls already work on the Mac.

## VM continuity

| Original VM / role | V2 purpose | Mac migration status |
| --- | --- | --- |
| DC01 | Active Directory, domain identity and DNS | Preserve role and domain; Mac guest implementation and validation pending |
| Win11-Client01 | Windows domain workstation and access-control testing | Preserve role; rebuild/transfer and domain rejoin validation pending |
| UBUNTU01 | Linux administration, SSH and controlled lab target | Ubuntu ARM64 built; SSH, Internet/DNS and dual-NIC configuration reported verified |
| Kali01 / KALI01 | Security testing workstation for owned lab targets | Desktop reached and connectivity success reported; exact V2 network/SSH evidence still to capture |
| SEC01 | Centralized logging, detection and blue-team workstation/server | Planned addition; not yet verified as built |

V2 preserves the original VM roles and work. Any hostname changes will be recorded
explicitly rather than silently replacing the original inventory. The five-role
inventory remains the target; simultaneous runtime allocations will be checked
against the actual 8 GB host.

## Migration checkpoint — 2026-09-02

UBUNTU01 has shared/NAT address `192.168.64.2` and lab address `10.10.10.20/24`
on `enp0s2`, as reported during the Mac build. Kali reached its desktop and a
successful ping was reported after connectivity troubleshooting; its exact V2
address and successful SSH session are not yet recorded here.

**Address reconciliation required:** the original Windows client used
`10.10.10.20`, while V1 Ubuntu used `10.10.10.30`. Do not assign the old Windows
client address unchanged alongside the new Ubuntu. Record a unique V2 address
plan before reconnecting the complete inventory.

[Migration and revalidation checklist](docs/ENTERPRISE_CYBER_LAB_V2.md)

## Planned purple team

The purple team coordinates three roles within the owned, isolated lab:

| Role | Responsibility | Evidence |
| --- | --- | --- |
| Red team | Run a scoped, repeatable lab security test | Target, expected behavior and test timestamps |
| Blue team | Observe telemetry, investigate and improve controls | Logs, detection result and remediation |
| Verifier | Repeat the same test and check expected allowed/denied behavior | Before/after result, residual gaps and retest outcome |

Each exercise follows **scope → test → observe → remediate → retest → document**.
A finding is closed only when its expected outcome is verified. The purple-team
workflow is planned; it is not yet claimed as operational.

## Preserved original work

- Windows Server, AD DS, DNS and the `atlasiqlab.local` domain.
- Users, groups, organizational units, RBAC and share-permission work.
- Dual-NIC networking, SSH and Linux administration.
- Multihomed domain-controller DNS troubleshooting and remediation.
- Existing scripts, configuration records, validation notes and evidence.

Previously open checks remain open: domain-user authentication, effective SMB/NTFS
access, centralized telemetry and repeatable incident/detection exercises.

## Documentation and evidence

- [V2 migration, scope and purple-team plan](docs/ENTERPRISE_CYBER_LAB_V2.md)
- [Original V1 overview](docs/V1_OVERVIEW.md)
- [Portfolio case study and V1 accomplishments](docs/PORTFOLIO_CASE_STUDY.md)
- [Original core network validation — 2026-08-27](docs/core-network-validation-2026-08-27.md)
- [Evidence index](evidence/README.md)

The existing repository URL remains stable so earlier links and history continue
to work. The project display name and current documentation are Enterprise Cyber Lab V2.
