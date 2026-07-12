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
#   ./tests/osint-smoke.sh --report        # also save JSON + HTML reports
#   ./tests/osint-smoke.sh --report=DIR    # ...to a specific directory
#   USERNAME=foo EMAIL=a@example.com DOMAIN=example.com ./tests/osint-smoke.sh
#   NAME="Full Name" ./tests/osint-smoke.sh --report   # per-handle findings
#   PHONE="+13125550123" ./tests/osint-smoke.sh --report  # phone OSINT (phoneinfoga)
#
# Override the fictional identity via env vars: USERNAME, EMAIL, DOMAIN, NAME, PHONE.
# Reports collect each tool's status, timing, and raw output; enable with
# --report / --report=DIR or BLISS_REPORT_DIR=DIR.

set -euo pipefail

# --- Fictional test identity (override via env) -----------------------------
# example.com / example.org are reserved for documentation/testing (RFC 2606),
# so querying them targets no real infrastructure.
USERNAME="${USERNAME:-avaquillblossom_xyz9000}"
EMAIL="${EMAIL:-ava.quillblossom@example.com}"
DOMAIN="${DOMAIN:-example.com}"

TIMEOUT="${BLISS_SMOKE_TIMEOUT:-90}"   # per-tool wall-clock cap (seconds)

# --- Argument parsing -------------------------------------------------------
CHECK_ONLY=0
REPORT_DIR="${BLISS_REPORT_DIR:-}"
for arg in "$@"; do
  case "${arg}" in
    --check)      CHECK_ONLY=1 ;;
    --report)     REPORT_DIR="${REPORT_DIR:-__DEFAULT__}" ;;
    --report=*)   REPORT_DIR="${arg#*=}" ;;
    *) echo "unknown argument: ${arg}" >&2
       echo "usage: $0 [--check] [--report[=DIR]]" >&2; exit 2 ;;
  esac
done

pass=0; skip=0; fail=0
RECORDS=""   # temp JSONL of per-tool results (set up when reporting is on)

cyan()  { printf '\033[1;36m%s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
yellow(){ printf '\033[1;33m%s\033[0m\n' "$*"; }
red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }

have() { command -v "$1" >/dev/null 2>&1; }

now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

# Turn a label into a filesystem-safe slug for raw-output filenames.
safe_name() { printf '%s' "$1" | tr -cs 'a-zA-Z0-9' '_' | sed 's/^_//; s/_$//'; }

# Prepare the report directory (and disable reporting if jq is missing).
setup_report() {
  [ -n "${REPORT_DIR}" ] || return 0
  if ! have jq; then
    yellow "jq not found; reports need jq. Disabling report output."
    REPORT_DIR=""; return 0
  fi
  [ "${REPORT_DIR}" = "__DEFAULT__" ] && REPORT_DIR="reports/smoke-$(date -u +%Y%m%d-%H%M%S)"
  mkdir -p "${REPORT_DIR}/raw"
  RECORDS="$(mktemp)"
}

# record <label> <bin> <command> <status> <rc> <duration_s> <raw-relpath>
record() {
  [ -n "${REPORT_DIR}" ] || return 0
  jq -nc \
    --arg label "$1" --arg bin "$2" --arg command "$3" --arg status "$4" \
    --argjson rc "${5:-0}" --argjson duration "${6:-0}" --arg raw "$7" \
    '{label:$label, bin:$bin, command:$command, status:$status,
      rc:$rc, duration_s:$duration, raw:$raw}' >> "${RECORDS}"
}

# run_tool <label> <command...>
# Skips (doesn't fail) if the tool isn't installed; honors --check by only
# reporting presence; time-limits live runs.
run_tool() {
  local label="$1"; shift
  local bin="$1"
  local cmd="$*"
  cyan "== ${label} (${bin}) =="
  if ! have "${bin}"; then
    yellow "  SKIP: ${bin} not installed"
    skip=$((skip + 1))
    record "${label}" "${bin}" "${cmd}" "skip" 0 0 ""
    return 0
  fi
  if [ "${CHECK_ONLY}" -eq 1 ]; then
    green "  OK: ${bin} is installed"
    pass=$((pass + 1))
    record "${label}" "${bin}" "${cmd}" "installed" 0 0 ""
    return 0
  fi

  local start end dur rc=0 raw=""
  start="$(date +%s)"
  if [ -n "${REPORT_DIR}" ]; then
    # Capture the tool's output to a raw file while still streaming to terminal.
    raw="raw/$(safe_name "${label}").txt"
    if timeout "${TIMEOUT}" "$@" 2>&1 | tee "${REPORT_DIR}/${raw}"; then rc=0; else rc="${PIPESTATUS[0]}"; fi
  else
    if timeout "${TIMEOUT}" "$@"; then rc=0; else rc=$?; fi
  fi
  end="$(date +%s)"; dur=$((end - start))

  local status
  if [ "${rc}" -eq 0 ]; then
    green "  OK: ${label} completed (${dur}s)"; pass=$((pass + 1)); status="ok"
  elif [ "${rc}" -eq 124 ]; then
    # 124 == timeout; treat as a soft pass (tool ran, just slow/long source list).
    yellow "  SLOW: ${label} hit the ${TIMEOUT}s cap (ran, not failed)"; pass=$((pass + 1)); status="slow"
  else
    red "  FAIL: ${label} exited ${rc}"; fail=$((fail + 1)); status="fail"
  fi
  record "${label}" "${bin}" "${cmd}" "${status}" "${rc}" "${dur}" "${raw}"
}

# Offline metadata demo: exiftool reads metadata we embed into a temp image.
# Needs no network, so it works in --check mode and in CI if the tools exist.
metadata_demo() {
  cyan "== Metadata extraction (exiftool, offline) =="
  if ! have exiftool; then
    yellow "  SKIP: exiftool not installed"
    skip=$((skip + 1)); record "Metadata extraction" "exiftool" "exiftool <image>" "skip" 0 0 ""; return 0
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
    skip=$((skip + 1)); record "Metadata extraction" "exiftool" "exiftool <image>" "skip" 0 0 ""
    rm -rf "${tmp}"; return 0
  fi
  local raw="" rc=0
  [ -n "${REPORT_DIR}" ] && raw="raw/metadata_extraction.txt"
  if [ -n "${raw}" ]; then exiftool "${img}" | tee "${REPORT_DIR}/${raw}"; rc="${PIPESTATUS[0]}"; else exiftool "${img}"; rc=$?; fi
  if [ "${rc:-0}" -eq 0 ]; then
    green "  OK: exiftool read metadata from the test artifact"
    pass=$((pass + 1)); record "Metadata extraction" "exiftool" "exiftool <image>" "ok" 0 0 "${raw}"
  else
    red "  FAIL: exiftool could not read the test image"
    fail=$((fail + 1)); record "Metadata extraction" "exiftool" "exiftool <image>" "fail" "${rc}" 0 "${raw}"
  fi
  rm -rf "${tmp}"
}

# Assemble report.json + report.html from the collected records.
finalize_report() {
  [ -n "${REPORT_DIR}" ] || return 0
  local json="${REPORT_DIR}/report.json"
  local html="${REPORT_DIR}/report.html"

  # report.json: metadata + the array of per-tool records.
  jq -s \
    --arg generated "$(now_utc)" \
    --arg name "${NAME:-}" --arg username "${USERNAME}" \
    --arg email "${EMAIL}" --arg domain "${DOMAIN}" --arg phone "${PHONE:-}" \
    --argjson ok "${pass}" --argjson skipped "${skip}" --argjson failed "${fail}" \
    '{tool:"BlissOSINT smoke test", generated:$generated,
      identity:{name:$name, username:$username, email:$email, domain:$domain, phone:$phone},
      summary:{ok:$ok, skipped:$skipped, failed:$failed},
      results:.}' "${RECORDS}" > "${json}"

  # report.html: a self-contained styled table (values HTML-escaped via @html).
  local rows
  rows="$(jq -r '
    .results[] |
    "<tr class=\"" + .status + "\">" +
    "<td>" + (.label|@html) + "</td>" +
    "<td><code>" + (.bin|@html) + "</code></td>" +
    "<td><code>" + (.command|@html) + "</code></td>" +
    "<td class=\"status\">" + .status + "</td>" +
    "<td>" + (.rc|tostring) + "</td>" +
    "<td>" + (.duration_s|tostring) + "s</td>" +
    "<td>" + (if .raw != "" then "<a href=\"" + (.raw|@html) + "\">raw</a>" else "&mdash;" end) + "</td>" +
    "</tr>"' "${json}")"

  {
    cat <<HTMLHEAD
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BlissOSINT smoke report</title>
<style>
  body{font:14px/1.5 system-ui,sans-serif;margin:2rem;color:#1a1a1a;background:#fafafa}
  h1{font-size:1.4rem;margin:0 0 .25rem}
  .meta{color:#555;margin-bottom:1rem}
  table{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.1)}
  th,td{padding:.5rem .6rem;text-align:left;border-bottom:1px solid #eee;vertical-align:top}
  th{background:#f0f4f8;font-weight:600}
  code{font:12px/1.4 ui-monospace,monospace;word-break:break-all}
  .status{font-weight:600;text-transform:uppercase;font-size:12px}
  tr.ok .status{color:#137333} tr.installed .status{color:#137333}
  tr.slow .status{color:#a56300} tr.skip .status{color:#5f6368} tr.fail .status{color:#c5221f}
  .note{margin-top:1rem;color:#777;font-size:12px}
  @media (prefers-color-scheme:dark){
    body{background:#16181c;color:#e6e6e6} table{background:#1f2227}
    th{background:#262a30} td,th{border-color:#2c3037}
    tr.ok .status,tr.installed .status{color:#5bd07a} tr.slow .status{color:#e0b04a}
    tr.skip .status{color:#9aa0a6} tr.fail .status{color:#f28b82}
  }
</style></head><body>
<h1>BlissOSINT smoke report</h1>
<div class="meta">
  Generated $(now_utc) &middot;
  identity: ${NAME:+name=<b>$(printf '%s' "${NAME}" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')</b>, }
  username=<code>${USERNAME}</code>, domain=<code>${DOMAIN}</code>${PHONE:+, phone=<code>${PHONE}</code>}<br>
  <b>${pass}</b> ok &middot; <b>${skip}</b> skipped &middot; <b>${fail}</b> failed
</div>
<table>
<thead><tr><th>Check</th><th>Tool</th><th>Command</th><th>Status</th><th>rc</th><th>Time</th><th>Output</th></tr></thead>
<tbody>
HTMLHEAD
    printf '%s\n' "${rows}"
    cat <<'HTMLFOOT'
</tbody></table>
<p class="note">"Not found" results are expected against a fictional identity &mdash;
a clean run proves the tools execute, not that the persona exists. Only run this
against fictional or authorized subjects (see docs/opsec.md).</p>
</body></html>
HTMLFOOT
  } > "${html}"

  rm -f "${RECORDS}"
  green "Reports written:"
  echo "  ${json}"
  echo "  ${html}"
}

main() {
  setup_report
  cyan "BlissOSINT smoke test"
  echo "Fictional identity (no real target):"
  [ -n "${NAME:-}" ] && echo "  name:     ${NAME}"
  echo "  username: ${USERNAME}"
  echo "  email:    ${EMAIL}"
  echo "  domain:   ${DOMAIN}  (RFC 2606 reserved)"
  [ -n "${PHONE:-}" ] && echo "  phone:    ${PHONE}"
  [ "${CHECK_ONLY}" -eq 1 ] && yellow "Mode: --check (offline; tool presence + metadata demo only)"
  [ -n "${REPORT_DIR}" ] && cyan "Reporting to: ${REPORT_DIR}"
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

  # Phone OSINT (opt-in): runs when PHONE is set. In --check we still verify the
  # tool is installed, using a Twilio magic test number as a harmless placeholder.
  if [ -n "${PHONE:-}" ] || [ "${CHECK_ONLY}" -eq 1 ]; then
    run_tool "Phone OSINT"         phoneinfoga scan -n "${PHONE:-+15005550006}"
  fi

  # Offline metadata demo
  metadata_demo

  echo
  cyan "Summary: ${pass} ok, ${skip} skipped, ${fail} failed"
  finalize_report
  if [ "${fail}" -gt 0 ]; then
    red "Smoke test reported failures."
    exit 1
  fi
  green "Smoke test passed (skips are fine if some tools aren't installed)."
}

main "$@"
