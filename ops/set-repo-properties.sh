#!/usr/bin/env bash
# ops/set-repo-properties.sh
#
# Creates the org custom properties schema and bulk-sets initial values
# based on repo contents (auto-detection of language, CI version, seeding status).
#
# Usage:
#   ops/set-repo-properties.sh [--apply]
#
# Without --apply, runs in dry-run mode (reports what would be set).
# Requires: gh CLI with admin:org scope, jq.
set -euo pipefail

ORG="Quantum-L9"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="$SRC/ops/properties-schema.json"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

command -v gh >/dev/null || { echo "❌ gh CLI required" >&2; exit 1; }
command -v jq >/dev/null || { echo "❌ jq required" >&2; exit 1; }

echo "=== Custom Properties: ${APPLY:+APPLY}${APPLY:-DRY RUN} ==="
echo ""

# ── 1. Create/update schema ─────────────────────────────────────────────────
echo "── Schema ──"
PROPS=$(jq -c '.[]' "$SCHEMA")
while IFS= read -r prop; do
  NAME=$(echo "$prop" | jq -r '.property_name')
  if [[ $APPLY -eq 1 ]]; then
    # GitHub API for custom properties schema
    if gh api --method PUT "orgs/$ORG/properties/schema/$NAME" \
      --input <(echo "$prop" | jq '{
        value_type: .value_type,
        required: .required,
        default_value: .default_value,
        description: .description,
        allowed_values: .allowed_values
      } | with_entries(select(.value != null))') --silent 2>/dev/null; then
      echo "  ✓ $NAME"
    else
      echo "  ⚠ $NAME (failed — may need admin:org)"
    fi
  else
    echo "  would create: $NAME (${prop})"
  fi
done <<< "$PROPS"
echo ""

# ── 2. Auto-detect and set values per repo ──────────────────────────────────
echo "── Per-repo values ──"
REPOS=$(gh repo list "$ORG" --limit 200 --json name,isArchived,isFork \
  --jq '.[] | select(.isArchived==false and .isFork==false and .name!=".github") | .name')

while IFS= read -r REPO; do
  [[ -z "$REPO" ]] && continue

  # Detect language
  LANGS=""
  HAS_PY=$(gh api "repos/$ORG/$REPO/contents/pyproject.toml" --silent 2>/dev/null && echo "yes" || echo "no")
  HAS_TS=$(gh api "repos/$ORG/$REPO/contents/tsconfig.json" --silent 2>/dev/null && echo "yes" || echo "no")
  HAS_PKG=$(gh api "repos/$ORG/$REPO/contents/package.json" --silent 2>/dev/null && echo "yes" || echo "no")
  [[ "$HAS_PY" == "yes" ]] && LANGS="${LANGS:+$LANGS,}python"
  [[ "$HAS_TS" == "yes" ]] && LANGS="${LANGS:+$LANGS,}typescript"
  [[ "$HAS_PKG" == "yes" && "$HAS_TS" != "yes" ]] && LANGS="${LANGS:+$LANGS,}javascript"

  # Detect CI version
  HAS_V2=$(gh api "repos/$ORG/$REPO/contents/.github/workflows/l9-analysis.yml" --silent 2>/dev/null && echo "yes" || echo "no")
  HAS_V1=$(gh api "repos/$ORG/$REPO/contents/.github/workflows/pr-pipeline.yml" --silent 2>/dev/null && echo "yes" || echo "no")
  if [[ "$HAS_V2" == "yes" ]]; then CI_VER="v2"
  elif [[ "$HAS_V1" == "yes" ]]; then CI_VER="v1"
  else CI_VER="none"; fi

  # Detect seeded
  HAS_CO=$(gh api "repos/$ORG/$REPO/contents/.github/CODEOWNERS" --silent 2>/dev/null && echo "yes" || echo "no")
  HAS_DEP=$(gh api "repos/$ORG/$REPO/contents/.github/dependabot.yml" --silent 2>/dev/null && echo "yes" || echo "no")
  SEEDED="false"
  [[ "$HAS_CO" == "yes" && "$HAS_DEP" == "yes" ]] && SEEDED="true"

  # Determine tier (l9-ci-core, l9-ci-sdk, l9-assurance = critical)
  TIER="standard"
  case "$REPO" in
    l9-ci-core|l9-ci-sdk|l9-assurance|Cursor-Governance) TIER="critical" ;;
    *-template*|*-example*) TIER="experimental" ;;
  esac

  if [[ $APPLY -eq 1 ]]; then
    # Build properties payload
    PAYLOAD=$(jq -n \
      --arg ci "$CI_VER" \
      --arg tier "$TIER" \
      --arg seeded "$SEEDED" \
      --arg langs "$LANGS" \
      '{
        "properties": [
          {"property_name": "l9-ci-version", "value": $ci},
          {"property_name": "l9-tier", "value": $tier},
          {"property_name": "l9-seeded", "value": $seeded},
          {"property_name": "l9-team", "value": "platform"}
        ] + (if $langs != "" then [{"property_name": "l9-language", "value": ($langs | split(","))}] else [] end)
      }')
    gh api --method PATCH "repos/$ORG/$REPO/properties/values" \
      --input <(echo "$PAYLOAD") --silent 2>/dev/null \
      && printf '  ✓ %-35s ci=%s tier=%s seeded=%s lang=%s\n' "$REPO" "$CI_VER" "$TIER" "$SEEDED" "${LANGS:-none}" \
      || printf '  ⚠ %-35s (failed)\n' "$REPO"
  else
    printf '  %-35s ci=%s tier=%s seeded=%s lang=%s\n' "$REPO" "$CI_VER" "$TIER" "$SEEDED" "${LANGS:-none}"
  fi
done <<< "$REPOS"

echo ""
echo "Done. ${APPLY:+Properties applied.}${APPLY:-Re-run with --apply to commit changes.}"
