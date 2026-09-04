# Purple-Team Workflow Validation — 2026-09-04

## Status

**VERIFIED — Manual Purple-Team Workflow V1 complete**

This record documents the first completed end-to-end purple-team exercise in the MacBook/UTM version of Enterprise Cyber Lab V2. The exercise was limited to the owned, isolated `ATLASHOME-LAB` environment and used benign network-service testing only.

## Systems used

| Role | Host | Lab address | Purpose |
| --- | --- | --- | --- |
| Red-team workstation | KALI01 | `10.10.10.30` | Generate scoped Nmap probes against the owned Ubuntu target |
| Target / control | UBUNTU01 | `10.10.10.20` | Enforce UFW policy, generate firewall telemetry, and host a temporary test service |
| Blue-team / logging | SEC01 | `10.10.10.50` | Receive centralized Ubuntu/UFW logs over rsyslog TCP/514 |

## Objective

Prove the complete manual workflow:

**Test → Detect → Analyze → Change → Retest → Restore → Verify**

The exercise specifically tested whether the lab could correlate what the red-team system observed with what the target firewall logged and what the blue-team logging server received.

## Phase 1 — Baseline test and detection

KALI01 scanned selected TCP ports on UBUNTU01, including ports `80`, `443`, and `8080`.

Observed result from Kali:

- tested ports were reported as **filtered** under the baseline firewall policy;
- this indicated that the probes were not receiving normal host/service responses.

Observed result on UBUNTU01:

- UFW was active;
- default inbound policy was deny;
- OpenSSH remained the intended inbound exception;
- live firewall logging showed `[UFW BLOCK]` events;
- the events identified `SRC=10.10.10.30` and `DST=10.10.10.20` with destination ports matching the Kali probes.

Observed result on SEC01:

- the same UFW block events appeared under the centralized remote-log path for UBUNTU01;
- this verified that the Ubuntu → SEC01 rsyslog pipeline was carrying the firewall telemetry into the blue-team system.

### Phase 1 result

**PASS** — Red-team activity, target-side blocking, and blue-team telemetry were correlated successfully.

## Phase 2 — Firewall allowed, no service listening

A temporary UFW allow rule was added for TCP/8080 on UBUNTU01 while no application was listening on that port.

KALI01 repeated the test against TCP/8080.

Observed result:

- `8080/tcp` changed from **filtered** to **closed**.

This demonstrated that allowing a port through a firewall does not make the port open by itself. The host was reachable at that port, but there was no listening service.

### Phase 2 result

**PASS** — Firewall behavior and service-listener state were successfully distinguished.

## Phase 3 — Temporary service started

A temporary Python HTTP server was started on UBUNTU01 and bound to the private lab interface:

```text
10.10.10.20:8080
```

KALI01 repeated the same TCP/8080 test.

Observed result:

- `8080/tcp` changed from **closed** to **open**.

This confirmed the combined condition required for an open port in this lab: the network path and firewall must permit the traffic, and a service must be listening.

### Phase 3 result

**PASS** — The same port was observed as open only after the service listener existed.

## Phase 4 — Restore and verifier retest

The temporary HTTP server was stopped and the temporary UFW allow rule for TCP/8080 was removed.

KALI01 repeated the same test one final time.

Observed result:

- `8080/tcp` returned to **filtered**.

UFW logging was then returned to the normal low setting.

### Restored baseline

- UFW active;
- default inbound policy: deny;
- OpenSSH allowed;
- no temporary 8080 allow rule;
- no temporary HTTP service;
- TCP/8080 externally observed from KALI01 as filtered.

### Phase 4 result

**PASS** — The control was restored and the verifier retest reproduced the secure baseline.

## What this exercise proved

The lab now has a manually verified purple-team loop rather than only independent VM connectivity.

The exercise demonstrated all of the following:

- a scoped red-team test can be generated from KALI01;
- UBUNTU01 can enforce and log host-firewall policy;
- SEC01 can receive centralized firewall telemetry;
- red-team observations can be correlated with blue-team evidence;
- firewall behavior can be distinguished from service-listener behavior;
- a controlled change can be introduced and measured;
- the original secure state can be restored and independently retested.

The observed state transition was:

```text
FILTERED
  ↓ allow firewall rule
CLOSED
  ↓ start listening service
OPEN
  ↓ stop service + remove firewall rule
FILTERED
```

## Security and scope note

This exercise was performed only inside the user's owned, isolated homelab. No external systems, public targets, or third-party services were scanned or tested.

## Next lab direction

The first manual purple-team workflow is now operational and verified. Future work can build on this baseline with repeatable evidence collection, detection logic, Windows/Active Directory telemetry after those V2 roles are rebuilt, and eventually a constrained red/blue/verifier agent workflow after the manual procedures remain reliable.
