#!/usr/bin/env bash
#
# derive-persona.sh — turn a full name into candidate usernames + example emails.
#
# OSINT username/email tools (sherlock, maigret, holehe) don't take a full name;
# they take handles and addresses. This offline helper generates the common
# handle patterns an analyst would try, so the smoke test can enumerate them.
#
#   ./tests/derive-persona.sh "Ada Lovelace"
#   ./tests/derive-persona.sh --emails "Ada Lovelace"     # also print example emails
#
# Pure string manipulation — no network, targets nobody. Feed the output to the
# toolkit ONLY against fictional or authorized identities (see docs/opsec.md).

set -euo pipefail

EMAIL_DOMAIN="${EMAIL_DOMAIN:-example.com}"   # RFC 2606 reserved by default
WITH_EMAILS=0
[ "${1:-}" = "--emails" ] && { WITH_EMAILS=1; shift; }

FULLNAME="${*:-}"
if [ -z "${FULLNAME}" ]; then
  echo "usage: $0 [--emails] \"Full Name\"" >&2
  exit 2
fi

# Normalize a token: lowercase, keep only a-z0-9.
norm() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9'; }

# Split the name into normalized, non-empty tokens.
read -r -a raw <<< "${FULLNAME}"
tokens=()
for t in "${raw[@]}"; do
  n="$(norm "${t}")"
  [ -n "${n}" ] && tokens+=("${n}")
done

if [ "${#tokens[@]}" -eq 0 ]; then
  echo "No usable letters in name: ${FULLNAME}" >&2
  exit 2
fi

first="${tokens[0]}"
last="${tokens[$((${#tokens[@]} - 1))]}"
fi_="${first:0:1}"          # first initial
li_="${last:0:1}"           # last initial
# Leading initials = every token EXCEPT the last (so "ld" + "stone" -> "ldstone").
initials=""
for ((i = 0; i < ${#tokens[@]} - 1; i++)); do initials+="${tokens[i]:0:1}"; done
[ -z "${initials}" ] && initials="${fi_}"

# Candidate handle patterns (deduplicated, order preserved).
candidates=(
  "${first}${last}"          # adalovelace
  "${first}.${last}"         # ada.lovelace
  "${first}_${last}"         # ada_lovelace
  "${fi_}${last}"            # alovelace
  "${first}${li_}"          # adal
  "${last}${first}"          # lovelaceada
  "${last}${fi_}"           # lovelacea
  "${initials}${last}"       # (multi-token) alovelace / adlovelace
  "${first}"                 # ada
)

# Join tokens with no separator too (handles 3-part names): adalovelace already
# covered when 2 tokens; add the full concatenation for 3+.
if [ "${#tokens[@]}" -ge 3 ]; then
  all=""; for t in "${tokens[@]}"; do all+="${t}"; done
  candidates+=("${all}")     # adamiddlelovelace
fi

# Deduplicate while preserving order.
seen=" "
usernames=()
for c in "${candidates[@]}"; do
  [ -z "${c}" ] && continue
  case "${seen}" in *" ${c} "*) continue;; esac
  seen+="${c} "
  usernames+=("${c}")
done

# Emit usernames one per line (parsed by the smoke test).
for u in "${usernames[@]}"; do
  echo "${u}"
done

# Optionally emit a few example emails on the reserved domain.
if [ "${WITH_EMAILS}" -eq 1 ]; then
  for local_part in "${first}.${last}" "${fi_}${last}" "${first}${last}"; do
    echo "email:${local_part}@${EMAIL_DOMAIN}"
  done
fi
