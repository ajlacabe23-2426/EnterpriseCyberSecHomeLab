# Pure evaluation functions are shared by live collectors and offline regression tests.
Set-StrictMode -Version 2.0

function New-LabCheck {
    param([string]$Name, [ValidateSet('PASS','FAIL','WARN','INFO')][string]$Status,
          [string]$Detail, [string]$Next = '')
    [pscustomobject]@{ Check = $Name; Status = $Status; Detail = $Detail; Next = $Next }
}
function Get-LabVerdict {
    param([object[]]$Checks)
    if (-not $Checks -or @($Checks | Where-Object Status -eq 'FAIL').Count) { return 'FAIL' }
    if (@($Checks | Where-Object Status -eq 'WARN').Count) { return 'REVIEW' }
    if (-not @($Checks | Where-Object Status -eq 'PASS').Count) { return 'INCOMPLETE' }
    return 'PASS'
}
function Test-LabWindows {
    if ([Environment]::OSVersion.Platform -ne 'Win32NT') {
        throw 'Run this collector in Windows PowerShell on the indicated Windows machine.'
    }
}
function Test-LabAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Invoke-LabProbe {
    param([string]$Name, [scriptblock]$Action, [string]$Next = '')
    try {
        $value = & $Action
        New-LabCheck $Name 'INFO' (($value | Out-String -Width 220).Trim()) $Next
    } catch { New-LabCheck $Name 'FAIL' $_.Exception.Message $Next }
}
function Test-LabTcp {
    param([string]$Address, [int]$Port, [int]$TimeoutMs = 2500)
    $socket = New-Object Net.Sockets.TcpClient
    $pending = $null
    try {
        $pending = $socket.BeginConnect($Address, $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne($TimeoutMs)) { return $false }
        $socket.EndConnect($pending)
        return $socket.Connected
    } catch { return $false }
    finally {
        if ($pending) { $pending.AsyncWaitHandle.Close() }
        $socket.Close()
    }
}
function Test-LabARecords {
    param([object[]]$Records, [string]$ExpectedIp)
    $addresses = @($Records | Where-Object { $_.PSObject.Properties['IPAddress'] } |
        ForEach-Object { $_.IPAddress } | Where-Object { $_ } | Select-Object -Unique)
    return ($addresses.Count -eq 1 -and $addresses[0] -eq $ExpectedIp)
}
function ConvertFrom-LabVBoxInfo {
    param([string[]]$Lines)
    $result = @{}
    foreach ($line in $Lines) {
        if ($line -match '^([^=]+)="(.*)"$') { $result[$matches[1]] = $matches[2] }
        elseif ($line -match '^([^=]+)=(.*)$') { $result[$matches[1]] = $matches[2] }
    }
    return $result
}
function Test-LabVBoxInfo {
    param([hashtable]$Info, [string]$VmName, [string]$InternalNetwork)
    $labSlots = @($Info.Keys | Where-Object { $_ -match '^nic\d+$' -and $Info[$_] -eq 'intnet' } |
        ForEach-Object { $_ -replace '^nic','' })
    $matching = @($labSlots | Where-Object { $Info["intnet$_"] -ceq $InternalNetwork })
    if ($matching.Count -ne 1) {
        New-LabCheck "$VmName internal network" 'FAIL' 'Expected exactly one adapter on the named lab network.' 'Check Internal Network name in VirtualBox Settings > Network.'
    } else {
        $slot = $matching[0]
        $ok = $Info["cableconnected$slot"] -eq 'on'
        New-LabCheck "$VmName internal network" $(if ($ok) {'PASS'} else {'FAIL'}) "Adapter $slot; cable=$($Info["cableconnected$slot"]); network=$InternalNetwork" 'A disconnected virtual cable prevents Layer 2 traffic.'
    }
    $modes = @($Info.Keys | Where-Object { $_ -match '^nic\d+$' -and $Info[$_] -ne 'none' } |
        Sort-Object | ForEach-Object { "$_=$($Info[$_])" })
    $outside = @($Info.Keys | Where-Object { $_ -match '^nic\d+$' -and $Info[$_] -notin @('none','nat','intnet') })
    New-LabCheck "$VmName attachment modes" $(if ($outside.Count) {'WARN'} else {'PASS'}) ($modes -join '; ') 'Expected NAT plus Internal Network. Review any bridged, host-only, or NAT Network attachment.'
    New-LabCheck "$VmName power and memory" 'INFO' "State=$($Info['VMState']); memory=$($Info['memory']) MB"
}
function Test-LabClientAddress {
    param([object[]]$Addresses, [string]$ExpectedIp, [int]$PrefixLength)
    $found = @($Addresses | Where-Object IPAddress -eq $ExpectedIp)
    return ($found.Count -eq 1 -and $found[0].PrefixLength -eq $PrefixLength -and $found[0].AddressState -eq 'Preferred')
}
function Export-LabReport {
    param([string]$Role, [object[]]$Checks, [string]$OutputDirectory,
          [string]$Scope = 'Only the checks listed here; this does not certify the whole lab.')
    if (-not $OutputDirectory) { $OutputDirectory = Join-Path $PSScriptRoot '../evidence/private' }
    $null = New-Item -ItemType Directory -Path $OutputDirectory -Force
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    $id = [guid]::NewGuid().ToString('N').Substring(0,8)
    $base = Join-Path $OutputDirectory "$Role-$stamp-$id"
    $verdict = Get-LabVerdict $Checks
    $report = [ordered]@{ SchemaVersion=1; Role=$Role; CollectedAt=(Get-Date).ToUniversalTime().ToString('o');
        Computer=$env:COMPUTERNAME; Verdict=$verdict; Scope=$Scope; Checks=@($Checks) }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath "$base.json" -Encoding UTF8
    $lines = @("# $Role report", '', "UTC: $($report.CollectedAt)", "Verdict: $verdict", '', $Scope, '')
    foreach ($check in $Checks) {
        $lines += @("## [$($check.Status)] $($check.Check)", '', '```text', $check.Detail, '```', '')
        if ($check.Next) { $lines += @("Next: $($check.Next)", '') }
    }
    $lines | Set-Content -LiteralPath "$base.md" -Encoding UTF8
    $Checks | Select-Object Check,Status,Detail,Next | Format-Table -Wrap -AutoSize | Out-Host
    Write-Host "SCOPE: $Scope"
    Write-Host "RESULT: $verdict"
    Write-Host "Report: $base.md"
    Write-Host "JSON: $base.json"
    Write-Host 'Reports stay local. Review personal identifiers before sharing; do not commit raw output.'
    return $verdict
}

function Invoke-LabNative {
    param([string]$Executable, [string[]]$Arguments)
    # Windows PowerShell 5.1 treats redirected native stderr as ErrorRecord objects.
    $null = Get-Command $Executable -ErrorAction Stop
    $ErrorActionPreference = 'Continue'
    $output = & $Executable @Arguments 2>&1
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "$Executable exited $code : $($output -join ' ')" }
    return ($output -join "`n")
}
function Test-LabBroadSid {
    param([string]$Sid)
    return ($Sid -in @('S-1-1-0','S-1-5-11','S-1-5-32-545') -or $Sid -match '^S-1-5-21-\d+-\d+-\d+-513$')
}

function Test-LabSelectedRoute {
    param([object[]]$Selection, [string]$ExpectedSource)
    $source = @($Selection | Where-Object { $_.PSObject.Properties['IPAddress'] -and $_.IPAddress -eq $ExpectedSource })
    $route = @($Selection | Where-Object { $_.PSObject.Properties['NextHop'] -and $_.NextHop -eq '0.0.0.0' })
    return ($source.Count -eq 1 -and $route.Count -eq 1 -and $source[0].InterfaceIndex -eq $route[0].InterfaceIndex)
}
