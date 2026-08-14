# Boundaries — what this repo does NOT do

`Quantum-L9/.github` owns **org-level governance metadata and advisory reporting**.
It does not execute, lint, test, scan, or remediate code. Those are owned elsewhere
in the CI constellation and must not be reimplemented here.

## Ownership map

| Concern | Owner | This repo's role |
| --- | --- | --- |
| Test execution, lint, typecheck | `l9-ci-sdk` / `l9-ci-core` | distribute `l9-ci-pack` callers only — never execute here |
| Code scanning / CodeQL | `l9-ci-core` (already runs Code Quality + CodeQL) | none |
| CI failure diagnosis, log retrieval, bounded remediation | `l9-ci-debt-resolver` | none |
| CI debt measurement | `l9-ci-debt-intelligence` | consume as a link, never recompute |
| Reusable CI callees (`ci-python.yml` etc.) | `l9-ci-sdk` / `l9-ci-core` | **not built here** — pack callers are copied, not executed |
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

- **Reusable CI callees for pytest/ruff/pyright/semgrep.** `l9-ci-sdk` / `l9-ci-core`
  own execution. This repo may **distribute** thin callers from `l9-ci-pack/`
  (`l9-analysis.yml`, lint templates, `.github/governance/*.yaml`). It must not
  reimplement those jobs here.
- **Any code-scanning engine.** `l9-ci-core` already runs CodeQL / analysis.
  Seeding the Core caller is distribution, not a second scanner.
- **Any CI-failure triage or auto-fix.** `l9-ci-debt-resolver` owns bounded recovery.

## Interface, not duplication

Where governance needs a CI signal, it **references** the owning component rather
than recomputing it. `templates/governance-caller.yml` contains only governance
jobs. The Core hub pack (`l9-ci-pack/`) is the consumer-side caller that points at
`l9-ci-core`. This repo **ships** that pack via the seeder; it does not run
ruff, pytest, or semgrep itself. `make sync-ci` remains an optional refresh path,
not the first-install path.
