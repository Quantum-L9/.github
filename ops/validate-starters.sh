#!/usr/bin/env bash
# ops/validate-starters.sh
# Validates every workflow-templates/*.yml has a matching *.properties.json.
# Validates each properties.json contains required fields: name, description, iconName, categories, filePatterns.
# Validates the l9-ci-pack/ (v2) required CI file set is present and pinned to
# a full commit SHA or a Core release tag — never @main.
# Runs the ops/test-*.js suites: seed payload selection, the repo-class birth
# profile contract, the shared label taxonomy parser, the seed-branch safety
# gate, and the branch guard inside both seed workflows.
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

TEMPLATES_DIR="workflow-templates"
PACK_DIR="l9-ci-pack"
# Print every first-party Quantum-L9 `uses:` reference in $1 that is not a full
# 40-hex commit SHA. Comment lines are stripped first: l9-analysis.yml states
# the pin policy in prose that quotes a `uses:` line, and matching that text
# reported a correctly pinned file as unpinned.
unpinned_internal_refs() {
  grep -vE '^[[:space:]]*#' "$1" \
    | grep -oE 'uses:[[:space:]]*Quantum-L9/[^@[:space:]]+@[^[:space:]]+' \
    | grep -vE '@[0-9a-f]{40}$' || true
}

REQUIRED_FIELDS=("name" "description" "iconName" "categories" "filePatterns")
REQUIRED_PACK_GOVERNANCE=("execution-profiles.yaml" "provider-requiredness.yaml" "rule-modes.yaml" "waivers.yaml" "promotion-policy.yaml" "quality-thresholds.yaml" "semgrep-identity-map.yaml" "semgrep-finding-policy.yaml")
REQUIRED_PACK_WORKFLOWS=("l9-analysis.yml" "l9-lint-test.yml" "l9-lint-test-node.yml")
REQUIRED_PACK_FORMATTER=("biome.json" ".biomeignore" ".editorconfig" ".vscode/extensions.json")
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
echo ""
echo "Templates directory: $TEMPLATES_DIR"
echo ""

if [ ! -d "$TEMPLATES_DIR" ]; then
  echo "❌ FATAL: $TEMPLATES_DIR directory not found."
  exit 1
fi

# Check each .yml has a matching .properties.json
for yml in "$TEMPLATES_DIR"/*.yml; do
  basename_no_ext="${yml%.yml}"
  props="${basename_no_ext}.properties.json"
  starter_name=$(basename "$yml")

  if [ ! -f "$props" ]; then
    echo "❌ MISSING properties.json: $props (for $starter_name)"
    FAIL=$((FAIL+1))
    continue
  fi

  # Validate required fields in properties.json
  FIELDS_OK=true
  for field in "${REQUIRED_FIELDS[@]}"; do
    # Use node if available, else python3
    if command -v node &>/dev/null; then
      val=$(node -e "const p=require('./$props'); console.log(p.$field !== undefined ? 'ok' : 'missing')" 2>/dev/null || echo "parse-error")
    elif command -v python3 &>/dev/null; then
      val=$(python3 -c "import json; p=json.load(open('$props')); print('ok' if '$field' in p else 'missing')" 2>/dev/null || echo "parse-error")
    else
      echo "⚠️  Neither node nor python3 available — cannot validate JSON fields"
      val="ok"
    fi

    if [ "$val" != "ok" ]; then
      echo "❌ MISSING FIELD '$field' in $props"
      FIELDS_OK=false
      FAIL=$((FAIL+1))
    fi
  done

  # Every first-party Quantum-L9 reference must be a full 40-hex commit SHA.
  # audit-pins-org.yml rates an unpinned internal action HIGH (higher than an
  # unpinned external one), and a floating tag is how a starter silently
  # breaks: l9-ci-core@v2 was referenced org-wide for weeks and never existed.
  if unpinned_internal_refs "$yml" | grep -q .; then
    echo "❌ $yml has an internal Quantum-L9 ref that is not a full commit SHA:"
    unpinned_internal_refs "$yml" | sed 's/^/     /'
    FAIL=$((FAIL+1))
    FIELDS_OK=false
  fi
  if grep -q "@main" "$yml"; then
    echo "❌ @main REFERENCE found in $yml — must use a full commit SHA"
    FAIL=$((FAIL+1))
    FIELDS_OK=false
  fi

  if $FIELDS_OK; then
    echo "✅ $starter_name — properties.json valid, no @main refs"
    PASS=$((PASS+1))
  fi
done

echo ""
echo "=== l9-ci-pack (v2) completeness ==="

if [ ! -d "$PACK_DIR" ]; then
  echo "❌ FATAL: $PACK_DIR directory not found."
  FAIL=$((FAIL+1))
else
  for f in "${REQUIRED_PACK_GOVERNANCE[@]}"; do
    path="$PACK_DIR/governance/$f"
    if [ -f "$path" ]; then
      if python3 -c 'import json,sys; json.loads(sys.stdin.read())' < "$path"; then
        echo "✅ $path present (JSON-in-YAML)"
        PASS=$((PASS+1))
      else
        echo "❌ $path is not JSON-in-YAML"
        FAIL=$((FAIL+1))
      fi
    else
      echo "❌ MISSING required governance file: $path"
      FAIL=$((FAIL+1))
    fi
  done

  for f in "${REQUIRED_PACK_WORKFLOWS[@]}"; do
    path="$PACK_DIR/workflows/$f"
    if [ ! -f "$path" ]; then
      echo "❌ MISSING required workflow template: $path"
      FAIL=$((FAIL+1))
      continue
    fi
    if grep -q "@main" "$path"; then
      echo "❌ @main REFERENCE found in $path — must be a full commit SHA"
      FAIL=$((FAIL+1))
      continue
    fi
    if unpinned_internal_refs "$path" | grep -q .; then
      echo "❌ $path has an internal Quantum-L9 ref that is not a full commit SHA:"
      unpinned_internal_refs "$path" | sed 's/^/     /'
      FAIL=$((FAIL+1))
      continue
    fi
    echo "✅ $path present, internal refs SHA-pinned"
    PASS=$((PASS+1))
  done

  py_wf="$PACK_DIR/workflows/l9-lint-test.yml"
  if [ -f "$py_wf" ]; then
    # The CI toolchain is pinned by install-consumer-ci@v2, so the caller must
    # not pip-install ruff / mypy / pytest or fall back to unpinned plugins.
    # Installing the CONSUMER's own package is required, not forbidden —
    # without it pytest fails on import before running a test.
    if grep -qE 'name: Python Test Suite' "$py_wf" \
      && grep -qE 'name: Detect Python package' "$py_wf" \
      && grep -qE 'name: Install consumer package and dependencies' "$py_wf" \
      && ! grep -qE 'pip install (ruff|mypy|pytest)[[:space:]]|python -c "import pytest_cov"' "$py_wf"; then
      echo "✅ $py_wf is skip-safe (Python Test Suite, consumer deps, no unpinned toolchain pip)"
      PASS=$((PASS+1))
    else
      echo "❌ $py_wf must skip without manifests, name Python Test Suite, install consumer deps, and take its toolchain from install-consumer-ci only"
      FAIL=$((FAIL+1))
    fi
  fi

  node_wf="$PACK_DIR/workflows/l9-lint-test-node.yml"
  if [ -f "$node_wf" ]; then
    if grep -qE 'npx --no-install eslint|name: ESLint' "$node_wf"; then
      echo "❌ $node_wf still invokes ESLint — pack must ship the Biome SDK caller"
      FAIL=$((FAIL+1))
    elif grep -q 'l9-biome-scan.yml' "$node_wf"; then
      echo "✅ $node_wf calls SDK Biome scanner"
      PASS=$((PASS+1))
    else
      echo "❌ $node_wf missing l9-biome-scan.yml pin"
      FAIL=$((FAIL+1))
    fi
  fi

  for f in "${REQUIRED_PACK_FORMATTER[@]}"; do
    path="$PACK_DIR/$f"
    if [ -f "$path" ]; then
      echo "✅ $path present"
      PASS=$((PASS+1))
    else
      echo "❌ MISSING required formatter contract: $path"
      FAIL=$((FAIL+1))
    fi
  done

  if [ ! -f "$PACK_DIR/README.md" ]; then
    echo "❌ MISSING $PACK_DIR/README.md"
    FAIL=$((FAIL+1))
  else
    echo "✅ $PACK_DIR/README.md present"
    PASS=$((PASS+1))
  fi

  # Explicitly NOT required in the pack: issue/PR templates are owned solely
  # by this repo's own community-health files (.github/ISSUE_TEMPLATE/,
  # root PULL_REQUEST_TEMPLATE.md), never synced from l9-ci-core.
fi

if command -v yamllint &>/dev/null; then
  echo ""
  echo "=== yamllint (distributed labels) ==="
  if yamllint -c .yamllint.yml .github/labels.yml templates/labels.yml; then
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
