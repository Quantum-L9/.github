#!/usr/bin/env bash
# Preflight: verify assumptions BEFORE seeding. Read-only, safe to run anytime.
set -euo pipefail
ORG=Quantum-L9
# gh may colorize JSON output (ANSI escapes) when a terminal/clicolor is forced,
# which silently breaks every grep-based parse below. Disable color and strip
# any residual escapes defensively.
export GH_FORCE_TTY=0 CLICOLOR=0 CLICOLOR_FORCE=0 NO_COLOR=1
strip_ansi() { sed -e 's/\x1b\[[0-9;]*m//g'; }
command -v gh >/dev/null || { echo "gh CLI required" >&2; exit 1; }

echo "== 1. CODEOWNERS team slugs must resolve =="
mapfile -t SLUGS < <(grep -oE '@'"$ORG"'/[a-z0-9-]+' .github/CODEOWNERS | sed "s|@$ORG/||" | sort -u)
REAL=$(gh api "orgs/$ORG/teams" --paginate --jq '.[].slug' 2>/dev/null || true)
[[ -z "$REAL" ]] && REAL="__no_team_read__"  # empty list and read-denied are both unverifiable
for s in "${SLUGS[@]}"; do
  if [[ "$REAL" == "__no_team_read__" ]]; then echo "  ?  $s (cannot read teams — need admin:org)"
  elif grep -qx "$s" <<<"$REAL"; then echo "  OK $s"
  else echo "  !! $s DOES NOT EXIST — rule will be silently inert"; fi
done

echo
echo "== 2. .github repo must be public (or nothing inherits) =="
gh api "repos/$ORG/.github" --jq 'if .private then "  !! PRIVATE — inheritance is OFF" else "  OK public" end'

echo
echo "== 3. Which repos already inherit vs need seeding =="
gh repo list "$ORG" --limit 200 --json name,isArchived,isFork \
  --jq '.[] | select(.isArchived==false and .isFork==false and .name!=".github") | .name' \
| while read -r r; do
    co=$(gh api "repos/$ORG/$r/contents/.github/CODEOWNERS" --silent 2>/dev/null && echo yes || echo no)
    wf=$(gh api "repos/$ORG/$r/contents/.github/workflows/governance.yml" --silent 2>/dev/null && echo yes || echo no)
    printf '  %-40s CODEOWNERS=%-3s caller=%s\n' "$r" "$co" "$wf"
  done

echo
echo "== 4. Repos with LOCAL overrides that block inheritance =="
gh repo list "$ORG" --limit 200 --json name --jq '.[].name' | while read -r r; do
  for p in .github/pull_request_template.md PULL_REQUEST_TEMPLATE.md SECURITY.md .github/ISSUE_TEMPLATE; do
    if gh api "repos/$ORG/$r/contents/$p" --silent 2>/dev/null; then
      echo "  $r has local $p (org default IGNORED)"
    fi
  done
done || true  # probe misses must not abort the script under set -e

echo
echo "== 5. Actions policy must permit cross-repo reusable workflows =="
echo "   (a caller referencing Quantum-L9/.github@v1 fails before any step if blocked)"
ORG_POL=$(gh api "orgs/$ORG/actions/permissions" 2>/dev/null | strip_ansi || echo '{}')
echo "   org policy: $(echo "$ORG_POL" | tr -d '\n' | cut -c1-160)"
ORG_AA=$(echo "$ORG_POL" | tr -d ' \n' | grep -o '"allowed_actions":"[a-z_]*"' | cut -d'"' -f4 || true)
case "$ORG_AA" in
  all)      echo "   OK org allows all actions and reusable workflows" ;;
  local_only) echo "   !! org is LOCAL_ONLY — every cross-repo caller will fail org-wide" ;;
  selected) echo "   ?  org uses an allow-list — confirm Quantum-L9/* is included:"
            gh api "orgs/$ORG/actions/permissions/selected-actions" 2>/dev/null | tr -d '\n' | sed 's/^/      /' ; echo ;;
  *)        echo "   ?  cannot read org policy (need admin:org) — check repo-level below" ;;
esac

gh repo list "$ORG" --limit 200 --json name,isArchived,isFork \
  --jq '.[] | select(.isArchived==false and .isFork==false and .name!=".github") | .name' \
| while read -r r; do
    P=$(gh api "repos/$ORG/$r/actions/permissions" 2>/dev/null | strip_ansi | tr -d ' \n' || echo '{}')
    EN=$(echo "$P" | grep -o '"enabled":[a-z]*' | cut -d: -f2 || true)
    AA=$(echo "$P" | grep -o '"allowed_actions":"[a-z_]*"' | cut -d'"' -f4 || true)
    case "$EN:$AA" in
      true:all)        printf '  OK %-40s actions=on allowed=all\n' "$r" ;;
      true:local_only) printf '  !! %-40s LOCAL_ONLY — caller will fail\n' "$r" ;;
      true:selected)   printf '  ?  %-40s allow-list — verify Quantum-L9/* included\n' "$r" ;;
      false:*)         printf '  !! %-40s ACTIONS DISABLED — caller will never run\n' "$r" ;;
      true:)           printf '  OK %-40s actions=on (inherits org policy)\n' "$r" ;;
      *)               printf '  ?  %-40s unreadable (need admin)\n' "$r" ;;
    esac
  done || true  # per-repo probe misses must not abort under set -e

echo
echo "Remediation for a blocked repo:"
echo "  gh api -X PUT repos/$ORG/<repo>/actions/permissions -F enabled=true -f allowed_actions=all"
echo "Or once at org level (higher leverage):"
echo "  gh api -X PUT orgs/$ORG/actions/permissions -f enabled_repositories=all -f allowed_actions=all"
echo
echo "NOTE: settings hierarchy is enterprise > org > repo. If a setting looks locked"
echo "      at repo level it is set at org level; if locked there, at the enterprise."
echo
echo "preflight complete — no changes were made."
