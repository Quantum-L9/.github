#!/usr/bin/env bash
# Idempotent label sync from .github/labels.yml. Creates or updates; never deletes.
#
# ops/label-taxonomy.js is the shared parser: this CLI, the org-wide sweep
# (.github/workflows/sync-labels-all.yml), and the targeted birth bootstrap
# (.github/workflows/repo-birth-bootstrap.yml) all read the taxonomy through
# it, so a birth and a sweep can never disagree about what the labels are.
set -euo pipefail

REPO="${1:-}"
[[ -z "$REPO" ]] && { echo "usage: $0 owner/repo" >&2; exit 2; }
command -v gh >/dev/null || { echo "error: gh CLI required" >&2; exit 1; }
command -v node >/dev/null || { echo "error: node required (ops/label-taxonomy.js)" >&2; exit 1; }

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FILE="$SRC/.github/labels.yml"

node -e '
const fs = require("fs");
const { parseLabels } = require(process.argv[1] + "/ops/label-taxonomy.js");
for (const l of parseLabels(fs.readFileSync(process.argv[2], "utf8"))) {
  process.stdout.write([l.name, l.color, l.description].join("\t") + "\n");
}
' "$SRC" "$FILE" | while IFS=$'\t' read -r name color desc; do
  [[ -z "$name" ]] && continue
  if gh label create "$name" --color "$color" --description "$desc" --repo "$REPO" 2>/dev/null; then
    echo "created  $name"
  else
    gh label edit "$name" --color "$color" --description "$desc" --repo "$REPO" >/dev/null
    echo "updated  $name"
  fi
done
