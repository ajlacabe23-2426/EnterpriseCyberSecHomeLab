# Linux exercise — Identify one rejected SSH login

## Outcome

Use one deliberate incorrect-password attempt against your own UBUNTU01 account, then identify the corresponding event by account, source address and timestamp. A timeout and an authentication rejection represent different failure stages.

Status: prepared, not yet completed. The [September 1 checkpoint](UBUNTU_RECOVERY_2026-09-01.md) already records a successful SSH login after UFW activation.

## Starting state

- UBUNTU01 is running with its existing 1536 MB allocation; additional VMs are not needed.
- Windows SSH reaches guest TCP/22 through 127.0.0.1:2222.
- UFW permits this connection on enp0s3 from 10.0.2.2.
- Password authentication worked in the observed session.
- Keep a working Ubuntu session and the VirtualBox console available.

## Produce one event from Windows

In a separate Windows PowerShell window, enter your Ubuntu username and run:

```powershell
$LabUser = Read-Host "Ubuntu username"
ssh -o ConnectTimeout=10 -o PreferredAuthentications=password -o NumberOfPasswordPrompts=1 -p 2222 "$LabUser@127.0.0.1"
```

At the password prompt, enter one deliberately incorrect password. The options select password authentication for this invocation and allow only one password prompt. The expected result is an authentication rejection, usually Permission denied. Do not repeat the attempt in a loop. A timeout, refusal or unexpected host-key warning should be investigated before another attempt. Do not disable host-key checking.

## Find the evidence in Ubuntu

Immediately return to the working Ubuntu session and run:

```bash
sudo journalctl -u ssh.service --since "5 minutes ago" --no-pager
```

Find the new Failed password entry and correlate it with the attempt just made. Record the timestamp and timezone, attempted account, source IP and source port, server/service, and outcome. Use the relevant lines; do not publish credentials or an entire unrelated authentication history.

The previously observed NAT source was 10.0.2.2. Read the actual new event rather than assuming the source or treating an older failed login as the new result. If no matching entry appears, verify the time window and service log before making another attempt.

## Explain the result

1. Which source IP does Ubuntu record, and how does it relate to VirtualBox NAT?
2. Did the firewall block the connection, or did SSH reject authentication? What evidence distinguishes them?
3. Can one failed login alone establish malicious intent? What additional context would you investigate?

This exercise validates an authentication failure and local log visibility. It does not validate firewall deny rules, brute-force protection, alerting, domain authentication or centralized log ingestion.

## Completion evidence

- One deliberately wrong password submitted through the existing local forwarding rule.
- Client-side authentication rejection.
- Matching recent server-side event with account, source and timestamp.
- A short explanation distinguishing network reachability from authentication.

Preserve the relevant evidence privately and add a sanitized result to the checkpoint after verification. No server configuration changes are part of this exercise.

References: [OpenSSH client options](https://manpages.ubuntu.com/manpages/noble/man5/ssh_config.5.html), [Ubuntu OpenSSH server](https://ubuntu.com/server/docs/how-to/security/openssh-server/).
