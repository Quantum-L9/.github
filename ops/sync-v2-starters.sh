#!/usr/bin/env bash
# ops/sync-v2-starters.sh
# Syncs the v2 CI instantiation surface from Quantum-L9/l9-ci-core into
# this repo's l9-ci-pack/, then rewrites every Core pin in l9-ci-pack/ +
# workflow-templates/l9-v2-*.yml to the given ref.
#
# Sources (both required at the Core ref):
#   docs/templates/              analysis + Python lint + governance YAMLs
#   presets/typescript/          locked Biome contract + Node lint caller
# Never copy the stale ESLint docs/templates/l9-lint-test-node.yml when the
# typescript preset is present — that is what made org fan-out invent ESLint.
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

echo "Fetching docs/templates/ and presets/typescript/ from ${CORE_REPO}@${CORE_REF}..."
git clone --quiet --no-checkout "https://github.com/${CORE_REPO}.git" "$WORKDIR/core"
git -C "$WORKDIR/core" fetch --quiet --depth=1 origin "$CORE_REF"
git -C "$WORKDIR/core" checkout --quiet FETCH_HEAD -- docs/templates presets/typescript

mkdir -p "$PACK_DIR/governance" "$PACK_DIR/workflows" "$PACK_DIR/.vscode"

for f in execution-profiles provider-requiredness rule-modes waivers promotion-policy quality-thresholds; do
  cp "$WORKDIR/core/docs/templates/governance/${f}.yaml" "$PACK_DIR/governance/${f}.yaml"
done

cp "$WORKDIR/core/docs/templates/l9-analysis.yml" "$PACK_DIR/workflows/l9-analysis.yml"

# A pack file marked L9_SEED_OWNED is maintained here, not upstream. Core's
# templates target a human who copies one into a repo and edits it; the pack
# copy is written unattended into ~45 repositories that never edit it, and it
# carries seed-safety hardening (stack detection, language-qualified job names,
# no unpinned plugin flags) that Core's audience does not need. Copying over it
# reverts that hardening silently, which is how the seeder went back to opening
# red PRs after each `make sync-core`.
sync_pack_file() {
  local src="$1" dest="$2"
  if [[ -f "$dest" ]] && grep -q 'L9_SEED_OWNED' "$dest"; then
    echo "⏭️  keeping seed-owned $dest (not synced from Core)"
    if ! diff -q "$src" "$dest" >/dev/null 2>&1; then
      echo "    Core's $(basename "$src") differs; review by hand if Core changed materially." >&2
    fi
    return 0
  fi
  cp "$src" "$dest"
}

sync_pack_file "$WORKDIR/core/docs/templates/l9-lint-test.yml" "$PACK_DIR/workflows/l9-lint-test.yml"

# Node/TS caller: prefer the locked typescript preset (Biome + tsc + tests).
# Fall back to docs/templates only if the preset is absent at this ref.
PRESET_NODE="$WORKDIR/core/presets/typescript/.github/workflows/l9-lint-test.yml"
TEMPLATE_NODE="$WORKDIR/core/docs/templates/l9-lint-test-node.yml"
if [[ -f "$PRESET_NODE" ]]; then
  cp "$PRESET_NODE" "$PACK_DIR/workflows/l9-lint-test-node.yml"
elif [[ -f "$TEMPLATE_NODE" ]]; then
  echo "⚠️  presets/typescript workflow missing at ${CORE_REF}; using docs/templates/l9-lint-test-node.yml" >&2
  cp "$TEMPLATE_NODE" "$PACK_DIR/workflows/l9-lint-test-node.yml"
else
  echo "❌ ERROR: no Node lint workflow at ${CORE_REF}" >&2
  exit 2
fi

if grep -qE 'npx --no-install eslint|name: ESLint' "$PACK_DIR/workflows/l9-lint-test-node.yml"; then
  echo "❌ ERROR: Node lint workflow at ${CORE_REF} is still the ESLint template." >&2
  echo "   Refusing to sync an ESLint caller into l9-ci-pack. Use a Core ref that" >&2
  echo "   contains presets/typescript (Biome) or docs/templates Biome content." >&2
  exit 2
fi

PRESET_DIR="$WORKDIR/core/presets/typescript"
if [[ ! -f "$PRESET_DIR/biome.json" ]]; then
  echo "❌ ERROR: presets/typescript/biome.json missing at ${CORE_REF}." >&2
  echo "   The org seeder cannot fan out a locked Biome contract from this ref." >&2
  exit 2
fi
cp "$PRESET_DIR/biome.json" "$PACK_DIR/biome.json"
cp "$PRESET_DIR/.biomeignore" "$PACK_DIR/.biomeignore"
cp "$PRESET_DIR/.editorconfig" "$PACK_DIR/.editorconfig"
cp "$PRESET_DIR/.vscode/extensions.json" "$PACK_DIR/.vscode/extensions.json"

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
  # Rewrite SHA pins and frozen Core tags (@v2 / @v2.0.0 / @v1) — never @main.
  # Keep install-consumer-ci@v2 floating so pin-file retags percolate.
  sed -i.bak -E "/install-consumer-ci@v2/!s#(Quantum-L9/l9-ci-core/[A-Za-z0-9._/-]+)@([0-9a-f]{40}|v[0-9]+(\.[0-9]+)*)#\1@${CORE_REF}#g" "$f"
  rm -f "${f}.bak"
done
# README uses "Pin Core at **`SHA`**" (bold+backticks); also accept legacy "pin Core at `SHA`".
sed -i.bak -E \
  -e "s#(Pin Core at \*\*\`)([0-9a-f]{40}|v[0-9]+(\.[0-9]+)*)(\`\*\*)#\1${CORE_REF}\4#g" \
  -e "s#(pin Core at \`)([0-9a-f]{40}|v[0-9]+(\.[0-9]+)*)(\`)#\1${CORE_REF}\4#gi" \
  "$PACK_DIR/README.md" 2>/dev/null || true
rm -f "$PACK_DIR/README.md.bak"

echo ""
echo "✅ Synced. Review the diff, then run ops/validate-starters.sh before committing:"
echo "   git diff --stat"
echo "   ops/validate-starters.sh"
