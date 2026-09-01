[CmdletBinding()]
param([ValidateSet('Host','Client','DC')][string]$Role = 'Host', [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$scripts = @{Host='inspect-virtualbox-host.ps1'; Client='verify-domain-path.ps1'; DC='collect-dc01.ps1'}
Write-Host "Selected role: $Role. This runs diagnostics and writes local reports; it does not repair settings."
& (Join-Path $PSScriptRoot "scripts/$($scripts[$Role])") -OutputDirectory $OutputDirectory
exit $LASTEXITCODE
