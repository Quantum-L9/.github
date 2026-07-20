#!/usr/bin/env bash
# ops/verify-v1-anchor.sh
#
# Lightweight, read-only pre-tag check: re-confirms zero floating (non-SHA)
# third-party GitHub Action references in the workflow_call kernels at the
# EXPECTED_SHA anchor that ops/tag-v1.sh is about to freeze as v1.0.0 / v1
# on Quantum-L9/l9-ci-core.
#
# Run this BEFORE ops/tag-v1.sh, every time, even if EXPECTED_SHA "hasn't
# changed" — it costs seconds and is the only thing standing between an
# "immutable" tag and permanently frozen floating-tag supply-chain risk.
#
# This script does not tag, push, or mutate any repository. It only fetches
# the single anchor commit (read-only) from Quantum-L9/l9-ci-core into a
# throwaway temp directory and inspects file contents at that commit.
#
# Scope: only the workflow_call kernels (the reusable workflows consumers
# actually import via @v1 / @v1.0.0) are checked. l9-self-ci.yml is
# deliberately excluded — it is a self-triggering, repo-internal gate with
# no workflow_call trigger, so it is never exposed to downstream consumers
# and its (pre-existing, unrelated) floating refs do not carry consumer
# supply-chain risk. See AGENTS.md-equivalent note in tag-v1.sh.
#
# Usage: ops/verify-v1-anchor.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAG_SCRIPT="$SCRIPT_DIR/tag-v1.sh"
SOURCE_REPO="https://github.com/Quantum-L9/l9-ci-core.git"

echo "=== v1 anchor verification (read-only) ==="
echo ""

# 1. Read EXPECTED_SHA out of tag-v1.sh so the two scripts can never drift
#    into disagreement about which commit is being tagged.
if [[ ! -f "$TAG_SCRIPT" ]]; then
  echo "❌ ERROR: $TAG_SCRIPT not found (run this script from the ops/ dir, or keep both scripts together)."
  exit 1
fi

EXPECTED_SHA=$(grep -m1 '^EXPECTED_SHA=' "$TAG_SCRIPT" | sed -E 's/^EXPECTED_SHA="([0-9a-f]{40})"$/\1/')
if [[ ! "$EXPECTED_SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "❌ ERROR: Could not parse a 40-char EXPECTED_SHA out of $TAG_SCRIPT"
  exit 1
fi

echo "Anchor SHA (parsed from ops/tag-v1.sh): $EXPECTED_SHA"
echo ""

# 2. Fetch just that commit from l9-ci-core into a scratch work dir.
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

git -C "$WORK_DIR" init -q
echo "Fetching $EXPECTED_SHA from $SOURCE_REPO..."
if ! git -C "$WORK_DIR" fetch -q "$SOURCE_REPO" "$EXPECTED_SHA" 2>/dev/null; then
  echo "❌ ERROR: Could not fetch $EXPECTED_SHA from $SOURCE_REPO."
  echo "   Confirm the SHA exists and is reachable from some branch/tag on that repo."
  exit 1
fi

RESOLVED_SHA=$(git -C "$WORK_DIR" rev-parse FETCH_HEAD)
if [[ "$RESOLVED_SHA" != "$EXPECTED_SHA" ]]; then
  echo "❌ ERROR: Fetched commit ($RESOLVED_SHA) does not match EXPECTED_SHA ($EXPECTED_SHA)."
  exit 1
fi
echo "✅ Fetched commit matches EXPECTED_SHA exactly."
echo ""

# 3. Enumerate workflow_call kernels at this SHA (auto-detected by trigger,
#    not a hardcoded filename list, so this self-adapts if kernels are
#    renamed/added/removed later).
ALL_WORKFLOW_FILES=()
while IFS= read -r f; do
  ALL_WORKFLOW_FILES+=("$f")
done < <(git -C "$WORK_DIR" ls-tree -r FETCH_HEAD --name-only -- .github/workflows 2>/dev/null | sort)
if [[ "${#ALL_WORKFLOW_FILES[@]}" -eq 0 ]]; then
  echo "❌ ERROR: No .github/workflows/*.yml files found at $EXPECTED_SHA."
  exit 1
fi

KERNEL_FILES=()
for f in "${ALL_WORKFLOW_FILES[@]}"; do
  if git -C "$WORK_DIR" show "FETCH_HEAD:$f" | grep -q '^\s*workflow_call:'; then
    KERNEL_FILES+=("$f")
  fi
done

if [[ "${#KERNEL_FILES[@]}" -eq 0 ]]; then
  echo "❌ ERROR: No workflow_call kernels found at $EXPECTED_SHA — anchor looks wrong."
  exit 1
fi

echo "Total workflow files at anchor:      ${#ALL_WORKFLOW_FILES[@]}"
echo "workflow_call kernels (in scope):    ${#KERNEL_FILES[@]}"
printf '  - %s\n' "${KERNEL_FILES[@]}"
echo "Excluded (no workflow_call trigger — not consumer-facing):"
for f in "${ALL_WORKFLOW_FILES[@]}"; do
  skip=false
  for k in "${KERNEL_FILES[@]}"; do
    [[ "$f" == "$k" ]] && skip=true && break
  done
  [[ "$skip" == false ]] && echo "  - $f"
done
echo ""

# 4. Documented exceptions: dynamic (non-static) uses: refs that cannot be
#    SHA-pinned because the action path itself is computed at runtime, not
#    a floating-tag oversight. Each entry MUST carry a one-line
#    justification. Do NOT add entries here to silence a real finding —
#    only for genuinely dynamic/computed uses: paths.
ALLOWLIST_FILES=("pr-pipeline.yml")
ALLOWLIST_PATTERNS=('^oxsecurity/megalinter/flavors/\$\{\{[^}]*\}\}@v8$')
ALLOWLIST_REASONS=("MegaLinter flavor is resolved from a prior step's output (steps.flavor.outputs.flavor); the action path is computed at runtime and cannot be a static SHA pin. Advisory job only (DISABLE_ERRORS: true), does not gate merges.")

violations=()
exceptions=0
total_refs=0

for f in "${KERNEL_FILES[@]}"; do
  base="$(basename "$f")"
  while IFS= read -r line_no_and_text; do
    line_no="${line_no_and_text%%:*}"
    line_text="${line_no_and_text#*:}"

    # Extract the uses: value: strip leading list marker, key, quotes, comments.
    uses_value=$(printf '%s' "$line_text" | sed -E 's/^[[:space:]]*-?[[:space:]]*uses:[[:space:]]*//; s/^"//; s/"[[:space:]]*$//; s/#.*$//' | xargs)
    [[ -z "$uses_value" ]] && continue

    # Skip local composite actions / docker refs — not third-party supply chain.
    case "$uses_value" in
      ./*|docker://*) continue ;;
    esac

    total_refs=$((total_refs + 1))
    ref="${uses_value##*@}"

    if [[ "$ref" =~ ^[0-9a-f]{40}$ ]]; then
      continue  # properly SHA-pinned
    fi

    matched_exception=false
    for i in "${!ALLOWLIST_PATTERNS[@]}"; do
      if [[ "$base" == "${ALLOWLIST_FILES[$i]}" && "$uses_value" =~ ${ALLOWLIST_PATTERNS[$i]} ]]; then
        echo "⚠️  DOCUMENTED EXCEPTION  $f:$line_no  $uses_value"
        echo "     Reason: ${ALLOWLIST_REASONS[$i]}"
        exceptions=$((exceptions + 1))
        matched_exception=true
        break
      fi
    done
    [[ "$matched_exception" == true ]] && continue

    violations+=("$f:$line_no  $uses_value")
  done < <(git -C "$WORK_DIR" show "FETCH_HEAD:$f" | grep -nE '^[[:space:]]*-?[[:space:]]*uses:[[:space:]]*[A-Za-z0-9./]')
done

echo ""
echo "=== Result ==="
echo "Third-party 'uses:' refs inspected (kernels only): $total_refs"
echo "Documented exceptions:                             $exceptions"
echo "Floating (unpinned) violations:                    ${#violations[@]}"
echo ""

if [[ "${#violations[@]}" -gt 0 ]]; then
  echo "❌ FAIL — floating third-party Action refs found in workflow_call kernels at $EXPECTED_SHA:"
  printf '   %s\n' "${violations[@]}"
  echo ""
  echo "Do NOT run ops/tag-v1.sh against this SHA. Fix EXPECTED_SHA or the anchor commit first."
  exit 1
fi

echo "✅ PASS — $EXPECTED_SHA has zero unpinned third-party Action refs in its workflow_call kernels"
echo "   ($exceptions documented exception(s) allow-listed above)."
echo "It is now safe to run ops/tag-v1.sh."
