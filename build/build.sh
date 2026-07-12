#!/usr/bin/env bash
#
# BlissOSINT ISO builder.
#
# Wraps Debian `live-build` to produce a bootable hybrid ISO that boots into the
# XP-themed XFCE desktop with the OSINT toolkit preinstalled.
#
#   sudo ./build/build.sh
#
# Requirements (Debian host): live-build, debootstrap. Install with:
#   sudo apt-get install live-build
#
# The build reads the SAME package lists as the in-place provisioner
# (provision/packages.apt and provision/packages.pipx) so the ISO and the
# provisioned VM stay in sync.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"
WORK_DIR="${BUILD_DIR}/work"
PROVISION_DIR="${REPO_ROOT}/provision"
DIST="${BLISS_DIST:-bookworm}"   # Debian 12

log()  { printf '\033[1;32m[build]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[build]\033[0m %s\n' "$*" >&2; exit 1; }

command -v lb >/dev/null 2>&1 || die "live-build not installed. Run: apt-get install live-build"

# BLISS_CONFIG_ONLY=1 prepares + validates the live-build config without doing
# the (root-only, multi-GB) full build. Used by CI to catch bad flags early.
CONFIG_ONLY="${BLISS_CONFIG_ONLY:-0}"

strip_list() { sed -e 's/#.*$//' -e 's/[[:space:]]*$//' "$1" | grep -v '^[[:space:]]*$' || true; }

prepare_config() {
  log "Preparing live-build config in ${WORK_DIR} (dist=${DIST})"
  rm -rf "${WORK_DIR}"
  mkdir -p "${WORK_DIR}"
  cd "${WORK_DIR}"

  lb config \
    --distribution "${DIST}" \
    --architectures amd64 \
    --debian-installer none \
    --archive-areas "main contrib non-free non-free-firmware" \
    --iso-application "BlissOSINT" \
    --iso-volume "BlissOSINT"

  # --- apt package list baked into the chroot (core + OSINT + desktop) ---
  mkdir -p config/package-lists
  {
    strip_list "${PROVISION_DIR}/packages.apt"
    strip_list "${PROVISION_DIR}/packages.desktop.apt"
    # live-system runtime is required for a bootable live image.
    printf 'live-boot\nlive-config\nlive-config-systemd\n'
  } > config/package-lists/bliss-osint.list.chroot

  # --- bake the repo into the image so hooks can call provisioner pieces ---
  mkdir -p config/includes.chroot/opt/bliss-osint
  cp -r "${REPO_ROOT}/provision" "${REPO_ROOT}/theme" "${REPO_ROOT}/docs" \
        config/includes.chroot/opt/bliss-osint/

  # --- chroot hook: pipx tools + theme, run inside the building image ---
  mkdir -p config/hooks/normal
  cat > config/hooks/normal/9000-bliss-osint.hook.chroot <<'HOOK'
#!/bin/sh
set -e
echo "[bliss-hook] installing pipx OSINT tools + theme into image"

# Install pipx tools system-wide so every live user gets them on PATH.
export PIPX_HOME=/opt/pipx
export PIPX_BIN_DIR=/usr/local/bin
mkdir -p "$PIPX_HOME" "$PIPX_BIN_DIR"

sed -e 's/#.*$//' -e 's/[[:space:]]*$//' /opt/bliss-osint/provision/packages.pipx \
  | grep -v '^[[:space:]]*$' \
  | while read -r tool; do
      echo "[bliss-hook] pipx install $tool"
      pipx install "$tool" || echo "[bliss-hook] WARN: pipx failed for $tool"
    done

# Apply the XP theme into /etc/skel so the live user inherits it at boot.
chmod +x /opt/bliss-osint/theme/install-theme.sh || true
BLISS_TARGET_USER="" /opt/bliss-osint/theme/install-theme.sh || \
  echo "[bliss-hook] WARN: theme install reported a problem"
HOOK
  chmod +x config/hooks/normal/9000-bliss-osint.hook.chroot
}

run_build() {
  [ "$(id -u)" -eq 0 ] || die "live-build needs root for the full build: run with sudo."
  log "Running lb build (this takes a while and downloads a lot)..."
  cd "${WORK_DIR}"
  lb build

  local iso
  iso="$(find "${WORK_DIR}" -maxdepth 1 -name '*.iso' -print -quit)"
  if [ -n "${iso}" ]; then
    local out
    out="${BUILD_DIR}/bliss-osint-${DIST}-$(date +%Y%m%d).iso"
    mv "${iso}" "${out}"
    log "ISO ready: ${out}"
    log "Boot it in a VM (VirtualBox/QEMU) and read docs/opsec.md before use."
  else
    die "Build finished but no ISO was produced; check live-build output above."
  fi
}

prepare_config
if [ "${CONFIG_ONLY}" = "1" ]; then
  log "BLISS_CONFIG_ONLY=1: config prepared and validated; skipping full build."
  exit 0
fi
run_build
