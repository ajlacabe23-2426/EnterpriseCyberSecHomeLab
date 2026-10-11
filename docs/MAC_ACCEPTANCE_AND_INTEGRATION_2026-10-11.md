# Mac acceptance and PR integration handoff — 2026-10-11

**Status:** READY FOR MANUAL ACCEPTANCE (checklist only). This document records planned checks; **none of the Mac/UTM checks below was performed by this documentation change**. Keep fictional/test data separate from real host evidence.

## Remote evidence baseline

All SHAs refer to PR heads inspected or updated on 2026-10-11. The historical #3–#7 PR-head GitHub Actions workflow runs were **completed / success** at those SHAs; PR #8 was updated with a timestamp-validation fix and its new SHA's GitHub Actions run completed successfully. It still needs integrated-system and Mac verification. None is an integrated-system test.

| PR | Branch | Frozen inspected head | Verified GitHub Actions workflow | Integration state |
| --- | --- | --- | --- | --- |
| [#3](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/3) | `feat/promptguard-lab-v1` | `1109786433e7781eafb1155010d4bcc9ce74ae35` | Verify PromptGuard Lab: success | Open; prerequisite for #4 |
| [#4](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/4) | `feat/promptguard-local-dashboard-v2` | `25aeb1e1d90d4fe8f2b1a73e89900ba20c042d3b` | Verify PromptGuard Lab: success | Open; base is #3 branch; prerequisite for #6 |
| [#6](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/6) | `feat/promptguard-source-evaluation-v3` | `763ea913e9ee303cd3bc018ceb23a6d9f1ce3158` | Verify PromptGuard Lab: success | Open; base is #4 branch |
| [#5](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/5) | `feat/soc-detection-engine-v1` | `4b5a9e894504814ec661bcfe6a99dd64d1e65130` | Verify SOC Detection Engine: success | Open; based on main |
| [#7](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/7) | `feat/linux-hardening-auditor-v1` | `0e173a9a4846d829d7c5c48c60c626f2267af72e` | Verify Linux Hardening Auditor: success | Open; based on main |
| [#8](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/8) | `feat/incident-response-toolkit-v1` | `eed9057df422bf609a096976e994da1f1a1a7151` | Verify Incident Response Toolkit: success | Open; based on main |

**Important:** All of #3, #5, #7 and #8 add a different section to main's `README.md`. Review and retain **all** sections during integration; independently green CI does not prove the later merges will be conflict-free. #1 is an older Windows/VirtualBox diagnostics draft (`2046f9054a97e8a97db01a8565d7133762767058`, currently not mergeable) and should **not** be merged into the Mac migration by assumption. #2 was previously merged. #9 is a governance draft; its changes require their own review.

## Guardrails for the session

- MacBook Air M3 / Apple Silicon / 8 GB unified memory is the recorded target. Only proceed on personally controlled, isolated virtual hosts. No external scans, real credentials, sensitive input, production data, paid services or hosted configuration changes.
- First check current repository branch and working-tree state. Do not switch branches with uncommitted user changes. Commands below use separate **detached worktrees** on candidate PR commits (the checkouts are writable, so avoid edits) and do not merge anything.
- Keep test fixture results separate from **host-observed** measurements. Screenshots must redact identifying details, usernames, tokens, non-lab addresses and raw logs before being shared or committed.
- Capture date/time, macOS / UTM version, Git SHA, test command, expected result, observed result, sanitized evidence reference and PASS/FAIL/BLOCKED for each gate. Record exact failures rather than retitling them as PASS.
- Full-stack acceptance requires a new combined candidate after authorized integration. Individual PR tests do not certify a shared runtime.

## A. Mac inventory and VM topology — MANUAL, NOT RUN

- [ ] Verify actual Mac host architecture, OS, available memory and Python version; record `uname -m`, `sw_vers`, `python3 --version`, and memory observations. Do not infer usable VM capacity from installed RAM.
- [ ] Open UTM; record **actual** machines present, CPU/RAM assigned, network mode/adapter, state, and each role: KALI01, UBUNTU01, SEC01, DC01, Win11-Client01. Mark absent/rebuild-pending explicitly.
- [ ] Verify the private lab network is isolated from unintended external targets; distinguish intentionally configured shared/NAT Internet access from private host-to-host links.
- [ ] Check approved teardown / VM backup strategy without deleting anything. Record known-good baseline and resource-pressure blockers.

## B. Prepare clean candidate checkouts — MANUAL, NOT RUN

With Git and Python 3.11+ available, from the **repository root** of a clean clone (or existing clean repository). Each later command block also starts from this repository root; stay in the same Terminal session so the exported `HOMELAB_ROOT` variable remains available; each module command uses that absolute root even if the current directory changes:

```sh
git status --short
# Stop if the working tree is not clean; preserve local changes.
export HOMELAB_ROOT="$PWD"
git fetch origin
git worktree add --detach "$HOMELAB_ROOT/../homelab-promptguard" origin/feat/promptguard-source-evaluation-v3
git worktree add --detach "$HOMELAB_ROOT/../homelab-soc" origin/feat/soc-detection-engine-v1
git worktree add --detach "$HOMELAB_ROOT/../homelab-audit" origin/feat/linux-hardening-auditor-v1
git worktree add --detach "$HOMELAB_ROOT/../homelab-ir" origin/feat/incident-response-toolkit-v1
```

Record each `git -C "$HOMELAB_ROOT/../homelab-..." rev-parse HEAD` and compare with the SHA table. **If a branch has changed, stop and rebaseline the evidence instead of asserting the old CI success applies to it.** If a worktree folder already exists, inspect it first; do not overwrite it. Avoid adding this document's branch as a runtime feature dependency.

## C. PromptGuard local acceptance — MANUAL, NOT RUN

```sh
cd "$HOMELAB_ROOT/../homelab-promptguard/projects/promptguard-lab"
python3 -m unittest discover -s promptguard -p 'test_*.py' -v
python3 -m promptguard.evaluate
python3 -m promptguard.evaluation_v3
python3 -m promptguard.dashboard
```

- [ ] Browser opens at `http://127.0.0.1:4186` on the **same Mac**. Confirm listening is loopback-only, not bound to an external interface.
- [ ] Use only the included harmless synthetic examples. Confirm normal text remains low-signal, suspicious rule indicators are explained, source-type selection works and data is not persisted.
- [ ] Check a clearly labeled benign false-positive example and a missed-indicator example; document limitations rather than reporting real-world detection accuracy.
- [ ] Confirm dashboard rejects a cross-origin submission/invalid request using the project's safe tests. Stop server with Ctrl+C after acceptance.

## D. SOC and hardening offline acceptance — MANUAL, NOT RUN

```sh
cd "$HOMELAB_ROOT/../homelab-soc/projects/soc-detection-engine"
python3 -m unittest discover -s soclab -p 'test_*.py' -v
python3 -m soclab.cli --file fixtures/synthetic-sec01.log
python3 -m soclab.cli --file fixtures/synthetic-benign.log
```

- [ ] Confirm suspicious fixture reports explained alerts; benign fixture reports no inappropriate high-confidence intrusion claims. Record input line counts and skipped lines.
- [ ] Confirm malformed / incomplete input fails safely; no real SEC01 data has been contacted by these commands.

```sh
cd "$HOMELAB_ROOT/../homelab-audit/projects/linux-hardening-auditor"
python3 -m unittest discover -s auditlab -p 'test_*.py' -v
python3 -m auditlab.cli --file fixtures/secure-fictional.json
python3 -m auditlab.cli --file fixtures/review-fictional.json
python3 -m auditlab.cli --file fixtures/incomplete-fictional.json
```

- [ ] Secure fixture yields expected PASS findings; review fixture surfaces configuration concerns; incomplete fixture yields NOT_CHECKED rather than invented PASS.
- [ ] Ensure this is offline snapshot assessment, **not** live host hardening or remediation.

## E. Incident casework acceptance — MANUAL, NOT RUN

```sh
cd "$HOMELAB_ROOT/../homelab-ir/projects/incident-response-toolkit"
python3 -m unittest discover -s irkit -p 'test_*.py' -v
python3 -m irkit.cli --file fixtures/synthetic-case.json --format markdown
python3 -m irkit.cli --file fixtures/benign-case.json --format markdown
```

- [ ] Validate timeline ordering, provenance fingerprints, synthetic source redaction and open investigative questions.
- [ ] Validate the report explicitly remains `triage_unverified`; no claimed compromise, identity, or remediation outcome.
- [ ] The IR toolkit's included reports are fictional input objects, **not evidence that SOC and hardening programs have executed together**. Integration from newly generated outputs must be checked after approved branch reconciliation.

## F. Existing Mac V2 purple-team workflow revalidation — MANUAL, NOT RUN

- [ ] Independently verify UTM boot/resource capacity and that KALI01, UBUNTU01, SEC01 roles use only the owned lab network.
- [ ] Reconfirm the prior documented `KALI01 → UBUNTU01 → SEC01` telemetry and response workflow with a strictly scoped and authorized exercise; record expected/observed results, timestamps, log delivery and secure-state restoration.
- [ ] Confirm UFW state and observed connectivity were actually restored before ending the exercise.
- [ ] Do not claim a working Windows AD/SMB domain until DC01 and Windows client identity, DNS, sign-in and effective share permissions have fresh V2 Mac evidence.

## G. Integration sequence — PENDING HUMAN APPROVAL

1. Review changed-file diffs and verify CI again on exact proposed SHAs. Reconcile #3 → #4 → #6 in order. After each approved merge, update the next PR base, rerun its relevant checks and verify that all PromptGuard files survive.
2. Review #5 and #7 against current main, preserving their README additions. Re-run independent tests and verify expected report schemas/fields.
3. Review #8 against current main, preserve its README addition, and generate a **new** integration test taking freshly produced SOC and hardening outputs into the IR case manifest; sanitized fictional data only.
4. Recheck branch protection, changed files, tests, no secrets, no unexpected host/system actions, and newly frozen integrated SHA. Do not merge merely because old PR workflows were green.
5. Keep #1 and Windows/AD migration separate pending a host inventory decision. Review #9 governance independently.

No merges, production deployments, hosted mutations, network scans or VM operations are authorized by this document.

## Mac acceptance observations — 2026-10-11 (user-provided screenshots)

The following are **observed host results**, not re-executions by GitHub CI or by the assistant. Screenshot evidence was supplied in the conversation; **no screenshots or raw logs have been committed**.

| Check | Source / observation | Status |
| --- | --- | --- |
| SEC01 boot and interactive login | User successfully booted and logged in on UTM | PASS (user observed) |
| SEC01 host and IPv4 addresses | Screenshot shows `sec01`, private lab `10.10.10.50/24`, and shared/NAT `192.168.64.5/24` | PASS (configuration observed); isolation not yet verified |
| SEC01 rsyslog service | `systemctl is-active rsyslog` returned `active` | PASS |
| SEC01 TCP listener | `ss -lnt` showed `0.0.0.0:514` and `[::]:514` | PASS (listener exists); exposure/interface filtering requires review |
| SEC01 historical centralized files | `sudo find /var/log/remote -type f` returned files beneath `/var/log/remote/ubuntu001/`; file timestamps shown in listing were September 3 | PASS (historical files found) |
| Fresh UBUNTU01 → SEC01 log message | After user generated `logger "LAB-CHECK-1011"` on UBUNTU01, a SEC01 screenshot showed `LAB-CHECK-1011` in its centralized log path at `2026-10-11T18:21:38+00:00` | PASS (fresh application-layer log receipt) |
| Actual private network isolation and firewall filtering | Listener is bound on all interfaces, but ingress filtering and topology have not yet been checked | NOT_RUN |
| DC01 and Win11-Client01 on Mac | User confirmed both Windows VMs are absent from UTM | BLOCKED (VMs not installed) |
| KALI01 / UBUNTU01 detailed UTM topology | Presence/config/resource budget not recorded yet | NOT_RUN |

A successful logged test marker proves **message receipt**, not that a full intrusion-detection pipeline or network isolation is secure. Continue with UTM topology, repository candidate checks, and offline software acceptance. Do not treat the Windows V1 historical results as current Mac V2 verification.

## Results worksheet (fill only after execution)

| Gate | Commit / host evidence | Expected | Observed | Result (PASS / FAIL / BLOCKED / NOT_RUN) | Redacted evidence link |
| --- | --- | --- | --- | --- | --- |
| Mac UTM inventory | | Five-role target, explicit actual/pending | | NOT_RUN | |
| PromptGuard tests/dashboard | | Offline tests and functional local UI | | NOT_RUN | |
| SOC fixture checks | | Explained alerts and benign controls | | NOT_RUN | |
| Linux hardening fixtures | | PASS/REVIEW/NOT_CHECKED as appropriate | | NOT_RUN | |
| Incident-response reports | | Unverified, cited fictional case | | NOT_RUN | |
| Actual three-VM telemetry | | Authorized observation and secure retest | | NOT_RUN | |
| Windows V2 AD and permissions | | Fresh identity/DNS/share evidence | | NOT_RUN | |
| Combined integration candidate | | Newly frozen SHA with relevant gates | | NOT_RUN | |

**Exit condition:** Present an evidence-backed PASS/FAIL/BLOCKED report, not an inferred percentage of readiness. Keep remaining failures as explicit follow-ups.
