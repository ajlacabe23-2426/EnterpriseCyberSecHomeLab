[CmdletBinding()]
param(
    [string]$DomainControllerIp = "10.10.10.10",
    [string]$DomainName = "atlasiqlab.local",
    [string]$DomainControllerFqdn = "DC01.atlasiqlab.local"
)

$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path $PSScriptRoot "..\evidence"
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$outFile = Join-Path $evidenceDir "CLIENT01-network-$stamp.txt"

Start-Transcript -Path $outFile -Force

Write-Host "=== CLIENT01 NETWORK COLLECTION ==="
Get-Date
hostname
Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, PartOfDomain

Write-Host "\n=== ADAPTERS ==="
Get-NetAdapter | Sort-Object ifIndex | Format-Table -AutoSize Name, InterfaceDescription, ifIndex, Status, MacAddress, LinkSpeed

Write-Host "\n=== IP CONFIGURATION ==="
Get-NetIPConfiguration | Format-List InterfaceAlias, InterfaceIndex, IPv4Address, IPv4DefaultGateway, DNSServer
Get-NetIPAddress -AddressFamily IPv4 | Sort-Object InterfaceIndex | Format-Table -AutoSize InterfaceAlias, InterfaceIndex, IPAddress, PrefixLength, AddressState

Write-Host "\n=== DNS SERVERS ==="
Get-DnsClientServerAddress -AddressFamily IPv4 | Format-Table -AutoSize InterfaceAlias, InterfaceIndex, ServerAddresses

Write-Host "\n=== ROUTES ==="
Get-NetRoute -AddressFamily IPv4 | Sort-Object RouteMetric | Format-Table -AutoSize ifIndex, DestinationPrefix, NextHop, RouteMetric, InterfaceMetric

Write-Host "\n=== ARP CACHE ==="
arp -a

Write-Host "\n=== BASIC CONNECTIVITY ==="
ping.exe -n 2 $DomainControllerIp

Write-Host "\n=== SERVICE PORT TESTS ==="
foreach ($port in 53,88,389,445) {
    Test-NetConnection -ComputerName $DomainControllerIp -Port $port -InformationLevel Detailed
}

Write-Host "\n=== DNS LOOKUPS ==="
nslookup.exe $DomainName $DomainControllerIp
nslookup.exe $DomainControllerFqdn $DomainControllerIp

Write-Host "\n=== DOMAIN DISCOVERY ==="
nltest.exe /dsgetdc:$DomainName

Stop-Transcript
Write-Host "\nEvidence saved to: $outFile"
