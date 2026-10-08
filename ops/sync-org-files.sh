#!/usr/bin/env bash
# ops/sync-org-files.sh
# Syncs org-level files into a consumer repo. Inheritable files are read from
# the canonical copies GitHub serves (repo root and .github/). Consumer-only
# CODEOWNERS and the governance caller live in policies/.
#
# Org-side seeding of community-health and ownership files. CI is NOT seeded
# from this repository. The on-org-update category is RETIRED and fails closed.
# Canonical CI is l9-ci-core.
#
# Usage (from the org repo root):
#   ops/sync-org-files.sh <consumer-repo-path> [--include-all|--include <category>...]
#
# Categories (default `all` = DEFAULT set; labels is opt-in):
#   codeowners        .github/CODEOWNERS (path-scoped; skip if root CODEOWNERS)
#   dependabot        .github/dependabot.yml (github-actions only)
#   governance        .github/workflows/governance.yml
#   community-health  SECURITY.md only; advisory links are rewritten to the
#                     consumer's origin remote. CODE_OF_CONDUCT.md,
#                     CONTRIBUTING.md, SUPPORT.md, FUNDING.yml and
#                     VULNERABILITY_REPORT.yml are INHERIT (GitHub serves
#                     them org-wide) and are never copied. No LICENSE.
#   issue-templates   numbered chooser + ci-failure +
#                     gov-violation + config.yml
#                     (no bug_report / feature_request / EXAMPLE.md)
#   pr-templates      .github/pull_request_template.md (the file make pr fills)
#                     + .github/PULL_REQUEST_TEMPLATE/release.md
#   labels            OPT-IN — org sync-labels-all.yml already fans labels
#   on-org-update     RETIRED — legacy receiver; fails closed
#
# Default (no --include flag): DEFAULT_CATEGORIES (not labels).
# Actions twin: .github/workflows/seed-governance.yml (ops/build-seed-payload.js).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
POLICIES_DIR="$ORG_ROOT/policies"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--include-all|--include <category>...]" >&2
  echo "Default: codeowners dependabot governance community-health issue-templates pr-templates" >&2
  echo "Opt-in:  labels" >&2
  echo "Retired: on-org-update, l9-ci-pack (fail closed)" >&2
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
RETIRED_CATEGORIES=(on-org-update l9-ci-pack)
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
        sync_file "$POLICIES_DIR/CODEOWNERS" "$CONSUMER_ROOT/.github/CODEOWNERS"
      fi
      ;;
    dependabot)
      echo "── dependabot.yml ──"
      sync_file ".github/dependabot.yml" "$CONSUMER_ROOT/.github/dependabot.yml"
      ;;
    governance)
      echo "── governance caller ──"
      sync_file "$POLICIES_DIR/governance-caller.yml" "$CONSUMER_ROOT/.github/workflows/governance.yml"
      ;;
    labels)
      echo "── labels.yml ──"
      sync_file ".github/labels.yml" "$CONSUMER_ROOT/.github/labels.yml"
      ;;
    community-health)
      # SECURITY.md is the one community-health file with consumer-specific
      # content. CODE_OF_CONDUCT.md / CONTRIBUTING.md / SUPPORT.md are INHERIT
      # and must not be copied. Mirrors COMMUNITY_HEALTH_MATERIALIZED.
      echo "── community health ──"
      if [[ -f SECURITY.md ]]; then
        sync_file_with_placeholders SECURITY.md "$CONSUMER_ROOT/SECURITY.md"
      fi
      ;;
    issue-templates)
      echo "── issue templates ──"
      mkdir -p "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE"
      for f in .github/ISSUE_TEMPLATE/*; do
        [[ -f "$f" ]] || continue
        name="$(basename "$f")"
        case "$name" in
          bug_report.yml|feature_request.yml|EXAMPLE.md) continue ;;
        esac
        sync_file_with_placeholders "$f" "$CONSUMER_ROOT/.github/ISSUE_TEMPLATE/$name"
      done
      ;;
    pr-templates)
      # Named, never a directory copy: a template added under
      # .github/PULL_REQUEST_TEMPLATE/ is not distributed until it is listed
      # here. Mirrors PR_TEMPLATES_MATERIALIZED.
      echo "── PR templates ──"
      for f in .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE/release.md; do
        sync_file "$f" "$CONSUMER_ROOT/$f"
      done
      ;;
    on-org-update)
      # RETIRED. This receiver's only action was running
      # scripts/sync_ci_from_pack.py, the consumer half of the old copy loop.
      echo "❌ ERROR: seed category 'on-org-update' is RETIRED." >&2
      echo "   It existed to run scripts/sync_ci_from_pack.py, which is gone." >&2
      exit 1
      ;;
    l9-ci-pack)
      # RETIRED. The pack files are gone. An explicit include must not
      # report a completed sync that copied nothing.
      echo "❌ ERROR: seed category 'l9-ci-pack' is RETIRED." >&2
      echo "   CI is Quantum-L9/l9-ci-core, not a pack copied from this repo." >&2
      exit 1
      ;;
    *)
      echo "⚠️  WARNING: unknown category '$cat', skipping." >&2
      ;;
  esac
  echo ""
done

echo "✅ Sync complete."
