# tests/

## `osint-smoke.sh` — exercise the toolkit against a fictional identity

A safe end-to-end check that the OSINT tools are installed and working. It runs
them against an **invented persona** on **RFC 2606 reserved domains**
(`example.com`), so no real person or infrastructure is targeted.

> A clean run mostly returns "not found" — that's the point. It proves the tools
> *execute and reach their sources*, not that the fake persona exists.

### Run it (on the provisioned VM, where the network works)

```bash
# Full live run against the default fictional identity:
./tests/osint-smoke.sh

# Use your own fictional values:
USERNAME=madeup_handle_42 EMAIL=nobody@example.com DOMAIN=example.org \
  ./tests/osint-smoke.sh

# Offline mode: just verify tools are installed + run the metadata demo:
./tests/osint-smoke.sh --check
```

### What it checks

| Step | Tool | Needs network |
|------|------|---------------|
| Username search | `sherlock` | yes |
| Username enumeration | `maigret` | yes |
| Email registration lookup | `holehe` | yes |
| Domain harvest | `theHarvester` | yes |
| DNS recon | `dnsrecon` | yes |
| Metadata extraction | `exiftool` | **no** (offline demo) |

Each step **skips** (doesn't fail) if its tool isn't installed, and every live
step is time-capped (`BLISS_SMOKE_TIMEOUT`, default 90s) so a slow source list
can't hang the run.

### Why it can't run in this repo's CI

CI runners don't have the OSINT tools installed (and shouldn't make live external
queries), so CI only **shellchecks** this script. Run the actual smoke test on a
booted BlissOSINT VM. Remember `docs/opsec.md`: run it from a disposable VM and
never point it at a real person.
