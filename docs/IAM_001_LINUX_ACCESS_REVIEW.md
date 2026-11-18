# IAM-001 — Linux Identity & Access Review (guided lab)

**Status:** READY FOR MANUAL EXERCISE; not executed on Mac/UTM by this PR.
**Prerequisite:** Complete or honestly record blockers from [IAM-000](IAM_000_LIVE_BASELINE_2026-11-17.md).
**Roles:** UBUNTU01 = review target; SEC01 = optional evidence receiver. KALI01 and Windows VMs are not required.
**Duration:** approximately 20–30 minutes.

## Why this belongs in an IAM portfolio

A Linux host has *identities*, *authentication controls*, and *authorization policies* even without Active Directory. Learn what a local identity can access before attempting hybrid Windows/cloud IAM.

- **Identity:** a local username and its UID, known through NSS (`id`, `getent`).
- **Authentication:** proving control of that identity; this exercise never requests a password.
- **Authorization:** group memberships, filesystem mode bits/ACLs and sudo policy; these may differ from merely being able to log in.
- **Session:** an existing SSH/login shell is not necessarily ended just by making a future-login change.
- **Lifecycle:** an offboarding workflow must address all authorized accounts, group grants, sessions, services, owners and evidence without destroying records.

## Exercise A: read-only inventory on UBUNTU01

Use your owned VM console and the existing `labadmin` test operator. Do not edit `/etc/passwd`, `/etc/shadow`, `sudoers` or accounts.

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
whoami
id
getent passwd labadmin
getent group sudo
```

Questions to answer from **actual** output:
1. Does the account record exist? If not, record NOT_FOUND, rather than creating it.
2. What UID and primary/supplementary groups does the identity have?
3. Does membership in `sudo` appear? Does this alone prove every sudo command is allowed? **No:** policy can include other groups, direct sudoers rules and restrictions.
4. What further authorization evidence would be needed to determine effective access to a particular resource?

Optional if you are explicitly authorized to query administrator policy on this personally controlled VM:

```bash
sudo -l -U labadmin
```

This **lists** policy; it does not grant permissions. If the command requires an unexpected privilege or fails, document NOT_CHECKED and do not change policy to make the exercise pass.

## Exercise B: resource-specific access (read-only)

Choose only a **non-sensitive, ordinary lab-owned test directory** that already exists; do not choose `/etc/shadow`, sensitive user homes or actual company/customer data.

```bash
ls -ld /path/to/your/existing/lab-test-directory
namei -l /path/to/your/existing/lab-test-directory
```

Replace the placeholder with the verified existing path. These commands inspect directory ownership and permission components; they do not change them. If there is no appropriate test directory, record BLOCKED rather than creating or changing files without a separate exercise plan.

Explain why being a member of a group does not automatically mean a particular resource is readable. Distinguish the account's group membership from the target directory's effective permissions, including traversal through parent directories.

## Exercise C: hypothetical mover/leaver case (no VM changes)

A **fictional** employee `finance01` transfers from Finance to HR.

| Resource | Existing authorization | Expected after approved transfer | Verification evidence |
| --- | --- | --- | --- |
| Finance folder | Finance group grants read | Denied unless documented exception | Effective permissions plus an authorized access test |
| HR folder | HR group grants read | Read allowed after approval | Group policy and an authorized access test |
| General employee folder | Employees group grants read | Remains allowed | Effective permissions |
| Linux elevated commands | Separate sudo policy | Only if explicitly justified | Read-only effective sudo policy review |

List the approver, requested role change, exact group changes, freshness of the login session, and both **positive and negative** tests. Do not use another employee's password or enable a privileged account merely for testing.

For a fictional leaver, build an offboarding matrix:

| Identity surface | Control to review | Verification |
| --- | --- | --- |
| Local Linux account | Disable or expire sign-in under policy; retain audit records | Account state and authorized controlled test |
| Existing SSH/login session | Separate approved session termination | Session inventory and post-action state |
| AD/Entra identity (future Windows/cloud lab) | Disable authentication and handle token/session revocation | Separate directory and cloud audit evidence |
| VPN or independently managed app | Explicitly terminate sessions and revoke entitlement | Application/gateway-side evidence |

These are **reasoning exercises only**. No real `labadmin` account, connection or permission is disabled here. In particular, do not lock out your only administrator, terminate your sole management session, or alter your VM's firewall.

## Evidence template (do not commit raw identity records)

```text
Exercise: IAM-001 Linux identity review
Date/time UTC:
VM / role:
Operator (sanitized):
Git commit / runbook revision:
Identity source examined:
Account/group observations:
Resource policy inspected:
Expected access:
Observed access:
Evidence location (private):
Decision: PASS / REVIEW / FAIL / BLOCKED / NOT_CHECKED
What was NOT tested:
Next safe action:
```

### Acceptance gate

- **PASS:** The student can independently distinguish identity, authentication, group membership, effective authorization and existing sessions, and provides sanitized read-only evidence for the selected checks.
- **REVIEW:** Observed grants/denies differ from the documented intended matrix or effective authorization remains unclear.
- **BLOCKED:** VM inaccessible, no suitable test resource, permission to inspect unavailable, or prerequisites unresolved.
- **NOT_CHECKED:** No fresh measurement was performed.

This exercise does **not** claim working AD, Entra ID, GPO, SMB/NTFS permissions, successful offboarding or cloud session revocation. The next VM-changing exercise needs a dedicated disposable test identity, preapproved change/rollback plan and after-action verification.
