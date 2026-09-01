# Compatibility entrypoint; run inside Win11-Client01, elevated for the trust check.
[CmdletBinding()]
param([string]$OutputDirectory, [switch]$NetworkOnly)
& "$PSScriptRoot/verify-domain-path.ps1" -OutputDirectory $OutputDirectory -NetworkOnly:$NetworkOnly
exit $LASTEXITCODE
