#!/usr/bin/env bash
# ops/test-sync-org-files.sh
# Regression tests for the shell seed path (ops/sync-org-files.sh). The Actions
# seeder (ops/build-seed-payload.js) applies repository placeholders and skips
# .github/CODEOWNERS when a root CODEOWNERS exists; this asserts the documented
# shell path does the same, so a manually synced consumer is not seeded with
# advisory links pointing at Quantum-L9/.github or with its root ownership
# rules suppressed.
# Run from the root of the Quantum-L9/.github repo:
#   bash ops/test-sync-org-files.sh
set -euo pipefail

ORG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CATEGORIES=(--include codeowners community-health issue-templates)

make_consumer() {
  local dir="$1"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" remote add origin "https://github.com/Quantum-L9/example.git"
}

fail() {
  echo "❌ $1" >&2
  exit 1
}

# ── 1. consumer WITH a root CODEOWNERS ────────────────────────────────────────
WITH_ROOT="$WORK/with-root"
make_consumer "$WITH_ROOT"
printf '* @Quantum-L9/example-owners\n' > "$WITH_ROOT/CODEOWNERS"

(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$WITH_ROOT" "${CATEGORIES[@]}") > /dev/null

if [[ -f "$WITH_ROOT/.github/CODEOWNERS" ]]; then
  fail "root CODEOWNERS was overridden by .github/CODEOWNERS"
fi
grep -q '@Quantum-L9/example-owners' "$WITH_ROOT/CODEOWNERS" || \
  fail "root CODEOWNERS was modified"
echo "✅ root CODEOWNERS preserved (no .github/CODEOWNERS written)"

grep -q 'https://github.com/Quantum-L9/example/security/advisories/new' \
  "$WITH_ROOT/SECURITY.md" || fail "SECURITY.md advisory link not rewritten"
if grep -q 'https://github.com/Quantum-L9/.github/security/advisories/new' \
  "$WITH_ROOT/SECURITY.md"; then
  fail "SECURITY.md still points at Quantum-L9/.github"
fi
echo "✅ SECURITY.md advisory link rewritten to the consumer"

CFG="$WITH_ROOT/.github/ISSUE_TEMPLATE/config.yml"
[[ -f "$CFG" ]] || fail "issue-template config.yml not synced"
grep -q 'https://github.com/Quantum-L9/example/security/advisories/new' "$CFG" || \
  fail "config.yml advisory link not rewritten"
if grep -q 'https://github.com/Quantum-L9/.github/security/advisories/new' "$CFG"; then
  fail "config.yml still points at Quantum-L9/.github"
fi
echo "✅ issue-template config.yml advisory link rewritten to the consumer"

# ── 2. consumer WITHOUT a root CODEOWNERS ─────────────────────────────────────
NO_ROOT="$WORK/no-root"
make_consumer "$NO_ROOT"

(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NO_ROOT" --include codeowners) > /dev/null

[[ -f "$NO_ROOT/.github/CODEOWNERS" ]] || \
  fail ".github/CODEOWNERS not seeded when no root CODEOWNERS exists"
echo "✅ .github/CODEOWNERS still seeded when the consumer has no root file"

# ── 3. consumer with no git remote falls back to a verbatim copy ──────────────
NO_REMOTE="$WORK/no-remote"
mkdir -p "$NO_REMOTE"
(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NO_REMOTE" --include community-health) > /dev/null
[[ -f "$NO_REMOTE/SECURITY.md" ]] || fail "SECURITY.md not synced without a remote"
echo "✅ no-remote consumer still syncs (verbatim, no invented repository)"

echo "ok: shell seeder preserves root CODEOWNERS and rewrites advisory links"
