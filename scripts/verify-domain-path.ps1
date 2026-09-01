[CmdletBinding()]
param([switch]$NetworkOnly, [string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/Lab.Common.ps1"
Test-LabWindows
$config = Import-PowerShellDataFile "$PSScriptRoot/../config/lab.psd1"
$checks = @()
try {
    $system = Get-CimInstance Win32_ComputerSystem
    if ($system.DomainRole -ge 4) { throw 'Run the client validator inside Win11-Client01, not on DC01.' }
    $addresses = @(Get-NetIPAddress -AddressFamily IPv4)
    $validAddress = Test-LabClientAddress $addresses $config.ClientIp $config.PrefixLength
    $checks += New-LabCheck 'Client lab address and prefix' $(if ($validAddress) {'PASS'} else {'FAIL'}) (($addresses | Select-Object InterfaceIndex,IPAddress,PrefixLength,AddressState | Out-String).Trim()) 'Expected one Preferred 10.10.10.20/24 address on the lab adapter.'
    $labAddresses = @($addresses | Where-Object IPAddress -eq $config.ClientIp)
    if ($labAddresses.Count -eq 1) {
        $index = $labAddresses[0].InterfaceIndex
        $adapter = Get-NetAdapter | Where-Object ifIndex -eq $index | Select-Object -First 1
        $checks += New-LabCheck 'Lab adapter link' $(if ($adapter.Status -eq 'Up') {'PASS'} else {'FAIL'}) "$($adapter.Name): $($adapter.Status)"
        $dns = @(Get-DnsClientServerAddress -InterfaceIndex $index -AddressFamily IPv4 | ForEach-Object ServerAddresses)
        $checks += New-LabCheck 'Lab adapter DNS configuration' $(if ($dns.Count -eq 1 -and $dns[0] -eq $config.DomainControllerIp) {'PASS'} else {'FAIL'}) ($dns -join ', ') 'The lab NIC must use only 10.10.10.10 for this single-DC lab.'
        $gateways = @(Get-NetRoute -InterfaceIndex $index -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue)
        $checks += New-LabCheck 'No lab default gateway' $(if (-not $gateways.Count) {'PASS'} else {'FAIL'}) (($gateways | Out-String).Trim()) 'Outbound default route belongs on NAT; do not assign DC01 as the lab gateway.'
    }
    try {
        $selectedRoute = @(Find-NetRoute -RemoteIPAddress $config.DomainControllerIp)
        $routeOK = Test-LabSelectedRoute $selectedRoute $config.ClientIp
        $checks += New-LabCheck 'Route selected for DC01' $(if ($routeOK) {'PASS'} else {'FAIL'}) (($selectedRoute | Format-List | Out-String).Trim()) 'Expected source 10.10.10.20 and an on-link route through the same interface.'
    } catch { $checks += New-LabCheck 'Route selected for DC01' 'FAIL' $_.Exception.Message }
    $ping = Test-Connection -ComputerName $config.DomainControllerIp -Count 1 -Quiet -ErrorAction SilentlyContinue
    $checks += New-LabCheck 'ICMP to DC01 (advisory)' 'INFO' "Reply=$ping. Lack of ICMP alone does not prove a broken service path."
    foreach ($port in $config.RequiredPorts) {
        $open = Test-LabTcp $config.DomainControllerIp $port
        $checks += New-LabCheck "DC01 TCP/$port" $(if ($open) {'PASS'} else {'FAIL'}) "$($config.DomainControllerIp):$port" 'A successful TCP connection proves a listener/path, not authentication or all AD requirements.'
    }
    foreach ($server in @('configured resolver', $config.DomainControllerIp)) {
        foreach ($name in @($config.DomainName, $config.DomainControllerFqdn)) {
            try {
                $queryParameters = @{Name=$name; Type='A'; DnsOnly=$true; NoHostsFile=$true; ErrorAction='Stop'}
                if ($server -ne 'configured resolver') { $queryParameters.Server = $server }
                $records = @(Resolve-DnsName @queryParameters)
                $correct = Test-LabARecords $records $config.DomainControllerIp
                $checks += New-LabCheck "A record: $name via $server" $(if ($correct) {'PASS'} else {'FAIL'}) (($records | Out-String).Trim()) 'Expected only 10.10.10.10; a NAT address or empty answer fails.'
            } catch { $checks += New-LabCheck "A record: $name via $server" 'FAIL' $_.Exception.Message }
        }
        try {
            $queryParameters = @{Name="_ldap._tcp.dc._msdcs.$($config.DomainName)"; Type='SRV'; DnsOnly=$true; NoHostsFile=$true; ErrorAction='Stop'}
            if ($server -ne 'configured resolver') { $queryParameters.Server = $server }
            $records = @(Resolve-DnsName @queryParameters)
            $srv = @($records | Where-Object { $_.PSObject.Properties['NameTarget'] -and $_.NameTarget.TrimEnd('.') -ieq $config.DomainControllerFqdn -and $_.Port -eq 389 })
            $checks += New-LabCheck "AD SRV discovery via $server" $(if ($srv.Count) {'PASS'} else {'FAIL'}) (($records | Out-String).Trim()) 'Expected DC01.atlasiqlab.local on LDAP port 389.'
        } catch { $checks += New-LabCheck "AD SRV discovery via $server" 'FAIL' $_.Exception.Message }
    }
    try {
        $discovery = Invoke-LabNative 'nltest.exe' @("/dsgetdc:$($config.DomainName)",'/force')
        $checks += New-LabCheck 'DC locator' 'PASS' $discovery
    } catch { $checks += New-LabCheck 'DC locator' 'FAIL' $_.Exception.Message }
    if (-not $NetworkOnly) {
        $joined = $system.PartOfDomain -and $system.Domain -ieq $config.DomainName
        $checks += New-LabCheck 'Joined to expected AD domain' $(if ($joined) {'PASS'} else {'FAIL'}) "Computer=$($system.Name); domain=$($system.Domain); joined=$($system.PartOfDomain)"
        if ($joined -and (Test-LabAdministrator)) {
            try {
                $trust = Test-ComputerSecureChannel -Server $config.DomainControllerFqdn -ErrorAction Stop
                $checks += New-LabCheck 'Computer secure channel' $(if ($trust) {'PASS'} else {'FAIL'}) "Trusted=$trust. No repair attempted."
            } catch { $checks += New-LabCheck 'Computer secure channel' 'FAIL' $_.Exception.Message }
        } else {
            $checks += New-LabCheck 'Computer secure channel' 'FAIL' 'Not tested: join the expected domain and run elevated inside the client.'
        }
    }
    $checks += Invoke-LabProbe 'DNS on all active adapters' {
        foreach ($nic in @(Get-NetAdapter | Where-Object Status -eq 'Up')) {
            Get-DnsClientServerAddress -InterfaceIndex $nic.ifIndex | Select-Object InterfaceAlias,AddressFamily,ServerAddresses
        }
    } 'If default-resolver queries fail but forced DC queries pass, inspect NAT/public DNS and .local resolution.'
    $checks += Invoke-LabProbe 'Neighbors after probes' { Get-NetNeighbor -AddressFamily IPv4 | Select-Object InterfaceIndex,IPAddress,LinkLayerAddress,State }
} catch { $checks += New-LabCheck 'Client collection prerequisite' 'FAIL' $_.Exception.Message }
$scope = if ($NetworkOnly) { 'Network and domain discovery only; domain membership and trust deliberately excluded.' } else { 'Network, domain discovery, membership and computer trust. Interactive user login, SMB authorization, UDP/RPC completeness and event correlation still require live exercises.' }
$result = Export-LabReport 'CLIENT01' $checks $OutputDirectory $scope
if ($result -ne 'PASS') { exit 1 }
exit 0
