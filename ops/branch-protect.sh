#!/usr/bin/env bash
# ops/branch-protect.sh
# Applies branch protection rules to Quantum-L9/.github main branch via GitHub API.
# PREREQUISITE: gh CLI authenticated with repo admin permissions on Quantum-L9/.github
set -euo pipefail

OWNER="Quantum-L9"
REPO=".github"
BRANCH="main"

echo "=== Applying Branch Protection: $OWNER/$REPO @ $BRANCH ==="
echo ""

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 2,
    "require_last_push_approval": true
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
EOF

echo "✅ Branch protection applied to $OWNER/$REPO/$BRANCH"
echo ""
echo "Protection summary:"
echo "  required_approving_review_count: 2"
echo "  dismiss_stale_reviews:           true"
echo "  require_code_owner_reviews:      true"
echo "  require_last_push_approval:      true"
echo "  allow_force_pushes:              false"
echo "  allow_deletions:                 false"
echo "  required_conversation_resolution: true"
echo "  enforce_admins:                  true"
