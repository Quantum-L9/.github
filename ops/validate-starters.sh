#!/usr/bin/env bash
# ops/validate-starters.sh
# Boundary validator — asserts that the retired L9 CI distribution surfaces
# cannot be reintroduced into Quantum-L9/.github (campaign
# l9-dot-github-ci-boundary-v1). Replaces the former CI starter-gallery and
# l9-ci-pack completeness checks; surviving workflows must parse as YAML.
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

PASS=0
FAIL=0

RETIRED_PATHS=(
  ".github/workflows/auto-seed-new-repo.yml"
  ".github/workflows/seed-governance.yml"
  ".github/workflows/continuous-sync.yml"
  ".github/workflows/dispatch-template-update.yml"
  "l9-ci-pack"
  "templates/sync_ci_from_pack.py"
  "templates/on-org-update.yml"
  "ops/build-seed-payload.js"
  "ops/sync-org-files.sh"
  "ops/sync-v2-starters.sh"
)

echo "=== Quantum-L9/.github boundary validation ==="
echo ""

for p in "${RETIRED_PATHS[@]}"; do
  if [ -e "$p" ]; then
    echo "❌ retired CI-distribution surface present: $p"
    FAIL=$((FAIL+1))
  else
    echo "✅ absent (retired): $p"
    PASS=$((PASS+1))
  fi
done

# Surviving workflows must at least parse as YAML.
if ! python3 -c "import yaml" 2>/dev/null; then
  echo "⚠️  PyYAML unavailable — skipping workflow YAML parse"
else
  for w in .github/workflows/*.yml; do
    if python3 -c "import yaml,sys; yaml.safe_load(open('$w'))" 2>/dev/null; then
      echo "✅ YAML valid: $w"
      PASS=$((PASS+1))
    else
      echo "❌ YAML parse failed: $w"
      FAIL=$((FAIL+1))
    fi
  done
fi

echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Boundary validation FAILED — fix issues above before committing"
  exit 1
else
  echo "✅ Boundary validation passed"
  exit 0
fi
