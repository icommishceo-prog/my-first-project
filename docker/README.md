# docker/ — headless OSINT toolkit image

Build and smoke-test the OSINT toolkit in ~2 minutes, without building a full
themed VM/ISO. This image ships the **tools only** (headless) — no XP desktop.

## Build

```bash
docker build -t bliss-osint -f docker/Dockerfile .
```

## Run

```bash
# Offline: verify every tool is installed + the metadata demo (no network).
docker run --rm bliss-osint

# Live: run the fictional-identity smoke test against public sources.
docker run --rm bliss-osint ./tests/osint-smoke.sh

# Your own fictional values:
docker run --rm -e USERNAME=madeup_handle_42 -e EMAIL=nobody@example.com \
  -e DOMAIN=example.org bliss-osint ./tests/osint-smoke.sh

# Interactive shell with the toolkit on PATH:
docker run --rm -it bliss-osint bash
```

## What this proves

The default `docker run` executes the **real install path** end-to-end
(`BLISS_HEADLESS=1 provision.sh`), so a green result confirms the apt/pipx
package names actually resolve and the tools launch — the thing config-only CI
couldn't verify. This same image backs the CI `toolkit-smoke` job.

## Want the full XP desktop?

Use the Vagrant VM (`vagrant up`) or the live ISO (`sudo ./build/build.sh`).
The desktop and theming are deliberately out of scope for this image.

Remember [`../docs/opsec.md`](../docs/opsec.md): only run live checks against
fictional or authorized targets.
