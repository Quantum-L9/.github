#!/usr/bin/env bash
# Enables secret scanning ALERTS org-wide (detection, non-blocking).
# Push protection is BLOCKING and is therefore opt-in, off by default.
set -euo pipefail
ORG=Quantum-L9
WITH_PP=0
[[ "${1:-}" == "--with-push-protection" ]] && WITH_PP=1

echo "== current org security posture =="
gh api "orgs/$ORG" --jq '{
  secret_scanning: .secret_scanning_enabled_for_new_repositories,
  push_protection: .secret_scanning_push_protection_enabled_for_new_repositories,
  dependency_graph: .dependency_graph_enabled_for_new_repositories
}' 2>/dev/null || echo "  (need admin:org to read)"

echo
echo "== enabling detection for NEW repos =="
gh api -X PATCH "orgs/$ORG" \
  -F secret_scanning_enabled_for_new_repositories=true \
  -F dependency_graph_enabled_for_new_repositories=true >/dev/null
echo "  secret scanning alerts: on"
echo "  dependency graph: on (prerequisite for Dependabot)"

echo
echo "== enabling detection on EXISTING repos =="
gh api -X POST "orgs/$ORG/security-products/secret-scanning/enable-all" >/dev/null 2>&1 \
  || echo "  (bulk enable unavailable on this plan — enable per repo in Settings)"

if [[ "$WITH_PP" == "1" ]]; then
  cat <<'EOF'

!! PUSH PROTECTION IS A BLOCKING CONTROL.
   It rejects pushes containing detected secrets. That is the correct end state,
   but it is NOT advisory. Confirm you intend to leave advisory posture.
EOF
  read -r -p "type ENFORCE to continue: " C
  [[ "$C" == "ENFORCE" ]] || { echo "aborted — still advisory."; exit 0; }
  gh api -X PATCH "orgs/$ORG" \
    -F secret_scanning_push_protection_enabled_for_new_repositories=true >/dev/null
  echo "push protection: on for new repos"
else
  cat <<'EOF'

push protection: NOT enabled (advisory posture preserved).
  Detection is on, so leaked secrets raise an alert you can act on.
  Re-run with --with-push-protection when ready to block.

REMINDER: a detected secret must be ROTATED with the provider. Deleting the
commit does not invalidate the credential.
EOF
fi
