#!/usr/bin/env bash
# ops/validate-starters.sh
# Runs the ops/test-*.js suites: seed payload selection, the rendered
# dependabot.yml (ops/render-dependabot.js, ADR 0019), the repo-class birth
# profile contract, the shared label taxonomy parser, the seed-branch safety
# gate, the branch guard inside both seed workflows and continuous-sync
# (including its class-aware PR-template and caller re-pin management and its
# Preview / Apply modes), the manual-only trigger contract of the distribution
# workflows, the governance-pr.yml PR-body refresh job, and the advisory
# governance-report.yml posture classification (no unverified all-clear) over
# the registry-derived governed census (needs python3 with PyYAML).
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

PASS=0
FAIL=0

echo "=== Quantum-L9 Workflow Starter Validation ==="

# The JS suites are most of this gate. A runner without node used to skip
# them and still report success; that is a failure, not a pass.
if ! command -v node &>/dev/null; then
  echo "❌ node not found — the ops/test-*.js suites cannot run"
  FAIL=$((FAIL+1))
else
  for t in \
    ops/test-build-seed-payload.js \
    ops/test-render-dependabot.js \
    ops/test-repo-class-profile.js \
    ops/test-label-taxonomy.js \
    ops/test-seed-branch-safety.js \
    ops/test-seed-workflow-branch-guard.js \
    ops/test-continuous-sync-branch-guard.js \
    ops/test-distribution-triggers.js \
    ops/test-governance-pr-body.js \
    ops/test-governance-report.js; do
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

if bash ops/test-activate-all.sh; then
  echo "✅ ops/test-activate-all.sh"
  PASS=$((PASS+1))
else
  echo "❌ ops/test-activate-all.sh"
  FAIL=$((FAIL+1))
fi
# The canonical PR template's machine contract. node is required here, not
# optional: every governed PR body is composed from this one file.
if node ops/test-pr-template.js; then
  echo "✅ ops/test-pr-template.js"
  PASS=$((PASS+1))
else
  echo "❌ ops/test-pr-template.js"
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
