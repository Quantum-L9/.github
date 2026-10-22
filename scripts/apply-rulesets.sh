#!/usr/bin/env bash
# Applies org rulesets. Advisory rulesets are applied in EVALUATE mode only;
# the canonical CI ruleset (rulesets/l9-canonical-ci-required.json) is the one
# ACTIVE ruleset and is applied exactly as recorded, so a change to it (for
# example strict_required_status_checks_policy) ships through a reviewed PR.
set -euo pipefail
ORG=Quantum-L9
DRY="${DRY_RUN:-1}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CANONICAL=l9-canonical-ci-required.json

command -v gh >/dev/null || { echo "gh CLI required" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq required" >&2; exit 1; }

PLAN=$(gh api "orgs/$ORG" --jq '.plan.name // "unknown"' 2>/dev/null || echo unknown)
echo "org plan: $PLAN"

apply_one() {
  local f="$1" mode name existing
  mode=$(jq -r '.enforcement' "$f")
  name=$(jq -r '.name' "$f")
  if [[ "$DRY" == "1" ]]; then
    echo "would apply ($mode): $name"
    return 0
  fi
  existing=$(gh api "orgs/$ORG/rulesets" --jq ".[] | select(.name==\"$name\") | .id" 2>/dev/null || true)
  if [[ -n "$existing" ]]; then
    gh api -X PUT "orgs/$ORG/rulesets/$existing" --input "$f" >/dev/null
    echo "updated ($mode): $name (id $existing)"
  else
    gh api -X POST "orgs/$ORG/rulesets" --input "$f" >/dev/null
    echo "created ($mode): $name"
  fi
}

# 1. Canonical CI: active, plan-independent (required workflows need no
#    evaluate support). Refuse to apply it in any state but active.
canonical="$SRC/rulesets/$CANONICAL"
if [[ -f "$canonical" ]]; then
  if [[ "$(jq -r '.enforcement' "$canonical")" != "active" ]]; then
    echo "!! REFUSING $canonical — the canonical CI ruleset must be active" >&2
    exit 1
  fi
  apply_one "$canonical"
fi

# 2. Advisory rulesets: evaluate only. evaluate mode requires GitHub
#    Enterprise Cloud; never trade advisory posture for availability.
if [[ "$PLAN" != "enterprise" ]]; then
  cat <<'EOF'
!! evaluate mode requires GitHub Enterprise Cloud.
   Skipping the advisory rulesets. Options:
     1. Skip them entirely for now (recommended while advisory).
     2. Use a repo-level branch ruleset with enforcement=active and
        required_approving_review_count=0 — blocks nothing but direct pushes.
   This script will NOT silently create an active advisory org ruleset.
EOF
else
  for f in "$SRC"/rulesets/*.json; do
    [[ "$(basename "$f")" == "$CANONICAL" ]] && continue
    if [[ "$(jq -r '.enforcement' "$f")" != "evaluate" ]]; then
      echo "!! REFUSING $f — enforcement is '$(jq -r '.enforcement' "$f")', expected 'evaluate'" >&2
      exit 1
    fi
    apply_one "$f"
  done
fi

echo
echo "Advisory findings (no blocking): Org Settings -> Rulesets -> Insights"
echo "Canonical CI binding: Org Settings -> Rulesets -> 'L9 canonical CI required'"
[[ "$DRY" == "1" ]] && echo "Re-run with DRY_RUN=0 to apply."
