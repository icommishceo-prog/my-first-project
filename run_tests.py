#!/usr/bin/env python3
"""
Bug Bounty Automated Test Runner
Usage:  python3 run_tests.py [--skip-recon] [--skip-discovery] [--skip-nuclei] [--skip-burp]

Reads config/scope.txt and config/config.yaml, runs all phases, writes output/.
"""

import argparse
import os
import subprocess
import sys
import time
import yaml


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_scope(path: str) -> list[str]:
    targets = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                targets.append(line)
    return targets


def run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd)
    return result.returncode


def safe_name(target: str) -> str:
    return target.replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_")


def ensure_http(target: str) -> str:
    if not target.startswith("http"):
        return f"https://{target}"
    return target


def check_tools(skip_burp: bool) -> None:
    required = ["nmap", "ffuf", "nuclei"]
    missing = [t for t in required if subprocess.run(["which", t], capture_output=True).returncode != 0]
    if missing:
        print(f"[!] Missing tools: {', '.join(missing)}")
        print("    Install them before running. Aborting.")
        sys.exit(1)
    if not skip_burp:
        if subprocess.run(["which", "python3"], capture_output=True).returncode != 0:
            print("[!] python3 required for Burp integration.")
            sys.exit(1)


# ── phases ───────────────────────────────────────────────────────────────────

def phase_recon(target: str, cfg: dict, out_dir: str) -> None:
    nmap_cfg = cfg.get("nmap", {})
    run(
        [
            "bash", "scripts/recon.sh",
            target,
            out_dir,
            nmap_cfg.get("flags", "-sV -sC -T4 --open"),
            nmap_cfg.get("ports", "80,443,8080,8443"),
        ],
        f"[RECON] nmap → {target}",
    )


def phase_discovery(target: str, cfg: dict, out_dir: str) -> None:
    url = ensure_http(target)
    ffuf_cfg = cfg.get("ffuf", {})
    run(
        [
            "bash", "scripts/discovery.sh",
            url,
            out_dir,
            ffuf_cfg.get("wordlist", "wordlists/common.txt"),
            str(ffuf_cfg.get("threads", 40)),
            str(ffuf_cfg.get("rate_limit", 100)),
            ffuf_cfg.get("extensions", "php,html,js,json"),
        ],
        f"[DISCOVERY] ffuf → {url}",
    )


def phase_nuclei(target: str, cfg: dict, out_dir: str) -> None:
    url = ensure_http(target)
    nuclei_cfg = cfg.get("nuclei", {})
    sn = safe_name(target)
    extra_urls = f"{out_dir}/discovery/{safe_name(url)}/discovered_urls.txt"

    run(
        [
            "bash", "scripts/vuln_scan.sh",
            url,
            out_dir,
            nuclei_cfg.get("severity", "low,medium,high,critical"),
            str(nuclei_cfg.get("rate_limit", 50)),
            extra_urls,
        ],
        f"[NUCLEI] vuln scan → {url}",
    )


def phase_burp(target: str, cfg: dict, out_dir: str) -> None:
    url = ensure_http(target)
    burp_cfg = cfg.get("burp", {})
    api_url = burp_cfg.get("api_url", "http://127.0.0.1:1337")
    api_key = burp_cfg.get("api_key", "")
    sn = safe_name(target)
    out_file = f"{out_dir}/vulns/{sn}_burp.json"

    if not api_key:
        print(f"[!] Burp API key not set in config/config.yaml — skipping Burp scan for {target}")
        return

    run(
        ["python3", "scripts/burp_scan.py", url, api_url, api_key, out_file],
        f"[BURP] active scan → {url}",
    )


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Bug Bounty Automated Test Runner")
    parser.add_argument("--skip-recon",     action="store_true", help="Skip nmap recon phase")
    parser.add_argument("--skip-discovery", action="store_true", help="Skip ffuf discovery phase")
    parser.add_argument("--skip-nuclei",    action="store_true", help="Skip nuclei vuln scan phase")
    parser.add_argument("--skip-burp",      action="store_true", help="Skip Burp Suite active scan")
    parser.add_argument("--config",         default="config/config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    scope_file = cfg.get("scope_file", "config/scope.txt")
    out_dir = cfg.get("output_dir", "output")

    targets = load_scope(scope_file)
    if not targets:
        print(f"[!] No targets found in {scope_file}. Add your scope first.")
        sys.exit(1)

    check_tools(skip_burp=args.skip_burp)

    os.makedirs(f"{out_dir}/recon", exist_ok=True)
    os.makedirs(f"{out_dir}/discovery", exist_ok=True)
    os.makedirs(f"{out_dir}/vulns", exist_ok=True)
    os.makedirs(f"{out_dir}/reports", exist_ok=True)

    print(f"\n[*] Targets loaded: {len(targets)}")
    for t in targets:
        print(f"    {t}")

    start = time.time()

    for target in targets:
        print(f"\n\n{'#'*60}")
        print(f"  TARGET: {target}")
        print(f"{'#'*60}")

        if not args.skip_recon:
            phase_recon(target, cfg, out_dir)

        if not args.skip_discovery:
            phase_discovery(target, cfg, out_dir)

        if not args.skip_nuclei:
            phase_nuclei(target, cfg, out_dir)

        if not args.skip_burp:
            phase_burp(target, cfg, out_dir)

    # Generate report
    print("\n\n[*] Generating report...")
    subprocess.run(["python3", "scripts/report.py", out_dir, scope_file])

    elapsed = int(time.time() - start)
    print(f"\n[+] All phases complete in {elapsed//60}m {elapsed%60}s")
    print(f"[+] Results in: {out_dir}/")
    print(f"[+] Manual checklist: {out_dir}/reports/manual_checklist.md")


if __name__ == "__main__":
    main()
