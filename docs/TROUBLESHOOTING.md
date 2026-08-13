# Troubleshooting Log

## Windows client VM instability

### Symptom

The Windows client virtual machine became unreliable during setup and recovery attempts.

### Impact

This delayed completion of the domain-client portion of the lab.

### Response

The issue was isolated from the rest of the environment rather than allowing it to block all homelab progress. Core server, identity, Linux, and documentation work continued while the client issue remained open.

### Lesson

A lab should be modular enough that one failed endpoint does not stop progress on unrelated infrastructure work.

## Ubuntu SSH service

### Symptom

SSH was initially inactive after the Ubuntu server was created or reinstalled.

### Response

The service state and connectivity were corrected and SSH access was subsequently validated.

### Lesson

Service installation, service state, network reachability, and application-level connectivity should be validated independently.

## VirtualBox connectivity

### Symptom

Virtual-machine connectivity produced connection-closed behavior during setup.

### Response

Networking was reviewed around the intended NAT plus internal-network design.

### Lesson

Virtual networking should be documented as part of the system architecture rather than treated as an invisible dependency.

## Documentation rule

Every significant issue should record the symptom, impact, remediation, validation result, and lesson learned. This turns troubleshooting into reusable technical evidence rather than lost work.
