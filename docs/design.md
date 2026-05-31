# Design notes

## Goal

A reproducible, *secure* OSINT workstation that looks like Windows XP, for
learning and personal research.

## Key decisions

### Why not real Windows XP?

- **Security:** XP is end-of-life (April 2014). Unpatched RCE vulnerabilities
  (EternalBlue and friends) make it a liability for any online activity,
  especially OSINT where the whole point is *not* getting compromised.
- **Legal:** Windows XP is proprietary Microsoft IP; redistributing a modified
  image is not permitted.
- **Tooling:** Modern OSINT tools need Python 3.9+, modern TLS, current browsers.
  The XP-era stack can't run them and can't even load most modern websites.

So we ship the **aesthetic** of XP on a **modern Debian** base.

### Why Debian + XFCE?

- **Debian stable** — well-supported, secure, the base most security/OSINT
  distros (Kali, Tsurugi) build on. `live-build` is the standard, well-documented
  ISO toolchain.
- **XFCE** — lightweight and *extremely* themeable. With the right GTK theme,
  icon set, panel layout, wallpaper, and a Whisker/Start-style menu, it
  convincingly mimics the XP "Luna" desktop while staying fast in a VM.

### Two delivery paths

1. **`provision/provision.sh`** — runs on an existing Debian/Ubuntu install.
   Lowest barrier for learners: spin up a VM, run one script. Idempotent-ish;
   safe to re-run.
2. **`build/build.sh`** — `live-build` config that bakes the same package lists +
   theming into a bootable hybrid ISO. Same source of truth (`provision/packages.*`)
   so the two paths don't drift.

### Theming approach

- GTK theme + window decorations: an open XP-style theme (e.g. B00merang's
  "Windows XP" GTK theme) dropped into `/usr/share/themes`.
- Icons: an XP-style icon set in `/usr/share/icons`.
- Panel: a single bottom panel with a Start-style Whisker menu, task list, and
  clock, configured via the XFCE config in [`theme/`](../theme).
- Wallpaper: a Bliss-style green-hills wallpaper. **We ship a placeholder /
  generator, not Microsoft's copyrighted Bliss photo.** Drop your own in
  `theme/wallpaper/`.

We deliberately ship **no Microsoft assets**. Everything is either open-licensed
look-alikes or user-supplied.

## Repository layout

```
.
├── README.md
├── LICENSE
├── docs/            # design, tools, opsec
├── provision/       # in-place provisioner + package lists (source of truth)
├── build/           # live-build ISO builder (consumes provision/ lists)
└── theme/           # XFCE config, GTK/icon theme installers, wallpaper
```

## Roadmap ideas

- Pre-seeded Firefox profile with OSINT bookmarks + privacy hardening.
- Optional Tor/VPN toggle in the panel.
- A "boot to investigation" guided checklist app.
- CI to build the ISO and run shellcheck on the scripts.
