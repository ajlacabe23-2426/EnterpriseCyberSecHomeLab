[CmdletBinding()]
param(
    [string]$DomainControllerIp = "10.10.10.10",
    [string]$DomainName = "atlasiqlab.local"
)

$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path $PSScriptRoot "..\evidence"
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$outFile = Join-Path $evidenceDir "DC01-network-$stamp.txt"

Start-Transcript -Path $outFile -Force

Write-Host "=== DC01 NETWORK / DIRECTORY COLLECTION ==="
Get-Date
hostname
Get-CimInstance Win32_ComputerSystem | Select-Object Name, Domain, PartOfDomain

Write-Host "=== ADAPTERS ==="
Get-NetAdapter | Sort-Object ifIndex | Format-Table -AutoSize Name, InterfaceDescription, ifIndex, Status, MacAddress, LinkSpeed

Write-Host "=== IP CONFIGURATION ==="
Get-NetIPConfiguration | Format-List InterfaceAlias, InterfaceIndex, IPv4Address, IPv4DefaultGateway, DNSServer
Get-NetIPAddress -AddressFamily IPv4 | Sort-Object InterfaceIndex | Format-Table -AutoSize InterfaceAlias, InterfaceIndex, IPAddress, PrefixLength, AddressState

Write-Host "=== DNS CONFIGURATION ==="
Get-DnsClientServerAddress -AddressFamily IPv4 | Format-Table -AutoSize InterfaceAlias, InterfaceIndex, ServerAddresses

Write-Host "=== ROUTES ==="
Get-NetRoute -AddressFamily IPv4 | Sort-Object RouteMetric | Format-Table -AutoSize ifIndex, DestinationPrefix, NextHop, RouteMetric, InterfaceMetric

Write-Host "=== FIREWALL PROFILES ==="
Get-NetFirewallProfile | Format-Table -AutoSize Name, Enabled, DefaultInboundAction, DefaultOutboundAction

Write-Host "=== CORE SERVICES ==="
Get-Service DNS,Netlogon,Kdc -ErrorAction SilentlyContinue | Format-Table -AutoSize Name, Status, StartType
Get-Service NTDS -ErrorAction SilentlyContinue | Format-Table -AutoSize Name, Status, StartType

Write-Host "=== SELF TEST ==="
Test-Connection -ComputerName $DomainControllerIp -Count 2
nslookup.exe $DomainName $DomainControllerIp
nslookup.exe "DC01.$DomainName" $DomainControllerIp

Write-Host "=== DIRECTORY INFO ==="
if (Get-Module -ListAvailable ActiveDirectory) {
    Import-Module ActiveDirectory
    Get-ADDomain | Select-Object DNSRoot, NetBIOSName, DomainMode, PDCEmulator
    Get-ADDomainController -Identity $env:COMPUTERNAME | Select-Object HostName, IPv4Address, Site, IsGlobalCatalog
} else {
    Write-Host "ActiveDirectory PowerShell module not available."
}

Stop-Transcript
Write-Host "Evidence saved to: $outFile"
