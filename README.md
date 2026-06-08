# BlissOSINT

A **Windows XP–themed OSINT workstation** built on a modern, *secure* Linux base.

> The look of 2001, the security patches of today.

BlissOSINT is **not** Windows XP. Running actual Windows XP for OSINT is a bad
idea — it lost security support in 2014, it's full of unpatched remote-code-
execution holes, and you legally can't redistribute a modified XP image. So
instead this project takes a current, fully-patched **Debian** base and *skins*
the desktop to look and feel like XP (Luna theme, Bliss-style wallpaper, that
Start menu), then preloads a curated set of open-source OSINT tools.

You get the nostalgia without the security disaster.

---

## What you get

- A lightweight **XFCE** desktop skinned to look like Windows XP "Luna".
- A curated, open-source **OSINT toolkit** (recon, username/email enumeration,
  metadata, subdomain discovery, etc.) — see [`docs/tools.md`](docs/tools.md).
- **Firefox ESR** pre-loaded with an OSINT bookmarks toolbar and privacy
  hardening via enterprise policy.
- Two ways to use it:
  1. **Build a bootable live ISO** (run it in a VM or off a USB) — [`build/`](build/)
  2. **Provision an existing Debian/Ubuntu VM** in place — [`provision/`](provision/)
- OPSEC and legal guidance written for learners — [`docs/opsec.md`](docs/opsec.md).

## Quick start (provision a VM — easiest)

Spin up a fresh **Debian 12** or **Ubuntu 24.04** VM, clone this repo, then:

```bash
sudo ./provision/provision.sh
```

That installs the desktop theming + OSINT tools onto the running system. Log out
and back in to get the XP look. This is the recommended path for learning —
no ISO build required.

## Build a live ISO (advanced)

On a Debian host with `live-build` installed:

```bash
sudo ./build/build.sh
```

Produces `bliss-osint-*.hybrid.iso` you can boot in a VM or write to USB. See
[`build/README.md`](build/README.md) for details and requirements.

## Intended use

This project is for **learning and personal OSINT research**. OSINT means
*open-source intelligence* — collecting information that is already public.
Read [`docs/opsec.md`](docs/opsec.md) before you start: only investigate targets
you're authorized to, respect local law and platform terms of service, and don't
use these tools to harass, stalk, or dox anyone.

## Testing

Validate the toolkit safely against an **invented persona** on RFC 2606 reserved
domains — no real target:

```bash
./tests/osint-smoke.sh            # live run on the provisioned VM
./tests/osint-smoke.sh --check    # offline: tool presence + metadata demo
```

See [`tests/README.md`](tests/README.md). A clean run mostly returns "not found"
— that's success.

## CI

A GitHub Actions workflow ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
runs ShellCheck on the scripts, validates the XFCE XML and Firefox JSON, checks
the package lists, and validates the live-build config (`BLISS_CONFIG_ONLY=1`)
without doing the heavyweight full ISO build.

## Status

Early scaffold. The build system and provisioning scripts are functional
starting points; theming assets pull from open theme projects and you can drop
your own XP assets into [`theme/`](theme/). Contributions welcome.

## License

Project scripts and config: MIT (see [`LICENSE`](LICENSE)). Bundled tools and
themes retain their own licenses.
