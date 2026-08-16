# Boundaries — what this repo does NOT do

`Quantum-L9/.github` owns **org-level governance metadata, advisory reporting,
and GitHub-native organization defaults**. It does not execute, lint, test,
scan, or remediate code, and it no longer distributes, seeds, synchronizes, or
versions L9 CI implementation. Those are owned elsewhere in the CI
constellation and must not be reimplemented here.

## Ownership map

| Concern | Owner | This repo's role |
| --- | --- | --- |
| Test execution, lint, typecheck | `l9-ci-sdk` / `l9-ci-core` | none — CI callers are no longer distributed from this repo |
| Code scanning / CodeQL | `l9-ci-core` (already runs Code Quality + CodeQL) | none |
| CI failure diagnosis, log retrieval, bounded remediation | `l9-ci-debt-resolver` | none |
| CI debt measurement | `l9-ci-debt-intelligence` | consume as a link, never recompute |
| Reusable CI callees (`ci-python.yml` etc.) | `l9-ci-sdk` / `l9-ci-core` | **not built here** — CI distribution retired (campaign l9-dot-github-ci-boundary-v1) |
| CI targeting, versioning, reconciliation, enforcement | `l9-ci-control-plane` (planned) | none — this repo must not acquire it |
| PR/issue description quality | **this repo** | advisory gates |
| Community health files (SECURITY, CONTRIBUTING, templates) | **this repo** | inherited org-wide |
| CODEOWNERS, dependabot.yml (non-inheritable) | **this repo** | manual copy source (`templates/`) |
| Org rulesets (advisory), secret scanning posture | **this repo** | advisory rule definitions (evaluate); no in-repo apply automation |
| Cross-repo governance *reporting* | **this repo** | read-only weekly report |

## The rule

If a proposed addition here would run a test, parse a build log, decide whether
code is correct, or copy CI implementation into another repository, it belongs
in `l9-ci-sdk` / `l9-ci-core` / `l9-ci-debt-resolver` / `l9-ci-control-plane`.
This repo only ever asks: *is the governance metadata present and coherent?*

## Explicitly rejected additions

- **Reusable CI callees for pytest/ruff/pyright/semgrep.** `l9-ci-sdk` /
  `l9-ci-core` own execution; `l9-ci-control-plane` will own targeting and
  reconciliation. This repo must not reimplement those jobs here.
- **Any CI pack, seeder, or sync mechanism.** The `l9-ci-pack`, Actions
  seeders, drift sync, and template dispatch were retired in campaign
  l9-dot-github-ci-boundary-v1. `ops/validate-starters.sh` mechanically
  rejects their reintroduction.
- **Any CI-failure triage or auto-fix.** `l9-ci-debt-resolver` owns bounded recovery.

## Interface, not duplication

Where governance needs a CI signal, it **references** the owning component rather
than recomputing it. `templates/governance-caller.yml` contains only governance
jobs and calls the org governance workflows here (`governance-pr.yml`,
`governance-issue.yml`); it does not invoke CI. CI policy and Core-version
selection live outside this repository (`l9-ci-control-plane`); `l9-ci-core`
is a runtime orchestrator, not a policy owner.
