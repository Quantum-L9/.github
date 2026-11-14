#!/usr/bin/env bash
# ops/validate-starters.sh
# Runs the ops/test-*.js suites: seed payload selection, the rendered
# dependabot.yml (ops/render-dependabot.js, ADR 0019), the rendered
# .coderabbit.yaml (ops/render-coderabbit.js, ADR 0020; fetches CodeRabbit's
# schema with curl and validates with python3 jsonschema), the repo-class birth
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
  # ops/test-seed-pr-body.js composes seed PR bodies with the real PR-body
  # renderer at the governance-pr.yml pin. CI checks that pin out and sets
  # SEED_COMPOSER_ROOT; a local run fetches it once into .cache/composer.
  if [[ -z "${SEED_COMPOSER_ROOT:-}" ]]; then
    if ! command -v git &>/dev/null; then
      echo "❌ git not found — needed to fetch the pinned PR-body composer"
      FAIL=$((FAIL+1))
    elif bash ops/fetch-composer.sh .cache/composer; then
      export SEED_COMPOSER_ROOT=.cache/composer
    else
      echo "❌ could not fetch the pinned PR-body composer (ops/fetch-composer.sh)"
      FAIL=$((FAIL+1))
    fi
  fi
  # The composer itself, and the governance-report suite, run under python3.
  if ! command -v python3 &>/dev/null; then
    echo "❌ python3 not found — the composer and the governance-report suite cannot run"
    FAIL=$((FAIL+1))
  fi
  for t in \
    ops/test-build-seed-payload.js \
    ops/test-seed-payload-consumer-gates.js \
    ops/test-render-dependabot.js \
    ops/test-render-coderabbit.js \
    ops/test-repo-class-profile.js \
    ops/test-label-taxonomy.js \
    ops/test-seed-branch-safety.js \
    ops/test-seed-pr-body.js \
    ops/test-seed-workflow-branch-guard.js \
    ops/test-continuous-sync-branch-guard.js \
    ops/test-distribution-triggers.js \
    ops/test-governance-pr-body.js \
    ops/test-birth-registry-workflow.js \
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

# Factory-born repository registration (ADR-039): the real tool against
# fixture births and a copy of this tree (needs git and python3 with PyYAML).
if python3 ops/test-register-birth.py; then
  echo "✅ ops/test-register-birth.py"
  PASS=$((PASS+1))
else
  echo "❌ ops/test-register-birth.py"
  FAIL=$((FAIL+1))
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
