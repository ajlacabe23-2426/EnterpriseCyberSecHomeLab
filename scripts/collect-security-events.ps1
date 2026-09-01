[CmdletBinding()]
param([ValidateRange(1,24)][int]$Hours = 2, [ValidateRange(1,100)][int]$MaxEvents = 30, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Lab.Common.ps1"
Test-LabWindows
$checks = @()
try {
    if (-not (Test-LabAdministrator)) { throw 'Run elevated on the lab Windows guest to read its Security log.' }
    $system = Get-CimInstance Win32_ComputerSystem
    if ($system.Domain -ine 'atlasiqlab.local') { throw 'Run on a Windows guest joined to atlasiqlab.local.' }
    $filter = @{LogName='Security'; Id=@(4624,4625,4740,4768,4769,4771,4776); StartTime=(Get-Date).AddHours(-$Hours)}
    try { $events = @(Get-WinEvent -FilterHashtable $filter -MaxEvents $MaxEvents -ErrorAction Stop) }
    catch {
        if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') { $events = @() }
        else { throw }
    }
    $rows = foreach ($event in $events) {
        [xml]$xml = $event.ToXml()
        $fields = @{}
        foreach ($node in $xml.Event.EventData.Data) { $fields[$node.Name] = $node.InnerText }
        [pscustomobject]@{
            UTC=$event.TimeCreated.ToUniversalTime().ToString('o'); Id=$event.Id; RecordId=$event.RecordId;
            TargetUser=$fields['TargetUserName']; TargetDomain=$fields['TargetDomainName'];
            LogonType=$fields['LogonType']; SourceIp=$fields['IpAddress'];
            Workstation=$fields['WorkstationName']; Status=$fields['Status']; SubStatus=$fields['SubStatus']
        }
    }
    $checks += New-LabCheck 'Matching security events' $(if ($events.Count) {'INFO'} else {'WARN'}) "Returned $($events.Count) event(s), capped at $MaxEvents, within $Hours hour(s)." 'No events can mean auditing, timing, log location or no matching action. It is not proof of no activity.'
    $checks += New-LabCheck 'Selected event fields' 'INFO' (($rows | Format-List | Out-String -Width 220).Trim())
    $checks += New-LabCheck 'Detection verification' 'WARN' 'Human correlation pending: match UTC time, test account, source and result to the exercise.' 'See docs/DETECTION_LAB.md. Raw XML/messages and credentials are not exported.'
} catch { $checks += New-LabCheck 'Security event collection' 'FAIL' $_.Exception.Message }
$result = Export-LabReport 'SECURITY' $checks $OutputDirectory 'Bounded local event inventory; no audit-policy changes, forwarding configuration, or SIEM deployment.'
if ($result -eq 'FAIL') { exit 1 }
exit 0
