#!/usr/bin/env python3
"""Link extractor — pull URLs out of a web page, a file, or piped text.

Examples:
    # Extract every link from a web page
    python link_extractor.py https://example.com

    # Extract links from a local HTML or text file
    python link_extractor.py page.html

    # Pipe text in and grab any URLs it contains
    cat notes.txt | python link_extractor.py

    # Only show links from a specific domain
    python link_extractor.py https://example.com --filter example.com

Uses the Python standard library only, so there's nothing to install.
"""

import argparse
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

# Matches bare URLs sitting in plain text (e.g. inside notes or transcripts).
URL_RE = re.compile(r"https?://[^\s<>\"'()]+", re.IGNORECASE)

# Tags whose attributes commonly hold links, and which attribute to read.
LINK_ATTRS = {
    "a": "href",
    "link": "href",
    "area": "href",
    "img": "src",
    "script": "src",
    "iframe": "src",
    "source": "src",
    "video": "src",
    "audio": "src",
}


class LinkParser(HTMLParser):
    """Collect link-bearing attribute values from HTML, in document order."""

    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url
        self.links = []

    def handle_starttag(self, tag, attrs):
        attr_name = LINK_ATTRS.get(tag)
        if not attr_name:
            return
        for name, value in attrs:
            if name == attr_name and value:
                # Resolve relative URLs against the page they came from.
                self.links.append(urljoin(self.base_url, value.strip()))


def fetch(url):
    """Download a URL and return (text, final_url)."""
    request = Request(url, headers={"User-Agent": "link-extractor/1.0"})
    with urlopen(request, timeout=30) as response:
        final_url = response.geturl()
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
    return body, final_url


def read_source(source):
    """Return (text, base_url) from a URL, a file path, or stdin."""
    if source is None:
        return sys.stdin.read(), ""
    if re.match(r"^https?://", source, re.IGNORECASE):
        return fetch(source)
    with open(source, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(), ""


def extract_links(text, base_url=""):
    """Extract links from HTML markup and from bare URLs in plain text."""
    parser = LinkParser(base_url)
    parser.feed(text)
    links = list(parser.links)
    links.extend(URL_RE.findall(text))
    return links


def dedupe(items):
    """Drop duplicates while preserving first-seen order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract links from a web page, a file, or piped text."
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="URL or file path. Omit to read from stdin.",
    )
    parser.add_argument(
        "-f",
        "--filter",
        metavar="DOMAIN",
        help="Only show links whose host contains this substring.",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Keep duplicate links instead of removing them.",
    )
    args = parser.parse_args(argv)

    if args.source is None and sys.stdin.isatty():
        parser.error("no source given; pass a URL/file or pipe text via stdin")

    try:
        text, base_url = read_source(args.source)
    except OSError as error:
        print(f"error: could not read {args.source!r}: {error}", file=sys.stderr)
        return 1

    links = extract_links(text, base_url)

    if args.filter:
        needle = args.filter.lower()
        links = [u for u in links if needle in (urlparse(u).netloc.lower())]

    if not args.no_dedupe:
        links = dedupe(links)

    for link in links:
        print(link)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
