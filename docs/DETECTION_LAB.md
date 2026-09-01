# Exercise 3 — Investigate a controlled authentication event

## Outcome

Generate a known login result, find the right event on the right guest, and explain the account, source, time and outcome. A SIEM is not required to learn this first investigation.

## Prepare

Use the DC/client pair and a nonprivileged lab account. Check the account's lockout policy and current state before intentionally entering a wrong password. Do not repeatedly guess passwords or use an administrator account for this exercise. One controlled failure is enough; skip the failure attempt if the lockout state is uncertain.

On DC01, elevated:

```powershell
Get-ADDefaultDomainPasswordPolicy | Select-Object LockoutThreshold,LockoutDuration,LockoutObservationWindow
```

Fine-grained policy can override that default. Inspect `Get-ADUserResultantPasswordPolicy` for the chosen user before relying on the default. Existing bad-password counters also matter.

On each guest, inspect current audit settings:

```powershell
auditpol.exe /get /category:*
```

If relevant events are missing, inspect the effective audit policy/GPO before changing it. This workflow does not automatically enable audit policy or forwarding.

## Generate, collect, correlate

1. Note the UTC time: `(Get-Date).ToUniversalTime().ToString('o')`.
2. Perform a successful standard domain-user login or allowed share access. Optionally make one controlled incorrect-password attempt after the checks above.
3. Within the next two hours, run `scripts/collect-security-events.ps1` elevated on the client and DC. It reads at most 30 relevant events by default, and exports selected fields rather than raw messages.
4. Match time, account, source, event ID, status/substatus and logon type. Background services also generate events; the newest event may not belong to your test.

| Event | Meaning / likely observation point |
|---|---|
| 4624 | Successful logon session on the destination computer. Type 2 is interactive, type 3 network; other types need interpretation. |
| 4625 | Failed logon on the machine where the attempt is recorded. Check status/substatus. |
| 4768 / 4769 | Kerberos ticket activity on a DC when relevant auditing is enabled. |
| 4771 | Kerberos pre-authentication failure on a DC. |
| 4776 | Credential validation, commonly relevant to NTLM; inspect the validating system. |
| 4740 | Account lockout. It is not an event to intentionally trigger for this exercise. |

No matching events is an **incomplete observation**, not a detection success. Check time window, audit policy, correct machine and authentication method. Increase `-MaxEvents` up to 100 if the relevant entries were outside the default cap; use the local Event Viewer for deeper inspection.

## Explain it back

- Why might a failed Kerberos login show 4771 on the DC instead of the 4625 you expected there?
- Why is one failed login insufficient evidence of a brute-force attack?
- Which fields distinguish your test from background service activity?

## Completion gate

A written, evidence-backed account of one successful login and, if performed, one controlled failure. State where each event was found and what remains unknown. Centralized collection is a later step after this local visibility and memory capacity are verified.

References: [Microsoft 4624](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624), [Microsoft 4625](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625), [AD events to monitor](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/appendix-l--events-to-monitor).
