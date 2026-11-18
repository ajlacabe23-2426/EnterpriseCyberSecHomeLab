#!/usr/bin/env bash
# IAM-000: read-only local evidence collection for an owned Linux UTM guest.
# Does not create users, change groups, connect to another host, or emit log events.
set -u

usage() {
  printf 'Usage: bash %s {ubuntu01|sec01}\n' "${0##*/}" >&2
}
if [[ "$#" -ne 1 ]]; then usage; exit 2; fi
case "$1" in
  ubuntu01|sec01) role="$1" ;;
  *) usage; exit 2 ;;
esac

section() { printf '\n== %s ==\n' "$1"; }
observe() {
  local label="$1"; shift
  printf '\n[%s]\n' "$label"
  if ! "$@"; then printf 'OBSERVATION_FAILED: %s (investigate manually)\n' "$label"; fi
}
section "IAM-000 local guest observation: $role"
printf 'NOT A PASS/FAIL CERTIFICATE. Do not commit raw output to a public repo.\n'
observe "UTC timestamp" date -u '+%Y-%m-%dT%H:%M:%SZ'
observe "Hostname" hostname
observe "Kernel and architecture" uname -m
observe "Current operator identity" id
if command -v ip >/dev/null 2>&1; then
  observe "Local IPv4 interfaces (review NAT versus private lab)" ip -br -4 addr
else
  printf '\n[Local interfaces] NOT_CHECKED: ip command unavailable\n'
fi
if command -v systemctl >/dev/null 2>&1; then
  observe "rsyslog service state" systemctl is-active rsyslog
else
  printf '\n[rsyslog] NOT_CHECKED: systemctl unavailable\n'
fi
if command -v getent >/dev/null 2>&1; then
  observe "Local sudo group record (review only)" getent group sudo
else
  printf '\n[Local sudo group] NOT_CHECKED: getent unavailable\n'
fi
if [[ "$role" == "sec01" ]]; then
  if command -v ss >/dev/null 2>&1; then
    section "TCP listeners (review whether syslog/514 is bound to all interfaces)"
    ss -lnt || printf 'OBSERVATION_FAILED: ss -lnt\n'
  else
    printf '\n[TCP listeners] NOT_CHECKED: ss unavailable\n'
  fi
  printf '\nFor remote log receipt, use the existing SOC-001 runbook after inspecting the configured destination.\n'
fi
section "Next"
printf 'Record actual output, timestamps, and observed evidence separately.\n'
printf 'Status remains NOT_VERIFIED until an operator interprets the results.\n'
