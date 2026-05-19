#!/usr/bin/env python3
"""
Phase 4: Burp Suite Pro active scan via REST API.
Requires Burp Suite Pro with REST API enabled:
  Burp > Settings > Suite > REST API > Service running on port 1337
"""

import sys
import json
import time
import urllib.request
import urllib.error

def burp_scan(target_url: str, api_url: str, api_key: str, out_file: str) -> None:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Start scan
    payload = json.dumps({
        "urls": [target_url],
        "scan_configurations": [{"name": "Crawl and Audit - Balanced", "type": "NamedConfiguration"}],
    }).encode()

    req = urllib.request.Request(
        f"{api_url}/v0.1/scan",
        data=payload,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            location = resp.headers.get("Location", "")
            task_id = location.strip("/").split("/")[-1]
    except urllib.error.URLError as e:
        print(f"[-] Burp API unreachable ({api_url}): {e}. Skipping Burp scan.")
        print("    → Make sure Burp Suite Pro is open with REST API enabled.")
        return

    print(f"[*] Burp scan started: task {task_id} for {target_url}")

    # Poll until done
    while True:
        status_req = urllib.request.Request(
            f"{api_url}/v0.1/scan/{task_id}",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(status_req, timeout=10) as resp:
                data = json.loads(resp.read())
        except urllib.error.URLError:
            time.sleep(15)
            continue

        status = data.get("scan_status", "")
        issue_count = len(data.get("issue_events", []))
        print(f"    status={status}  issues_so_far={issue_count}", end="\r")

        if status in ("succeeded", "failed"):
            print()
            break
        time.sleep(15)

    # Save results
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    issues = data.get("issue_events", [])
    print(f"[+] Burp done: {len(issues)} issues — saved to {out_file}")
    for ev in issues:
        issue = ev.get("issue", {})
        sev = issue.get("severity", "?").upper()
        name = issue.get("name", "unknown")
        path = issue.get("path", "")
        print(f"    [{sev}] {name}  {path}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: burp_scan.py <target_url> <api_url> <api_key> <out_file>")
        sys.exit(1)
    burp_scan(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
