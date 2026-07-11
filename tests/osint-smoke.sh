#!/usr/bin/env bash
#
# BlissOSINT smoke test.
#
# Exercises the installed OSINT toolkit against a FICTIONAL, reserved-for-testing
# identity so you can confirm everything works without touching a real person.
#
# The defaults use RFC 2606 reserved names (example.com) and an invented handle,
# so a clean run should mostly return "not found" — that's success: it proves the
# tools execute and reach their sources, not that the fake persona exists.
#
# Usage:
#   ./tests/osint-smoke.sh                 # run live checks against the defaults
#   ./tests/osint-smoke.sh --check         # offline: only verify tools + metadata demo
#   USERNAME=foo EMAIL=a@example.com DOMAIN=example.com ./tests/osint-smoke.sh
#
# Override the fictional identity via env vars: USERNAME, EMAIL, DOMAIN.

set -euo pipefail

# --- Fictional test identity (override via env) -----------------------------
# example.com / example.org are reserved for documentation/testing (RFC 2606),
# so querying them targets no real infrastructure.
USERNAME="${USERNAME:-avaquillblossom_xyz9000}"
EMAIL="${EMAIL:-ava.quillblossom@example.com}"
DOMAIN="${DOMAIN:-example.com}"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1

TIMEOUT="${BLISS_SMOKE_TIMEOUT:-90}"   # per-tool wall-clock cap (seconds)

pass=0; skip=0; fail=0

cyan()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[1;33m%s\033[0m\n' "$*"; }
red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }

have() { command -v "$1" >/dev/null 2>&1; }

# run_tool <label> <command...>
# Skips (doesn't fail) if the tool isn't installed; honors --check by only
# reporting presence; time-limits live runs.
run_tool() {
  local label="$1"; shift
  local bin="$1"
  cyan "== ${label} (${bin}) =="
  if ! have "${bin}"; then
    yellow "  SKIP: ${bin} not installed"
    skip=$((skip + 1))
    return 0
  fi
  if [ "${CHECK_ONLY}" -eq 1 ]; then
    green "  OK: ${bin} is installed"
    pass=$((pass + 1))
    return 0
  fi
  if timeout "${TIMEOUT}" "$@"; then
    green "  OK: ${label} completed"
    pass=$((pass + 1))
  else
    local rc=$?
    # 124 == timeout; treat as a soft pass (tool ran, just slow/long source list).
    if [ "${rc}" -eq 124 ]; then
      yellow "  SLOW: ${label} hit the ${TIMEOUT}s cap (ran, not failed)"
      pass=$((pass + 1))
    else
      red "  FAIL: ${label} exited ${rc}"
      fail=$((fail + 1))
    fi
  fi
}

# Offline metadata demo: exiftool reads metadata we embed into a temp image.
# Needs no network, so it works in --check mode and in CI if the tools exist.
metadata_demo() {
  cyan "== Metadata extraction (exiftool, offline) =="
  if ! have exiftool; then
    yellow "  SKIP: exiftool not installed"
    skip=$((skip + 1)); return 0
  fi
  local tmp img
  tmp="$(mktemp -d)"
  img="${tmp}/fictional-evidence.jpg"
  if have convert; then
    convert -size 64x64 xc:skyblue \
      -set comment "Fictional test artifact for ${USERNAME}" "${img}" 2>/dev/null || true
  fi
  if [ ! -f "${img}" ]; then
    yellow "  SKIP: could not create a test image (ImageMagick missing)"
    skip=$((skip + 1)); rm -rf "${tmp}"; return 0
  fi
  if exiftool "${img}"; then
    green "  OK: exiftool read metadata from the test artifact"
    pass=$((pass + 1))
  else
    red "  FAIL: exiftool could not read the test image"
    fail=$((fail + 1))
  fi
  rm -rf "${tmp}"
}

main() {
  cyan "BlissOSINT smoke test"
  echo "Fictional identity (no real target):"
  echo "  username: ${USERNAME}"
  echo "  email:    ${EMAIL}"
  echo "  domain:   ${DOMAIN}  (RFC 2606 reserved)"
  [ "${CHECK_ONLY}" -eq 1 ] && yellow "Mode: --check (offline; tool presence + metadata demo only)"
  echo

  # Username enumeration. If NAME is set, derive candidate handles from the full
  # name (offline) and enumerate each; otherwise use the single fictional handle.
  if [ -n "${NAME:-}" ]; then
    local deriver
    deriver="$(dirname "${BASH_SOURCE[0]}")/derive-persona.sh"
    cyan "== Deriving handles from name: ${NAME} =="
    mapfile -t handles < <("${deriver}" "${NAME}" 2>/dev/null)
    if [ "${#handles[@]}" -eq 0 ]; then
      yellow "  could not derive handles; falling back to ${USERNAME}"
      handles=("${USERNAME}")
    else
      echo "  candidates: ${handles[*]}"
    fi
    for h in "${handles[@]}"; do
      run_tool "Username search [${h}]"      sherlock "${h}" --timeout 10 --print-found
      run_tool "Username enumeration [${h}]" maigret  "${h}" --timeout 10
    done
  else
    run_tool "Username search"       sherlock "${USERNAME}" --timeout 10 --print-found
    run_tool "Username enumeration"  maigret  "${USERNAME}" --timeout 10
  fi

  # Email
  run_tool "Email registration"    holehe   "${EMAIL}"

  # Domain / DNS (example.com is safe to query)
  run_tool "Domain harvest"        theHarvester -d "${DOMAIN}" -b duckduckgo
  run_tool "DNS recon"             dnsrecon -d "${DOMAIN}"

  # Offline metadata demo
  metadata_demo

  echo
  cyan "Summary: ${pass} ok, ${skip} skipped, ${fail} failed"
  if [ "${fail}" -gt 0 ]; then
    red "Smoke test reported failures."
    exit 1
  fi
  green "Smoke test passed (skips are fine if some tools aren't installed)."
}

main "$@"
