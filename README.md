# Bug Bounty Automation

Automated test runner for web app / API bug bounties. Runs nmap → ffuf → nuclei → Burp Suite in sequence, then generates a report + manual testing checklist.

## Quick Start

```bash
# 1. Add your scope targets
nano config/scope.txt

# 2. Get a wordlist (pick one)
cp /usr/share/seclists/Discovery/Web-Content/common.txt wordlists/common.txt
# or: wget <seclists-url> -O wordlists/common.txt

# 3. Install Python deps
pip3 install pyyaml

# 4. Run everything
python3 run_tests.py
```

## What Gets Automated

| Phase | Tool | What it does |
|-------|------|--------------|
| 1. Recon | nmap | Port scan, service/version detection, default scripts |
| 2. Discovery | ffuf | Directory bruteforce, API endpoint discovery, JS file hunting |
| 3. Vuln scan | nuclei | CVEs, misconfigs, exposed panels, default logins, takeovers, fuzzing |
| 4. Active scan | Burp Suite Pro | Full crawl + audit via REST API |
| 5. Report | Python | Aggregates findings + generates manual checklist |

## Flags

```bash
python3 run_tests.py --skip-recon        # skip nmap
python3 run_tests.py --skip-discovery    # skip ffuf
python3 run_tests.py --skip-nuclei       # skip nuclei
python3 run_tests.py --skip-burp         # skip Burp (default if no API key set)
```

## Output Structure

```
output/
├── recon/          # nmap .txt + .xml per target
├── discovery/      # ffuf JSON results per target
├── vulns/          # nuclei + Burp findings per target
└── reports/
    ├── report_<timestamp>.md    # full report
    └── manual_checklist.md     # what you still need to test manually
```

## Burp Suite Setup

1. Open Burp Suite Pro
2. Settings → Suite → REST API → enable, note the port (default 1337)
3. Copy API key into `config/config.yaml` under `burp.api_key`

## Manual Checklist

After automation completes, open `output/reports/manual_checklist.md` — it covers
IDOR, business logic, race conditions, auth bypasses, and other things that
automation reliably misses.

## Requirements

- `nmap`
- `ffuf`
- `nuclei` (`go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest`)
- `python3` + `pyyaml` (`pip3 install pyyaml`)
- Burp Suite Pro (optional, for active scanning phase)
