# IAM-000 — Current Mac/UTM Linux Lab Baseline

**Status: PREPARED; Mac guest execution NOT RUN by this change.**
**Last documentation update:** 2026-11-17
**Timebox:** 20–30 minutes, with SEC01 and UBUNTU01 only.
**Purpose:** Re-establish current identity, network, service, and logging facts before adding new IAM controls.

## Existing historical evidence — not fresh validation

- Host: MacBook Air M3 / ARM64 / 8 GB using UTM.
- UTM network: private `ATLASHOME-LAB` and separate Shared/NAT interfaces as previously observed.
- `UBUNTU01`: historically `10.10.10.20`, lab target and rsyslog sender.
- `SEC01`: historically `10.10.10.50`, rsyslog receiver; prior TCP/514 listener observed on all addresses. **Interface exposure and isolation remain REVIEW, not PASS.**
- `KALI01`: historically `10.10.10.30`; not needed for this exercise.
- Historical cross-host telemetry: September purple-team validation and an October 11 tagged event. Neither proves present-day service health.
- `DC01` and `Win11-Client01`: NOT PRESENT in Mac UTM as of the last documented inventory. Do not mark domain-join, AD sign-in or SMB/NTFS verification PASS based on Windows V1 records.
- A separate offline IAM policy simulator exists in draft PR #14; its passing CI does not prove any VM state.

## Prerequisites and safety

Use only personally owned, isolated UTM guest consoles. First check available memory, VM state and the intended Host Only versus Shared/NAT adapters. Start **SEC01 and UBUNTU01 only**; stop if host memory or guest stability becomes a problem. No external scans, account disabling, passwords, firewall changes, new listeners or internet exposure. This exercise only reads local state.

The repository is public. **Do not commit unredacted shell output**, home-directory paths, tokens, passwords, real usernames or logs. Capture timestamps, commands and a redacted summary for portfolio evidence.

## Step 1: Open SEC01, observe (read-only)

From SEC01's UTM console, inspect the current hostname, local IPs and rsyslog service. If this repository exists on SEC01, use:

```bash
bash scripts/iam-linux-readonly-check.sh sec01
```

Otherwise run these equivalent commands directly in SEC01's terminal:

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
hostname
uname -m
id
ip -br -4 addr
systemctl is-active rsyslog
getent group sudo
ss -lnt
```

Record whether TCP/514 is listening and on which address(es). A `0.0.0.0:514` listener is an **exposure review item** until interface firewalling and actual reachability are assessed; do not change controls during this baseline.

## Step 2: Open UBUNTU01, observe (read-only)

If the repository is present:

```bash
bash scripts/iam-linux-readonly-check.sh ubuntu01
```

Otherwise use:

```bash
date -u '+%Y-%m-%dT%H:%M:%SZ'
hostname
uname -m
id
ip -br -4 addr
systemctl is-active rsyslog
getent group sudo
```

Notice that Linux user identity and sudo-group membership are only **evidence inputs**. Group membership does not prove the full set of effective sudo rules, account status or application permissions.

## Step 3: Verify central logging using the already prepared procedure

Follow [SOC-001 centralized telemetry triage](SOC_001_TELEMETRY_TRIAGE.md) in order. That runbook's `logger` action is a deliberately benign synthetic event, unlike the read-only IAM-000 observer. Check local receipt and, **only after discovering the actual destination**, corresponding SEC01 receipt.

Classify: PASS if local and remote event lineage is evidenced; PARTIAL if forwarding coverage differs; BLOCKED if the source, path or listener cannot be confirmed. Never equate a heartbeat with intrusion detection.

## Step 4: Explain the IAM relevance

Record what is known about (1) the Linux operator's identity, (2) local group entitlement, (3) service/telemetry health, and (4) the boundary between a local account and other identity providers. Do **not** interpret `getent group sudo` as proof of full enterprise IAM governance.

| Gate | Evidence to record | Initial status |
| --- | --- | --- |
| SEC01 reachable via its UTM console | UTM VM state and fresh timestamp | NOT_RUN |
| UBUNTU01 reachable via its UTM console | UTM VM state and fresh timestamp | NOT_RUN |
| Actual private/NAT interface addresses | Sanitized `ip -br -4 addr` | NOT_RUN |
| SEC01 rsyslog listener and interface review | `systemctl`, `ss` | NOT_RUN |
| Current local and remote syslog event lineage | SOC-001 evidence with timestamp | NOT_RUN |
| Linux user/group review | `id`, `getent group sudo` | NOT_RUN |
| DC01/Windows role readiness | Fresh Mac UTM inventory | BLOCKED pending rebuild |

## Decision gate

Once IAM-000 is recorded, proceed with [IAM-001 Linux identity and access review](IAM_001_LINUX_ACCESS_REVIEW.md), using only read-only observations. A later phase can provision a **dedicated fictional test account**, check expected/actual permissions, and safely deprovision it under an explicit rollback plan; never disable the sole `labadmin` or administrator account.

**Done means:** fresh observations and an evidence-linked explanation, not the mere presence of scripts or green GitHub Actions.
