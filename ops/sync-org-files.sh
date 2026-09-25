#!/usr/bin/env bash
# ops/sync-org-files.sh
# Syncs a consumer checkout with its compiled governance plan: the org-level
# files its repo class authorizes, from Quantum-L9/.github/templates/.
#
# This is a plan adapter, not a second policy owner. The file set comes from
# ops/compile-repo-governance.js (via ops/sync-org-files.js) — the same plan
# auto-seed-new-repo.yml and seed-governance.yml apply — so the consumer's
# class, INHERIT, FORBID, and mandatory waivers all hold here too. See
# docs/adr/0001-one-governance-brain.md.
#
# Writes are missing-only, as the plan's write mode says: an existing file is
# never overwritten (a stock replaceable caller is the one exception the plan
# can carry). CI is never synced from this repository.
#
# Usage (from anywhere; paths resolve against this org repo):
#   ops/sync-org-files.sh <consumer-repo-path> [--repo owner/name]
#                         [--include-all | --include <category>...]
#
# --repo       target identity; defaults to the consumer's origin remote.
#              A plan must name its target, so with neither the sync refuses.
# --include    narrow the plan to these capabilities. A category the
#              consumer's class does not authorize is refused, and the retired
#              l9-ci-pack / on-org-update categories fail closed.
# (none) or --include-all: the whole plan.
#
# Actions twins: .github/workflows/seed-governance.yml, auto-seed-new-repo.yml.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "Usage: $0 <consumer-repo-path> [--repo owner/name] [--include-all|--include <category>...]" >&2
  echo "Categories narrow the consumer's compiled governance plan; none = the whole plan." >&2
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

CONSUMER_REPO=""
CATEGORIES=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || usage
      CONSUMER_REPO="$2"
      shift 2
      ;;
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
    *)
      echo "❌ ERROR: unknown argument: $1" >&2
      usage
      ;;
  esac
done

# owner/name of the consumer from its origin remote, unless given.
if [[ -z "$CONSUMER_REPO" ]] && remote_url="$(git -C "$CONSUMER_ROOT" remote get-url origin 2>/dev/null)"; then
  CONSUMER_REPO="$(printf '%s' "$remote_url" \
    | sed -E 's#^git@github\.com:#https://github.com/#; s#^https://[^/]*/##; s#\.git$##')"
fi

echo "=== Syncing governance plan to $(basename "$CONSUMER_ROOT") ==="
if [[ ${#CATEGORIES[@]} -gt 0 ]]; then
  echo "Categories: ${CATEGORIES[*]} (narrowing the plan)"
fi

node "$SCRIPT_DIR/sync-org-files.js" "$CONSUMER_ROOT" "$CONSUMER_REPO" "${CATEGORIES[@]}"

echo "✅ Sync complete."
