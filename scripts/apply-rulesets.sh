#!/usr/bin/env bash
# Applies org rulesets in EVALUATE mode. Refuses to create anything enforcing.
set -euo pipefail
ORG=Quantum-L9
DRY="${DRY_RUN:-1}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

command -v gh >/dev/null || { echo "gh CLI required" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq required" >&2; exit 1; }

PLAN=$(gh api "orgs/$ORG" --jq '.plan.name // "unknown"' 2>/dev/null || echo unknown)
echo "org plan: $PLAN"
if [[ "$PLAN" != "enterprise" ]]; then
  cat <<'EOF'
!! evaluate mode requires GitHub Enterprise Cloud.
   Refusing to apply. Options:
     1. Skip rulesets entirely for now (recommended while advisory).
     2. Use a repo-level branch ruleset with enforcement=active and
        required_approving_review_count=0 — blocks nothing but direct pushes.
   This script will NOT silently create an active org ruleset.
EOF
  exit 0
fi

for f in "$SRC"/rulesets/*.json; do
  MODE=$(jq -r '.enforcement' "$f")
  NAME=$(jq -r '.name' "$f")
  if [[ "$MODE" != "evaluate" ]]; then
    echo "!! REFUSING $f — enforcement is '$MODE', expected 'evaluate'" >&2
    exit 1
  fi
  if [[ "$DRY" == "1" ]]; then
    echo "would create (evaluate): $NAME"
    continue
  fi
  EXISTING=$(gh api "orgs/$ORG/rulesets" --jq ".[] | select(.name==\"$NAME\") | .id" 2>/dev/null || true)
  if [[ -n "$EXISTING" ]]; then
    gh api -X PUT "orgs/$ORG/rulesets/$EXISTING" --input "$f" >/dev/null
    echo "updated (evaluate): $NAME"
  else
    gh api -X POST "orgs/$ORG/rulesets" --input "$f" >/dev/null
    echo "created (evaluate): $NAME"
  fi
done

echo
echo "Review findings without blocking anyone:"
echo "  Org Settings -> Rulesets -> Insights"
echo "Re-run with DRY_RUN=0 to apply."
