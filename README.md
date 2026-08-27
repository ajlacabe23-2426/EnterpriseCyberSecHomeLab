# EnterpriseCyberSecHomeLab

An extensive enterprise-style cybersecurity homelab focused on Windows Active Directory, DNS, Linux administration, segmented networking, remote management, access control, and repeatable security operations.

## Current Lab Architecture

- **DC01** — Windows Server domain controller / DNS server
  - Domain: `atlasiqlab.local`
  - LAB IP: `10.10.10.10`
  - NAT adapter retained for outbound internet access
- **Win11-Client01** — Windows client
  - LAB IP: `10.10.10.20`
- **UBUNTU01** — Ubuntu Server
  - NAT IP: `10.0.2.15`
  - LAB IP: `10.10.10.30`
  - SSH enabled on TCP/22
- **Kali01** — Kali Linux security workstation
- **ATLASHOME-LAB** — isolated VirtualBox internal network

## Verified Milestone — 2026-08-27

The core lab network is functioning end-to-end.

Validated:
- Active Directory Domain Services running on DC01
- DNS, Kerberos, Netlogon, and NTDS services healthy
- `atlasiqlab.local` resolves to the lab-facing domain controller address
- DC01 isolated LAB interface configured at `10.10.10.10/24`
- Windows client DNS record present at `10.10.10.20`
- Ubuntu dual-NIC design verified
- Ubuntu can reach DC01 over the internal network
- Ubuntu retains internet access through VirtualBox NAT
- Ubuntu uses `10.10.10.10` for lab DNS resolution
- OpenSSH Server enabled and listening on TCP/22
- Ubuntu package-management interruption repaired with `dpkg --configure -a`

A multihomed domain-controller DNS issue was also remediated by preventing the NAT-facing address from being used as the domain-facing DNS endpoint and restricting DNS service listening to the lab interface.

See [docs/core-network-validation-2026-08-27.md](docs/core-network-validation-2026-08-27.md) for the validation record and troubleshooting lessons.

## Next Validation Targets

1. Confirm Windows client domain membership and domain-user authentication.
2. Validate SMB share permissions and remove overly broad access.
3. Add centralized logging and security telemetry.
4. Run repeatable incident-response and detection exercises.
5. Capture evidence suitable for resume and interview discussion.
