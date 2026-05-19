# Wordlists

`api_paths.txt` is included. For `common.txt`, use a standard list:

```bash
# Option 1 — SecLists (recommended)
wget https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt \
  -O wordlists/common.txt

# Option 2 — dirb built-in (already on most systems)
cp /usr/share/dirb/wordlists/common.txt wordlists/common.txt

# Option 3 — if SecLists is installed
cp /usr/share/seclists/Discovery/Web-Content/common.txt wordlists/common.txt
```
