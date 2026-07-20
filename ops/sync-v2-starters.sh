#!/usr/bin/env bash
# ops/sync-v2-starters.sh
# Syncs the v2 CI instantiation surface from Quantum-L9/l9-ci-core's
# docs/templates/ into this repo's l9-ci-pack/, then rewrites every Core pin
# in l9-ci-pack/ + workflow-templates/l9-v2-*.yml to the given ref.
#
# Usage:
#   ops/sync-v2-starters.sh <core-ref>
#
#   <core-ref>  Full 40-char commit SHA (pre-release candidate) or a Core
#               release tag (e.g. v2.0.0) once cut. Never `main`.
#
# Run from the root of the Quantum-L9/.github repo, with a clean working tree.
set -euo pipefail

CORE_REPO="Quantum-L9/l9-ci-core"
CORE_REF="${1:-}"
PACK_DIR="l9-ci-pack"

if [[ -z "$CORE_REF" ]]; then
  echo "❌ ERROR: usage: $0 <core-ref>" >&2
  echo "   <core-ref> must be a full 40-char commit SHA or a release tag (e.g. v2.0.0)." >&2
  exit 1
fi

if [[ "$CORE_REF" == "main" ]]; then
  echo "❌ ERROR: refusing to sync against a floating ref (main)." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ ERROR: working tree is not clean. Commit or stash changes first." >&2
  git status --short
  exit 1
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "=== Syncing l9-ci-pack from ${CORE_REPO}@${CORE_REF} ==="

echo "Fetching docs/templates/ from ${CORE_REPO}@${CORE_REF}..."
git clone --quiet --no-checkout "https://github.com/${CORE_REPO}.git" "$WORKDIR/core"
git -C "$WORKDIR/core" fetch --quiet --depth=1 origin "$CORE_REF"
git -C "$WORKDIR/core" checkout --quiet FETCH_HEAD -- docs/templates

mkdir -p "$PACK_DIR/governance" "$PACK_DIR/workflows"

for f in execution-profiles provider-requiredness rule-modes waivers promotion-policy quality-thresholds; do
  cp "$WORKDIR/core/docs/templates/governance/${f}.yaml" "$PACK_DIR/governance/${f}.yaml"
done

for f in l9-analysis l9-lint-test l9-lint-test-node; do
  cp "$WORKDIR/core/docs/templates/${f}.yml" "$PACK_DIR/workflows/${f}.yml"
done

echo "Rewriting Core pins to @${CORE_REF} in ${PACK_DIR}/ and workflow-templates/l9-v2-*.yml..."
# Matches full-40-char-SHA pins on Quantum-L9/l9-ci-core refs only — never
# touches @v1 legacy starter pins (different repo path pattern is not present
# in these files) and never introduces a floating ref.
FILES_TO_REPIN=("$PACK_DIR"/workflows/*.yml)
if compgen -G "workflow-templates/l9-v2-*.yml" >/dev/null; then
  FILES_TO_REPIN+=(workflow-templates/l9-v2-*.yml)
fi
for f in "${FILES_TO_REPIN[@]}"; do
  [[ -f "$f" ]] || continue
  sed -i.bak -E "s#(Quantum-L9/l9-ci-core/[A-Za-z0-9._/-]+)@[0-9a-f]{40}#\\1@${CORE_REF}#g" "$f"
  rm -f "${f}.bak"
done
sed -i.bak -E "s#(pin Core at \`)[0-9a-f]{40}(\`)#\\1${CORE_REF}\\2#gi" "$PACK_DIR/README.md" 2>/dev/null || true
rm -f "$PACK_DIR/README.md.bak"

echo ""
echo "✅ Synced. Review the diff, then run ops/validate-starters.sh before committing:"
echo "   git diff --stat"
echo "   ops/validate-starters.sh"
