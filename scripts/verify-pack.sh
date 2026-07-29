#!/usr/bin/env bash
# Offline, deterministic v3.1 assertions. Makes no network calls.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail=0
ok(){ echo "OK  $*"; }
bad(){ echo "!!  $*"; fail=1; }

if grep -A4 '^      strict:' .github/workflows/governance-pr.yml | grep -q 'default: false'; then
  ok "PR governance defaults advisory"
else bad "PR governance does not default strict=false"; fi

if grep -q 'core.setFailed' .github/workflows/governance-issue.yml; then
  bad "issue governance contains core.setFailed"
else ok "issue governance cannot fail the run"; fi

for f in rulesets/*.json; do
  mode=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["enforcement"])' "$f")
  [[ "$mode" == evaluate ]] && ok "$(basename "$f") evaluate" || bad "$(basename "$f") is $mode"
done

if grep -rEi '\b(pytest|ruff|pyright|semgrep|codeql|npm test|tox)\b' .github/workflows/; then
  bad "defaults workflow duplicates CI execution"
else ok "no CI execution duplicated in defaults workflows"; fi

if grep -q 'secret_scanning_push_protection_enabled_for_new_repositories=true' scripts/enable-secret-scanning.sh \
   && ! grep -q -- '--with-push-protection' scripts/enable-secret-scanning.sh; then
  bad "push protection can be enabled without explicit opt-in"
else ok "push protection guarded by explicit opt-in"; fi

for p in \
 .github/ISSUE_TEMPLATE/config.yml \
 .github/pull_request_template.md \
 .github/workflows/governance-report.yml \
 templates/dependabot.yml \
 templates/governance-caller.yml \
 docs/ADVISORY.md docs/BOUNDARIES.md; do
  [[ -f "$p" ]] && ok "present $p" || bad "missing $p"
done

for s in scripts/*.sh; do
  bash -n "$s" && ok "shell syntax $(basename "$s")" || bad "shell syntax $(basename "$s")"
done

python3 - <<'PY' || exit 1
import json, pathlib
try:
    import yaml
except ImportError:
    print('NOTE PyYAML unavailable; JSON validated, YAML validation skipped')
else:
    for p in list(pathlib.Path('.github/workflows').glob('*.yml')) + \
             list(pathlib.Path('.github/ISSUE_TEMPLATE').glob('*.yml')) + \
             list(pathlib.Path('templates').glob('*.yml')):
        yaml.safe_load(p.read_text())
        print('OK  yaml', p)
for p in pathlib.Path('rulesets').glob('*.json'):
    json.loads(p.read_text()); print('OK  json', p)
PY

[[ "$fail" == 0 ]] || exit 1
echo "PASS v3.1 pack is advisory and boundary-clean"
