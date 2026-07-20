#!/usr/bin/env bash
# ops/audit-sha-pins.sh
#
# Repo-wide SHA-pin audit. Every `uses:` reference in every workflow YAML file
# in this repo (workflow-templates/, l9-ci-pack/workflows/, .github/workflows/)
# must be pinned by a full 40-character commit SHA, EXCEPT the documented,
# intentionally-frozen Quantum-L9/l9-ci-core major-version tags (@v1 = frozen
# legacy kernel set; @v2 / @v2.0.0 = current major once published). `@main`,
# `@master`, `@latest`, or any other floating tag is a failure.
#
# This generalizes the l9-ci-pack-only pin check already in
# ops/validate-starters.sh to every workflow file in the repo, including the
# workflow-templates/ gallery (which validate-starters.sh does not scan for
# pins beyond the @main check).
set -euo pipefail

FAILED=0
CHECKED=0

# Directories that can contain `uses:` lines.
SEARCH_DIRS=("workflow-templates" "l9-ci-pack/workflows" ".github/workflows")

is_sha() {
  local ref="$1"
  [[ "$ref" =~ ^[0-9a-f]{40}$ ]]
}

is_frozen_core_tag() {
  local repo="$1" ref="$2"
  [[ "$repo" == "Quantum-L9/l9-ci-core"* ]] && [[ "$ref" =~ ^v(1|2|2\.0\.0)$ ]]
}

for dir in "${SEARCH_DIRS[@]}"; do
  [[ -d "$dir" ]] || continue
  while IFS= read -r -d '' f; do
    line_no=0
    while IFS= read -r line; do
      line_no=$((line_no + 1))
      # Strip leading whitespace and an optional YAML list-item dash
      # ("  - uses: ..." is the common steps: syntax; "uses: ..." is the
      # job-level reusable-workflow-call syntax).
      trimmed="$(echo "$line" | sed -E 's/^[[:space:]]*(-[[:space:]]+)?//')"
      # Skip full-line comments; only inspect live `uses:` keys.
      [[ "$trimmed" == \#* ]] && continue
      [[ "$trimmed" =~ ^uses:[[:space:]]*(.+)$ ]] || continue
      spec="${BASH_REMATCH[1]}"
      # Strip a trailing inline comment (e.g. "... # v4.2.2").
      spec="$(echo "$spec" | sed -E 's/[[:space:]]+#.*$//')"
      # Local/relative actions (./.github/actions/...) have no ref to pin.
      [[ "$spec" == .* ]] && continue
      [[ "$spec" == *"@"* ]] || continue
      ref="${spec##*@}"
      repo="${spec%@*}"
      CHECKED=$((CHECKED + 1))
      if is_sha "$ref"; then
        continue
      fi
      if is_frozen_core_tag "$repo" "$ref"; then
        continue
      fi
      echo "FAIL: ${f}:${line_no}: floating ref '${ref}' on '${repo}' — pin by full 40-char commit SHA"
      FAILED=$((FAILED + 1))
    done < "$f"
  done < <(find "$dir" -type f \( -name "*.yml" -o -name "*.yaml" \) -print0)
done

echo "---"
echo "Checked ${CHECKED} uses: references."
if [[ "$FAILED" -gt 0 ]]; then
  echo "${FAILED} floating (non-SHA, non-frozen-tag) reference(s) found."
  exit 1
fi
echo "All references pinned by SHA or a documented frozen Core tag (@v1/@v2/@v2.0.0)."
