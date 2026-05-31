# Bundled OSINT tools

All open-source, all installed by the provisioning script / ISO build. Grouped
by what they do. Every one of these works with **public** data — read
[`opsec.md`](opsec.md) for the rules of engagement.

## Recon frameworks

| Tool | Purpose | Install source |
|------|---------|----------------|
| SpiderFoot | Automated OSINT collection + correlation, web UI | pipx |
| recon-ng | Modular web recon framework | apt / pipx |
| theHarvester | Emails, subdomains, hosts, names from public sources | apt / pipx |

## Username / email / people

| Tool | Purpose | Install source |
|------|---------|----------------|
| Sherlock | Find usernames across social networks | pipx |
| Maigret | Username enumeration + report generation | pipx |
| holehe | Check which sites an email is registered on | pipx |

## Domain / subdomain / infrastructure

| Tool | Purpose | Install source |
|------|---------|----------------|
| Amass | In-depth attack-surface / subdomain mapping | apt |
| dnsrecon | DNS enumeration | apt |
| whois / dnsutils | Classic WHOIS + dig/host | apt |
| Photon | Fast web crawler for OSINT | pipx |

## Metadata / files / images

| Tool | Purpose | Install source |
|------|---------|----------------|
| exiftool | Read/strip file & image metadata | apt |
| metagoofil | Harvest metadata from public documents | pipx |

## Browser & manual workflow

- **Firefox ESR** with a starter set of OSINT bookmarks (search engines,
  archives, image search, certificate transparency, etc.).
- Note-taking + screenshot tools for documenting findings.

## Optional / not bundled (license or footprint reasons)

- **Maltego** — excellent link-analysis tool, but proprietary (free Community
  Edition requires manual download/registration). Install it yourself if you
  want it.
- **subfinder / amass advanced sources** — many premium data sources need API
  keys you must register for. The tools are installed; the keys are up to you.

## Adding more

Edit [`provision/packages.apt`](../provision/packages.apt) (Debian packages) or
[`provision/packages.pipx`](../provision/packages.pipx) (Python tools) and
re-run the provisioner. The ISO build reads the same lists.
