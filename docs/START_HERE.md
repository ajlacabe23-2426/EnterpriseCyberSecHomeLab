# Start here: live homelab verification

The repository preparation is ready. Live VM results are still pending. Start on the **physical Windows computer**, with the VM windows closed or left as they are; this first command does not start or stop them.

## 1. Get the prepared recovery branch

Use the Git checkout below for the current scripts. The previously downloaded private recovery kit is also usable: extract it and run the host command from the folder containing `Start-Lab.ps1`. Its publication-status notes describe the earlier snapshot.

In Windows PowerShell, use a new folder so existing edits are preserved:

```powershell
Set-Location $env:USERPROFILE
$labFolder = Join-Path $env:USERPROFILE ('EnterpriseCyberSecHomeLab-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
git clone --branch fix/client01-dc01-connectivity --single-branch https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab.git $labFolder
if ($LASTEXITCODE -ne 0) { throw 'Clone failed. Stop here and share the error.' }
Set-Location $labFolder
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab.ps1 -Role Host
```

`-ExecutionPolicy Bypass` applies to that child PowerShell process only. It does not persist a machine policy change. Use only for this reviewed lab checkout, not a work-managed system with restrictions. If organizational policy blocks it, report the error rather than changing policy.

If Git is unavailable, open [the recovery branch](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/tree/fix/client01-dc01-connectivity), choose **Code > Download ZIP**, extract the whole folder, open PowerShell there, and run the final command above. Keep `config` and `scripts` together with `Start-Lab.ps1`.

## 2. Return the host report

The command prints its Markdown and JSON paths under `evidence/private/`. Send the Markdown report back for review. It includes VM names and resource information; review it for personal identifiers. No automatic upload occurs.

The output answers:

- Does VirtualBox exist and can its management command run?
- Are the actual VMs `DC01`, `Win11-Client01`, `UBUNTU01`, and `Kali01` registered?
- Is each attached to exactly one `ATLASHOME-LAB` internal network with its cable connected?
- Is an unexpected bridge or other attachment present?
- What RAM is available now, and how much is configured per VM?

A missing optional VM can fail the full inventory without blocking work on the DC/client pair. Inspect by check, not just the headline result. If VM names differ, pass the actual names to `scripts/inspect-virtualbox-host.ps1 -VmNames ...`; do not rename or rebuild VMs to satisfy a script.

## 3. After reviewing resources: DC01 + Windows client

Start only the required pair if current free RAM supports it. Wait for DC01 to finish booting before testing the client. Historical memory constraints make booting all four VMs a poor default; the report provides current evidence before deciding.

Get the same checkout **inside each guest** using Git or the branch ZIP. Guest NAT can provide outbound download access. If the guest cannot download it, use a temporary VirtualBox shared folder to copy only this repository, then remove the share. Do not attach a guest to the home LAN simply to transfer these files.

Inside **DC01**, in an elevated Windows PowerShell window:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab.ps1 -Role DC
```

Inside **Win11-Client01**, elevated:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Start-Lab.ps1 -Role Client
```

A not-yet-joined client should fail the membership/trust checks. To isolate pre-join network readiness:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-domain-path.ps1 -NetworkOnly
```

A NetworkOnly PASS does not prove domain membership or login. The script never joins or repairs the domain automatically.

## 4. Make only the repair supported by the output

Use [the recovery decision table](NETWORK_RECOVERY_RUNBOOK.md). Capture before/after results and preserve the existing working configuration. No collectors edit NICs, IPs, DNS, firewall rules, users, passwords, groups or ACLs.

## 5. Learn and verify

1. [Networking and domain login](NETWORK_AND_IDENTITY_LAB.md)
2. [SMB allowed and denied access](ACCESS_CONTROL_LAB.md)
3. [Windows authentication event investigation](DETECTION_LAB.md)

Stop after a working, documented milestone. Centralized logging and more security tools come after baseline verification.

## Other collectors

Inside UBUNTU01, with DC01 running:

```bash
bash scripts/collect-ubuntu.sh
```

On an elevated lab Windows guest after a controlled test login:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\collect-security-events.ps1
```

Report meanings: PASS = the listed required checks passed; FAIL = a required check or collection failed; REVIEW = warnings need judgment; INCOMPLETE = inventory only. Client verification returns exit 1 unless its selected scope passes. Inventory collectors return exit 1 on failures, but may return 0 with REVIEW; always read the scope and report.
