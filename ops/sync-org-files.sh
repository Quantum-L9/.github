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
# Categories:
#   codeowners        .github/CODEOWNERS
#   dependabot        .github/dependabot.yml
#   governance        .github/workflows/governance.yml
#   labels            .github/labels.yml
#   community-health  CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md, SUPPORT.md, LICENSE, .github/FUNDING.yml
#   issue-templates   .github/ISSUE_TEMPLATE/*
#   pr-templates      .github/pull_request_template.md
#   on-org-update     .github/workflows/on-org-update.yml
#   l9-ci-pack        .github/workflows/l9-analysis.yml + lint callers +
#                     .github/governance/* + locked Biome contract (biome.json,
#                     .biomeignore, .editorconfig, .vscode/extensions.json)
#
# Default (no --include flag): seeds all categories.
# Actions twin: .github/workflows/seed-governance.yml (ops/build-seed-payload.js).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$ORG_ROOT/templates"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--include-all|--include <category>...]" >&2
  echo "Categories: codeowners dependabot governance labels community-health issue-templates pr-templates on-org-update l9-ci-pack" >&2
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
ALL_CATEGORIES=(codeowners dependabot governance labels community-health issue-templates pr-templates on-org-update l9-ci-pack)
PACK_DIR="$ORG_ROOT/l9-ci-pack"
CATEGORIES=()

if [[ $# -eq 0 ]] || [[ "${1:-}" == "--include-all" ]]; then
  CATEGORIES=("${ALL_CATEGORIES[@]}")
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
      for f in CODE_OF_CONDUCT.md CONTRIBUTING.md SECURITY.md SUPPORT.md LICENSE; do
        if [[ -f "$TEMPLATES_DIR/community-health/$f" ]]; then
          sync_file "$TEMPLATES_DIR/community-health/$f" "$CONSUMER_ROOT/$f"
        fi
      done
      # FUNDING.yml goes to .github/ (GitHub reads it from there for non-org repos)
      if [[ -f "$TEMPLATES_DIR/community-health/FUNDING.yml" ]]; then
        sync_file "$TEMPLATES_DIR/community-health/FUNDING.yml" "$CONSUMER_ROOT/.github/FUNDING.yml"
      fi
      ;;
    issue-templates)
      echo "── issue templates ──"
      mkdir -p "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE"
      for f in "$TEMPLATES_DIR/issue-templates/"*; do
        [[ -f "$f" ]] || continue
        sync_file "$f" "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE/$(basename "$f")"
      done
      ;;
    pr-templates)
      echo "── PR template ──"
      sync_file "$TEMPLATES_DIR/pr-templates/pull_request_template.md" \
        "$CONSUMER_ROOT/.github/pull_request_template.md"
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
          sync_file "$f" "$CONSUMER_ROOT/.github/workflows/$(basename "$f")"
        done
      fi
      if [[ -d "$PACK_DIR/governance" ]]; then
        for f in "$PACK_DIR/governance/"*; do
          [[ -f "$f" ]] || continue
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
