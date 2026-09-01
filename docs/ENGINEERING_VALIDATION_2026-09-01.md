# Engineering validation — 2026-09-01

This record concerns repository tooling, not the live homelab.

## Problems fixed

- Recovery scripts were absent from main and the draft branch had stale VM naming and checkpoint documentation.
- Client validation could accept any successful DNS response, did not verify configured DNS, mask/address state, selected route, service ports or membership/trust, and did not return a failing process code.
- The host collector used `CLIENT01` rather than the recorded VirtualBox name `Win11-Client01`; native errors and executable discovery needed reliable handling.
- Runtime reports needed recursive Git exclusion, unique filenames and explicit scope.

## Local evidence

- PowerShell 7.6.5: 42 parsing/behavioral assertions passed in the remote Linux workspace.
- Cases cover mixed NAT/lab DNS, empty DNS results, wrong masks, duplicate addresses, wrong routes, wrong switch names, disconnected cables, unexpected bridges, collector/native-command failures and report persistence.
- TCP tests use a real temporary loopback listener and then its closed port; no live lab endpoint is contacted by the tests.
- Bash syntax validation passed.
- Relative Markdown links resolved.

## Windows CI gate

The workflow is prepared to run the test suite under Windows PowerShell 5.1 and PowerShell 7, including three additional host-collector smoke assertions, plus Bash syntax/ShellCheck on Ubuntu. Check [PR #1](https://github.com/ajlacabe23-2426/EnterpriseCyberSecHomeLab/pull/1) for the result on the published commit. CI uses hosted runners, not AJ's machine.

## Pending machine evidence

VirtualBox inventory, current resource budget, client/DC path, standard-user authentication, effective SMB authorization and event correlation are pending. The draft PR remains open for the live verification gate; neither this document nor a green CI run closes the lab incident.

## Publication status

Publication to the public recovery branch was explicitly authorized on September 1. A private recovery kit also preserves the earlier snapshot. Live incident closure remains pending the separate machine-side verification gates above.
