# BlissOSINT headless OSINT toolkit image.
#
# Installs ONLY the OSINT toolkit (no XP desktop) via the provisioner's headless
# mode, so you can build and smoke-test the tools in ~2 minutes.
#
#   docker build -t bliss-osint -f docker/Dockerfile .
#   docker run --rm bliss-osint                       # offline tool-presence check
#   docker run --rm bliss-osint ./tests/osint-smoke.sh  # live fictional-identity run
#
# The XP desktop is intentionally NOT here -- use the Vagrant VM or the live ISO
# for the full themed experience.
FROM debian:12-slim

LABEL org.opencontainers.image.title="BlissOSINT toolkit" \
      org.opencontainers.image.description="Headless open-source OSINT toolkit (no desktop)"

ENV DEBIAN_FRONTEND=noninteractive
# pipx installs land in root's ~/.local/bin; put it on PATH for the tools + CMD.
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /opt/bliss-osint
COPY . .

# Headless provision: core + OSINT apt packages, pipx tools, no desktop/theming.
RUN chmod +x provision/provision.sh tests/osint-smoke.sh \
    && BLISS_HEADLESS=1 ./provision/provision.sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Default: offline check that every tool is installed and importable.
CMD ["./tests/osint-smoke.sh", "--check"]
