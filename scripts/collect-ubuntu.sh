#!/usr/bin/env bash
# Read-only diagnostics for UBUNTU01. No sudo, package installs or network edits.
set -u
umask 077
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="$root/evidence/private"
mkdir -p -- "$out_dir" || exit 1
report="$(mktemp "$out_dir/UBUNTU01-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX.txt")" || exit 1
failures=0
run() {
    printf '\n=== %s ===\n' "$1"
    shift
    "$@"
    status=$?
    printf 'Command exit: %s\n' "$status"
    if ((status != 0)); then failures=$((failures + 1)); fi
}
{
    printf 'UBUNTU01 diagnostic inventory | UTC %s\n' "$(date -u +%FT%TZ)"
    printf 'Collection is not proof of complete connectivity or authentication.\n'
    run 'Guest hostname' hostname
    run 'IPv4 interfaces' ip -br -4 address
    run 'Route to DC01 (expected lab NIC, source 10.10.10.30)' ip -4 route get 10.10.10.10
    run 'Default routes (expected NAT only)' ip -4 route show default
    run 'Neighbors' ip -4 neigh
    run 'Resolver configuration' resolvectl status
    run 'Lab DNS lookup' resolvectl query DC01.atlasiqlab.local
    run 'Application resolver lookup' getent ahostsv4 DC01.atlasiqlab.local
    run 'SSH service state' systemctl is-active ssh
    run 'Listening TCP sockets (inspect :22)' ss -lnt
    run 'Package audit (empty output expected)' dpkg --audit
    run 'Memory' free -m
    run 'Root filesystem capacity' df -h /
    printf '\nCommands with nonzero exit: %s\n' "$failures"
    printf 'Review address, route, DNS answer and SSH listener output; exit 0 alone is not a lab PASS.\n'
} > "$report" 2>&1
cat -- "$report"
printf '\nReport: %s\n' "$report"
((failures == 0))
