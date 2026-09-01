[CmdletBinding()]
param([string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Lab.Common.ps1"
Test-LabWindows
$config = Import-PowerShellDataFile "$PSScriptRoot/../config/lab.psd1"
$checks = @()
try {
    $system = Get-CimInstance Win32_ComputerSystem
    if ($system.DomainRole -lt 4 -or $system.Domain -ine $config.DomainName) {
        throw 'Run inside the domain controller for atlasiqlab.local.'
    }
    $checks += New-LabCheck 'Expected domain controller role' 'PASS' "$($system.Name); $($system.Domain)"
    foreach ($name in @('DNS','NTDS','Kdc','Netlogon')) {
        try {
            $service = Get-Service $name
            $checks += New-LabCheck "Service $name" $(if ($service.Status -eq 'Running') {'PASS'} else {'FAIL'}) "$($service.Status)"
        } catch { $checks += New-LabCheck "Service $name" 'FAIL' $_.Exception.Message }
    }
    $checks += Invoke-LabProbe 'Addresses and gateways' {
        Get-NetIPConfiguration | Format-List InterfaceAlias,InterfaceIndex,IPv4Address,IPv4DefaultGateway,DNSServer
        Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceIndex,IPAddress,PrefixLength,AddressState
    }
    $checks += Invoke-LabProbe 'DNS registration per adapter' {
        Get-DnsClient | Select-Object InterfaceAlias,InterfaceIndex,RegisterThisConnectionsAddress,ConnectionSpecificSuffix
    } 'NAT should not register its address in AD DNS; lab NIC should.'
    $checks += Invoke-LabProbe 'DNS listening and host record' {
        Get-NetTCPConnection -State Listen -LocalPort 53 | Select-Object LocalAddress,LocalPort
        Get-DnsServerResourceRecord -ZoneName $config.DomainName -Name 'DC01' -RRType A |
            Select-Object HostName,@{n='Address';e={$_.RecordData.IPv4Address.IPAddressToString}}
    } 'Expect lab-facing DNS and the DC01 A record at 10.10.10.10; investigate NAT registration if present.'
    $checks += Invoke-LabProbe 'Domain and DC discovery' {
        Import-Module ActiveDirectory
        Get-ADDomain | Select-Object DNSRoot,NetBIOSName,PDCEmulator
        Get-ADDomainController -Identity $env:COMPUTERNAME | Select-Object HostName,IPv4Address,Site
    }
    $checks += Invoke-LabProbe 'Firewall and time state' {
        Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction
        Invoke-LabNative 'w32tm.exe' @('/query','/status')
    } 'Record time and firewall state; do not disable the firewall to make a test pass.'
    $checks += Invoke-LabProbe 'Lab group membership' {
        Import-Module ActiveDirectory
        foreach ($name in @('GG-AtlasIQ-Standard-Users','GG-AtlasIQ-Executives','GG-AtlasIQ-IT-Admins','GG-AtlasIQ-Security-Analysts','GG-AtlasIQ-Finance')) {
            $members = @(Get-ADGroupMember -Identity $name | Select-Object -ExpandProperty SamAccountName)
            [pscustomobject]@{Group=$name; Members=$members -join ', '}
        }
    } 'Inventory only: membership is not an effective-access test.'
    foreach ($shareName in $config.Shares) {
        try {
            $share = Get-SmbShare -Name $shareName
            $access = @(Get-SmbShareAccess -Name $shareName)
            $checks += New-LabCheck "$shareName share ACL" 'INFO' (($access | Format-Table AccountName,AccessControlType,AccessRight | Out-String).Trim())
            $broad = @()
            $unresolved = @()
            foreach ($entry in $access) {
                if ($entry.AccessControlType -ne 'Allow') { continue }
                try {
                    $account = New-Object Security.Principal.NTAccount($entry.AccountName)
                    $sid = $account.Translate([Security.Principal.SecurityIdentifier]).Value
                    if (Test-LabBroadSid $sid) { $broad += "$($entry.AccountName): $($entry.AccessRight)" }
                } catch { $unresolved += $entry.AccountName }
            }
            if ($shareName -ne 'AtlasIQ-Public' -and $broad.Count) {
                $checks += New-LabCheck "$shareName broad share access" 'WARN' ($broad -join '; ') 'Compare intended group access and NTFS before removing any ACE. Broad share access alone does not prove effective unauthorized access.'
            }
            if ($unresolved.Count) { $checks += New-LabCheck "$shareName unresolved identities" 'WARN' ($unresolved -join '; ') 'Broad-access review is incomplete until these SIDs resolve.' }
            $acl = Get-Acl -LiteralPath $share.Path
            $checks += New-LabCheck "$shareName NTFS ACL" 'INFO' (($acl.Access | Select-Object IdentityReference,FileSystemRights,AccessControlType,IsInherited | Format-Table | Out-String -Width 220).Trim())
        } catch { $checks += New-LabCheck "$shareName inventory" 'FAIL' $_.Exception.Message }
    }
    $checks += New-LabCheck 'Effective authorization gate' 'WARN' 'Pending allowed-user and denied-user tests from the Windows client.' 'Follow docs/ACCESS_CONTROL_LAB.md; do not claim least privilege from ACL listings alone.'
} catch { $checks += New-LabCheck 'DC collection prerequisite' 'FAIL' $_.Exception.Message }
$result = Export-LabReport 'DC01' $checks $OutputDirectory 'Service and permission inventory. Effective access and current live user authentication are not certified.'
if ($result -eq 'FAIL') { exit 1 }
exit 0
