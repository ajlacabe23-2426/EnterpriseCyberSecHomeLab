# Network and identity recovery decision table

Run [START_HERE](START_HERE.md) first. The expected network is `10.10.10.0/24`, DC `.10`, Windows client `.20`, Ubuntu `.30`, domain `atlasiqlab.local`. VM names and baseline values live in `config/lab.psd1`.

| Evidence | Likely boundary | Smallest next action |
|---|---|---|
| VM name missing from inventory | Host/registration | Compare actual registered names; inspect VM manager before considering disk recovery. |
| Wrong Internal Network name or disconnected cable | Layer 2 | Shut the affected guest down cleanly; set its lab NIC to Internal Network `ATLASHOME-LAB`, Cable Connected; preserve NAT and recheck. |
| Client IP absent, APIPA, wrong prefix or Duplicate | Layer 3 | Match the guest adapter MAC to the VirtualBox lab NIC; inspect existing IPs before setting `.20/24`. Resolve duplicate ownership first. |
| Selected DC route uses NAT | Routing | Inspect interface/prefix and route table; lab traffic should use an on-link route. Do not make the DC the lab default gateway. |
| Ping fails, TCP ports work | ICMP policy | Continue with service checks; do not disable the firewall. |
| All DC TCP checks fail | Link, route, firewall, server power | Review DC power/services and both guest reports before changing firewall rules. |
| Forced DNS works, configured resolver fails | DNS client selection | Inspect DNS on all active NICs, including NAT and IPv6. AD queries must reach lab DNS. |
| DC A answer contains `10.0.2.15` | Multihomed DNS regression | Inspect NAT registration, DNS listening, exact stale A record and cache. Preserve the lab A record. |
| A records work, SRV or locator fails | AD DNS/service discovery | Inspect `_ldap._tcp.dc._msdcs`, Netlogon/KDC/DNS state and time. |
| NetworkOnly passes, membership fails | Client domain join | Confirm Windows guest edition supports AD join, use the lab console and an authorized domain credential, reboot, revalidate. |
| Membership passes, secure channel fails | Trust/time/reachability | Compare clock and DC locator, then investigate machine trust; do not immediately remove/rejoin the domain. |
| Login works, share access wrong | Authorization | Use the [access-control exercise](ACCESS_CONTROL_LAB.md). Authentication and authorization are separate. |

## Inspection commands inside the Windows client

```powershell
Get-NetAdapter | Format-Table Name,ifIndex,MacAddress,Status
Get-NetIPAddress -AddressFamily IPv4 | Format-Table InterfaceIndex,IPAddress,PrefixLength,AddressState
Get-DnsClientServerAddress
Find-NetRoute -RemoteIPAddress 10.10.10.10
Get-NetNeighbor -AddressFamily IPv4
```

Do not paste a guessed interface index into a configuration command. Keep the VirtualBox console available during a network change. Capture original values first; change one cause and rerun the same checks.

## If client domain join is the only missing step

Use Windows **Settings > System > About > Domain or workgroup / advanced system settings > Computer Name > Change** in the client guest. Join `atlasiqlab.local` using the credential prompt. Windows Home cannot join on-premises AD; that limitation concerns the guest edition, not the physical host's ability to run VirtualBox.

After the join/reboot, run the full client validator elevated and then perform a standard domain-user login. Never put passwords in scripts, Git, screenshots or chat.

## What the port checks do not establish

TCP 53/88/135/389/445 checks are useful path probes, not an exhaustive AD firewall test. AD also uses UDP and dynamic RPC, and requirements vary by operation. A TCP connection does not prove protocol health. The secure-channel and real login/share exercises provide additional evidence.

## Ubuntu DNS note

With two NICs, adding a DNS server to one interface does not by itself prove every application query uses it. The `.local` suffix also needs care with mDNS-aware resolvers. Compare `resolvectl status`, `resolvectl query DC01.atlasiqlab.local` and `getent ahostsv4 DC01.atlasiqlab.local`. Review active Netplan files before editing; preserve the NAT route and use the console if applying changes.

## References

- [Oracle VirtualBox networking](https://www.virtualbox.org/manual/ch06.html)
- [Microsoft Resolve-DnsName](https://learn.microsoft.com/en-us/powershell/module/dnsclient/resolve-dnsname)
- [Microsoft Test-ComputerSecureChannel](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/test-computersecurechannel) — use on a domain member, not a DC.
