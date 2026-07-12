# Bundled OSINT tools

All open-source, all installed by the provisioning script / ISO build. Grouped
by what they do. Every one of these works with **public** data — read
[`opsec.md`](opsec.md) for the rules of engagement.

> **Install source legend.** `apt` = in Debian 12 repos. `pipx` = Python tool,
> not in Debian, installed in an isolated venv. `go` = Go tool, installed with
> `go install` only if a Go toolchain is present. Verified against Debian 12
> (bookworm) — theHarvester, recon-ng and amass are **not** Debian packages, so
> they come from pipx/go rather than apt.

## Recon frameworks

| Tool | Purpose | Install source |
|------|---------|----------------|
| SpiderFoot | Automated OSINT collection + correlation, web UI | pipx |
| recon-ng | Modular web recon framework | pipx |
| theHarvester | Emails, subdomains, hosts, names from public sources | pipx |

## Username / email / people

| Tool | Purpose | Install source |
|------|---------|----------------|
| Sherlock | Find usernames across social networks | pipx |
| Maigret | Username enumeration + report generation | pipx |
| holehe | Check which sites an email is registered on | pipx |

## Domain / subdomain / infrastructure

| Tool | Purpose | Install source |
|------|---------|----------------|
| Amass | In-depth attack-surface / subdomain mapping | go (or `snap install amass`) |
| dnsrecon | DNS enumeration | apt |
| whois / bind9-dnsutils | Classic WHOIS + dig/host | apt |
| Photon | Fast web crawler for OSINT | pipx |

## Phone numbers

| Tool | Purpose | Install source |
|------|---------|----------------|
| PhoneInfoga | Phone-number recon (format, carrier, line type, footprint) | prebuilt binary (`provision/install-phoneinfoga.sh`) |

Installed from the official GitHub release binary by
[`provision/install-phoneinfoga.sh`](../provision/install-phoneinfoga.sh) (called
by the provisioner, so the Docker image and VM both get it). `go install` is
deliberately **not** used — PhoneInfoga's web client is only embedded in release
builds, so a source build fails with `pattern client/dist/*: no matching files`.
Pin a version with `PHONEINFOGA_VERSION=v2.11.0`. Some scanners (numverify,
Google CSE) need API keys — the local scanner runs without them. Scan with
`phoneinfoga scan -n "+13125550123"`.

## Metadata / files / images

| Tool | Purpose | Install source |
|------|---------|----------------|
| exiftool | Read/strip file & image metadata | apt |
| metagoofil | Harvest metadata from public documents | pipx |

## Browser & manual workflow

- **Firefox ESR**, pre-loaded via enterprise policy
  ([`theme/firefox/policies.json`](../theme/firefox/policies.json)) with an
  **OSINT** bookmarks toolbar folder (search engines, archives, reverse image
  search, certificate transparency, breach lookup, etc.) and privacy hardening
  (telemetry/Pocket/sponsored content off).
- Note-taking + screenshot tools for documenting findings.

## Optional / not bundled (license or footprint reasons)

- **Maltego** — excellent link-analysis tool, but proprietary (free Community
  Edition requires manual download/registration). Install it yourself if you
  want it.
- **Premium data sources** — many tools (amass, theHarvester, SpiderFoot) can
  pull from sources that need API keys you must register for. The tools are
  installed; the keys are up to you. Keys are attributable — see
  [`opsec.md`](opsec.md).

## Adding more

Edit the relevant list and re-run the provisioner (the ISO build reads the same
lists):

- [`provision/packages.apt`](../provision/packages.apt) — Debian packages
- [`provision/packages.pipx`](../provision/packages.pipx) — Python tools
- [`provision/packages.go`](../provision/packages.go) — Go tools (installed only
  when a Go toolchain is present)
