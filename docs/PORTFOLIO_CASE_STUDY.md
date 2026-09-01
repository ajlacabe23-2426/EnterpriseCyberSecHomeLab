# Portfolio Case Study — Enterprise Cybersecurity Homelab

## Project objective

Build an enterprise-style virtual environment that turns classroom and certification concepts into hands-on systems work across Windows, Linux, networking, identity, access control, troubleshooting, and security validation.

The project is designed to answer a practical interview question:

> What have you actually configured, broken, fixed, verified, and documented?

## Environment

The lab uses VirtualBox with a dual-network design:

- **ATLASHOME-LAB** — isolated internal network for domain and lab traffic
- **NAT** — controlled outbound internet access where required

Core systems:

| Host | Purpose | Address |
|---|---|---|
| DC01 | Windows Server, AD DS, DNS | `10.10.10.10` |
| Win11-Client01 | Windows endpoint | `10.10.10.20` |
| UBUNTU01 | Ubuntu Server, SSH | `10.10.10.30` |
| Kali01 | Security testing workstation | internal lab |

Domain: `atlasiqlab.local`

## Key implementation work

### Identity and infrastructure

- Configured Windows Server as the domain controller.
- Implemented Active Directory Domain Services and DNS.
- Established the internal lab subnet and static addressing.
- Built Windows and Linux endpoints around the same isolated environment.

### Linux administration

- Configured Ubuntu with dual network adapters.
- Preserved outbound internet access through NAT.
- Routed lab DNS through the domain controller.
- Enabled and verified OpenSSH on TCP/22.
- Recovered from an interrupted package-management state.

### Troubleshooting

A major lab issue involved a multihomed domain controller advertising or using the wrong network interface for domain DNS behavior.

The remediation required reasoning across multiple layers rather than simply confirming that the DNS service was running.

The solution included:

- preserving NAT for outbound connectivity;
- using the isolated interface for domain traffic;
- preventing the NAT-facing address from acting as the domain DNS endpoint;
- restricting DNS behavior to the intended lab interface;
- revalidating DNS resolution and endpoint-to-server connectivity.

## Verification evidence

The core network milestone was validated on **2026-08-27**.

Verified outcomes included:

- AD DS operational on DC01;
- DNS, Kerberos, Netlogon, and NTDS healthy;
- domain resolution returning the lab-facing DC address;
- Windows client DNS record present;
- Ubuntu-to-DC connectivity over the internal network;
- outbound connectivity retained through NAT;
- lab DNS resolution using `10.10.10.10`;
- SSH listening successfully on Ubuntu.

See [Core Network Validation — 2026-08-27](core-network-validation-2026-08-27.md).

## Technical lessons

### 1. Running is not the same as working correctly

A service can be healthy while listening on, registering, or advertising the wrong interface.

### 2. Troubleshooting should follow the traffic path

For connectivity problems, validate:

1. interface state;
2. addressing;
3. routing;
4. DNS;
5. service state;
6. listening ports;
7. endpoint reachability;
8. authentication or authorization.

### 3. Evidence matters

A successful fix is stronger when it leaves behind:

- command output;
- screenshots;
- configuration state;
- before/after behavior;
- root-cause notes;
- validation results.

## Skills demonstrated

- Active Directory
- Windows Server
- DNS
- Linux administration
- SSH
- VirtualBox networking
- static IP configuration
- multi-NIC troubleshooting
- access-control reasoning
- layered IT troubleshooting
- technical documentation
- verification and evidence collection

## Current development path

The next lab work focuses on:

1. domain-user authentication;
2. SMB permission hardening;
3. centralized security telemetry;
4. repeatable detection and incident-response exercises;
5. structured evidence collection.

## Interview summary

**30-second version**

I built an enterprise-style cybersecurity homelab with Windows Server, Active Directory, DNS, Windows and Linux endpoints, and an isolated VirtualBox network. One major issue involved a multihomed domain controller using the wrong interface for DNS. I isolated the problem by validating addressing, name resolution, interfaces, and service behavior, corrected the DNS binding/registration path, and then verified end-to-end connectivity. I document each milestone so I can explain not just what I built, but how I troubleshoot and prove that it works.
