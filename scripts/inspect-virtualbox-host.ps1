[CmdletBinding()]
param(
    [string[]]$VmNames = @("DC01","CLIENT01")
)

$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$evidenceDir = Join-Path $PSScriptRoot "..\evidence"
New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
$outFile = Join-Path $evidenceDir "HOST-virtualbox-$stamp.txt"

$possiblePaths = @(
    "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe",
    "$env:ProgramFiles(x86)\Oracle\VirtualBox\VBoxManage.exe"
)

$vbox = $possiblePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

Start-Transcript -Path $outFile -Force

Write-Host "=== VIRTUALBOX HOST INSPECTION ==="
Get-Date
hostname

if (-not $vbox) {
    Write-Host "VBoxManage.exe was not found in the standard Oracle VirtualBox install paths."
    Write-Host "Checked:"
    $possiblePaths
    Stop-Transcript
    exit 1
}

Write-Host "VBoxManage: $vbox"
& $vbox --version

Write-Host "=== REGISTERED VMS ==="
& $vbox list vms

foreach ($vm in $VmNames) {
    Write-Host "=== $vm ==="
    & $vbox showvminfo $vm --machinereadable 2>&1 |
        Select-String -Pattern 'name=|VMState=|nic[0-9]+=|nictype[0-9]+=|intnet[0-9]+=|cableconnected[0-9]+='
}

Stop-Transcript
Write-Host "Evidence saved to: $outFile"
