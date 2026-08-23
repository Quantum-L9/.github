#!/usr/bin/env bash
# ops/sync-org-files.sh
# Syncs all org-level template files from Quantum-L9/.github/templates/ into a
# consumer repo. Designed to be called FROM the consumer repo (or by a seeding
# script that targets a consumer checkout).
#
# This is the org-side counterpart to the consumer's `sync_ci_from_pack.py`.
# Health files come from templates/. Category l9-ci-pack copies the Core hub
# pack (analysis caller + governance YAMLs + lint callers) from l9-ci-pack/.
# This repo distributes those callers; l9-ci-core executes CI.
#
# Usage (from the org repo root):
#   ops/sync-org-files.sh <consumer-repo-path> [--include-all|--include <category>...]
#
# Categories (default `all` = DEFAULT set; labels + on-org-update are opt-in):
#   codeowners        .github/CODEOWNERS (path-scoped; skip if root CODEOWNERS)
#   dependabot        .github/dependabot.yml (github-actions only)
#   governance        .github/workflows/governance.yml
#   community-health  CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md
#                     (no LICENSE, FUNDING.yml, SUPPORT.md)
#   issue-templates   numbered chooser + ci-failure + seed-ci-failure +
#                     gov-violation + config.yml (no bug_report / feature_request)
#   pr-templates      pull_request_template.md + PULL_REQUEST_TEMPLATE/agent.md
#   l9-ci-pack        analysis + Node lint + governance YAMLs + Biome contract;
#                     Python lint only when pyproject.toml or requirements.txt
#   labels            OPT-IN — org sync-labels-all.yml already fans labels
#   on-org-update     OPT-IN — do not seed until sync_ci_from_pack.py is real
#
# Default (no --include flag): DEFAULT_CATEGORIES (not labels / on-org-update).
# Actions twin: .github/workflows/seed-governance.yml (ops/build-seed-payload.js).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$ORG_ROOT/templates"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--include-all|--include <category>...]" >&2
  echo "Default: codeowners dependabot governance community-health issue-templates pr-templates l9-ci-pack" >&2
  echo "Opt-in:  labels on-org-update" >&2
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

CONSUMER_ROOT="$1"
shift

if [[ ! -d "$CONSUMER_ROOT" ]]; then
  echo "❌ ERROR: consumer repo path does not exist: $CONSUMER_ROOT" >&2
  exit 1
fi

# Parse categories
DEFAULT_CATEGORIES=(codeowners dependabot governance community-health issue-templates pr-templates l9-ci-pack)
ALL_CATEGORIES=("${DEFAULT_CATEGORIES[@]}" labels on-org-update)
PACK_DIR="$ORG_ROOT/l9-ci-pack"
CATEGORIES=()
HAS_PYTHON=0
if [[ -f "$CONSUMER_ROOT/pyproject.toml" || -f "$CONSUMER_ROOT/requirements.txt" ]]; then
  HAS_PYTHON=1
fi

if [[ $# -eq 0 ]] || [[ "${1:-}" == "--include-all" ]]; then
  CATEGORIES=("${DEFAULT_CATEGORIES[@]}")
else
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --include)
        shift
        while [[ $# -gt 0 && "$1" != --* ]]; do
          CATEGORIES+=("$1")
          shift
        done
        ;;
      *)
        echo "❌ ERROR: unknown argument: $1" >&2
        usage
        ;;
    esac
  done
fi

if [[ ${#CATEGORIES[@]} -eq 0 ]]; then
  echo "❌ ERROR: no categories specified." >&2
  usage
fi

sync_file() {
  local src="$1"
  local dest="$2"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  rel="${dest#"$CONSUMER_ROOT"/}"
  echo "  ✓ $rel"
}

echo "=== Syncing org files to $(basename "$CONSUMER_ROOT") ==="
echo "Categories: ${CATEGORIES[*]}"
echo ""

for cat in "${CATEGORIES[@]}"; do
  case "$cat" in
    codeowners)
      echo "── CODEOWNERS ──"
      sync_file "$TEMPLATES_DIR/CODEOWNERS.repo" "$CONSUMER_ROOT/.github/CODEOWNERS"
      ;;
    dependabot)
      echo "── dependabot.yml ──"
      sync_file "$TEMPLATES_DIR/dependabot.yml" "$CONSUMER_ROOT/.github/dependabot.yml"
      ;;
    governance)
      echo "── governance caller ──"
      sync_file "$TEMPLATES_DIR/governance-caller.yml" "$CONSUMER_ROOT/.github/workflows/governance.yml"
      ;;
    labels)
      echo "── labels.yml ──"
      sync_file "$TEMPLATES_DIR/labels.yml" "$CONSUMER_ROOT/.github/labels.yml"
      ;;
    community-health)
      echo "── community health ──"
      for f in CODE_OF_CONDUCT.md CONTRIBUTING.md SECURITY.md; do
        if [[ -f "$TEMPLATES_DIR/community-health/$f" ]]; then
          sync_file "$TEMPLATES_DIR/community-health/$f" "$CONSUMER_ROOT/$f"
        fi
      done
      ;;
    issue-templates)
      echo "── issue templates ──"
      mkdir -p "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE"
      for f in "$TEMPLATES_DIR/issue-templates/"*; do
        [[ -f "$f" ]] || continue
        name="$(basename "$f")"
        case "$name" in
          bug_report.yml|feature_request.yml) continue ;;
        esac
        sync_file "$f" "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE/$name"
      done
      ;;
    pr-templates)
      echo "── PR template ──"
      sync_file "$TEMPLATES_DIR/pr-templates/pull_request_template.md" \
        "$CONSUMER_ROOT/.github/pull_request_template.md"
      if [[ -f "$TEMPLATES_DIR/pr-templates/agent.md" ]]; then
        sync_file "$TEMPLATES_DIR/pr-templates/agent.md" \
          "$CONSUMER_ROOT/.github/PULL_REQUEST_TEMPLATE/agent.md"
      fi
      ;;
    on-org-update)
      echo "── on-org-update receiver ──"
      sync_file "$TEMPLATES_DIR/on-org-update.yml" \
        "$CONSUMER_ROOT/.github/workflows/on-org-update.yml"
      ;;
    l9-ci-pack)
      echo "── l9-ci-pack (Core hub callers + Biome contract) ──"
      if [[ -d "$PACK_DIR/workflows" ]]; then
        for f in "$PACK_DIR/workflows/"*; do
          [[ -f "$f" ]] || continue
          name="$(basename "$f")"
          if [[ "$name" == "l9-lint-test.yml" && "$HAS_PYTHON" -ne 1 ]]; then
            echo "  skip $name (no Python manifest)"
            continue
          fi
          sync_file "$f" "$CONSUMER_ROOT/.github/workflows/$name"
        done
      fi
      if [[ -d "$PACK_DIR/governance" ]]; then
        for f in "$PACK_DIR/governance/"*; do
          [[ -f "$f" ]] || continue
          if [[ "$f" == *.yaml ]]; then
            if ! python3 -c 'import json,sys; json.loads(sys.stdin.read())' < "$f"; then
              echo "❌ ERROR: $f is not JSON-in-YAML" >&2
              exit 1
            fi
          fi
          sync_file "$f" "$CONSUMER_ROOT/.github/governance/$(basename "$f")"
        done
      fi
      # Formatter contract: missing-only, matching stamp.sh / Actions seeder.
      # Never overwrite a consumer biome.json or .editorconfig.
      for pair in \
        "biome.json:biome.json" \
        ".biomeignore:.biomeignore" \
        ".editorconfig:.editorconfig" \
        ".vscode/extensions.json:.vscode/extensions.json"
      do
        src="$PACK_DIR/${pair%%:*}"
        dest="$CONSUMER_ROOT/${pair##*:}"
        if [[ ! -f "$src" ]]; then
          continue
        fi
        if [[ -e "$dest" ]]; then
          echo "  keep existing ${pair##*:}"
          continue
        fi
        sync_file "$src" "$dest"
      done
      ;;
    *)
      echo "⚠️  WARNING: unknown category '$cat', skipping." >&2
      ;;
  esac
  echo ""
done

echo "✅ Sync complete."
