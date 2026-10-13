#!/usr/bin/env bash
# ops/test-sync-org-files.sh
# Regression tests for the shell seed path (ops/sync-org-files.sh). The shell
# entrypoint delegates to ops/build-seed-payload.js (planConsumerSeed), so a
# manually synced consumer gets the same decisions as the Actions seeders:
# repo class (marker > override > default, malformed fails closed), FORBID
# refused, INHERIT dropped, MATERIALIZE missing-only, advisory links rewritten
# to the consumer, root CODEOWNERS left authoritative.
# Run from the root of the Quantum-L9/.github repo:
#   bash ops/test-sync-org-files.sh
set -euo pipefail

ORG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

CATEGORIES=(--include codeowners community-health issue-templates pr-templates)

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

# community-health copies SECURITY.md alone. The passive surfaces are INHERIT
# (GitHub serves them org-wide) and a copy would create a second owner.
for f in CODE_OF_CONDUCT.md CONTRIBUTING.md SUPPORT.md LICENSE .github/FUNDING.yml .github/VULNERABILITY_REPORT.yml; do
  if [[ -e "$WITH_ROOT/$f" ]]; then
    fail "community-health copied INHERIT surface $f"
  fi
done
echo "✅ community-health copies only SECURITY.md (CoC/CONTRIBUTING/SUPPORT inherited)"

[[ -f "$WITH_ROOT/.github/pull_request_template.md" ]] || \
  fail "pr-templates did not copy .github/pull_request_template.md"
[[ -f "$WITH_ROOT/.github/PULL_REQUEST_TEMPLATE/release.md" ]] || \
  fail "pr-templates did not copy .github/PULL_REQUEST_TEMPLATE/release.md"
if [[ -e "$WITH_ROOT/.github/PULL_REQUEST_TEMPLATE/infra.md" ]]; then
  fail "pr-templates copied the deleted infra.md"
fi
echo "✅ pr-templates copies the default + release templates and never infra.md"

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

# ── 4. MATERIALIZE is missing-only: a second run keeps consumer bytes ─────────
# Customize the three consumer-owned files the first run wrote, re-run the
# same categories, and prove every byte survived and the tool said "kept".
for f in SECURITY.md .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE/release.md; do
  printf '# consumer-owned %s\nlocal edit\n' "$f" > "$WITH_ROOT/$f"
done
BEFORE="$(cd "$WITH_ROOT" && find . -type f -not -path './.git/*' -print0 | sort -z | xargs -0 sha256sum)"
RERUN="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$WITH_ROOT" "${CATEGORIES[@]}")"
AFTER="$(cd "$WITH_ROOT" && find . -type f -not -path './.git/*' -print0 | sort -z | xargs -0 sha256sum)"
[[ "$BEFORE" == "$AFTER" ]] || fail "second sync changed consumer files:
$(diff <(printf '%s\n' "$BEFORE") <(printf '%s\n' "$AFTER") || true)"
grep -q 'consumer-owned SECURITY.md' "$WITH_ROOT/SECURITY.md" || fail "SECURITY.md was overwritten"
grep -q 'consumer-owned .github/pull_request_template.md' "$WITH_ROOT/.github/pull_request_template.md" || \
  fail "pull_request_template.md was overwritten"
grep -q 'consumer-owned .github/PULL_REQUEST_TEMPLATE/release.md' "$WITH_ROOT/.github/PULL_REQUEST_TEMPLATE/release.md" || \
  fail "release.md was overwritten"
grep -q '@Quantum-L9/example-owners' "$WITH_ROOT/CODEOWNERS" || \
  fail "root CODEOWNERS changed on re-run"
for f in SECURITY.md .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE/release.md .github/ISSUE_TEMPLATE/config.yml; do
  grep -q "= $f (exists; kept)" <<< "$RERUN" || fail "re-run did not report $f as kept"
done
echo "✅ second sync is byte-identical; existing files reported as kept"

# ── 5. repo class decides: non_constellation_python ──────────────────────────
NCP="$WORK/ncp"
make_consumer "$NCP"
mkdir -p "$NCP/.l9"
printf 'schema: l9.org-birth-profile-marker/v1\nprofile: non_constellation_python\n' \
  > "$NCP/.l9/org-birth-profile.yaml"
NCP_OUT="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NCP" --include-all)"
grep -q 'class: non_constellation_python (marker)' <<< "$NCP_OUT" || fail "ncp class not reported"
for f in .github/CODEOWNERS .github/dependabot.yml .github/labels.yml SECURITY.md; do
  [[ -f "$NCP/$f" ]] || fail "ncp did not receive $f"
done
for f in .github/workflows/governance.yml .github/workflows/l9-analysis.yml .github/workflows/l9-lint-test.yml \
         .github/workflows/on-org-update.yml CODE_OF_CONDUCT.md CONTRIBUTING.md SUPPORT.md \
         .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE/release.md .github/ISSUE_TEMPLATE/config.yml; do
  [[ -e "$NCP/$f" ]] && fail "ncp received forbidden or inherited $f"
done
[[ -d "$NCP/.github/workflows" ]] && fail "ncp received a workflows directory"
grep -q 'https://github.com/Quantum-L9/example/security/advisories/new' "$NCP/SECURITY.md" || \
  fail "ncp SECURITY.md advisory link not rewritten"
echo "✅ non_constellation_python gets exactly CODEOWNERS, dependabot, labels, SECURITY.md — no CI, no inherited files"

# An explicit category the class forbids is refused, with nothing written.
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NCP" --include governance) > "$WORK/forbid.out" 2>&1; then
  fail "explicit forbidden category was accepted"
fi
grep -q 'violates repo class non_constellation_python' "$WORK/forbid.out" || \
  fail "forbidden category refusal did not name the class"
grep -q 'governance.yml' "$WORK/forbid.out" || fail "forbidden category refusal did not name the path"
[[ -e "$NCP/.github/workflows/governance.yml" ]] && fail "forbidden governance.yml was written"
echo "✅ explicit forbidden category is refused with class and path named; nothing written"

# An explicit category the class inherits drops: only SECURITY.md remains.
NCP2="$WORK/ncp2"
make_consumer "$NCP2"
mkdir -p "$NCP2/.l9"
cp "$NCP/.l9/org-birth-profile.yaml" "$NCP2/.l9/"
NCP2_OUT="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$NCP2" --include community-health pr-templates issue-templates)"
grep -q '~ .github/pull_request_template.md (inherited' <<< "$NCP2_OUT" || fail "inherited PR template not reported"
[[ -f "$NCP2/SECURITY.md" ]] || fail "ncp explicit community-health did not write SECURITY.md"
[[ -e "$NCP2/.github/pull_request_template.md" ]] && fail "ncp copied an inherited PR template"
[[ -e "$NCP2/.github/ISSUE_TEMPLATE" ]] && fail "ncp copied inherited issue templates"
echo "✅ explicit inherited categories drop for non_constellation_python; only SECURITY.md written"

# ── 6. self_governed materializes nothing ────────────────────────────────────
SG="$WORK/self-governed"
make_consumer "$SG"
mkdir -p "$SG/.l9"
printf 'profile: self_governed\n' > "$SG/.l9/org-birth-profile.yaml"
SG_OUT="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$SG" --include-all)"
grep -q 'class: self_governed (marker)' <<< "$SG_OUT" || fail "self_governed class not reported"
SG_FILES="$(cd "$SG" && find . -type f -not -path './.git/*' -not -path './.l9/*')"
[[ -z "$SG_FILES" ]] || fail "self_governed received files:
$SG_FILES"
echo "✅ self_governed receives zero files"

# ── 7. a malformed explicit marker fails closed ───────────────────────────────
BAD="$WORK/bad-marker"
make_consumer "$BAD"
mkdir -p "$BAD/.l9"
printf 'profile: non_constelation_python\n' > "$BAD/.l9/org-birth-profile.yaml"
if (cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$BAD" --include-all) > "$WORK/bad.out" 2>&1; then
  fail "malformed marker was seeded"
fi
grep -q 'unknown class non_constelation_python' "$WORK/bad.out" || fail "malformed marker refusal did not name the class"
BAD_FILES="$(cd "$BAD" && find . -type f -not -path './.git/*' -not -path './.l9/*')"
[[ -z "$BAD_FILES" ]] || fail "malformed marker consumer received files"
echo "✅ malformed explicit marker is refused; nothing written (never widened to default)"

# ── 8. an org override classifies a repo with no marker ──────────────────────
OVR="$WORK/l9-ci-core"
mkdir -p "$OVR"
git -C "$OVR" init -q
git -C "$OVR" remote add origin "https://github.com/Quantum-L9/l9-ci-core.git"
OVR_OUT="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$OVR" --include-all)"
grep -q 'class: self_governed (org override)' <<< "$OVR_OUT" || fail "org override not applied to l9-ci-core"
OVR_FILES="$(cd "$OVR" && find . -type f -not -path './.git/*')"
[[ -z "$OVR_FILES" ]] || fail "override-classified repo received files"
echo "✅ org override classifies an unmarked repo; self_governed override writes nothing"

# ── 9. dry run writes nothing ─────────────────────────────────────────────────
DRY="$WORK/dry"
make_consumer "$DRY"
DRY_OUT="$(cd "$ORG_ROOT" && bash ops/sync-org-files.sh "$DRY" --dry-run)"
grep -q '+ SECURITY.md (would write)' <<< "$DRY_OUT" || fail "dry run did not preview SECURITY.md"
DRY_FILES="$(cd "$DRY" && find . -type f -not -path './.git/*')"
[[ -z "$DRY_FILES" ]] || fail "dry run wrote files"
echo "✅ dry run previews the class payload and writes nothing"

echo "ok: shell seeder is class-bound (marker > override > default, FORBID refuses, INHERIT drops, malformed fails closed), missing-only, rewrites advisory links, preserves root CODEOWNERS"
