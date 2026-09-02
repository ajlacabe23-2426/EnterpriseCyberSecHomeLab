# Enterprise Cyber Lab V2 — migration and purple-team plan

Decision recorded: 2026-09-02. AJ has officially selected the MacBook as the new
lab host. V2 retains the original VM roles, configurations, accomplishments and
learning objectives while adding a planned purple-team workflow.

## Dedicated machine responsibilities

| Machine | Assigned work |
| --- | --- |
| MacBook | Entire Enterprise Cyber Lab V2: original VM roles, planned SEC01 and purple-team practice |
| Lenovo | AtlasIQ, Projects 6 and 7, and eventually Project 5; original Windows lab VMs will be removed by AJ |

This is a complete lab move, not a lab split across two hosts. The purpose is to
reduce the RAM pressure experienced on the Lenovo and dedicate the Mac to hands-on
lab practice. VM removal is planned, not performed by this documentation update.
The Mac's actual available memory and workload performance will be measured during
practice; total installed RAM alone does not establish how many VMs run comfortably.

## Host and implementation status

The reported host is a MacBook Air M3 (ARM64), 8 GB unified memory, using UTM.
This supersedes the earlier tentative assumption of a 16 GB Mac. Keep the complete
four original VM roles plus the planned SEC01 role; measure resource use and run
exercise-specific subsets as needed rather than silently reducing the inventory.

This is a migration/rebuild with functional parity as its acceptance criterion.
Do not assume old VirtualBox disks or x86 guest images will run unchanged. Record
the guest architecture and implementation selected for each role, particularly
the Windows Server/domain-controller role, before claiming it is transferred.

| Role | Historical V1 identity/address | Recorded V2 state |
| --- | --- | --- |
| Domain controller / DNS | DC01, `10.10.10.10` | Domain and role retained as requirements; guest choice/address verification pending |
| Windows workstation | Win11-Client01, `10.10.10.20` | Pending; assign a unique address within the Mac lab |
| Linux server | UBUNTU01, `10.10.10.30` | ARM64 Ubuntu; NAT `192.168.64.2`; LAB `10.10.10.20/24`, `enp0s2`; SSH/Internet/DNS/dual NIC reported verified |
| Security workstation | Kali01 | KALI01 desktop reached; successful connectivity reported; exact V2 IP, routes and SSH evidence pending |
| Logging / detection | SEC01, planned | Planned blue-team role; no completed installation claimed |

The original domain is `atlasiqlab.local`. Historical hostnames remain the inventory
reference until any new names are explicitly verified. Old screenshots and IPs
must remain labeled V1.

## Carry-forward checklist

- [ ] Preserve the original VM backups, scripts, configuration exports and evidence.
- [ ] Record each guest's architecture, OS, hostname, RAM and disk allocation.
- [ ] Define unique V2 private addresses on the Mac; historical Lenovo IPs need not be retained.
- [ ] Verify each NIC, subnet, default route, DNS resolver and required connectivity.
- [ ] Restore or rebuild the AD/DNS role and verify `atlasiqlab.local` resolution.
- [ ] Recreate/restore the existing OU, users, groups and membership relationships.
- [ ] Validate Windows domain membership and domain-user authentication.
- [ ] Carry forward shares and NTFS RBAC; verify effective SMB and filesystem access
      with allowed and denied users. Preserve unresolved permission findings.
- [ ] Revalidate SSH, Linux administration and the original DNS remediation lessons.
- [ ] Capture KALI01 address/route and actual SSH evidence, beyond successful ping.
- [ ] Establish SEC01 telemetry ingestion and confirm source timestamps/host identity.
- [ ] Complete and document the first purple-team exercise and verifier retest.
- [ ] Mark each role and control complete only with fresh V2 evidence.

Existing V1 validation records remain historical proof of work. Reported Mac
checkpoints are recorded here without claiming fresh remote access to those VMs.

## Purple-team workflow — planned

Use only owned lab systems and explicitly scoped test targets. Keep test traffic
on the intended private lab network. Shared/NAT connectivity supports administration
and updates; it does not enlarge the exercise scope.

1. **Scope:** identify the VM, control, expected result and recovery point.
2. **Red team:** reproduce a controlled test against the approved lab target.
3. **Blue team:** inspect logs/detections, explain any gap and improve the control.
4. **Verifier:** repeat the same test and an allowed-use check after the change.
5. **Document:** retain before/after evidence, timestamps, findings and residual gaps.

Initial exercise themes: failed-login visibility, SMB least-privilege checks and
firewall allowed/denied behavior. Choose the first exercise only once its target
and telemetry are verified. No external scanning or production testing is implied.

## Exercise record template

- Exercise ID/date and lab version:
- Authorized VM/target and control:
- Expected allowed and denied behavior:
- Red-team test and timestamp:
- Blue-team logs, detection and interpretation:
- Remediation and recovery notes:
- Verifier retest and normal-use result:
- Evidence paths:
- Outcome: pass / fail / blocked / not tested:
- Remaining gaps and next action:

## Completion definition

V2 reaches parity when all original roles and previously completed workflows are
restored or equivalently rebuilt and independently revalidated on the Mac host.
The purple-team addition is complete only after a documented test, observation,
remediation and retest cycle. Neither completion is implied by this documentation update.
