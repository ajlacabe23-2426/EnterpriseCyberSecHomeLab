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

## Ubuntu observations

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

The supplied connection command used SSH to 127.0.0.1 on port 2222 with the user's existing Ubuntu account. The user then supplied an Ubuntu welcome banner and shell prompt. This is evidence of a successful login after the procedure; the screenshot does not independently expose SSH_CONNECTION, the authentication method or the host-key verification step. Capture those session/log details next. Reconnection and forwarding persistence after a VM restart remain untested.

The rule targets Ubuntu TCP port 22 through the NAT adapter and binds the host side to loopback. It leaves the internal lab network unchanged. Do not repeatedly add the same named rule; inspect existing rules first. To remove this particular rule while the guest is running:

```powershell
& "$env:ProgramFiles\Oracle\VirtualBox\VBoxManage.exe" controlvm "UBUNTU01" natpf1 delete "ubuntu-ssh"
```

## Next machine checks

Run these as separate commands in the Ubuntu shell:

```bash
echo "$SSH_CONNECTION"
sudo ss -lntup
sudo ufw status verbose
sudo journalctl -u ssh.service -n 15 --no-pager
```

Interpret the session endpoints, expected listeners, firewall policy and recent authentication events before changing access controls. Keep console access available when later changing SSH or firewall settings. Then verify repository/DNS access, refresh package metadata and apply the applicable updates. The banner alone does not establish current patch counts or completed patching.

DC01/client connectivity, domain authentication, effective SMB authorization and centralized detection remain separate open gates. This checkpoint does not mark the entire lab healthy.

## References

- [Lenovo model specifications](https://psref.lenovo.com/syspool/Sys/PDF/Yoga/Yoga_7_2_in_1_14AHP9/Yoga_7_2_in_1_14AHP9_Spec.PDF)
- [VirtualBox 7.1 networking and NAT forwarding](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/networkingdetails.html)
- [VirtualBox 7.1 controlvm](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/vboxmanage.html)
- [Ubuntu OpenSSH documentation](https://ubuntu.com/server/docs/how-to/security/openssh-server/)
- [Ubuntu firewall documentation](https://ubuntu.com/server/docs/how-to/security/firewalls/)
