#!/usr/bin/env bash
# Idempotent label sync for one repository. Creates or updates; never deletes.
#
# Which labels, and whether the repository gets labels at all, is its compiled
# governance plan's answer (ops/compile-repo-governance.js,
# docs/adr/0001-one-governance-brain.md) — the same plan the org-wide sweep
# (.github/workflows/sync-labels-all.yml) and the birth bootstrap
# (.github/workflows/repo-birth-bootstrap.yml) apply. A class that does not
# remote-apply labels is skipped, not labelled.
#
# The plan is compiled by the provenance-checked CLI, so this checkout must be
# clean and its HEAD is the authority revision the plan names.
set -euo pipefail

REPO="${1:-}"
[[ -z "$REPO" ]] && { echo "usage: $0 owner/repo" >&2; exit 2; }
command -v gh >/dev/null || { echo "error: gh CLI required" >&2; exit 1; }
command -v node >/dev/null || { echo "error: node required (ops/compile-repo-governance.js)" >&2; exit 1; }

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Existence of a path on the target's default branch. A 404 is "absent"; any
# other error stops the sync — an unreadable fact must never read as absent,
# which could resolve a wider class than the repository declared.
exists() {
  local out
  if out="$(gh api "repos/$REPO/contents/$1" --silent 2>&1)"; then
    return 0
  fi
  if grep -q "HTTP 404" <<<"$out"; then
    return 1
  fi
  echo "error: cannot probe $REPO:$1 — $out" >&2
  exit 1
}

MARKER_PATH="$(cd "$SRC" && node -e 'console.log(require("./ops/plan-adapter.js").loadAuthority(require("fs")).classes.marker_path)')"

ARGS=(--repo "$REPO" --authority-sha HEAD)
if exists "$MARKER_PATH"; then
  gh api "repos/$REPO/contents/$MARKER_PATH" --jq .content | base64 -d > "$WORK/marker"
  ARGS+=(--marker-file "$WORK/marker")
else
  ARGS+=(--marker-absent)
fi
exists CODEOWNERS && ARGS+=(--has-root-codeowners)
{ exists pyproject.toml || exists requirements.txt; } && ARGS+=(--has-python)
exists package.json && ARGS+=(--has-package-json)

node "$SRC/ops/compile-repo-governance.js" "${ARGS[@]}" > "$WORK/plan.json"

node -e '
const fs = require("fs");
const plan = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
const id = `class ${plan.repo_class.name} (${plan.repo_class.resolved_from}), plan ${plan.digest.value.slice(0, 12)} @ ${plan.authority.sha.slice(0, 12)}`;
if (!plan.remote_apply.labels.enabled) {
  process.stderr.write(`SKIP: ${id} does not remote-apply labels\n`);
  process.exit(0);
}
process.stderr.write(`applying ${plan.remote_apply.labels.items.length} labels: ${id}\n`);
for (const l of plan.remote_apply.labels.items) {
  process.stdout.write([l.name, l.color, l.description].join("\t") + "\n");
}
' "$WORK/plan.json" | while IFS=$'\t' read -r name color desc; do
  [[ -z "$name" ]] && continue
  if gh label create "$name" --color "$color" --description "$desc" --repo "$REPO" 2>/dev/null; then
    echo "created  $name"
  else
    gh label edit "$name" --color "$color" --description "$desc" --repo "$REPO" >/dev/null
    echo "updated  $name"
  fi
done
