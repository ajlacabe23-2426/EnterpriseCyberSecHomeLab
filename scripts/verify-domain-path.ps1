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
$outFile = Join-Path $evidenceDir "CLIENT01-validation-$stamp.txt"

Start-Transcript -Path $outFile -Force

$checks = @()

function Add-Check {
    param([string]$Name,[bool]$Pass,[string]$Evidence)
    $script:checks += [pscustomobject]@{
        Check = $Name
        Result = if ($Pass) { "PASS" } else { "FAIL" }
        Evidence = $Evidence
    }
}

$labIp = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -like "10.10.10.*" -and $_.IPAddress -ne $DomainControllerIp } |
    Select-Object -First 1

Add-Check "Client has lab IPv4" ([bool]$labIp) ($(if ($labIp) { "$($labIp.IPAddress)/$($labIp.PrefixLength)" } else { "No 10.10.10.x client address" }))

$ping = Test-Connection -ComputerName $DomainControllerIp -Count 2 -Quiet -ErrorAction SilentlyContinue
Add-Check "Reach DC01 by IP" $ping $DomainControllerIp

try {
    $dns1 = Resolve-DnsName $DomainName -Server $DomainControllerIp -ErrorAction Stop
    Add-Check "Resolve domain through DC01 DNS" $true (($dns1 | Select-Object -First 2 Name,Type,IPAddress | Out-String).Trim())
} catch {
    Add-Check "Resolve domain through DC01 DNS" $false $_.Exception.Message
}

try {
    $dns2 = Resolve-DnsName $DomainControllerFqdn -Server $DomainControllerIp -ErrorAction Stop
    Add-Check "Resolve DC01 FQDN" $true (($dns2 | Select-Object -First 2 Name,Type,IPAddress | Out-String).Trim())
} catch {
    Add-Check "Resolve DC01 FQDN" $false $_.Exception.Message
}

$nl = & nltest.exe /dsgetdc:$DomainName 2>&1
Add-Check "Discover domain controller" ($LASTEXITCODE -eq 0) (($nl | Out-String).Trim())

Write-Host "=== VALIDATION SUMMARY ==="
$checks | Format-Table -AutoSize

if ($checks.Result -contains "FAIL") {
    Write-Host "OVERALL: FAIL"
} else {
    Write-Host "OVERALL: PASS"
}

Stop-Transcript
Write-Host "Evidence saved to: $outFile"
