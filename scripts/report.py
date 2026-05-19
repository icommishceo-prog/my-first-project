#!/usr/bin/env python3
"""
Aggregate all tool output into a markdown summary + manual testing checklist.
"""

import json
import os
import glob
import sys
from datetime import datetime


def load_nuclei_findings(vuln_dir: str) -> list[dict]:
    findings = []
    for jf in glob.glob(f"{vuln_dir}/*_nuclei.json"):
        try:
            with open(jf) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        findings.append(json.loads(line))
        except Exception:
            pass
    return findings


def load_burp_findings(vuln_dir: str) -> list[dict]:
    findings = []
    for jf in glob.glob(f"{vuln_dir}/*_burp.json"):
        try:
            with open(jf) as f:
                data = json.load(f)
            for ev in data.get("issue_events", []):
                findings.append(ev.get("issue", {}))
        except Exception:
            pass
    return findings


def load_discovered_urls(disc_dir: str) -> list[str]:
    urls = []
    for uf in glob.glob(f"{disc_dir}/**/discovered_urls.txt", recursive=True):
        try:
            with open(uf) as f:
                urls.extend(l.strip() for l in f if l.strip())
        except Exception:
            pass
    return list(set(urls))


def severity_order(s: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(s.lower(), 5)


def generate_report(output_dir: str, scope_file: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    targets = []
    try:
        with open(scope_file) as f:
            targets = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    except Exception:
        pass

    nuclei = load_nuclei_findings(f"{output_dir}/vulns")
    burp = load_burp_findings(f"{output_dir}/vulns")
    disc_urls = load_discovered_urls(f"{output_dir}/discovery")

    nuclei_sorted = sorted(nuclei, key=lambda x: severity_order(x.get("info", {}).get("severity", "info")))

    lines = [
        f"# Bug Bounty Automated Scan Report",
        f"**Generated:** {now}  ",
        f"**Targets:** {len(targets)}  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Source | Findings |",
        f"|--------|----------|",
        f"| Nuclei | {len(nuclei)} |",
        f"| Burp Suite | {len(burp)} |",
        f"| Discovered URLs | {len(disc_urls)} |",
        "",
        "---",
        "",
        "## Nuclei Findings",
        "",
    ]

    if nuclei_sorted:
        lines += ["| Severity | Template | Host | Info |", "|----------|----------|------|------|"]
        for f in nuclei_sorted:
            info = f.get("info", {})
            sev = info.get("severity", "info").upper()
            name = info.get("name", f.get("template-id", "?"))
            host = f.get("host", f.get("url", "?"))
            matched = f.get("matched-at", "")
            lines.append(f"| **{sev}** | {name} | {host} | {matched} |")
    else:
        lines.append("_No nuclei findings._")

    lines += ["", "---", "", "## Burp Suite Findings", ""]
    if burp:
        lines += ["| Severity | Issue | Path |", "|----------|-------|------|"]
        for f in sorted(burp, key=lambda x: severity_order(x.get("severity", "info"))):
            sev = f.get("severity", "?").upper()
            name = f.get("name", "?")
            path = f.get("path", "")
            lines.append(f"| **{sev}** | {name} | {path} |")
    else:
        lines.append("_No Burp findings (or Burp was not run)._")

    lines += [
        "",
        "---",
        "",
        "## Discovered URLs (top 50)",
        "",
        "```",
    ]
    lines += disc_urls[:50]
    lines += ["```", "", "---", ""]

    # Manual checklist — things automation cannot reliably test
    lines += [
        "## Manual Testing Checklist",
        "",
        "These require human judgment — automation skipped or is unreliable for them.",
        "",
        "### Authentication & Session",
        "- [ ] Password reset flow — token expiry, reuse, predictability",
        "- [ ] Account takeover via email change without confirmation",
        "- [ ] MFA bypass — code reuse, null/empty OTP, brute-force rate limits",
        "- [ ] Session fixation after login",
        "- [ ] Remember-me token scope and expiry",
        "- [ ] Logout invalidates server-side session",
        "",
        "### Authorization",
        "- [ ] IDOR — swap user/resource IDs across accounts",
        "- [ ] Horizontal privilege escalation (user A accessing user B data)",
        "- [ ] Vertical privilege escalation (user → admin endpoints)",
        "- [ ] Mass assignment — extra fields in POST/PUT requests",
        "- [ ] API versioning — older /v1/ endpoints with looser auth",
        "",
        "### Business Logic",
        "- [ ] Negative quantities, zero-price, or free items in checkout flow",
        "- [ ] Coupon/promo code stacking or reuse",
        "- [ ] Race conditions — concurrent requests on balance/points/voting",
        "- [ ] Workflow skip — jump steps in multi-step process",
        "- [ ] Import/export abuse — CSV injection, oversized payloads",
        "",
        "### Injection (context-specific)",
        "- [ ] Second-order SQLi — injected data rendered later",
        "- [ ] Stored XSS in low-traffic areas (admin panels, notifications)",
        "- [ ] Template injection in user-controlled fields rendered server-side",
        "- [ ] SSTI in error messages, emails, PDF generation",
        "",
        "### File Handling",
        "- [ ] Upload bypass — content-type spoofing, polyglot files",
        "- [ ] Path traversal in file download parameters",
        "- [ ] SVG XSS via file upload",
        "- [ ] XXE via XML/docx/xlsx upload",
        "",
        "### API-Specific",
        "- [ ] GraphQL introspection enabled in production",
        "- [ ] GraphQL batching attacks / query depth abuse",
        "- [ ] Undocumented or internal API endpoints (check JS bundles)",
        "- [ ] Insecure Direct Object Reference in API responses (extra fields)",
        "",
        "### Misc",
        "- [ ] SSRF via webhooks, URL preview, PDF generation, integrations",
        "- [ ] OAuth flow — state parameter missing, redirect_uri bypass",
        "- [ ] Subdomain takeover candidates (check CNAME to dangling services)",
        "- [ ] Email-based attacks — SPF/DKIM/DMARC, email header injection",
        "- [ ] Browser cache — sensitive pages cached with no-cache headers missing",
        "",
    ]

    report = "\n".join(lines)
    out_path = f"{output_dir}/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs(f"{output_dir}/reports", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(report)

    # Also write the manual checklist standalone
    checklist_path = f"{output_dir}/reports/manual_checklist.md"
    checklist_start = report.index("## Manual Testing Checklist")
    with open(checklist_path, "w") as f:
        f.write(report[checklist_start:])

    return out_path


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    scope_file = sys.argv[2] if len(sys.argv) > 2 else "config/scope.txt"
    path = generate_report(output_dir, scope_file)
    print(f"[+] Report written to {path}")
