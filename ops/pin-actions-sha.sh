#!/usr/bin/env bash
# ops/pin-actions-sha.sh
# SHA-pins all GitHub Actions 'uses:' references in workflow-templates/ and thin caller YAMLs.
# Uses ratchet (preferred) with fallback to pin-github-action (pip).
# Run from the root of the Quantum-L9/.github repo.
set -euo pipefail

echo "=== Quantum-L9 GitHub Actions SHA Pinner ==="
echo ""

WORKFLOW_DIRS=(
  "workflow-templates"
  "Cursor-Governance/.github/workflows"
  "l9-assurance/.github/workflows"
)

# 1. Check for ratchet (preferred)
if command -v ratchet &>/dev/null; then
  echo "✅ Using ratchet for SHA pinning"
  PINNER="ratchet"
elif command -v pin-github-action &>/dev/null; then
  echo "⚠️  ratchet not found. Falling back to pin-github-action (pip)"
  PINNER="pin-github-action"
else
  echo "Neither ratchet nor pin-github-action found. Attempting to install..."
  # Attempt ratchet install via Go
  if command -v go &>/dev/null; then
    echo "Installing ratchet via go install..."
    go install github.com/sethvargo/ratchet@latest
    PINNER="ratchet"
  else
    echo "Go not available. Installing pin-github-action via pip..."
    pip install pin-github-action --quiet
    PINNER="pin-github-action"
  fi
fi

echo ""

# 2. Pin each directory
for dir in "${WORKFLOW_DIRS[@]}"; do
  if [ ! -d "$dir" ]; then
    echo "⚠️  Directory not found: $dir — skipping"
    continue
  fi

  echo "Pinning YAMLs in: $dir"
  for yml_file in "$dir"/*.yml "$dir"/*.yaml; do
    [ -f "$yml_file" ] || continue

    echo "  → $yml_file"
    if [ "$PINNER" = "ratchet" ]; then
      ratchet pin "$yml_file"
    else
      pin-github-action "$yml_file"
    fi
  done
  echo ""
done

echo "✅ SHA pinning complete."
echo "Review changes with: git diff workflow-templates/ Cursor-Governance/.github/ l9-assurance/.github/"
echo "Commit with: git commit -am 'chore(deps): pin GitHub Actions to SHAs'"
