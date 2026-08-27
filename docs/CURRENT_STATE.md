# Current State

## Known good / previously completed
- Active Directory domain: `atlasiqlab.local`
- Domain controller: `DC01`
- DC01 intended lab address: `10.10.10.10/24`
- DNS is hosted on DC01.
- AD users, groups, OUs, and lab shares were previously created.
- VirtualBox internal-network name used by the lab: `ATLASHOME-LAB`.

## Current incident
CLIENT01 has not yet demonstrated reliable connectivity to DC01 at `10.10.10.10`.

The recovery scope is intentionally narrow:

`CLIENT01 -> VirtualBox internal network -> DC01 -> DNS/AD services`

Do not rebuild the domain, users, shares, or Active Directory unless evidence proves those components are damaged.

## Definition of done
The incident is closed only when all applicable checks pass:

- CLIENT01 has a valid lab IPv4 address in `10.10.10.0/24`.
- CLIENT01 can reach `10.10.10.10`.
- CLIENT01 uses `10.10.10.10` as DNS for the lab/domain path.
- `atlasiqlab.local` resolves from CLIENT01.
- `DC01.atlasiqlab.local` resolves from CLIENT01.
- TCP 53, 88, 389, and 445 are reachable from CLIENT01 when the corresponding service is expected.
- Domain discovery succeeds.
- Root cause, remediation, and validation evidence are recorded.

## Learning objective
Troubleshoot bottom-up rather than guessing:

1. Virtual NIC / Layer 2
2. IPv4 addressing / Layer 3
3. Routing
4. Host firewall
5. DNS
6. Active Directory service discovery
