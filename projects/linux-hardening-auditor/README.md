# Linux Hardening Auditor V1 — offline configuration review

**Purpose:** Develop practical Linux administration, SSH, firewall, identity, and service-exposure auditing skills for junior IT and cybersecurity roles.

This is an **offline, read-only learning module**. It reviews a JSON snapshot *provided by the analyst* and reports evidence-scoped **PASS / REVIEW / FAIL / NOT_CHECKED** findings. It does **not** connect to a virtual machine, read real system files, execute shell commands, modify settings, or automatically apply fixes.

## Quick start

Python 3.11+; no third-party packages or online services. From the existing Enterprise Cyber Lab V2 repository:

~~~sh
cd projects/linux-hardening-auditor
python3 -m unittest discover -s auditlab -p 'test_*.py' -v
python3 -m auditlab.cli --file fixtures/secure-fictional.json
python3 -m auditlab.cli --file fixtures/review-fictional.json
python3 -m auditlab.cli --file fixtures/incomplete-fictional.json
~~~

The last fixture deliberately lacks evidence. All eight checks should show **NOT_CHECKED**, not PASS. This demonstrates the important difference between "no detected problem" and "verified configuration."

## What is checked

| ID | Snapshot input | Finding |
| --- | --- | --- |
| `permitrootlogin` | Effective SSH settings | Root login disabled / allowed / restricted mode |
| `passwordauthentication` | Effective SSH settings | Password authentication disabled or requires review |
| `permitemptypasswords` | Effective SSH settings | Empty-password SSH login |
| `ufw_status` | UFW status | Firewall reports active / inactive |
| `ufw_incoming` | UFW default policy | Incoming deny/reject or allow *only if active* |
| `uid_zero` | Local account database | Exactly one UID 0 identity named root |
| `sudo_group` | Local group database | Number of explicitly listed sudo members; other privilege paths not evaluated |
| `tcp_listeners` | TCP listening snapshot | Wildcard interface binds vs scoped binds; reachability not tested |

A PASS is **only a PASS for that narrow check on the provided snapshot**, not a certificate that the host is secure. For example, a non-wildcard TCP listener can still be reachable from other machines, and UFW can be supplemented/replaced by other firewall systems. SSH `Match` blocks may change effective settings for specific users/addresses.

## Snapshot format

Create a JSON object with the required `schema` and up to five optional *text* fields:

~~~json
{
  "schema": "linux-audit-snapshot-v1",
  "ssh_effective": "permitrootlogin no\npasswordauthentication no\npermitemptypasswords no",
  "ufw_status": "Status: active\nDefault: deny (incoming), allow (outgoing)",
  "passwd_text": "root:x:0:0:root:/root:/bin/bash",
  "group_text": "sudo:x:27:",
  "tcp_listening": "LISTEN 0 128 127.0.0.1:8080 0.0.0.0:*"
}
~~~

This is **fictional configuration data only**. The SSH field is intended to reflect *effective* configuration output (not merely grepping a file); user-specific contexts are not evaluated. The socket snapshot expects `ss -lntH`-style TCP listener rows. Unsupported or malformed inputs produce NOT_CHECKED, and unknown snapshot keys are rejected.

To examine actual **owned UBUNTU01** later, first work locally, collect *read-only* sanitized observations for those five categories, and compare them to the synthetic examples. Treat usernames, network addresses, and configuration details as private until redacted. **Do not share a raw `/etc/passwd` or `/etc/group` listing** or confidential host data in this public GitHub repository. Keep any unsanitized source snapshots outside the repository.

## Practical IT and security learning exercise

1. Explain the difference between effective SSH policy, firewall activation, and open listening sockets.
2. Compare the `secure-fictional.json` and `review-fictional.json` reports: distinguish outright FAIL from items needing investigation.
3. Show how missing firewall state changes an incoming-policy conclusion to NOT_CHECKED.
4. Document one hypothetical root cause, safe remediation plan, approval/recovery considerations, and verification evidence. **Do not automatically change the host configuration.**
5. At your MacBook, independently revalidate UBUNTU01 with controlled read-only observations. Record which sample formats need adjustment and whether the host's actual output was parsed correctly.

## Input/data protection

- File data is read only; JSON file size is limited to 150 KB and each section to 24,000 characters.
- The detector emits fixed findings with counts and generic summaries; it does not echo raw account rows, usernames, passwords, IP addresses, or the original configuration.
- Place private working data in the ignored `private-snapshots/` directory; never commit private host logs or credentials.
- No remediation or external scanning is performed. This is not a substitute for a real system audit, verified configuration state, or a professional hardening baseline.

**Next milestone:** Verify against a sanitized export of owned UBUNTU01 on the MacBook. Document unknown formats, root causes, and changes to the test suite before extending scope.
