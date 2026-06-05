# my-first-project

A small, dependency-free **link extractor**. It pulls URLs out of a web page,
a local file, or piped text using only the Python standard library — nothing to
install.

## Usage

```bash
# Extract every link from a web page
python3 link_extractor.py https://example.com

# Extract links from a local HTML or text file
python3 link_extractor.py page.html

# Pipe text in and grab any URLs it contains
cat notes.txt | python3 link_extractor.py

# Only show links from a specific domain
python3 link_extractor.py https://example.com --filter example.com

# Keep duplicate links instead of removing them
python3 link_extractor.py https://example.com --no-dedupe
```

## What it does

- Parses HTML and reads link-bearing attributes from `<a>`, `<link>`, `<img>`,
  `<script>`, `<iframe>`, `<video>`, `<audio>`, and more.
- Also catches bare `http(s)://` URLs sitting in plain text.
- Resolves relative links (e.g. `/about`) against the page they came from.
- Removes duplicates by default while preserving order.

Requires Python 3.6+.
