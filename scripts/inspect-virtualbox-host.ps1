[CmdletBinding()]
param([string[]]$VmNames, [string]$VBoxManagePath, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Lab.Common.ps1"
Test-LabWindows
$config = Import-PowerShellDataFile "$PSScriptRoot/../config/lab.psd1"
if (-not $VmNames) { $VmNames = $config.VmNames }
$checks = @()
if (-not $VBoxManagePath) {
    $command = Get-Command VBoxManage.exe -ErrorAction SilentlyContinue
    if ($command) { $VBoxManagePath = $command.Source }
    foreach ($root in @($env:ProgramFiles, ${env:ProgramFiles(x86)})) {
        if (-not $VBoxManagePath -and $root) {
            $candidate = Join-Path $root 'Oracle/VirtualBox/VBoxManage.exe'
            if (Test-Path -LiteralPath $candidate) { $VBoxManagePath = $candidate }
        }
    }
}
if (-not $VBoxManagePath -or -not (Test-Path -LiteralPath $VBoxManagePath)) {
    $checks += New-LabCheck 'VirtualBox executable' 'FAIL' 'VBoxManage.exe was not found.' 'Pass -VBoxManagePath with the installed executable path. Do not reinstall or rebuild VMs yet.'
} else {
    try {
        $version = Invoke-LabNative $VBoxManagePath @('--version')
        $checks += New-LabCheck 'VirtualBox version' 'PASS' $version
        $registered = Invoke-LabNative $VBoxManagePath @('list','vms')
        $checks += New-LabCheck 'Registered VMs' 'INFO' $registered
    } catch { $checks += New-LabCheck 'VirtualBox command' 'FAIL' $_.Exception.Message }
    foreach ($vm in $VmNames) {
        try {
            $raw = Invoke-LabNative $VBoxManagePath @('showvminfo',$vm,'--machinereadable')
            $info = ConvertFrom-LabVBoxInfo -Lines ($raw -split "`n")
            $checks += @(Test-LabVBoxInfo $info $vm $config.InternalNetwork)
        } catch {
            $checks += New-LabCheck "$vm registered" 'FAIL' $_.Exception.Message 'Compare Registered VMs above. A missing name is not proof the virtual disk is gone.'
        }
    }
}
$checks += Invoke-LabProbe 'Host resources now' {
    $os = Get-CimInstance Win32_OperatingSystem
    [pscustomobject]@{ OS=$os.Caption; TotalMemoryGB=[math]::Round($os.TotalVisibleMemorySize/1MB,2);
        FreeMemoryGB=[math]::Round($os.FreePhysicalMemory/1MB,2) }
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' |
        Select-Object DeviceID,@{n='FreeGB';e={[math]::Round($_.FreeSpace/1GB,1)}}
} 'Use current free RAM and configured VM memory before starting a VM pair; avoid booting all four together.'
$checks += New-LabCheck 'Where to run connectivity tests' 'INFO' 'Run them INSIDE the guests. This host is not attached to ATLASHOME-LAB by the Internal Network adapter.'
$result = Export-LabReport 'HOST' $checks $OutputDirectory 'VirtualBox configuration and host capacity only. Guest networking and authentication are not tested.'
if ($result -eq 'FAIL') { exit 1 }
exit 0
