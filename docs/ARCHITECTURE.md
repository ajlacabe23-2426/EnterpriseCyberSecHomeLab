# Architecture

## Overview

The homelab is designed as a small enterprise environment running in VirtualBox. It combines Windows domain services, Linux administration, internal networking, and controlled access to departmental resources.

## Core components

### Windows domain services

- Domain: `atlasiqlab.local`
- Active Directory Domain Services
- DNS service
- Organizational Units for department-based administration
- Security groups for role-based access
- Departmental file shares

### Linux systems

- Ubuntu server VM
- SSH enabled and validated
- Internal-network connectivity through `ATLASHOME-LAB`

### Virtual networking

Lab systems use two network concepts:

1. NAT connectivity for controlled outbound access when needed.
2. Internal network `ATLASHOME-LAB` for communication between lab systems.

## Logical architecture

```text
Host Computer
    |
    +-- VirtualBox
          |
          +-- Windows Server / Domain Services
          |      +-- Active Directory
          |      +-- DNS
          |      +-- File Shares
          |
          +-- Ubuntu Server
          |
          +-- Windows Client (stabilization in progress)
          |
          +-- ATLASHOME-LAB Internal Network
```

## Design goals

- Centralized identity management
- Department-based access control
- Least-privilege permissions
- Repeatable administrative validation
- Clear separation between verified controls and planned improvements
- Documentation suitable for technical review and portfolio presentation
