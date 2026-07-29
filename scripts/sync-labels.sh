#!/usr/bin/env bash
# Idempotent label sync from .github/labels.yml. Creates or updates; never deletes.
set -euo pipefail

REPO="${1:-}"
[[ -z "$REPO" ]] && { echo "usage: $0 owner/repo" >&2; exit 2; }
command -v gh >/dev/null || { echo "error: gh CLI required" >&2; exit 1; }

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$SRC/.github/labels.yml"

python3 - "$FILE" <<'PY' | while IFS=$'\t' read -r name color desc; do
import re, sys
for line in open(sys.argv[1]):
    m = re.search(r'name:\s*"([^"]+)".*color:\s*"([^"]+)".*description:\s*"([^"]*)"', line)
    if m:
        print("\t".join(m.groups()))
PY
  if gh label create "$name" --color "$color" --description "$desc" --repo "$REPO" 2>/dev/null; then
    echo "created  $name"
  else
    gh label edit "$name" --color "$color" --description "$desc" --repo "$REPO" >/dev/null
    echo "updated  $name"
  fi
done
