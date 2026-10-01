#!/usr/bin/env bash
# ops/validate-starters.sh
# Runs the ops/test-*.js suites: seed payload selection, the repo-class birth
# profile contract, the shared label taxonomy parser, the seed-branch safety
# gate, and the branch guard inside both seed workflows.
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

PASS=0
FAIL=0

echo "=== Quantum-L9 Workflow Starter Validation ==="

if command -v node &>/dev/null; then
  for t in \
    ops/test-build-seed-payload.js \
    ops/test-repo-class-profile.js \
    ops/test-label-taxonomy.js \
    ops/test-seed-branch-safety.js \
    ops/test-seed-workflow-branch-guard.js; do
    if node "$t"; then
      echo "✅ $t"
      PASS=$((PASS+1))
    else
      echo "❌ $t"
      FAIL=$((FAIL+1))
    fi
  done
  echo ""
fi

if bash ops/test-sync-org-files.sh; then
  echo "✅ ops/test-sync-org-files.sh"
  PASS=$((PASS+1))
else
  echo "❌ ops/test-sync-org-files.sh"
  FAIL=$((FAIL+1))
fi
if command -v yamllint &>/dev/null; then
  echo ""
  echo "=== yamllint (distributed labels) ==="
  if yamllint -c .yamllint.yml .github/labels.yml; then
    echo "✅ yamllint labels.yml"
    PASS=$((PASS+1))
  else
    echo "❌ yamllint labels.yml"
    FAIL=$((FAIL+1))
  fi
fi

echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"

if [ "$FAIL" -gt 0 ]; then
  echo "❌ Validation FAILED — fix issues above before committing"
  exit 1
else
  echo "✅ All starters validated successfully"
  exit 0
fi
