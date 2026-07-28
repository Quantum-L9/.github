#!/usr/bin/env bash
# Idempotent bootstrap for a Quantum-L9 repo. Replaces manual clone-based setup.
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

mkdir -p .github
for f in pull_request_template.md CODEOWNERS SECURITY.md CONTRIBUTING.md; do
  if [[ -f ".github/$f" || -f "$f" ]]; then
    echo "skip $f (local override present)"
    continue
  fi
  echo "using org default for $f (no local copy needed — inherited from Quantum-L9/.github)"
done

echo "bootstrap complete. Org defaults are inherited automatically; no files were duplicated."
