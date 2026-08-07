#!/usr/bin/env bash
# ops/tag-v1.sh
# Creates v1.0.0 annotated tag and moving v1 tag on Quantum-L9/l9-ci-core,
# or verifies that published tags already match EXPECTED_SHA (idempotent).
# PREREQUISITE: Run from inside the l9-ci-core repo root with a clean working tree.
# PREREQUISITE: git remote 'origin' must point to Quantum-L9/l9-ci-core.
# PREREQUISITE: Run ops/verify-v1-anchor.sh first to re-confirm zero floating
#               third-party Action refs at EXPECTED_SHA before tagging.
set -euo pipefail

# Anchor: published @v1.0.0 / @v1 tip on l9-ci-core — PR #44
# ("feat: add v1 compatibility kernels restoring the @v1 reusable-workflow
# contracts"). Supersedes 2a3270be5f5184099c33a101807f65b1becf4e7c (PR #11
# preventive pin on the pre-v2-rewrite lineage), which was never what got
# tagged. Also supersedes the originally-planned
# 2b330a5aab90cd7781bef08f14c5e7904b61bc56 (pre-SHA-pinning hardening).
EXPECTED_SHA="978cf948133fa4d9cd6b78ecbb383295869cb70f"
REPO="Quantum-L9/l9-ci-core"

echo "=== Quantum-L9 l9-ci-core @v1 Tag Creation Script ==="
echo ""

# 1. Verify we are in the correct repo
remote_url=$(git remote get-url origin 2>/dev/null || echo "")
if [[ "$remote_url" != *"Quantum-L9/l9-ci-core"* ]]; then
  echo "❌ ERROR: Remote origin does not point to Quantum-L9/l9-ci-core"
  echo "   Got: $remote_url"
  echo "   Expected URL containing: Quantum-L9/l9-ci-core"
  exit 1
fi

# 2. Ensure working tree is clean
if [[ -n "$(git status --porcelain)" ]]; then
  echo "❌ ERROR: Working tree is not clean. Commit or stash changes before tagging."
  git status --short
  exit 1
fi

# 3. Fetch the pinned anchor and any existing v1 tags (do NOT require main ==
#    EXPECTED_SHA — the freeze is historical; main advances past it).
echo "Fetching EXPECTED_SHA and v1 tags from origin..."
git fetch origin "$EXPECTED_SHA"
git fetch origin tag v1.0.0 tag v1 2>/dev/null || true

if ! git cat-file -e "${EXPECTED_SHA}^{commit}" 2>/dev/null; then
  echo "❌ ERROR: EXPECTED_SHA $EXPECTED_SHA is not a reachable commit after fetch."
  exit 1
fi
echo "Expected anchor: $EXPECTED_SHA"
echo ""

# 4. Tag-consistency / no-retag guards
peel_remote_tag() {
  # Print peeled commit SHA for refs/tags/$1 on origin, or empty if absent.
  # Annotated tags: prefer the ls-remote "refs/tags/<tag>^{}" line. Some hosts
  # omit that advertisement — then fetch the tip and peel with rev-parse.
  local tag="$1"
  local out peeled tip typ tmp_ref
  out=$(git ls-remote --tags origin "refs/tags/${tag}" "refs/tags/${tag}^{}" 2>/dev/null || true)
  peeled=$(printf '%s\n' "$out" | awk -v ref="refs/tags/${tag}^{}" '$2 == ref { print $1; exit }')
  if [[ -n "$peeled" ]]; then
    printf '%s\n' "$peeled"
    return 0
  fi
  tip=$(printf '%s\n' "$out" | awk -v ref="refs/tags/${tag}" '$2 == ref { print $1; exit }')
  if [[ -z "$tip" ]]; then
    return 0
  fi

  # Ensure the tip object exists locally (commit or tag).
  if ! git cat-file -e "$tip" 2>/dev/null; then
    tmp_ref="refs/tags/.peel-tmp-${tag}-$$"
    if git fetch -q origin "refs/tags/${tag}:${tmp_ref}" 2>/dev/null; then
      :
    elif git fetch -q origin tag "$tag" 2>/dev/null; then
      :
    else
      git fetch -q origin "$tip" 2>/dev/null || true
    fi
  fi

  if git cat-file -e "$tip" 2>/dev/null; then
    typ=$(git cat-file -t "$tip")
    if [[ "$typ" == "commit" ]]; then
      printf '%s\n' "$tip"
      git update-ref -d "refs/tags/.peel-tmp-${tag}-$$" 2>/dev/null || true
      return 0
    fi
    if [[ "$typ" == "tag" ]]; then
      peeled=$(git rev-parse "${tip}^{commit}")
      printf '%s\n' "$peeled"
      git update-ref -d "refs/tags/.peel-tmp-${tag}-$$" 2>/dev/null || true
      return 0
    fi
  fi

  # Fetch tag ref into FETCH_HEAD and peel (annotated or lightweight).
  if git fetch -q origin "refs/tags/${tag}" 2>/dev/null; then
    peeled=$(git rev-parse "FETCH_HEAD^{commit}")
    printf '%s\n' "$peeled"
    git update-ref -d "refs/tags/.peel-tmp-${tag}-$$" 2>/dev/null || true
    return 0
  fi

  tmp_ref="refs/tags/.peel-tmp-${tag}-$$"
  if git rev-parse -q --verify "${tmp_ref}^{commit}" >/dev/null 2>&1; then
    peeled=$(git rev-parse "${tmp_ref}^{commit}")
    printf '%s\n' "$peeled"
    git update-ref -d "$tmp_ref" 2>/dev/null || true
    return 0
  fi
  if git rev-parse -q --verify "refs/tags/${tag}^{commit}" >/dev/null 2>&1; then
    git rev-parse "refs/tags/${tag}^{commit}"
    git update-ref -d "$tmp_ref" 2>/dev/null || true
    return 0
  fi

  git update-ref -d "refs/tags/.peel-tmp-${tag}-$$" 2>/dev/null || true
  # Last resort: return tip (may still be wrong for unfetched annotated tags).
  printf '%s\n' "$tip"
}

v100_sha=$(peel_remote_tag "v1.0.0")
v1_sha=$(peel_remote_tag "v1")

if [[ -n "$v100_sha" || -n "$v1_sha" ]]; then
  echo "Remote tag tips:"
  [[ -n "$v100_sha" ]] && echo "  v1.0.0 → $v100_sha" || echo "  v1.0.0 → (absent)"
  [[ -n "$v1_sha" ]] && echo "  v1     → $v1_sha" || echo "  v1     → (absent)"
  echo ""

  mismatch=false
  if [[ -n "$v100_sha" && "$v100_sha" != "$EXPECTED_SHA" ]]; then
    echo "❌ ERROR: v1.0.0 peels to $v100_sha, not EXPECTED_SHA $EXPECTED_SHA."
    echo "   Refusing to force-update immutable v1.0.0. Update EXPECTED_SHA only after an intentional retag decision."
    mismatch=true
  fi
  if [[ -n "$v1_sha" && "$v1_sha" != "$EXPECTED_SHA" ]]; then
    echo "❌ ERROR: v1 peels to $v1_sha, not EXPECTED_SHA $EXPECTED_SHA."
    echo "   Refusing to force-move v1. Align EXPECTED_SHA or advance tags in a separate, explicit release."
    mismatch=true
  fi
  if [[ "$mismatch" == true ]]; then
    exit 1
  fi

  # Tags present and match — idempotent success; do not push or retag.
  if [[ -n "$v100_sha" && -n "$v1_sha" ]]; then
    echo "✅ Tags already match EXPECTED_SHA. Nothing to create or push."
    echo "   v1.0.0 — immutable annotated tip"
    echo "   v1      — moving tag at same commit"
    exit 0
  fi

  # Partial presence at the correct SHA is unexpected; fail closed rather than
  # half-create or force-push the missing sibling.
  echo "❌ ERROR: Only one of v1.0.0 / v1 is present (both must exist together at EXPECTED_SHA)."
  echo "   Fix the missing tag manually; this script will not invent a half-state."
  exit 1
fi

echo "No v1 / v1.0.0 tags on origin — proceeding to create at EXPECTED_SHA."
echo ""

# 5. Checkout the exact SHA (historical freeze; main may be ahead)
git checkout "$EXPECTED_SHA"

# 6. Create annotated v1.0.0 tag (immutable)
git tag -a v1.0.0 -m "v1.0.0 — v1 compatibility kernels (PR #44): 8 workflow_call kernels (pr-pipeline, release-publish, nightly, pre-commit-ci, trio-governance, security, scorecard, sbom); all static third-party actions SHA-pinned"
echo "✅ Annotated tag v1.0.0 created."

# 7. Push v1.0.0 (immutable — never force-push this tag)
echo "Pushing v1.0.0..."
git push origin v1.0.0
echo "✅ v1.0.0 pushed."

# 8. Create moving v1 tag
git tag -a v1 -m "v1 moving tag → v1.0.0 (SHA: $EXPECTED_SHA)"
echo "Pushing v1..."
git push origin v1
echo "✅ v1 moving tag pushed."

# 9. Protect v1.0.0 as immutable via GitHub tag protection rule
echo "Creating tag protection rule for v1.0.0..."
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/$REPO/tags/protection" \
  -f "pattern=v1.0.0" || echo "⚠️  Tag protection API call failed — set manually in repo settings."

echo ""
echo "✅ v1.0.0 and v1 created."
echo "   v1.0.0 — immutable annotated tag (protected)"
echo "   v1      — moving tag, force-updatable by platform team only"
echo ""
echo "All thin callers can now reference @v1:"
echo "  uses: Quantum-L9/l9-ci-core/.github/workflows/<kernel>.yml@v1"
