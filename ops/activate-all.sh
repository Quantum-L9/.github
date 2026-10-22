#!/usr/bin/env bash
# ops/activate-all.sh
#
# One-shot activation of all dormant capabilities in Quantum-L9/.github.
# Run this ONCE after merging the activation PR. It enables:
#   1. Secret scanning (alerts only, advisory)
#   2. Dependency graph (prerequisite for Dependabot)
#   3. Org rulesets (evaluate mode only)
#   4. Label sync across all repos
#   5. Triggers the auto-seed workflow for unseeded repos
#   6. Triggers the preflight check
#
# Prerequisites:
#   - gh CLI authenticated with org admin permissions
#   - jq installed
#   - Run from the root of the Quantum-L9/.github repo
#
# This script is IDEMPOTENT — safe to run multiple times.
set -euo pipefail

ORG="Quantum-L9"
REPO=".github"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v gh >/dev/null || { echo "❌ gh CLI required" >&2; exit 1; }
command -v jq >/dev/null || { echo "❌ jq required" >&2; exit 1; }

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Quantum-L9 Governance Activation                           ║"
echo "║  Advisory controls stay advisory; canonical CI ruleset is   ║"
echo "║  active (merge-blocking) by design — see rulesets/README.md ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Secret Scanning ──────────────────────────────────────────────────────
echo "═══ 1/6: Secret Scanning (alerts only) ═══"
echo ""
if gh api -X PATCH "orgs/$ORG" \
  -F secret_scanning_enabled_for_new_repositories=true \
  -F dependency_graph_enabled_for_new_repositories=true \
  --silent 2>/dev/null; then
  echo "  ✓ Secret scanning alerts: enabled for new repos"
  echo "  ✓ Dependency graph: enabled for new repos"
else
  echo "  ⚠ Could not update org settings (may need admin:org scope)"
fi

# Enable on existing repos (bulk API, may not be available on all plans)
if gh api -X POST "orgs/$ORG/security-products/secret-scanning/enable-all" --silent 2>/dev/null; then
  echo "  ✓ Secret scanning: enabled on all existing repos"
else
  echo "  ⊘ Bulk enable unavailable on this plan — existing repos unchanged"
fi
echo ""

# ── 2. Dependency Graph ─────────────────────────────────────────────────────
echo "═══ 2/6: Dependency Graph ═══"
echo ""
if gh api -X POST "orgs/$ORG/security-products/dependency-graph/enable-all" --silent 2>/dev/null; then
  echo "  ✓ Dependency graph: enabled on all existing repos"
else
  echo "  ⊘ Bulk enable unavailable — existing repos use per-repo settings"
fi
echo ""

# ── 3. Org Rulesets ─────────────────────────────────────────────────────────
echo "═══ 3/6: Org Rulesets (advisory: evaluate; canonical CI: active) ═══"
echo ""
# One applier. scripts/apply-rulesets.sh applies the canonical CI ruleset
# exactly as recorded (active) and the advisory rulesets in evaluate mode only.
if DRY_RUN=0 bash "$SRC/scripts/apply-rulesets.sh"; then
  echo "  ✓ Rulesets applied"
else
  echo "  ⚠ Ruleset apply reported a failure (see output above)"
fi
echo ""

# ── 4. Label Sync ───────────────────────────────────────────────────────────
echo "═══ 4/6: Label Sync (all repos) ═══"
echo ""
echo "  Triggering sync-labels-all.yml workflow..."
if gh workflow run sync-labels-all.yml --repo "$ORG/$REPO" -f dry_run=false 2>/dev/null; then
  echo "  ✓ Label sync workflow dispatched"
else
  echo "  ⚠ Could not dispatch (workflow may not exist on default branch yet)"
  echo "    Run manually: gh workflow run sync-labels-all.yml --repo $ORG/$REPO -f dry_run=false"
fi
echo ""

# ── 5. Auto-Seed ────────────────────────────────────────────────────────────
echo "═══ 5/6: Auto-Seed (unseeded repos) ═══"
echo ""
echo "  Triggering auto-seed-new-repo.yml workflow (dry-run first)..."
if gh workflow run auto-seed-new-repo.yml --repo "$ORG/$REPO" -f dry_run=true 2>/dev/null; then
  echo "  ✓ Auto-seed workflow dispatched (DRY RUN)"
  echo "    Review the run, then re-dispatch with dry_run=false to apply"
else
  echo "  ⚠ Could not dispatch (workflow may not exist on default branch yet)"
  echo "    Run manually: gh workflow run auto-seed-new-repo.yml --repo $ORG/$REPO -f dry_run=false"
fi
echo ""

# ── 6. Preflight ────────────────────────────────────────────────────────────
echo "═══ 6/6: Preflight Check ═══"
echo ""
echo "  Triggering preflight-scheduled.yml workflow..."
if gh workflow run preflight-scheduled.yml --repo "$ORG/$REPO" 2>/dev/null; then
  echo "  ✓ Preflight workflow dispatched"
else
  echo "  ⚠ Could not dispatch (workflow may not exist on default branch yet)"
  echo "    Run manually: gh workflow run preflight-scheduled.yml --repo $ORG/$REPO"
fi
echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Activation Complete                                        ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Secret scanning:  alerts enabled (advisory)                ║"
echo "║  Dependency graph:  enabled                                 ║"
echo "║  Org rulesets:      advisory=evaluate, canonical CI=active  ║"
echo "║  Labels:            sync dispatched                         ║"
echo "║  Auto-seed:         dry-run dispatched                      ║"
echo "║  Preflight:         dispatched                              ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║  Only the canonical CI ruleset blocks (required workflow).   ║"
echo "║  See docs/ADVISORY.md for the promotion ladder.             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Check Actions tab for workflow run results"
echo "  2. Review auto-seed dry-run, then re-run with dry_run=false"
echo "  3. Check Org Settings → Rulesets → Insights after 1 week"
echo "  4. The governance-report.yml runs weekly — first report in ~7 days"
