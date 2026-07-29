# Boundaries — what this repo does NOT do

`Quantum-L9/.github` owns **org-level governance metadata and advisory reporting**.
It does not execute, lint, test, scan, or remediate code. Those are owned elsewhere
in the CI constellation and must not be reimplemented here.

## Ownership map

| Concern | Owner | This repo's role |
| --- | --- | --- |
| Test execution, lint, typecheck | `l9-ci-sdk` / `l9-ci-core` | none — never invoked from here |
| Code scanning / CodeQL | `l9-ci-core` (already runs Code Quality + CodeQL) | none |
| CI failure diagnosis, log retrieval, bounded remediation | `l9-ci-debt-resolver` | none |
| CI debt measurement | `l9-ci-debt-intelligence` | consume as a link, never recompute |
| Reusable CI callees (`ci-python.yml` etc.) | `l9-ci-sdk` | **deliberately not built here** |
| PR/issue description quality | **this repo** | advisory gates |
| Community health files (SECURITY, CONTRIBUTING, templates) | **this repo** | inherited org-wide |
| CODEOWNERS, dependabot.yml (non-inheritable) | **this repo** | one-time seed |
| Org rulesets, secret scanning posture | **this repo** | advisory / evaluate mode |
| Cross-repo governance *reporting* | **this repo** | read-only weekly report |

## The rule

If a proposed addition here would run a test, parse a build log, or decide whether
code is correct, it belongs in `l9-ci-sdk` / `l9-ci-core` / `l9-ci-debt-resolver`.
This repo only ever asks: *is the governance metadata present and coherent?*

## Explicitly rejected additions

- **Reusable CI callees for pytest/ruff/pyright/semgrep.** This was ranked the #3
  gap before the constraint was known. `l9-ci-sdk` owns it. Duplicating it here
  would create two competing sources of CI truth — the exact failure this whole
  effort exists to prevent.
- **Any code-scanning workflow.** `l9-ci-core` already runs CodeQL for Python.
- **Any CI-failure triage or auto-fix.** `l9-ci-debt-resolver` owns bounded recovery.

## Interface, not duplication

Where governance needs a CI signal, it **references** the owning component rather
than recomputing it. `templates/governance-caller.yml` therefore contains only
governance jobs; a repo's CI caller (pointing at `l9-ci-sdk`) is a separate file
this repo never writes.
