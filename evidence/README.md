# Evidence Index

This directory structure is the evidence catalog for Enterprise Cyber Lab V2 and its preserved V1 history.

The goal is to preserve **proof of configuration, troubleshooting, remediation, and validation** without storing credentials or sensitive personal data.

## Evidence categories

### 01 — Architecture
Examples:
- VirtualBox adapter configuration
- network topology
- IP addressing
- host roles

### 02 — Identity & Active Directory
Examples:
- domain configuration
- OU structure
- users and groups
- domain join validation
- authentication results

### 03 — DNS & Networking
Examples:
- `ipconfig`
- `ip addr`
- `nslookup`
- `Resolve-DnsName`
- route verification
- connectivity tests

### 04 — Linux & SSH
Examples:
- SSH service state
- listening-port evidence
- interface configuration
- package/service remediation
- successful remote connection

### 05 — Access Control
Examples:
- SMB share permissions
- NTFS permissions
- RBAC validation
- least-privilege remediation

### 06 — Security Telemetry
Examples:
- Windows Event Logs
- Sysmon
- Linux auth logs
- SIEM ingestion
- detection rules
- alert validation

### 07 — Incident / Troubleshooting Records
Examples:
- problem statement
- symptoms
- hypothesis
- commands used
- root cause
- remediation
- final verification

## Naming convention

Use a clear, sortable format:

```text
YYYY-MM-DD_system_topic_evidence-description.ext
```

Example:

```text
2026-08-27_DC01_dns_lab-interface-validation.png
2026-08-27_UBUNTU01_ssh-listening-port.txt
```

## Evidence rules

Before committing evidence:

- remove passwords, API keys, tokens, or secrets;
- avoid personal data;
- avoid real production information;
- crop screenshots to the relevant technical context;
- include enough surrounding information to make the evidence understandable;
- pair screenshots with a short Markdown explanation when context is important.

## Recorded checkpoints

| Date | Record | Status |
|---|---|---|
| 2026-08-27 | [Core Network Validation](../docs/core-network-validation-2026-08-27.md) | Verified in V1; Mac parity pending |
| 2026-09-02 | [V2 migration checkpoint](../docs/ENTERPRISE_CYBER_LAB_V2.md) | Partial Mac migration; Linux networking operational |
| 2026-09-04 | [Purple-Team Workflow Validation](../docs/purple-team-workflow-validation-2026-09-04.md) | **Verified — first complete manual red/blue/verifier loop** |

Future evidence should be linked here as the lab grows.

## V2 migration and purple-team evidence

Include the lab version, host/guest architecture and VM role with each new record.
Keep V1 evidence intact. A V2 exercise record should include its authorized scope,
red-team test, blue-team observations, remediation, verifier retest and unresolved
gaps. Mark untested controls as pending; do not reuse V1 evidence as a V2 pass.

The 2026-09-04 checkpoint establishes the first verified V2 purple-team baseline:
KALI01 generated scoped probes, UBUNTU01 enforced and logged UFW policy, SEC01
received the centralized telemetry, a controlled TCP/8080 state transition was
performed, and the original filtered state was restored and retested successfully.
