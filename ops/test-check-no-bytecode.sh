#!/usr/bin/env bash
# ops/check-no-bytecode.sh against throwaway repositories: a clean tree and
# ignored bytecode pass; tracked bytecode fails and is named.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
check="${here}/check-no-bytecode.sh"
work="$(mktemp -d)"
trap 'rm -rf -- "${work}"' EXIT

repo() {
  local dir="${work}/$1"
  mkdir -p "${dir}/scripts/__pycache__"
  git -C "${dir}" init -q
  git -C "${dir}" config user.email t@example.invalid
  git -C "${dir}" config user.name t
  printf 'x = 1\n' > "${dir}/scripts/mod.py"
  printf '\0bytecode' > "${dir}/scripts/__pycache__/mod.cpython-312.pyc"
  printf '__pycache__/\n*.pyc\n' > "${dir}/.gitignore"
  git -C "${dir}" add .gitignore scripts/mod.py
  git -C "${dir}" commit -q -m init
  echo "${dir}"
}

fail=0

clean="$(repo clean)"
if bash "${check}" "${clean}" >/dev/null 2>&1; then
  echo "✅ ignored, untracked bytecode passes"
else
  echo "❌ ignored, untracked bytecode failed"; fail=1
fi

dirty="$(repo dirty)"
git -C "${dirty}" add -f scripts/__pycache__/mod.cpython-312.pyc
git -C "${dirty}" commit -q -m "track bytecode"
if out="$(bash "${check}" "${dirty}" 2>&1)"; then
  echo "❌ tracked bytecode passed"; fail=1
elif grep -qF "::error file=scripts/__pycache__/mod.cpython-312.pyc," <<<"${out}" \
  && grep -qF "git rm --cached -- 'scripts/__pycache__/mod.cpython-312.pyc'" <<<"${out}"; then
  echo "✅ tracked bytecode fails and names the path and the fix"
else
  echo "❌ tracked bytecode failed without naming the path and the fix:"; echo "${out}"; fail=1
fi

exit "${fail}"
