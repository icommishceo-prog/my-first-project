#!/usr/bin/env bash
# Phase 3: Vulnerability Scanning — Nuclei against each target

set -euo pipefail
TARGET="$1"
OUT_DIR="$2"
SEVERITY="${3:-low,medium,high,critical}"
RATE="${4:-50}"
EXTRA_URLS="${5:-}"        # optional file of discovered URLs to also scan

SAFE_TARGET=$(echo "$TARGET" | sed 's|https\?://||g' | tr '/' '_' | tr ':' '_')
VULN_DIR="$OUT_DIR/vulns"
mkdir -p "$VULN_DIR"

# Build URL list: base target + any ffuf-discovered URLs
URL_LIST=$(mktemp)
echo "$TARGET" > "$URL_LIST"
[ -n "$EXTRA_URLS" ] && [ -f "$EXTRA_URLS" ] && cat "$EXTRA_URLS" >> "$URL_LIST"

echo "[*] nuclei: $TARGET ($(wc -l < "$URL_LIST") URLs)"

nuclei \
  -l "$URL_LIST" \
  -t cves \
  -t exposures \
  -t misconfiguration \
  -t takeovers \
  -t technologies \
  -t vulnerabilities \
  -t default-logins \
  -t exposed-panels \
  -t fuzzing \
  -severity "$SEVERITY" \
  -rate-limit "$RATE" \
  -bulk-size 25 \
  -c 10 \
  -o "${VULN_DIR}/${SAFE_TARGET}_nuclei.txt" \
  -json-export "${VULN_DIR}/${SAFE_TARGET}_nuclei.json" \
  -silent \
  2>/dev/null || true

COUNT=$(wc -l < "${VULN_DIR}/${SAFE_TARGET}_nuclei.txt" 2>/dev/null || echo 0)
echo "[+] nuclei done: $COUNT findings for $TARGET"
rm -f "$URL_LIST"
