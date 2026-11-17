# SOC-001 — Centralized Telemetry Triage (Mac / UTM)

**Status:** PREPARED / NOT YET EXECUTED
**Lab:** Enterprise Cyber Lab V2 · MacBook Air M3 / UTM · private `ATLASHOME-LAB`
**Time budget:** 20–30 minutes; start with SEC01 and UBUNTU01 only.
**Purpose:** Transition from “logs arrive” to a repeatable blue-team observation, evidence collection and explanation.

## Known, previously verified baseline (2026-09-04)
- `UBUNTU01`: private lab address `10.10.10.20`; UFW default inbound deny; rsyslog sends firewall events.
- `SEC01`: private lab address `10.10.10.50`; received Ubuntu/UFW events on rsyslog TCP/514.
- `KALI01`: `10.10.10.30`; participated in the previous scoped network test.
- The September 4 exercise observed a TCP/8080 FILTERED → CLOSED → OPEN → FILTERED transition and restored the baseline.
- This **does not** prove current telemetry, current interface addresses, or the delivery of all syslog facilities. Re-check rather than assume.
- Windows AD roles remain pending on this Mac; do not confuse VirtualBox/V1 and UTM/V2 status.

## Scope and safety
This is a **defensive, benign log-generation exercise**. Use only your own VM consoles. Do not probe public hosts or change firewall rules, listeners, passwords, permissions, rsyslog destinations, or service persistence during this step. No extra VM or paid service is required. If a service is down, **record the condition** and investigate before editing configuration.

## Step 1 — SEC01 baseline (5 minutes)
Open a terminal in **SEC01**. Run:

```bash
hostnamectl --static
ip -br addr
sudo systemctl is-active rsyslog
sudo ss -lnt | grep ':514 '
```

Expected, based on earlier records: hostname identifies SEC01, lab interface has an address in `10.10.10.0/24`, rsyslog is active, and TCP/514 is listening. A missing port does not automatically prove logging failed: inspect the actual config and sender/receiver mode.

To find where rsyslog routes remote events (read-only):

```bash
sudo grep -R -n -E 'imtcp|input\(|omfile|/var/log/|template\(' /etc/rsyslog.conf /etc/rsyslog.d 2>/dev/null
```

**Write down the actual remote log destination directory**. Do not assume a path from a tutorial. A result of *not found* should be reported as a finding.

## Step 2 — UBUNTU01 baseline and local event (5 minutes)
Open a terminal in **UBUNTU01**. Run:

```bash
hostnamectl --static
ip -br addr
sudo systemctl is-active rsyslog
logger -p user.notice -t SOC001 'exercise=SOC-001 event=heartbeat outcome=TEST owner=lab'
sudo journalctl --since '5 minutes ago' -t SOC001 --no-pager
```

The generated text is explicitly synthetic. Confirm it is observable locally before testing central forwarding. Note the local timestamp/time zone and hostname.

## Step 3 — SEC01 receipt and event integrity (5–10 minutes)
On **SEC01**, use the *actual file destination* discovered in Step 1. For example, only **if your real destination is `/var/log/remote`**:

```bash
sudo grep -R -n -- 'exercise=SOC-001 event=heartbeat' /var/log/remote 2>/dev/null | tail -n 10
```

Otherwise substitute the actual directory in your configuration. Look for matching event text, originating hostname, timestamp and source IP (if present).

Record one of three outcomes:
- **PASS:** synthetic event is visible locally and on SEC01 with an attributable origin and reasonable timestamp.
- **PARTIAL:** local event exists but the configured pipeline does not forward this facility; the earlier UFW ingestion baseline may still be working.
- **BLOCKED:** missing rsyslog service, unreachable destination, unclear routing, or no reliable event attribution.

**Do not call a missing heartbeat a security incident.** It is an engineering observation to investigate.

## Step 4 — SOC analyst mini-report (5 minutes)
Write a short report answering:
1. **What happened?** A lab owner emitted one harmless, tagged heartbeat.
2. **Where?** Which originating VM, destination VM, log file and timestamps?
3. **What can you prove?** Local receipt, forwarded receipt, integrity of fields, or only partial evidence?
4. **What is an alternative explanation?** Facility filtering, routing, time skew, service state, path mismatch, VM not booted.
5. **What action is warranted?** No remediation for PASS; one read-only next diagnostic for PARTIAL/BLOCKED.
6. **What was *not* tested?** Attack detection, Windows logs, alerting, incident response automation and hosted services.

## Evidence to keep
Use the repo naming convention, but sanitize addresses if publishing a public-facing portfolio screenshot would expose any unwanted information:

- `evidence/2026-10-27_SEC01_soc001-baseline.txt` — paste **redacted** hostname/IP/service/listener output.
- `evidence/2026-10-27_UBUNTU01_soc001-local-event.txt` — local tagged log event (redacted).
- `evidence/2026-10-27_SEC01_soc001-remote-receipt.txt` — SEC01 matching log or observed blocker.
- `evidence/2026-10-27_SOC001_investigation.md` — finding, interpretation, next control check.

**Do not commit credentials, tokens, SSH keys, personal information or raw bulk logs.** The names above are proposed output names; none of the evidence has been collected yet.

## Follow-on lab after SOC-001 passes
1. Characterize forwarding coverage across `user`, `auth`, and UFW facilities without generating real failed login traffic.
2. Write an auditable rule to flag deliberately tagged repeated synthetic events; check true positives and benign nonmatches.
3. Add a human-reviewed alert, response note, and verifier retest.
4. Later: restore `DC01` and `Win11-Client01` under UTM resource constraints, then collect safe Windows authentication and DNS telemetry.

**Acceptance:** A repeatable one-event lineage (local → centralized) with evidence, or a recorded blocker that names the missing link. This exercise is prepared, **not yet verified**.
