#!/usr/bin/env bash
# Phase 1: Recon — nmap port/service scan per target

set -euo pipefail
TARGET="$1"
OUT_DIR="$2"
NMAP_FLAGS="${3:--sV -sC -T4 --open}"
PORTS="${4:-80,443,8080,8443,8000,8888,3000,3001,5000,5001,9000,9090}"

SAFE_TARGET=$(echo "$TARGET" | sed 's|https\?://||g' | tr '/' '_' | tr ':' '_')
OUT_FILE="$OUT_DIR/recon/${SAFE_TARGET}"

echo "[*] nmap: $TARGET"
nmap $NMAP_FLAGS -p "$PORTS" "$TARGET" \
  -oN "${OUT_FILE}.txt" \
  -oX "${OUT_FILE}.xml" \
  2>/dev/null || true

# Extract open ports/services for downstream tools
if [ -f "${OUT_FILE}.txt" ]; then
  grep "^[0-9]" "${OUT_FILE}.txt" | grep "open" \
    > "${OUT_FILE}_open_ports.txt" 2>/dev/null || true
  echo "[+] nmap done: $(wc -l < "${OUT_FILE}_open_ports.txt" 2>/dev/null || echo 0) open ports found"
fi
