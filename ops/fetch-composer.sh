#!/usr/bin/env bash
# ops/fetch-composer.sh <dest>
#
# Fetch Cursor-Governance ops/scripts/compose_pr_body.py — the one PR-body
# renderer — at the commit .github/workflows/governance-pr.yml pins, into
# <dest>/ops/scripts/compose_pr_body.py. The pin is read from that workflow,
# so there is no second copy of it to drift. Used by ops/validate-starters.sh
# when SEED_COMPOSER_ROOT is unset; CI checks the same pin out with
# actions/checkout instead.
set -euo pipefail

dest="${1:?usage: ops/fetch-composer.sh <dest>}"
wf=".github/workflows/governance-pr.yml"
pin="$(sed -n 's/^ *COMPOSER: Quantum-L9\/Cursor-Governance@\([0-9a-f]\{40\}\) *$/\1/p' "$wf")"
if [ -z "$pin" ] || [ "$(printf '%s\n' "$pin" | wc -l)" -ne 1 ]; then
  echo "❌ $wf: expected exactly one 'COMPOSER: Quantum-L9/Cursor-Governance@<40-hex sha>' line" >&2
  exit 1
fi

target="$dest/ops/scripts/compose_pr_body.py"
if [ -f "$dest/.pin" ] && [ "$(cat "$dest/.pin")" = "$pin" ] && [ -f "$target" ]; then
  exit 0
fi

mkdir -p "$dest"
repo="$dest/.git-fetch"
if [ ! -d "$repo/.git" ]; then
  git init -q "$repo"
fi
git -C "$repo" fetch -q --depth=1 --filter=blob:none \
  https://github.com/Quantum-L9/Cursor-Governance.git "$pin"
mkdir -p "$(dirname "$target")"
git -C "$repo" show "$pin:ops/scripts/compose_pr_body.py" > "$target.tmp"
mv "$target.tmp" "$target"
printf '%s\n' "$pin" > "$dest/.pin"
