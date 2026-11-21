#!/usr/bin/env bash
# The SHA-pin audit and the semantic validator run once, inside the required
# Analyze check. Their result must not be dropped into the raw log: on GitHub
# Actions each failure is annotated on its file (and line where known), and the
# job summary carries the verdict (L9-SIGNAL-001). Off Actions both stay quiet.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "${here}/.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "${work}"' EXIT
fail=0

# 1. A floating ref: annotated on its line, FAIL in the summary, exit 1.
mkdir -p "${work}/pins/.github/workflows"
printf 'on: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n' \
  > "${work}/pins/.github/workflows/x.yml"
summary="${work}/pins-summary.md"
if out="$(cd "${work}/pins" && GITHUB_ACTIONS=true GITHUB_STEP_SUMMARY="${summary}" bash "${here}/audit-sha-pins.sh" 2>&1)"; then
  echo "❌ a floating ref passed the SHA-pin audit"; fail=1
elif grep -qF "::error file=.github/workflows/x.yml,line=6,title=floating action ref::'actions/checkout@v4'" <<<"${out}" \
  && grep -qF "**FAIL**: 1 floating reference(s)" "${summary}"; then
  echo "✅ SHA-pin audit: a floating ref is annotated on its line and summarised as FAIL"
else
  echo "❌ SHA-pin audit failed without the annotation or summary:"; echo "${out}"; cat "${summary}" 2>/dev/null || true; fail=1
fi

# 2. Off Actions the audit emits no annotation and writes no summary.
if out="$(cd "${work}/pins" && env -u GITHUB_ACTIONS -u GITHUB_STEP_SUMMARY bash "${here}/audit-sha-pins.sh" 2>&1)"; then
  echo "❌ a floating ref passed the SHA-pin audit off Actions"; fail=1
elif grep -qF "::error" <<<"${out}"; then
  echo "❌ the SHA-pin audit annotated off Actions"; fail=1
else
  echo "✅ SHA-pin audit: off Actions it fails plainly, without annotations"
fi

# 3. A semantic-closure FAIL: annotated on its path, listed in the summary.
summary="${work}/semantics-summary.md"
if out="$(GITHUB_ACTIONS=true GITHUB_STEP_SUMMARY="${summary}" python3 - "${root}/scripts/validate-semantics.py" <<'PY'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("validate_semantics", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
report = module.Report()
report.ok("SC-001", "fixture pass")
report.fail("RC-099", "semantics/example.yaml", "field", "bad", "fixture failure")
module._publish_ci_result(report)
PY
)"; then
  if grep -qF "::error file=semantics/example.yaml,title=semantic closure RC-099::field='bad': fixture failure" <<<"${out}" \
    && grep -qF "**FAIL**: 1 checks passed, 1 failed." "${summary}" \
    && grep -qF "FAIL RC-099 semantics/example.yaml field='bad': fixture failure" "${summary}"; then
    echo "✅ semantic closure: a FAIL is annotated on its path and listed in the summary"
  else
    echo "❌ semantic closure FAIL was not annotated or summarised:"; echo "${out}"; cat "${summary}" 2>/dev/null || true; fail=1
  fi
else
  echo "❌ could not exercise the semantic closure CI output:"; echo "${out}"; fail=1
fi

exit "${fail}"
