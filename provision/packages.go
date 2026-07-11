# Go-based OSINT tools, installed with `go install` (only if Go is present).
# Format: <module-path>@<version>   # optional comment
# Lines starting with '#' and blank lines are ignored.
#
# amass is OWASP's attack-surface mapper. It is NOT in Debian main and is
# distributed as a Go module (or via snap). The provisioner installs these only
# when a Go toolchain is available; otherwise it prints a note and skips them.

github.com/owasp-amass/amass/v4/...@master         # OWASP Amass (provides `amass`)
github.com/sundowndev/phoneinfoga/v2@latest        # PhoneInfoga (provides `phoneinfoga`)

