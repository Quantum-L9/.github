#!/usr/bin/env bash
# ops/sync-org-files.sh
# Seeds org-level files into a local consumer checkout. Thin shell entrypoint
# over the one policy path: ops/build-seed-payload.js (planConsumerSeed).
#
# The consumer's class is resolved from `.l9/org-birth-profile.yaml` against
# policies/repo-classes.yml exactly as the Actions seeders do (marker >
# override > default; a malformed or unknown explicit marker fails closed).
# INHERIT destinations are never copied, a FORBID destination refuses the
# run, and MATERIALIZE is missing-only: an existing consumer file is kept
# byte-for-byte and reported. CI is NOT seeded from this repository.
# The on-org-update / l9-ci-pack categories are RETIRED and fail closed.
# Canonical CI is l9-ci-core.
#
# Usage (from anywhere; the org root is resolved from this script):
#   ops/sync-org-files.sh <consumer-repo-path> [--include-all|--include <category>...] [--dry-run]
#
# Categories (`all` / no flag = the consumer's class decides; labels is opt-in
# for the default class and materialized for non_constellation_python):
#   codeowners        .github/CODEOWNERS (path-scoped; skip if root CODEOWNERS)
#   dependabot        .github/dependabot.yml (github-actions only)
#   governance        .github/workflows/governance.yml (FORBID for governed classes)
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
#   labels            opt-in for `default` — org sync-labels-all.yml fans labels
#   on-org-update     RETIRED — legacy receiver; fails closed
#
# An explicit --include that names a category the consumer's class forbids is
# refused with the class and path named; nothing is written.
# Actions twin: .github/workflows/seed-governance.yml (same module).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--include-all|--include <category>...] [--dry-run]" >&2
  echo "Default: the consumer's repo class decides (policies/repo-classes.yml)" >&2
  echo "Categories: codeowners dependabot governance community-health issue-templates pr-templates labels" >&2
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

# Policy, payload and missing-only selection live in Node. Without it the
# shell cannot honor the class contract, so it refuses rather than copying.
if ! command -v node >/dev/null 2>&1; then
  echo "❌ ERROR: node is required: ops/build-seed-payload.js resolves the consumer's repo class." >&2
  echo "   Refusing to copy files without class resolution (FORBID / INHERIT / missing-only)." >&2
  exit 1
fi

RETIRED_CATEGORIES=(on-org-update l9-ci-pack)
CATEGORIES=()
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-all)
      shift
      ;;
    --include)
      shift
      while [[ $# -gt 0 && "$1" != --* ]]; do
        CATEGORIES+=("$1")
        shift
      done
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    *)
      echo "❌ ERROR: unknown argument: $1" >&2
      usage
      ;;
  esac
done

for cat in "${CATEGORIES[@]+"${CATEGORIES[@]}"}"; do
  for retired in "${RETIRED_CATEGORIES[@]}"; do
    if [[ "$cat" == "$retired" ]]; then
      # RETIRED. An explicit include must not report a completed sync that
      # copied nothing. CI is Quantum-L9/l9-ci-core, not a pack copied here.
      echo "❌ ERROR: seed category '$cat' is RETIRED." >&2
      echo "   CI is Quantum-L9/l9-ci-core, not a file copied from this repo." >&2
      exit 1
    fi
  done
done

# owner/name of the consumer: names the repo for class overrides and points
# advisory links at the consumer rather than at this org repo.
CONSUMER_REPO=""
if remote_url="$(git -C "$CONSUMER_ROOT" remote get-url origin 2>/dev/null)"; then
  CONSUMER_REPO="$(printf '%s' "$remote_url" \
    | sed -E 's#^git@github\.com:#https://github.com/#; s#^https://[^/]*/##; s#\.git$##')"
fi

if [[ ${#CATEGORIES[@]} -eq 0 ]]; then
  CATEGORY_ARG="all"
else
  CATEGORY_ARG="$(IFS=,; printf '%s' "${CATEGORIES[*]}")"
fi

echo "=== Syncing org files to $(basename "$CONSUMER_ROOT") ==="
echo "Categories: ${CATEGORY_ARG}"
[[ -n "$CONSUMER_REPO" ]] && echo "Repository: ${CONSUMER_REPO}"
echo ""

NODE_ARGS=(--consumer "$CONSUMER_ROOT" --repository "$CONSUMER_REPO" --categories "$CATEGORY_ARG")
if [[ "$DRY_RUN" -eq 1 ]]; then
  NODE_ARGS+=(--dry-run)
fi

node "$ORG_ROOT/ops/build-seed-payload.js" "${NODE_ARGS[@]}"

echo ""
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "✅ Dry run complete (nothing written)."
else
  echo "✅ Sync complete."
fi
