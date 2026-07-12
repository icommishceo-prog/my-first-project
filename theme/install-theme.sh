#!/usr/bin/env bash
#
# Installs the Windows XP "Luna"-style desktop theme for XFCE.
#
# - Fetches an open-licensed XP-style GTK theme + icons (no Microsoft assets).
# - Installs the XFCE panel/desktop config that recreates the XP layout.
# - Sets a Bliss-style wallpaper (user-supplied or generated placeholder).
#
# Called by provision/provision.sh, but can be run standalone:
#   sudo ./theme/install-theme.sh
#
# Honors BLISS_TARGET_USER (the desktop user to configure). If unset, only
# /etc/skel is seeded so new users inherit the look.

set -euo pipefail

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_USER="${BLISS_TARGET_USER:-${SUDO_USER:-}}"

log()  { printf '\033[1;32m[theme]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[theme]\033[0m %s\n' "$*" >&2; }

# Open-licensed XP-style GTK theme. Swap this for any theme you prefer.
XP_GTK_THEME_REPO="https://github.com/B00merang-Project/Windows-XP"
XP_GTK_THEME_NAME="Windows XP"

install_gtk_theme() {
  local dest="/usr/share/themes/${XP_GTK_THEME_NAME}"
  if [ -d "${dest}" ]; then
    log "GTK theme already present: ${dest}"
    return 0
  fi
  if ! command -v git >/dev/null 2>&1; then
    warn "git not available; skipping XP GTK theme download."
    return 0
  fi
  log "Fetching XP-style GTK theme from ${XP_GTK_THEME_REPO}"
  local tmp
  tmp="$(mktemp -d)"
  if git clone --depth 1 "${XP_GTK_THEME_REPO}" "${tmp}/xp-theme"; then
    mkdir -p "${dest}"
    cp -r "${tmp}/xp-theme/." "${dest}/"
    log "Installed GTK theme -> ${dest}"
  else
    warn "Could not download GTK theme (offline?). Desktop will use the fallback theme."
  fi
  rm -rf "${tmp}"
}

install_wallpaper() {
  local wp_src="${THEME_DIR}/wallpaper/bliss.png"
  local wp_dest="/usr/share/backgrounds/bliss-osint.png"
  if [ -f "${wp_src}" ]; then
    cp "${wp_src}" "${wp_dest}"
    log "Installed wallpaper -> ${wp_dest}"
  elif command -v convert >/dev/null 2>&1; then
    # Generate a Bliss-style green-hills-under-blue-sky gradient as a placeholder.
    log "No wallpaper supplied; generating a Bliss-style placeholder."
    convert -size 1920x1080 \
      gradient:'#5b8fd6'-'#a8d0f0' \
      \( -size 1920x320 gradient:'#6cab3f'-'#3f7a26' \) \
      -gravity south -composite "${wp_dest}" \
      || warn "Wallpaper generation failed; skipping."
  else
    warn "No wallpaper and ImageMagick not installed; drop a PNG at theme/wallpaper/bliss.png."
  fi
}

install_firefox_policies() {
  # Deploy OSINT bookmarks + privacy hardening via Firefox enterprise policies.
  # Different Firefox builds read different system paths, so cover the common
  # ones (firefox-esr on Debian, plain firefox, and the generic /etc path).
  local src="${THEME_DIR}/firefox/policies.json"
  [ -f "${src}" ] || { warn "No Firefox policies at ${src}; skipping bookmarks."; return 0; }

  local installed=0
  for dir in /etc/firefox/policies \
             /etc/firefox-esr/policies \
             /usr/lib/firefox-esr/distribution \
             /usr/lib/firefox/distribution; do
    # Only target dirs whose parent exists (i.e. that browser flavor is present),
    # except /etc/firefox which we always create as the modern standard path.
    if [ "${dir}" = "/etc/firefox/policies" ] || [ -d "$(dirname "${dir}")" ]; then
      mkdir -p "${dir}"
      cp "${src}" "${dir}/policies.json"
      installed=1
    fi
  done
  if [ "${installed}" -eq 1 ]; then
    log "Installed Firefox OSINT bookmarks + privacy policy."
  else
    warn "Could not place Firefox policies anywhere."
  fi
}

seed_xfce_config() {
  # Copy the XFCE config tree into a home directory's ~/.config.
  local home_dir="$1"
  local owner="$2"
  local cfg_src="${THEME_DIR}/xfce4"
  [ -d "${cfg_src}" ] || { warn "No XFCE config at ${cfg_src}; skipping."; return 0; }

  log "Seeding XFCE config into ${home_dir}/.config/xfce4"
  mkdir -p "${home_dir}/.config"
  cp -r "${cfg_src}" "${home_dir}/.config/"
  if [ -n "${owner}" ]; then
    chown -R "${owner}:${owner}" "${home_dir}/.config/xfce4"
  fi
}

apply_to_users() {
  # Always seed /etc/skel so future users inherit the theme.
  seed_xfce_config "/etc/skel" ""

  if [ -n "${TARGET_USER}" ] && [ "${TARGET_USER}" != "root" ]; then
    local home_dir
    home_dir="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
    if [ -n "${home_dir}" ] && [ -d "${home_dir}" ]; then
      seed_xfce_config "${home_dir}" "${TARGET_USER}"
    else
      warn "Could not resolve home for ${TARGET_USER}; only /etc/skel seeded."
    fi
  fi
}

main() {
  [ "$(id -u)" -eq 0 ] || { warn "Run as root for system-wide theme install."; }
  install_gtk_theme
  install_wallpaper
  install_firefox_policies
  apply_to_users
  log "Theme applied. Set GTK theme '${XP_GTK_THEME_NAME}' + Papirus icons via"
  log "Settings > Appearance if it isn't picked up automatically."
}

main "$@"
