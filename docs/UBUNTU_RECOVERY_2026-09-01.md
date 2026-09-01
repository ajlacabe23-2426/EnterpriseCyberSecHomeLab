# Ubuntu recovery checkpoint — 2026-09-01

## Evidence and scope

These observations come from user-provided Windows and Ubuntu screenshots and pasted output. The assistant did not remotely execute commands on the physical host or VM. No credentials or raw screenshots are published in this record.

## Host constraint

- Windows 11 Home, Lenovo Yoga 7 2-in-1 14AHP9, type 83DK; VirtualBox 7.1.6r167084.
- Task Manager showed 8 GB installed, 2.2 GB hardware reserved and approximately 5.8 GB usable. At one post-restart observation, only 291 MB was available.
- Lenovo specifies soldered memory with no expansion slots. Graphics reservation was considered as a possible contributor, but no BIOS change or reclaimed RAM was verified. BIOS troubleshooting was stopped at the user's request.
- Registered guests were DC01 (2048 MB), Win11-Client01 (3072 MB), UBUNTU01 (1536 MB) and Kali01 (1792 MB), each with two virtual CPUs, NAT on adapter 1 and internal network ATLASHOME-LAB on adapter 2.
- Only UBUNTU01 was instructed to start. It reached a login shell with its existing allocation. This demonstrates that one Ubuntu guest could boot in the observed conditions; it does not prove capacity for the other guests or the complete lab.
- Windows Start/Search recovery was not confirmed.

## Ubuntu observations before patching

| Check | Observed result |
|---|---|
| OS login banner | Ubuntu 24.04.4 LTS, kernel 6.8.0-137-generic x86_64 |
| Guest memory from free -h | 1.4 GiB total, 331 MiB used, 1.1 GiB available |
| Guest swap | 2.0 GiB total, 0 B used |
| NAT interface | enp0s3 UP, 10.0.2.15/24 |
| Internal lab interface | enp0s8 UP, 10.10.10.30/24 |
| Default route | via 10.0.2.2 dev enp0s3, metric 100 |
| Connected lab route | 10.10.10.0/24 dev enp0s8 |
| SSH service check | systemctl is-active ssh returned active |
| Patch banner | 69 available updates, including 23 standard security updates; metadata freshness not verified |

The memory figures above describe the guest, not remaining host RAM. Interface and route output does not prove Internet access, working DNS or connectivity to another guest.

## Access recovery

The initial Start-Lab.ps1 attempt ran from C:\Windows\system32, where the repository files were absent. Pasting the script body into an interactive console then left PSScriptRoot empty. Neither error established that the guest itself was broken. Self-contained commands were used for the machine-side troubleshooting.

The user initially joined independent Ubuntu diagnostic commands with pipes. Running them separately exposed the memory, interface and route results.

Windows showvminfo output filtered for Forwarding returned no matching rules. The next procedure added the following rule while UBUNTU01 was running:

```powershell
& "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe" controlvm "UBUNTU01" natpf1 "ubuntu-ssh,tcp,127.0.0.1,2222,10.0.2.15,22"
```

The supplied connection command used SSH to 127.0.0.1 on port 2222 with the user's existing Ubuntu account. The user then supplied an Ubuntu welcome banner and shell prompt. Subsequent journal output recorded an accepted password and session opening at September 1, 23:06:06 from 10.0.2.2, consistent with the VirtualBox NAT path. Older August 27 failed passwords from 10.10.10.10 were followed by an accepted login; they are separate historical events. The host-key verification step was not captured.

An attempted environment-variable check used mixed-case SSH_Connection. Linux variable names are case-sensitive; its empty output cannot establish the connection type. The correct variable is SSH_CONNECTION. The journal provides the observed authentication evidence.

The rule targets Ubuntu TCP port 22 through the NAT adapter and binds the host side to loopback. It leaves the internal lab network unchanged. Do not repeatedly add the same named rule; inspect existing rules first. To remove this particular rule while the guest is running:

```powershell
& "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe" controlvm "UBUNTU01" natpf1 delete "ubuntu-ssh"
```

## Security checks, patching and firewall activation

The user ran these checks as separate commands in the Ubuntu shell:

```bash
echo "$SSH_CONNECTION"
sudo ss -lntup
sudo ufw status verbose
sudo journalctl -u ssh.service -n 15 --no-pager
```

Observed listeners included SSH on TCP/22 for IPv4 and IPv6, loopback DNS on port 53, and the NAT-facing DHCP client on UDP/68. UFW was inactive, and its added-rules report showed no custom user rules.

The user was instructed to run apt update, then apt upgrade. The supplied ending output showed service restarts and a request to reboot for a new kernel. After the requested guest reboot, later screenshots showed:

| Check | Observed result |
|---|---|
| Running kernel from uname -r | 6.8.0-138-generic, changed from 6.8.0-137-generic |
| Failed-unit query | 0 loaded units listed |
| sudo dpkg --audit | No findings printed |
| Post-upgrade login banner | 0 updates can be applied immediately |
| Guest usage in login banner | 14% memory, 0% swap; not a host-capacity measurement |

The zero-update banner describes that observation and configured update sources; it is not a guarantee that every vulnerability is remediated. Full update logs were not collected.

The following UFW configuration was applied in the guest:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow in on enp0s3 from 10.0.2.2 to any port 22 proto tcp
sudo ufw allow in on enp0s8 from 10.10.10.0/24 to any port 22 proto tcp
sudo ufw enable
sudo ufw status verbose
```

The status screenshot confirmed active UFW, logging on at low level, default deny incoming / allow outgoing, and both intended SSH rules. Activation reported enablement on system startup. A fresh SSH login was then requested from a second Windows PowerShell window; the user supplied the new login screen at 23:34:42 and the updated kernel output. This is the successful allowed-access test after activation. It does not test blocked traffic or prove the internal-network rule with another guest.

Guest-reboot recovery and fresh access were observed during this sequence. Persistence after a full VirtualBox power-off/start cycle and UFW behavior after its next reboot have not yet been tested. Keep console access available when later changing SSH or firewall settings.

## Next action

Perform the [single-attempt Linux authentication exercise](LINUX_AUTHENTICATION_LAB.md). Correlate a deliberately wrong password with its rejection event. The exercise is prepared; no new controlled failure result has been supplied yet. Authentication rejection is distinct from a network firewall denial.

DC01/client connectivity, domain authentication, effective SMB authorization and centralized detection remain separate open gates. This checkpoint does not mark the entire lab healthy.

## References

- [Lenovo model specifications](https://psref.lenovo.com/syspool/Sys/PDF/Yoga/Yoga_7_2_in_1_14AHP9/Yoga_7_2_in_1_14AHP9_Spec.PDF)
- [VirtualBox 7.1 networking and NAT forwarding](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/networkingdetails.html)
- [VirtualBox 7.1 controlvm](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/vboxmanage.html)
- [Ubuntu OpenSSH documentation](https://ubuntu.com/server/docs/how-to/security/openssh-server/)
- [Ubuntu firewall documentation](https://ubuntu.com/server/docs/how-to/security/firewalls/)
