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

### Saving reports (JSON + HTML)

Add `--report` (or `--report=DIR`, or `BLISS_REPORT_DIR=DIR`) to save findings:

```bash
NAME="Ada Lovelace" ./tests/osint-smoke.sh --report            # -> reports/smoke-<ts>/
./tests/osint-smoke.sh --report=out/run1                        # explicit dir
```

Each run writes:

- **`report.json`** — machine-readable: identity, summary counts, and a
  `results[]` array (per check: `label`, `bin`, `command`, `status`, `rc`,
  `duration_s`, `raw`).
- **`report.html`** — a self-contained, theme-aware table, one row per check,
  linking to each tool's captured raw output.
- **`raw/*.txt`** — the full stdout/stderr of every tool that ran.

Reporting needs `jq` (a core dependency); if it's missing the run continues
without reports. `reports/` is git-ignored — treat findings as sensitive and
keep them off the repo (see [`../docs/opsec.md`](../docs/opsec.md)).

### Testing with a *name* (not just a handle)

Username/email tools take handles, not full names. Set `NAME=` and the smoke
test derives candidate handles from the name (via `derive-persona.sh`, offline)
and enumerates each one:

```bash
# Derive handles from a name, then enumerate them (run only against fictional
# or authorized identities — see ../docs/opsec.md):
NAME="Ada Lovelace" ./tests/osint-smoke.sh

# Just see the candidate handles/emails without running anything:
./tests/derive-persona.sh --emails "Ada Lovelace"
```

`derive-persona.sh` produces the usual patterns — `firstlast`, `first.last`,
`first_last`, `flast`, `initials+last` (e.g. `ldstone`), etc. — deduplicated.
It is pure offline string work and targets nobody; the enumeration step it feeds
is what actually touches the network, so keep that pointed at fictional or
authorized subjects only.

### What it checks

| Step | Tool | Needs network |
|------|------|---------------|
| Username search | `sherlock` | yes |
| Username enumeration | `maigret` | yes |
| Email registration lookup | `holehe` | yes |
| Domain harvest | `theHarvester` | yes |
| DNS recon | `dnsrecon` | yes |
| Metadata extraction | `exiftool` | **no** (offline demo) |
| Name → handle derivation | `derive-persona.sh` | **no** (offline, when `NAME=` set) |

Each step **skips** (doesn't fail) if its tool isn't installed, and every live
step is time-capped (`BLISS_SMOKE_TIMEOUT`, default 90s) so a slow source list
can't hang the run.

### Why it can't run in this repo's CI

CI runners don't have the OSINT tools installed (and shouldn't make live external
queries), so CI only **shellchecks** this script. Run the actual smoke test on a
booted BlissOSINT VM. Remember `docs/opsec.md`: run it from a disposable VM and
never point it at a real person.
