# Homelab evidence and learning map

A local interactive 3D map for Enterprise Cyber Lab V2. Explore **VM & network**, **Telemetry path**, and **Code & tools**. Every node explains its role, relevant skills, source-dated claims, and the next verification gate.

## Run on the MacBook

From this candidate's repository root (Python 3.11+; no packages or credentials required):

```sh
cd projects/homelab-map
python3 -B -m labmap
```

Open `http://127.0.0.1:4187` on the same Mac. If that port is in use, choose another with `python3 -B -m labmap --port 4188`. Keep the full repository checkout; the source documents live under its root `docs/` directory. The service binds only to `127.0.0.1`; there is no option to expose it on another interface.

Stop with Ctrl+C. Reloading resets browser exploration and simulation; there are no saved changes or VM state to restore. Rollback is simply stopping the server and returning to the prior checkout. Use a clean detached candidate worktree for acceptance; do not replace user changes, merge PRs or change VM configuration to try the map.

## How to explore

- Rotate left/right, drag horizontally, or focus the map and use arrow keys. Home resets the angle. Flat view and the component buttons provide alternatives.
- Select SEC01 to compare observed rsyslog/listener evidence, configured log ingress and the management-access REVIEW. Current isolation stays NOT_RUN.
- **Trace fresh log receipt** highlights only the recorded UBUNTU01 → SEC01 → centralized-log path. It does not send another message or start detection.
- **Code & tools** links to pinned PromptGuard, SOC, hardening and incident-toolkit source revisions in their open PRs. These modules are separate candidates; the map does not import, install, execute or integrate them. PromptGuard is a separate untrusted-text exercise, not part of the syslog path.
- In the synthetic port model, default denied inbound produces FILTERED. Allow inbound with no listener produces CLOSED; allow inbound with a listener produces OPEN. A listener behind the synthetic deny still produces FILTERED. Restore resets both browser controls. This simplified model does not represent every network outcome or current host state.

## Evidence truth

The snapshot is recorded through **2026-10-11**. Source: the current Mac acceptance handoff at governance PR #9 revision `563bc45d1592168ee3b2ac84a0ed1f2c68d62a6c`, plus explicitly dated September V2 history and migration planning.

Fresh message receipt is recorded as observed, not as full detection, secure isolation or current host health. UTM adapter modes and SEC01 UFW ingress restrictions are configuration observations; actual filtering/exposure remains a distinct gate. SEC01 broad SSH access remains REVIEW. DC01 and Win11-Client01 remain absent/BLOCKED. KALI01/UBUNTU01 September addresses are labeled historical; adapter screenshots do not establish their current guest IPs. The legacy Windows V1 addresses/results are not used as current Mac V2 evidence.

Local source documents have SHA-256 fingerprints. If a source file changes, its source endpoint returns 409 rather than serving new content under an old revision label. To update the map, review real sanitized evidence, explicitly revise source/date/status and fingerprints in `labmap/public/data.json`, then rerun the gates on a new candidate. The UI cannot promote statuses or accept logs, snapshots or credentials.

## Verification

From `projects/homelab-map`:

```sh
python3 -B -m unittest labmap.test_server -v
node --check labmap/public/app.js
node --check labmap/public/core.mjs
node --test tests.mjs
RUN_BROWSER_ACCEPTANCE=1 CHROME_BIN=/path/to/google-chrome node --test tests/browser.test.mjs
```

Python tests cover loopback binding, fixed static/source allowlists, changed-source rejection, security headers, host/origin rejection, unavailable mutation/upload/scan routes, and evidence-state boundaries. JavaScript tests cover provenance, malformed/future evidence, projection and all synthetic port combinations. Actual Chromium checks all views, evidence detail, pointer selection/dragging, keyboard rotation, flat view, telemetry tracing, pinned code links, simulation, mobile containment, unchanged snapshot, renderer exceptions and request destinations. The browser contacts only its loopback map origin during the test. Manually opening external GitHub source links is an explicit user navigation; no background external requests occur.

Mac acceptance remains separate: start the candidate locally, inspect SEC01 and blocked Windows states, trace the recorded receipt, switch code/flat views, and run the browser simulation. No new VM action is needed. Running these tests verifies this software feature, not actual Mac resources, VM isolation, current host behavior or an integrated SOC pipeline.
