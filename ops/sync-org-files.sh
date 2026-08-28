#!/usr/bin/env bash
# ops/sync-org-files.sh
# Syncs all org-level template files from Quantum-L9/.github/templates/ into a
# consumer repo. Designed to be called FROM the consumer repo (or by a seeding
# script that targets a consumer checkout).
#
# Org-side seeding of community-health and ownership files. CI is NOT seeded
# from this repository (see l9-ci-pack/README.md).
# Health files come from templates/. The l9-ci-pack and on-org-update
# categories are RETIRED and fail closed.
# This repo distributes those callers; l9-ci-core executes CI.
#
# Usage (from the org repo root):
#   ops/sync-org-files.sh <consumer-repo-path> [--include-all|--include <category>...]
#
# Categories (default `all` = DEFAULT set; labels is opt-in):
#   codeowners        .github/CODEOWNERS (path-scoped; skip if root CODEOWNERS)
#   dependabot        .github/dependabot.yml (github-actions only)
#   governance        .github/workflows/governance.yml
#   community-health  CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md
#                     (no LICENSE, FUNDING.yml, SUPPORT.md); advisory links
#                     are rewritten to the consumer's origin remote
#   issue-templates   numbered chooser + ci-failure + seed-ci-failure +
#                     gov-violation + config.yml (no bug_report / feature_request)
#   pr-templates      pull_request_template.md + PULL_REQUEST_TEMPLATE/agent.md
#   l9-ci-pack        RETIRED — CI is never distributed from this repository;
#                     Python lint only when pyproject.toml or requirements.txt
#   labels            OPT-IN — org sync-labels-all.yml already fans labels
#   on-org-update     OPT-IN — legacy receiver; the pack it pulled is retired
#
# Default (no --include flag): DEFAULT_CATEGORIES (not labels).
# Actions twin: .github/workflows/seed-governance.yml (ops/build-seed-payload.js).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$ORG_ROOT/templates"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--include-all|--include <category>...]" >&2
  echo "Default: codeowners dependabot governance community-health issue-templates pr-templates" >&2
  echo "Opt-in:  labels" >&2
  echo "Retired: l9-ci-pack on-org-update (fail closed)" >&2
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
DEFAULT_CATEGORIES=(codeowners dependabot governance community-health issue-templates pr-templates)
ALL_CATEGORIES=("${DEFAULT_CATEGORIES[@]}" labels)
RETIRED_CATEGORIES=(l9-ci-pack on-org-update)
PACK_DIR="$ORG_ROOT/l9-ci-pack"
CATEGORIES=()
HAS_PYTHON=0
if [[ -f "$CONSUMER_ROOT/pyproject.toml" || -f "$CONSUMER_ROOT/requirements.txt" ]]; then
  HAS_PYTHON=1
fi

# GitHub reads .github/CODEOWNERS in preference to a root CODEOWNERS, so seeding
# the path-scoped template over an existing root file silently drops the
# consumer's ownership rules for every path the template does not list.
# Mirrors buildSeedPayload({ hasRootCodeowners }).
HAS_ROOT_CODEOWNERS=0
if [[ -f "$CONSUMER_ROOT/CODEOWNERS" ]]; then
  HAS_ROOT_CODEOWNERS=1
fi

# owner/name of the consumer, used to point advisory links at the consumer
# rather than at this org repo. Mirrors applyRepoPlaceholders(text, repository).
CONSUMER_REPO=""
if remote_url="$(git -C "$CONSUMER_ROOT" remote get-url origin 2>/dev/null)"; then
  CONSUMER_REPO="$(printf '%s' "$remote_url" \
    | sed -E 's#^git@github\.com:#https://github.com/#; s#^https://[^/]*/##; s#\.git$##')"
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

# Same copy, with this org repo's advisory URLs rewritten to the consumer's, so
# a synced SECURITY.md / issue-template config.yml does not route vulnerability
# reports to Quantum-L9/.github while claiming to target the consumer.
ADVISORY_INBOX_STOCK="https://github.com/Quantum-L9/.github/security/advisories/new"
ADVISORY_POLICY_STOCK="https://github.com/Quantum-L9/.github/security/policy"

sync_file_with_placeholders() {
  local src="$1"
  local dest="$2"
  if [[ -z "$CONSUMER_REPO" ]]; then
    sync_file "$src" "$dest"
    return
  fi
  local advisory="https://github.com/${CONSUMER_REPO}/security/advisories/new"
  mkdir -p "$(dirname "$dest")"
  ADVISORY_INBOX_STOCK="$ADVISORY_INBOX_STOCK" \
  ADVISORY_POLICY_STOCK="$ADVISORY_POLICY_STOCK" \
  ADVISORY_NEW="$advisory" \
  python3 -c 'import os,sys
src, dest = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as fh:
    text = fh.read()
new = os.environ["ADVISORY_NEW"]
for stock in (os.environ["ADVISORY_INBOX_STOCK"], os.environ["ADVISORY_POLICY_STOCK"]):
    text = text.replace(stock, new)
with open(dest, "w", encoding="utf-8") as fh:
    fh.write(text)' "$src" "$dest"
  rel="${dest#"$CONSUMER_ROOT"/}"
  echo "  ✓ $rel (advisory links → $CONSUMER_REPO)"
}

echo "=== Syncing org files to $(basename "$CONSUMER_ROOT") ==="
echo "Categories: ${CATEGORIES[*]}"
echo ""

for cat in "${CATEGORIES[@]}"; do
  case "$cat" in
    codeowners)
      echo "── CODEOWNERS ──"
      if [[ "$HAS_ROOT_CODEOWNERS" -eq 1 ]]; then
        echo "  skip .github/CODEOWNERS (root CODEOWNERS present; it stays authoritative)"
      else
        sync_file "$TEMPLATES_DIR/CODEOWNERS.repo" "$CONSUMER_ROOT/.github/CODEOWNERS"
      fi
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
          sync_file_with_placeholders "$TEMPLATES_DIR/community-health/$f" "$CONSUMER_ROOT/$f"
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
        sync_file_with_placeholders "$f" "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE/$name"
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
      # RETIRED with l9-ci-pack: this receiver's only action was running
      # scripts/sync_ci_from_pack.py, the consumer half of the same copy loop.
      echo "❌ ERROR: seed category 'on-org-update' is RETIRED." >&2
      echo "   It existed to run scripts/sync_ci_from_pack.py, which is gone." >&2
      exit 1
      ;;
    l9-ci-pack)
      # RETIRED. This category physically copied Core callers and a governance
      # pack into consumer repositories. Quantum-L9/l9-ci-core now declares
      # "CI distribution from Quantum-L9/.github" prohibited in
      # .l9/org-runtime-contract.yaml, and both governed repo classes FORBID
      # every destination it wrote. Canonical CI is
      # l9-ci-core/.github/workflows/org-ci.yml via an organization
      # required-workflow ruleset. Fail closed: a silent skip here would read
      # as "synced, nothing to do".
      echo "❌ ERROR: seed category 'l9-ci-pack' is RETIRED." >&2
      echo "   Quantum-L9/.github no longer distributes CI." >&2
      echo "   Canonical CI: Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml" >&2
      echo "   enforced by a GitHub organization required-workflow ruleset." >&2
      exit 1
      ;;
    *)
      echo "⚠️  WARNING: unknown category '$cat', skipping." >&2
      ;;
  esac
  echo ""
done

echo "✅ Sync complete."
