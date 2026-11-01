#!/usr/bin/env bash
# ops/test-activate-all.sh
# Regression test for ops/activate-all.sh: a failing scripts/apply-rulesets.sh
# must make activation exit nonzero, before it dispatches any later step or
# prints "Activation Complete". A passing applier is the control: the same
# harness then runs to completion and exits zero.
# Offline: gh and jq are stubs on PATH, and the applier is a stub beside a
# copy of the script under test. Run from the root of the Quantum-L9/.github repo:
#   bash ops/test-activate-all.sh
set -euo pipefail

ORG_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

fail() {
  echo "❌ $1" >&2
  exit 1
}

# Stub gh records every call and succeeds; stub jq is never reached because
# activate-all.sh only checks that it exists.
STUBS="$WORK/bin"
mkdir -p "$STUBS"
cat > "$STUBS/gh" <<'EOF'
#!/usr/bin/env bash
echo "gh $*" >> "$GH_CALLS"
EOF
printf '#!/usr/bin/env bash\nexit 0\n' > "$STUBS/jq"
chmod +x "$STUBS/gh" "$STUBS/jq"

# run_activation <case> <applier exit code>: copies activate-all.sh into a
# scratch tree whose scripts/apply-rulesets.sh exits with the given code.
run_activation() {
  local case_dir="$WORK/$1" rc
  mkdir -p "$case_dir/ops" "$case_dir/scripts"
  cp "$ORG_ROOT/ops/activate-all.sh" "$case_dir/ops/activate-all.sh"
  printf '#!/usr/bin/env bash\necho "stub apply-rulesets: exit %s"\nexit %s\n' "$2" "$2" \
    > "$case_dir/scripts/apply-rulesets.sh"
  : > "$case_dir/gh-calls"
  set +e
  GH_CALLS="$case_dir/gh-calls" PATH="$STUBS:$PATH" \
    bash "$case_dir/ops/activate-all.sh" > "$case_dir/out" 2>&1
  rc=$?
  set -e
  echo "$rc"
}

# ── 1. applier fails → activation fails, nothing after step 3 runs ───────────
rc="$(run_activation failing 1)"
out="$WORK/failing/out"
[[ "$rc" != 0 ]] || fail "activation exited 0 after scripts/apply-rulesets.sh failed"
grep -q "stub apply-rulesets: exit 1" "$out" || fail "the failing applier was not invoked"
grep -q "Activation Complete" "$out" && fail "activation claimed success after the ruleset apply failed"
grep -q "workflow run" "$WORK/failing/gh-calls" && fail "activation dispatched workflows after the ruleset apply failed"
grep -q "4/6" "$out" && fail "activation continued past the ruleset step"

# ── 2. control: applier succeeds → activation completes ──────────────────────
rc="$(run_activation passing 0)"
out="$WORK/passing/out"
[[ "$rc" == 0 ]] || fail "activation exited $rc with a passing applier"
grep -q "Activation Complete" "$out" || fail "activation did not complete with a passing applier"
grep -q "workflow run" "$WORK/passing/gh-calls" || fail "activation dispatched no workflows with a passing applier"

echo "✅ activate-all.sh exits nonzero when scripts/apply-rulesets.sh fails"
