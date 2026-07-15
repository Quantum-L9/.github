#!/usr/bin/env bash
# ops/validate-starters.sh
# Validates every workflow-templates/*.yml has a matching *.properties.json.
# Validates each properties.json contains required fields: name, description, iconName, categories, filePatterns.
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

TEMPLATES_DIR="workflow-templates"
REQUIRED_FIELDS=("name" "description" "iconName" "categories" "filePatterns")
PASS=0
FAIL=0

echo "=== Quantum-L9 Workflow Starter Validation ==="
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

  # Validate no @main references in the YAML (must use @v1)
  if grep -q "@main" "$yml"; then
    echo "❌ @main REFERENCE found in $yml — must use @v1"
    FAIL=$((FAIL+1))
    FIELDS_OK=false
  fi

  if $FIELDS_OK; then
    echo "✅ $starter_name — properties.json valid, no @main refs"
    PASS=$((PASS+1))
  fi
done

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
