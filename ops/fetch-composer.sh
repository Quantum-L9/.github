#!/usr/bin/env bash
# ops/fetch-composer.sh <dest>
#
# Fetch Cursor-Governance ops/scripts/compose_pr_body.py — the one PR-body
# renderer — and the module it imports (org_dotgithub.py) at the commit
# .github/workflows/governance-pr.yml pins, into <dest>/ops/scripts/. The pin is read from that workflow,
# so there is no second copy of it to drift. Used by ops/validate-starters.sh
# when SEED_COMPOSER_ROOT is unset. A pull-request check does not run this
# script: .github/workflows/validate-starters-composer.yml checks the same
# pin out from the default branch. When L9_GITHUB_READ_TOKEN is set, git
# receives it as an Authorization header through GIT_CONFIG_*, never in
# argv or the remote URL. Unset, the fetch stays anonymous and a private
# repository fails closed.
set -euo pipefail

dest="${1:?usage: ops/fetch-composer.sh <dest>}"
wf=".github/workflows/governance-pr.yml"
pin="$(sed -n 's/^ *COMPOSER: Quantum-L9\/Cursor-Governance@\([0-9a-f]\{40\}\) *$/\1/p' "$wf")"
if [[ -z "$pin" || "$(printf '%s\n' "$pin" | wc -l)" -ne 1 ]]; then
  echo "❌ $wf: expected exactly one 'COMPOSER: Quantum-L9/Cursor-Governance@<40-hex sha>' line" >&2
  exit 1
fi

# compose_pr_body.py imports org_dotgithub at load; both are stdlib-only.
files=(ops/scripts/compose_pr_body.py ops/scripts/org_dotgithub.py)
fresh=1
for f in "${files[@]}"; do [[ -f "$dest/$f" ]] || fresh=0; done
if [[ "$fresh" = 1 && -f "$dest/.pin" && "$(cat "$dest/.pin")" = "$pin" ]]; then
  exit 0
fi

mkdir -p "$dest"
repo="$dest/.git-fetch"
if [[ ! -d "$repo/.git" ]]; then
  git init -q "$repo"
fi
token="${L9_GITHUB_READ_TOKEN:-}"
unset L9_GITHUB_READ_TOKEN
export GIT_TERMINAL_PROMPT=0
if [[ -n "$token" ]]; then
  basic="$(printf 'x-access-token:%s' "$token" | base64 | tr -d '\n')"
  unset token
  count="${GIT_CONFIG_COUNT:-0}"
  export "GIT_CONFIG_KEY_${count}=http.https://github.com/.extraheader"
  export "GIT_CONFIG_VALUE_${count}=AUTHORIZATION: basic ${basic}"
  export GIT_CONFIG_COUNT="$((count + 1))"
  unset basic
fi
git -C "$repo" fetch -q --depth=1 --filter=blob:none \
  https://github.com/Quantum-L9/Cursor-Governance.git "$pin"
for f in "${files[@]}"; do
  mkdir -p "$(dirname "$dest/$f")"
  git -C "$repo" show "$pin:$f" > "$dest/$f.tmp"
  mv "$dest/$f.tmp" "$dest/$f"
done
printf '%s\n' "$pin" > "$dest/.pin"
