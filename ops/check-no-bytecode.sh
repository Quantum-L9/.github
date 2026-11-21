#!/usr/bin/env bash
# Fail when Python bytecode is tracked in git.
#
# A committed __pycache__/*.pyc is rewritten by whichever interpreter imports
# its module, so a checkout's tree changes under any run that imports it (the
# Python minor in the file name decides which runner rewrites it). That is how
# Quantum-L9/.github#278 left two tracked files modified after repository
# verification on Python 3.12 while a Python 3.13 run stayed clean.
#
# Signal law (L9-SIGNAL-001): every failure names each offending path and the
# exact command that removes it from the index.
#
# Usage: bash ops/check-no-bytecode.sh [repository-dir]   (default: .)
set -euo pipefail

root="${1:-.}"
# List once into a file and check git's own exit status before reading it: a
# failed listing (no such directory, not a repository) must fail the check,
# never read as "no bytecode" (a process substitution would hide the failure).
listing="$(mktemp)"
trap 'rm -f -- "${listing}"' EXIT
if ! git -C "${root}" ls-files -z -- '*.pyc' '*.pyo' '*/__pycache__/*' '__pycache__/*' > "${listing}"; then
  echo "::error title=bytecode check could not run::git ls-files failed in '${root}'; tracked bytecode cannot be ruled out" >&2
  exit 2
fi
mapfile -d '' tracked < "${listing}"

if [[ "${#tracked[@]}" -eq 0 ]]; then
  echo "✅ no Python bytecode is tracked"
  exit 0
fi

echo "❌ ${#tracked[@]} tracked Python bytecode file(s); bytecode is a build output and must not be committed:" >&2
for path in "${tracked[@]}"; do
  echo "::error file=${path},title=tracked Python bytecode::${path} is tracked; remove it with: git rm --cached -- '${path}'" >&2
done
echo "Fix: git rm --cached -- <each path above>, then commit. .gitignore ignores __pycache__/ and *.pyc, so they stay out." >&2
exit 1
