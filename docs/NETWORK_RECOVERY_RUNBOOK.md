# CLIENT01 to DC01 Network Recovery Runbook

## Goal
Restore the minimum required path for CLIENT01 to communicate with DC01 without rebuilding working lab components.

## Phase 1 — Host-side VirtualBox inspection
Run on the Windows host when back at the lab machine.

Confirm both VMs are powered off before changing adapter settings.

For each VM, verify:
- the lab-facing adapter exists,
- it is enabled,
- Attached To = **Internal Network**,
- Name = **ATLASHOME-LAB** exactly,
- Cable Connected = enabled.

A typo in the internal-network name creates two isolated virtual switches even if everything else looks correct.

## Phase 2 — CLIENT01 evidence
Open PowerShell on CLIENT01 from the repository root and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\collect-client01.ps1
```

Do not change IP or DNS settings yet.

Primary questions:
- Which NIC is the lab NIC?
- Does it have a `10.10.10.x/24` address?
- Is it showing APIPA `169.254.x.x`?
- Is a wrong gateway or route present?
- Can it ARP/ping `10.10.10.10`?
- Can it reach DNS/Kerberos/LDAP/SMB ports?

## Phase 3 — DC01 evidence
Run on DC01:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\scripts\collect-dc01.ps1
```

Confirm:
- DC01 still owns `10.10.10.10/24` on the lab NIC,
- DNS, Netlogon, and AD DS-related services are healthy,
- Windows Firewall profile/state is known,
- the lab NIC is Up,
- DC01 has not lost or reassigned the intended address.

## Phase 4 — Interpret the failure

### A. CLIENT01 has no lab NIC
Likely layer: VirtualBox configuration.

Action: repair adapter attachment before touching Windows networking.

### B. CLIENT01 has 169.254.x.x
Likely layer: no valid static/DHCP configuration on that interface.

Action: identify the correct lab interface, then configure a valid unused `10.10.10.x/24` address only after confirming DC01 is `10.10.10.10/24`.

### C. CLIENT01 has 10.10.10.x but cannot reach 10.10.10.10
Likely layers:
- mismatched VirtualBox internal-network names,
- disconnected virtual cable,
- incorrect subnet mask,
- duplicate IP,
- firewall filtering,
- wrong interface/route.

Use ARP, routing, and port tests before modifying firewall policy.

### D. IP connectivity works but names fail
Likely layer: DNS.

CLIENT01's lab/domain DNS server should be `10.10.10.10` for AD name resolution.

### E. DNS works but domain discovery fails
Move upward to AD/Kerberos/LDAP/Netlogon checks. Do not blame networking once the lower layers have passed.

## Phase 5 — Validation
After remediation, run on CLIENT01:

```powershell
.\scripts\verify-domain-path.ps1
```

Save the generated evidence output.

## Evidence to retain
Record:
- failing symptom,
- failing layer,
- root cause,
- exact remediation,
- commands/tests used,
- PASS evidence,
- what was learned.

## Interview explanation
Use the incident to demonstrate a structured troubleshooting method: verify the virtual network and NIC first, then IPv4/routing, then firewall, then DNS, then Active Directory service discovery. This shows that the fix was evidence-driven rather than a sequence of guesses.
