$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../scripts/Lab.Common.ps1"
$count = 0
function Assert-Lab {
    param([bool]$Condition, [string]$Name)
    if (-not $Condition) { throw "FAILED: $Name" }
    $script:count++
    Write-Host "PASS $Name"
}
$root = (Resolve-Path "$PSScriptRoot/..").Path
foreach ($file in @(Get-ChildItem -Path $root -Recurse -File | Where-Object Extension -in @('.ps1','.psd1'))) {
    $tokens = $null; $errors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    Assert-Lab ($errors.Count -eq 0) "PowerShell parses $($file.Name): $($errors -join '; ')"
}
$config = Import-PowerShellDataFile "$root/config/lab.psd1"
Assert-Lab ($config.VmNames -contains 'Win11-Client01') 'Uses actual VirtualBox client name'
$goodA = @([pscustomobject]@{IPAddress='10.10.10.10'})
Assert-Lab (Test-LabARecords $goodA '10.10.10.10') 'Correct single DC address accepted'
Assert-Lab (-not (Test-LabARecords @() '10.10.10.10')) 'Empty successful DNS query cannot pass'
Assert-Lab (-not (Test-LabARecords @([pscustomobject]@{Name='alias'}) '10.10.10.10')) 'Non-address DNS record cannot pass'
Assert-Lab (-not (Test-LabARecords @([pscustomobject]@{IPAddress='10.0.2.15'}) '10.10.10.10')) 'NAT-only DC response rejected'
Assert-Lab (-not (Test-LabARecords ($goodA + [pscustomobject]@{IPAddress='10.0.2.15'}) '10.10.10.10')) 'Mixed lab and NAT DNS regression rejected'
$address = [pscustomobject]@{IPAddress='10.10.10.20'; PrefixLength=24; AddressState='Preferred'}
Assert-Lab (Test-LabClientAddress @($address) '10.10.10.20' 24) 'Valid client address accepted'
$address.PrefixLength=16
Assert-Lab (-not (Test-LabClientAddress @($address) '10.10.10.20' 24)) 'Wrong subnet mask rejected'
$address.PrefixLength=24; $address.AddressState='Duplicate'
Assert-Lab (-not (Test-LabClientAddress @($address) '10.10.10.20' 24)) 'Duplicate address rejected'
Assert-Lab (-not (Test-LabClientAddress @() '10.10.10.20' 24)) 'Missing lab address rejected'
$source = [pscustomobject]@{IPAddress='10.10.10.20'; InterfaceIndex=7}
$route = [pscustomobject]@{NextHop='0.0.0.0'; InterfaceIndex=7}
Assert-Lab (Test-LabSelectedRoute @($source,$route) '10.10.10.20') 'DC route is on-link with expected source'
$route.NextHop='10.0.2.2'
Assert-Lab (-not (Test-LabSelectedRoute @($source,$route) '10.10.10.20')) 'DC route via gateway rejected'
$route.NextHop='0.0.0.0'; $route.InterfaceIndex=9
Assert-Lab (-not (Test-LabSelectedRoute @($source,$route) '10.10.10.20')) 'Route and source interfaces must match'
Assert-Lab (-not (Test-LabSelectedRoute @() '10.10.10.20')) 'Missing route cannot pass'
$vbox = ConvertFrom-LabVBoxInfo @('nic1="nat"','nic2="intnet"','intnet2="ATLASHOME-LAB"','cableconnected2="on"','VMState="poweroff"','memory=2048')
Assert-Lab ((Get-LabVerdict @(Test-LabVBoxInfo $vbox 'Client' 'ATLASHOME-LAB')) -eq 'PASS') 'Valid internal network accepted'
$vbox.intnet2='ATLASHOME-LAB-typo'
Assert-Lab ((Get-LabVerdict @(Test-LabVBoxInfo $vbox 'Client' 'ATLASHOME-LAB')) -eq 'FAIL') 'Different virtual switch rejected'
$vbox.intnet2='atlashome-lab'
Assert-Lab ((Get-LabVerdict @(Test-LabVBoxInfo $vbox 'Client' 'ATLASHOME-LAB')) -eq 'FAIL') 'Network names checked case sensitively'
$vbox.intnet2='ATLASHOME-LAB'; $vbox.cableconnected2='off'
Assert-Lab ((Get-LabVerdict @(Test-LabVBoxInfo $vbox 'Client' 'ATLASHOME-LAB')) -eq 'FAIL') 'Disconnected virtual cable rejected'
$vbox.cableconnected2='on'; $vbox.nic1='bridged'
Assert-Lab ((Get-LabVerdict @(Test-LabVBoxInfo $vbox 'Client' 'ATLASHOME-LAB')) -eq 'REVIEW') 'Unexpected bridge requires review'
Assert-Lab ((Get-LabVerdict @()) -eq 'FAIL') 'Zero checks cannot pass'
Assert-Lab ((Get-LabVerdict @(New-LabCheck 'Info' 'INFO' 'Collected')) -eq 'INCOMPLETE') 'Inventory alone cannot pass'
Assert-Lab ((Get-LabVerdict @((New-LabCheck 'a' 'PASS' ''),(New-LabCheck 'b' 'FAIL' ''))) -eq 'FAIL') 'Any failed required check fails verdict'
Assert-Lab (Test-LabBroadSid 'S-1-5-11') 'Authenticated Users found by SID'
Assert-Lab (Test-LabBroadSid 'S-1-5-21-123-456-789-513') 'Domain Users found by SID'
Assert-Lab (-not (Test-LabBroadSid 'S-1-5-21-123-456-789-1109')) 'Department group is not automatically broad'
$probe = Invoke-LabProbe 'Denied' { throw 'Access denied' }
Assert-Lab ($probe.Status -eq 'FAIL') 'Collector errors cannot silently pass'
# Exercise real sockets against loopback only, not the user lab or the internet.
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
$listener.Start()
$port = $listener.LocalEndpoint.Port
try { Assert-Lab (Test-LabTcp '127.0.0.1' $port) 'Real TCP listener reachable' }
finally { $listener.Stop() }
Assert-Lab (-not (Test-LabTcp '127.0.0.1' $port 500)) 'Closed TCP port rejected'
function Test-NativeFailure { $global:LASTEXITCODE=9; Write-Output 'fixture failure' }
$threw=$false
try { $null = Invoke-LabNative 'Test-NativeFailure' @() } catch { $threw=$true }
Assert-Lab $threw 'Native nonzero exit propagates'
$threw=$false
try { $null = Invoke-LabNative 'no-such-lab-command-182374' @() } catch { $threw=$true }
Assert-Lab $threw 'Missing executable cannot reuse a stale exit code'
$temp = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString('N'))
try {
    $result = Export-LabReport 'TEST' @((New-LabCheck 'Required' 'FAIL' 'Expected fixture')) $temp 'Offline fixture, not live evidence.'
    $report = Get-Content -Raw (Get-ChildItem $temp -Filter '*.json' | Select-Object -First 1).FullName | ConvertFrom-Json
    Assert-Lab ($result -eq 'FAIL' -and $report.Verdict -eq 'FAIL') 'Saved JSON preserves failure verdict'
    Assert-Lab ($report.Checks.Count -eq 1) 'Single-check report stays an array'
    Assert-Lab (@(Get-ChildItem $temp -Filter '*.md').Count -eq 1) 'Readable report produced'
} finally { if (Test-Path $temp) { Remove-Item -LiteralPath $temp -Recurse -Force } }
if ([Environment]::OSVersion.Platform -eq 'Win32NT') {
    $hostTemp = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString('N'))
    try {
        & "$root/scripts/inspect-virtualbox-host.ps1" -VBoxManagePath "$hostTemp/missing.exe" -OutputDirectory $hostTemp
        Assert-Lab ($LASTEXITCODE -eq 1) 'Windows host collector exits nonzero when VirtualBox is absent'
        $hostReport = Get-Content -Raw (Get-ChildItem $hostTemp -Filter '*.json' | Select-Object -First 1).FullName | ConvertFrom-Json
        Assert-Lab ($hostReport.Verdict -eq 'FAIL') 'Windows host failure still produces a structured report'
        Assert-Lab (@($hostReport.Checks | Where-Object Check -eq 'Host resources now').Count -eq 1) 'Windows host continues to collect real resource data'
    } finally { if (Test-Path $hostTemp) { Remove-Item -LiteralPath $hostTemp -Recurse -Force } }
}
Write-Host "PASS: $count assertions. These tests do not validate AJ's live VMs."
