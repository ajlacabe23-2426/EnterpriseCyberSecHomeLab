# Evidence Index

This directory structure is the evidence catalog for the Enterprise Cybersecurity Homelab.

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

## Current verified records

| Date | Record | Status |
|---|---|---|
| 2026-08-27 | [Core Network Validation](../docs/core-network-validation-2026-08-27.md) | Verified |

Future evidence should be linked here as the lab grows.

## Diagnostic reports

The new collectors write Markdown/JSON (Windows) or text (Ubuntu) under `evidence/private/`, which Git ignores recursively. A collection error is never silently reported as a passing validation. Review the declared scope, not just the exit code.

Use [the session template](../docs/templates/SESSION_RECORD.md) to create a deliberately redacted public summary after a live test. Offline regression results belong in engineering validation notes and must not be presented as proof that a VM, login or ACL worked.
