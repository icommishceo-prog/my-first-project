# OPSEC, legal, and ethics

OSINT works with information that is **already public**. That doesn't make
everything fair game. Read this before you investigate anything.

## Legal & ethical ground rules

- **Authorization.** Only investigate people, organizations, or assets you are
  authorized to (your own accounts, an explicit engagement, a CTF target, or
  public research with a legitimate purpose). "It's public" is not the same as
  "I'm allowed to compile a dossier on this private individual."
- **No harassment, stalking, or doxxing.** Don't use these tools to locate,
  intimidate, or expose private individuals. That's the line between research
  and harm.
- **Respect terms of service and law.** Scraping and automated querying can
  violate platform ToS and, in some jurisdictions, the law. Active recon
  (port scanning, subdomain brute-forcing against infrastructure you don't own)
  can be illegal. Know your local rules.
- **Data minimization.** Collect only what your purpose requires. Store it
  securely. Delete it when you're done.

## Operational security (protecting yourself)

Even passive OSINT leaks information about *you* to the things you query.

- **Run it in a VM.** Treat the investigation environment as disposable. Snapshot
  before, revert after. Never investigate from your daily-driver machine or
  personal accounts.
- **Separate identity.** Use research-only ("sock puppet") accounts and browsers,
  never personal logins. Don't cross-contaminate.
- **Network hygiene.** Consider a VPN or Tor for browsing so your home IP isn't
  attached to every lookup. Know that some tools (and API keys) deanonymize you
  regardless.
- **API keys are attributable.** Keys you register for (Shodan, Hunter, etc.)
  tie queries back to you. Use dedicated accounts.
- **No accidental active recon.** Many "OSINT" tools quietly touch the target
  (DNS, HTTP, WHOIS). Understand what each tool does on the wire before running
  it against anything you don't own.

## Why this distro is *themed* XP, not real XP

Real Windows XP is end-of-life and unpatched — running it online means *you* are
the easy target. BlissOSINT gives you the XP look on a current Debian base that
still receives security updates, so your research box isn't trivially
compromised. OPSEC starts with not running a 20-year-old unpatched OS.
