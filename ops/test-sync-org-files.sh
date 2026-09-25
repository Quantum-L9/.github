#!/usr/bin/env bash
# ops/test-sync-org-files.sh
# Regression tests for the shell seed path (ops/sync-org-files.sh), a plan
# adapter over ops/compile-repo-governance.js. The Actions
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

# ── 3. a consumer with no identity is refused, never given an invented one ────
# The sync applies a governance plan, and a plan names its target
# (AC-ADV-010). Before the compiler, a remote-less consumer got a verbatim copy
# whose advisory links pointed at Quantum-L9/.github; now it must say who it is.
NO_REMOTE="$WORK/no-remote"
mkdir -p "$NO_REMOTE"
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NO_REMOTE" --include community-health) > /dev/null 2>&1; then
  fail "consumer with no remote and no --repo was synced under an invented identity"
fi
[[ ! -f "$NO_REMOTE/SECURITY.md" ]] || fail "refused sync still wrote files"
(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NO_REMOTE" --repo Quantum-L9/named --include community-health) > /dev/null
grep -q 'https://github.com/Quantum-L9/named/security/advisories/new' "$NO_REMOTE/SECURITY.md" || \
  fail "--repo identity not applied to advisory links"
echo "✅ no-remote consumer is refused without --repo and syncs with it"

# ── 4. missing-only: an existing consumer file is never overwritten ───────────
KEEP="$WORK/keep"
make_consumer "$KEEP"
printf 'consumer-owned security policy\n' > "$KEEP/SECURITY.md"
(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$KEEP" --include community-health) > /dev/null
grep -qx 'consumer-owned security policy' "$KEEP/SECURITY.md" || fail "existing SECURITY.md was overwritten"
[[ -f "$KEEP/CONTRIBUTING.md" ]] || fail "missing CONTRIBUTING.md not written"
echo "✅ existing files kept; only missing files written (plan write mode missing_only)"

# ── 5. the consumer's class governs; a filter can only narrow it ──────────────
CLASSED="$WORK/classed"
make_consumer "$CLASSED"
mkdir -p "$CLASSED/.l9"
printf 'profile: non_constellation_python\n' > "$CLASSED/.l9/org-birth-profile.yaml"
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$CLASSED" --include governance) > /dev/null 2>&1; then
  fail "a category the class does not authorize was synced"
fi
[[ ! -f "$CLASSED/.github/workflows/governance.yml" ]] || fail "refused category still wrote a file"
(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$CLASSED") > /dev/null
[[ -f "$CLASSED/.github/labels.yml" ]] || fail "class plan (labels MATERIALIZE) not applied"
[[ ! -f "$CLASSED/CODE_OF_CONDUCT.md" ]] || fail "an INHERIT path was copied into the consumer"
[[ ! -f "$CLASSED/.github/workflows/governance.yml" ]] || fail "a FORBID path was written"
echo "✅ class plan applied: unauthorized category refused, INHERIT not copied, FORBID not written"

# ── 6. retired CI categories and malformed markers fail closed ────────────────
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$KEEP" --include l9-ci-pack) > /dev/null 2>&1; then
  fail "retired l9-ci-pack category did not fail closed"
fi
BAD="$WORK/bad-marker"
make_consumer "$BAD"
mkdir -p "$BAD/.l9"
printf 'profile: totally_made_up\n' > "$BAD/.l9/org-birth-profile.yaml"
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$BAD") > /dev/null 2>&1; then
  fail "unknown marker class was synced (must never fall back to default)"
fi
[[ -z "$(find "$BAD" -type f -not -path '*/.git/*' -not -path '*/.l9/*')" ]] || fail "malformed-marker sync wrote files"
echo "✅ retired category and unknown marker class fail closed with zero writes"

echo "ok: shell sync applies the compiled plan: identity, missing-only, class, fail-closed"
