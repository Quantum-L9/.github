#!/usr/bin/env bash
# ops/tag-v1.sh
# Creates v1.0.0 annotated tag and moving v1 tag on Quantum-L9/l9-ci-core.
# PREREQUISITE: Run from inside the l9-ci-core repo root with a clean working tree.
# PREREQUISITE: git remote 'origin' must point to Quantum-L9/l9-ci-core.
set -euo pipefail

EXPECTED_SHA="2b330a5aab90cd7781bef08f14c5e7904b61bc56"
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

# 3. Fetch latest from origin/main
echo "Fetching origin/main..."
git fetch origin main

# 4. Assert HEAD matches expected SHA
HEAD_SHA=$(git rev-parse origin/main)
echo "HEAD SHA: $HEAD_SHA"
echo "Expected: $EXPECTED_SHA"

if [[ "$HEAD_SHA" != "$EXPECTED_SHA" ]]; then
  echo "❌ ERROR: HEAD SHA does not match expected SHA."
  echo "   This script is pinned to SHA $EXPECTED_SHA."
  echo "   If main has advanced legitimately, update EXPECTED_SHA in this script."
  exit 1
fi

echo "✅ SHA assertion passed."

# 5. Checkout the exact SHA
git checkout "$EXPECTED_SHA"

# 6. Create annotated v1.0.0 tag (immutable)
if git rev-parse "v1.0.0" >/dev/null 2>&1; then
  echo "⚠️  Tag v1.0.0 already exists. Skipping creation."
else
  git tag -a v1.0.0 -m "v1.0.0 — initial kernel release: 8 workflow_call kernels (pr-pipeline, release-publish, nightly, pre-commit-ci, trio-governance, security, scorecard, sbom)"
  echo "✅ Annotated tag v1.0.0 created."
fi

# 7. Push v1.0.0 (immutable — never force-push this tag)
echo "Pushing v1.0.0..."
git push origin v1.0.0
echo "✅ v1.0.0 pushed."

# 8. Create/update moving v1 tag (force — this is the moving tag)
git tag -fa v1 -m "v1 moving tag → v1.0.0 (SHA: $EXPECTED_SHA)"
echo "Pushing v1 (force)..."
git push origin v1 --force
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
