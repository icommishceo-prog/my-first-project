#!/usr/bin/env bash
#
# Install PhoneInfoga (phone-number OSINT).
#
# PhoneInfoga isn't in Debian, and `go install` fails (its web client is only
# embedded in release builds: "pattern client/dist/*: no matching files found").
# So we install the official prebuilt binary from GitHub releases.
#
#   ./provision/install-phoneinfoga.sh [DEST_DIR]     # default: /usr/local/bin
#   PHONEINFOGA_VERSION=v2.11.0 ./provision/install-phoneinfoga.sh
#
# Idempotent: does nothing if `phoneinfoga` is already on PATH.

set -euo pipefail

DEST="${1:-/usr/local/bin}"
VERSION="${PHONEINFOGA_VERSION:-latest}"
REPO="sundowndev/phoneinfoga"

log()  { printf '\033[1;32m[phoneinfoga]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[phoneinfoga]\033[0m %s\n' "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

if have phoneinfoga; then
  log "already installed: $(command -v phoneinfoga)"
  exit 0
fi

# Map uname arch to PhoneInfoga's goreleaser asset naming.
case "$(uname -m)" in
  x86_64|amd64)  ARCH="x86_64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *)             ARCH="" ;;
esac

install_from_release() {
  have curl || { warn "curl not available"; return 1; }
  have tar  || { warn "tar not available"; return 1; }
  [ -n "${ARCH}" ] || { warn "unsupported arch $(uname -m) for prebuilt binary"; return 1; }

  local url=""
  if [ "${VERSION}" = "latest" ]; then
    # Resolve the latest release's Linux asset via the GitHub API (needs jq).
    if have jq; then
      url="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
            | jq -r '.assets[].browser_download_url' \
            | grep -iE "Linux_${ARCH}\.tar\.gz$" | head -n1)"
    fi
  else
    url="https://github.com/${REPO}/releases/download/${VERSION}/phoneinfoga_Linux_${ARCH}.tar.gz"
  fi
  [ -n "${url}" ] || { warn "could not resolve a release asset URL"; return 1; }

  log "downloading ${url}"
  local tmp
  tmp="$(mktemp -d)"
  if curl -fsSL "${url}" -o "${tmp}/phoneinfoga.tar.gz" \
     && tar -xzf "${tmp}/phoneinfoga.tar.gz" -C "${tmp}" phoneinfoga; then
    install -m 0755 "${tmp}/phoneinfoga" "${DEST}/phoneinfoga"
    rm -rf "${tmp}"
    log "installed -> ${DEST}/phoneinfoga"
    return 0
  fi
  rm -rf "${tmp}"
  warn "prebuilt install failed"
  return 1
}

if install_from_release; then
  exit 0
else
  warn "Could not install PhoneInfoga's prebuilt binary (offline or unsupported arch)."
  warn "  Install manually: https://sundowndev.github.io/phoneinfoga/getting-started/install/"
  # Non-fatal: the rest of the toolkit still works; phone checks will just skip.
  exit 0
fi
