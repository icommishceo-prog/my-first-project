#!/usr/bin/env bash
#
# BlissOSINT in-place provisioner.
#
# Installs the XP-style desktop theming and the OSINT toolkit onto an existing
# Debian 12 / Ubuntu 24.04 system. Intended to be run inside a disposable VM.
#
#   sudo ./provision/provision.sh              # full: desktop + theming + tools
#   sudo BLISS_HEADLESS=1 ./provision.sh       # OSINT toolkit only, no desktop
#
# Headless mode powers the Docker toolkit image and the CI smoke test.
# Re-runnable. Skips work that's already done where it can.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROVISION_DIR="${REPO_ROOT}/provision"
THEME_DIR="${REPO_ROOT}/theme"

# Headless = OSINT toolkit only: skip desktop packages and theming.
HEADLESS="${BLISS_HEADLESS:-0}"

log()  { printf '\033[1;32m[bliss]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[bliss]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[bliss]\033[0m %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Please run as root (sudo)."
command -v apt-get >/dev/null 2>&1 || die "This provisioner targets Debian/Ubuntu (apt not found)."

# The non-root user whose desktop we theme. Falls back sensibly under sudo.
TARGET_USER="${SUDO_USER:-${BLISS_USER:-}}"
if [ -z "${TARGET_USER}" ] || [ "${TARGET_USER}" = "root" ]; then
  warn "No non-root target user detected; desktop theming will be applied to /etc/skel only."
  TARGET_USER=""
fi

# --- Read a '# comment'-stripped, blank-stripped package list into a bash array.
read_list() {
  local file="$1"
  [ -f "${file}" ] || die "Missing package list: ${file}"
  sed -e 's/#.*$//' -e 's/[[:space:]]*$//' "${file}" | grep -v '^[[:space:]]*$' || true
}

install_apt_packages() {
  log "Updating apt and installing base + OSINT packages..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  # Read into an array so word-splitting is intentional.
  mapfile -t pkgs < <(read_list "${PROVISION_DIR}/packages.apt")
  # Add desktop/theming packages unless we're in headless (toolkit-only) mode.
  if [ "${HEADLESS}" != "1" ]; then
    mapfile -t -O "${#pkgs[@]}" pkgs < <(read_list "${PROVISION_DIR}/packages.desktop.apt")
  else
    log "Headless mode: skipping desktop/theming packages."
  fi
  if [ "${#pkgs[@]}" -gt 0 ]; then
    # Don't abort the whole run if one optional package is missing in this release;
    # install what we can and report the rest.
    apt-get install -y --no-install-recommends "${pkgs[@]}" || {
      warn "Batch install hit a snag; retrying package-by-package to skip unavailable ones."
      for p in "${pkgs[@]}"; do
        apt-get install -y --no-install-recommends "${p}" \
          || warn "Skipping unavailable package: ${p}"
      done
    }
  fi
}

install_pipx_tools() {
  log "Installing Python OSINT tools via pipx..."
  mapfile -t tools < <(read_list "${PROVISION_DIR}/packages.pipx")
  [ "${#tools[@]}" -gt 0 ] || return 0

  # pipx installs go to the target user's home so the tools land on their PATH.
  local run_as=()
  [ -n "${TARGET_USER}" ] && run_as=(sudo -u "${TARGET_USER}" -H)

  "${run_as[@]}" bash -c 'command -v pipx >/dev/null || python3 -m pip install --user pipx'
  "${run_as[@]}" bash -lc 'pipx ensurepath' || true

  for t in "${tools[@]}"; do
    log "  pipx install ${t}"
    "${run_as[@]}" bash -lc "pipx install '${t}'" \
      || warn "pipx failed for '${t}' (continuing)."
  done
}

install_go_tools() {
  mapfile -t gotools < <(read_list "${PROVISION_DIR}/packages.go")
  [ "${#gotools[@]}" -gt 0 ] || return 0

  if ! command -v go >/dev/null 2>&1; then
    warn "Go toolchain not found; skipping Go OSINT tools (e.g. amass)."
    warn "  Install Go and re-run, or grab amass via snap: 'snap install amass'."
    return 0
  fi

  log "Installing Go OSINT tools..."
  local run_as=()
  [ -n "${TARGET_USER}" ] && run_as=(sudo -u "${TARGET_USER}" -H)
  for g in "${gotools[@]}"; do
    log "  go install ${g}"
    # Land binaries on a system-wide PATH location.
    "${run_as[@]}" env GOBIN=/usr/local/bin go install "${g}" \
      || warn "go install failed for '${g}' (continuing)."
  done
}

apply_theme() {
  if [ "${HEADLESS}" = "1" ]; then
    log "Headless mode: skipping desktop theming."
    return 0
  fi
  log "Applying XP-style desktop theme..."
  if [ -x "${THEME_DIR}/install-theme.sh" ]; then
    BLISS_TARGET_USER="${TARGET_USER}" "${THEME_DIR}/install-theme.sh"
  else
    warn "theme/install-theme.sh not found or not executable; skipping theming."
  fi
}

main() {
  install_apt_packages
  install_pipx_tools
  install_go_tools
  apply_theme
  if [ "${HEADLESS}" = "1" ]; then
    log "Headless provision done: OSINT toolkit installed (no desktop)."
  else
    log "Done. Log out and back in (or reboot) to get the Windows XP look."
  fi
  log "Read docs/opsec.md before you start investigating anything."
}

main "$@"
