# Current state — 2026-09-01

## Recorded live evidence

The [August 27 record](core-network-validation-2026-08-27.md) reports DC01 AD/DNS, Ubuntu dual-NIC routing, lab DNS, SSH listening, and package repair validated. This is a historical checkpoint, not a fresh machine inspection.

The older recovery branch described CLIENT01 connectivity as an open incident. The later checkpoint improved the known state but did not prove client membership, fresh domain authentication, or effective SMB authorization. Those gates remain open; do not label the whole lab broken or fully verified.

The [September 1 Ubuntu recovery checkpoint](UBUNTU_RECOVERY_2026-09-01.md) records new user-provided console evidence: UBUNTU01 boots alone, both IPv4 interfaces and the NAT default route are present, and the SSH service is active. A login screen was supplied after the Windows localhost SSH forwarding procedure. Session endpoint and authentication-log evidence remain the next checks. Guest memory availability does not establish Windows host capacity for additional VMs.

## Prepared in this update

- Reconciled the existing recovery branch with the current main-branch portfolio documentation.
- One host-first entrypoint and centralized expected names/addresses.
- Host inventory with actual VM names, adapter/cable checks and current memory/disk reporting.
- Client validation of /24 address state, DNS configuration, TCP listeners, default and forced DNS A/SRV answers, DC locator, domain membership and secure channel.
- DC service, DNS and RBAC inventory, including broad share identities detected by SID.
- Ubuntu diagnostics and bounded Windows authentication event collection.
- Behavioral regression tests and Windows PowerShell 5.1 / PowerShell 7 CI plus Bash checks.
- Three practical exercises and a machine handoff.

## What is not yet proven

| Gate | Status | Required evidence |
|---|---|---|
| Current host/VM capacity and topology | Partial manual evidence; Ubuntu running alone | See September 1 checkpoint; fresh host headroom before additional guests |
| Ubuntu access and security baseline | Boot, addresses, routing and SSH service observed; login reached | SSH session endpoints, listening sockets, firewall and authentication logs; forwarding persistence after restart |
| Current client/DC network and domain trust | Pending local run | CLIENT01 report |
| Fresh domain-user authentication | Pending local action | Login identity + correlated DC/client event evidence |
| SMB least privilege | Pending local action | Expected allow and expected deny under separate standard-user sessions |
| Windows event visibility | Pending local action | Timestamp/account/source/event correlation |
| Centralized logging/SIEM | Not deployed by this update | Later resource decision and ingestion test |

## Next action

Continue in the running Ubuntu session with the read-only security checks in the [September 1 checkpoint](UBUNTU_RECOVERY_2026-09-01.md). Review the results before changing firewall or SSH settings, then refresh package metadata and address pending security updates. Keep other guests powered off until host capacity is reassessed. The assistant cannot inspect or operate the physical Windows host or its guests from the remote repository workspace; live findings here come from user-provided screenshots and output.

## Delivery status

Publication to the public recovery branch was authorized on September 1. Use [START_HERE](START_HERE.md) to obtain and run this update. GitHub checks validate the tooling; they do not validate the local VMs. The draft PR stays open until the machine-side gates have evidence.
