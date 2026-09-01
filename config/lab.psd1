@{
    DomainName = 'atlasiqlab.local'
    DomainControllerFqdn = 'DC01.atlasiqlab.local'
    DomainControllerIp = '10.10.10.10'
    ClientIp = '10.10.10.20'
    UbuntuIp = '10.10.10.30'
    PrefixLength = 24
    InternalNetwork = 'ATLASHOME-LAB'
    VmNames = @('DC01', 'Win11-Client01', 'UBUNTU01', 'Kali01')
    RequiredPorts = @(53, 88, 135, 389, 445)
    Shares = @('AtlasIQ-Finance', 'AtlasIQ-Executives', 'AtlasIQ-IT', 'AtlasIQ-Security', 'AtlasIQ-Public')
}
