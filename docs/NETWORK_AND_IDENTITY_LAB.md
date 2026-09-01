# Exercise 1 — Follow a packet, then prove domain identity

## Outcome

Explain the route and destination MAC before sending traffic, then distinguish a working network from a working domain login. Use DC01 and Win11-Client01 only after reviewing current host resources.

## Predict

Inside the Windows client, identify its lab IP/mask. For `10.10.10.20/24 -> 10.10.10.10`:

1. Is the destination local to that interface?
2. Whose MAC should the client use in its outgoing Ethernet frame?
3. Does DNS need to work for a connection directly to the numeric DC IP?

## Run and observe

```powershell
Find-NetRoute -RemoteIPAddress 10.10.10.10
ping.exe -n 1 10.10.10.10
Get-NetNeighbor -AddressFamily IPv4 | Where-Object IPAddress -eq '10.10.10.10'
Find-NetRoute -RemoteIPAddress 1.1.1.1
```

The final command inspects a route; it does not send a packet to the internet. Compare selected source, interface and next hop. The on-link DC destination uses the DC lab NIC's MAC. For a remote destination reached through NAT, the guest sends the first-hop frame to its NAT gateway's MAC. Always state **which machine and which outgoing link** you are describing. Across a router, a new frame is built; a gateway MAC is not the final remote host's MAC.

A cached neighbor entry may already exist, so a new ARP request is not guaranteed on every ping. Do not clear caches just to force an expected story. If ping is filtered, compare the validator's TCP results.

## Inspect DNS independently

```powershell
Resolve-DnsName DC01.atlasiqlab.local -Type A -DnsOnly -NoHostsFile
Resolve-DnsName DC01.atlasiqlab.local -Type A -Server 10.10.10.10 -DnsOnly -NoHostsFile
Resolve-DnsName _ldap._tcp.dc._msdcs.atlasiqlab.local -Type SRV -Server 10.10.10.10 -DnsOnly
```

Expected: DC A record returns only `10.10.10.10`; SRV points to the DC name on port 389. If only the forced-server query works, what does that imply about the client's normal resolver path?

## Verify identity

Run `Start-Lab.ps1 -Role Client` elevated. If not joined, complete only the documented join step after NetworkOnly passes. Sign out and sign in to the Windows guest using one existing standard lab-domain account whose credentials you know.

```powershell
whoami
whoami /groups
$env:LOGONSERVER
klist
```

Record the account and time. Cached interactive credentials can allow a login without a current DC connection; `whoami` and `LOGONSERVER` alone do not prove online authentication. Correlate a fresh authentication with DC events in Exercise 3 and confirm access to a domain resource. Do not publish account tokens or full environment dumps.

## Explain it back

- Why can ping by IP work while domain join fails?
- What does a TCP/445 success prove, and what does it leave unproven?
- What is the difference between DNS discovery, computer trust and user authentication?

## Completion evidence

A passing full client report, observed route/neighbor explanation, and a separately recorded fresh domain-login result. Use [the session record](templates/SESSION_RECORD.md). Do not mark the next two exercises complete yet.
