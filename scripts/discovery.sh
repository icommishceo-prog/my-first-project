#!/usr/bin/env bash
# Phase 2: Web Discovery — ffuf directory + parameter fuzzing per URL

set -euo pipefail
URL="$1"
OUT_DIR="$2"
WORDLIST="${3:-wordlists/common.txt}"
THREADS="${4:-40}"
RATE="${5:-100}"
EXTENSIONS="${6:-php,html,js,json,asp,aspx,txt,xml,bak,old}"

SAFE_URL=$(echo "$URL" | sed 's|https\?://||g' | tr '/' '_' | tr ':' '_')
DISC_DIR="$OUT_DIR/discovery/$SAFE_URL"
mkdir -p "$DISC_DIR"

# ---- Directory brute-force (ffuf) ----
echo "[*] ffuf dir scan: $URL"
ffuf \
  -u "${URL}/FUZZ" \
  -w "$WORDLIST" \
  -e ".$EXTENSIONS" \
  -t "$THREADS" \
  -rate "$RATE" \
  -mc 200,201,204,301,302,307,401,403 \
  -o "${DISC_DIR}/ffuf_dirs.json" \
  -of json \
  -s \
  2>/dev/null || true

# ---- Extract discovered paths for nuclei ----
if [ -f "${DISC_DIR}/ffuf_dirs.json" ]; then
  python3 -c "
import json, sys
try:
  d = json.load(open('${DISC_DIR}/ffuf_dirs.json'))
  urls = [r['url'] for r in d.get('results', [])]
  print('\n'.join(urls))
except: pass
" > "${DISC_DIR}/discovered_urls.txt" 2>/dev/null || true
  echo "[+] ffuf done: $(wc -l < "${DISC_DIR}/discovered_urls.txt" 2>/dev/null || echo 0) paths found"
fi

# ---- API endpoint discovery (common API paths) ----
echo "[*] ffuf API scan: $URL"
ffuf \
  -u "${URL}/FUZZ" \
  -w wordlists/api_paths.txt \
  -t "$THREADS" \
  -rate "$RATE" \
  -mc 200,201,204,301,302,307,401,403 \
  -o "${DISC_DIR}/ffuf_api.json" \
  -of json \
  -s \
  2>/dev/null || true

# ---- JS file discovery (secrets, endpoints) ----
echo "[*] Hunting .js files: $URL"
ffuf \
  -u "${URL}/FUZZ" \
  -w "$WORDLIST" \
  -e ".js" \
  -t "$THREADS" \
  -rate "$RATE" \
  -mc 200 \
  -o "${DISC_DIR}/ffuf_js.json" \
  -of json \
  -s \
  2>/dev/null || true
