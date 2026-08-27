# Core Network Validation — 2026-08-27

## Objective

Restore the homelab to a stable, enterprise-style network state without rebuilding working components, then validate Windows Server, Active Directory/DNS, Ubuntu networking, internet access, and SSH.

## Environment

### VirtualBox
Registered VMs:
- `DC01`
- `Win11-Client01`
- `UBUNTU01`
- `Kali01`

Each VM uses:
- Adapter 1: VirtualBox NAT
- Adapter 2: Internal Network `ATLASHOME-LAB`

### Addressing
- DC01 LAB: `10.10.10.10/24`
- Win11-Client01 LAB: `10.10.10.20`
- UBUNTU01 LAB: `10.10.10.30/24`
- UBUNTU01 NAT: `10.0.2.15`

## Validation Results

### DC01
Validated:
- Hostname: `DC01`
- AD domain: `atlasiqlab.local`
- NetBIOS domain: `ATLASIQLAB`
- PDC Emulator: `DC01.atlasiqlab.local`
- DNS Server: Running
- Kerberos KDC: Running
- Netlogon: Running
- Active Directory Domain Services / NTDS: Running
- LAB address: `10.10.10.10`
- LAB interface has no default gateway
- NAT provides outbound internet access

### DNS remediation
Observed issue:
- DC01 is multihomed.
- DNS responses exposed both the internal LAB address and NAT address.
- The NAT-facing address `10.0.2.15` is not appropriate for domain clients on `ATLASHOME-LAB`.

Remediation:
- Disabled DNS registration on the NAT NIC.
- Kept DNS registration enabled on the LAB NIC.
- Restricted DNS Server listening to the lab-facing interface/address.
- Verified the authoritative DNS zone contains the lab-facing DC host record.

Troubleshooting lesson:
A multihomed domain controller can advertise an address that is reachable for internet/NAT purposes but wrong for internal domain traffic. AD/DNS troubleshooting should distinguish:
1. NIC registration behavior,
2. DNS Server listening interfaces,
3. authoritative zone records,
4. resolver/server cache.

### UBUNTU01
Validated:
- Hostname: `ubuntu01`
- NAT interface: `enp0s3`
- LAB interface: `enp0s8`
- NAT address: `10.0.2.15`
- LAB address: `10.10.10.30/24`
- Reachability to DC01: PASS
- Internet reachability: PASS
- Lab DNS configured through `10.10.10.10`
- Search domain: `atlasiqlab.local`
- OpenSSH Server running
- SSH listening on IPv4 and IPv6 TCP/22
- TCP/22 local connectivity check: PASS

Netplan configuration:
```yaml
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: false
      addresses:
        - 10.10.10.30/24
      nameservers:
        addresses:
          - 10.10.10.10
        search:
          - atlasiqlab.local
```

### Package-manager repair
Ubuntu reported an interrupted `dpkg` transaction. The package state was repaired with:

```bash
sudo dpkg --configure -a
```

The initramfs update completed and the shell returned normally.

## Architecture Lesson

The working design separates two functions:

```text
                 Internet
                    |
             VirtualBox NAT
                    |
      +-------------+-------------+
      |                           |
    DC01                        UBUNTU01
    NAT                         NAT
      |                           |
      +----- ATLASHOME-LAB -------+
                 |
          10.10.10.0/24
          DC01:     .10
          Client01: .20
          Ubuntu:   .30
```

The NAT adapter is for outbound internet access. The LAB adapter is for internal enterprise traffic, DNS, domain communication, remote administration, and future security exercises.

## Evidence / Interview Value

This milestone demonstrates practical experience with:
- VirtualBox multi-NIC networking
- Windows Server administration
- Active Directory Domain Services
- DNS troubleshooting
- multihomed server behavior
- IPv4 addressing and routing
- Linux Netplan
- systemd-resolved
- OpenSSH
- cross-platform service validation
- troubleshooting by layer rather than rebuilding the environment

## Next

- Validate Win11-Client01 domain membership and domain-user authentication.
- Validate SMB/RBAC and remove broad share permissions.
- Add centralized logging/security telemetry.
- Run repeatable detection and incident-response exercises.
