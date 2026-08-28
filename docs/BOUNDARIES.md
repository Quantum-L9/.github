# Boundaries — what this repo does NOT do

`Quantum-L9/.github` owns **org-level governance metadata and advisory reporting**.
It does not execute, lint, test, scan, or remediate code. Those are owned elsewhere
in the CI constellation and must not be reimplemented here.

## Ownership map

| Concern | Owner | This repo's role |
| --- | --- | --- |
| Test execution, lint, typecheck | `l9-ci-sdk` / `l9-ci-core` | none — CI is no longer distributed from here (see `l9-ci-pack/README.md`) |
| Code scanning / CodeQL | `l9-ci-core` (already runs Code Quality + CodeQL) | none |
| CI failure diagnosis, log retrieval, bounded remediation | `l9-ci-debt-resolver` | none |
| CI debt measurement | `l9-ci-debt-intelligence` | consume as a link, never recompute |
| Reusable CI callees (`ci-python.yml` etc.) | `l9-ci-sdk` / `l9-ci-core` | **not built here** — pack callers are copied, not executed |
| PR/issue description quality | **this repo** | advisory gates |
| Community health files (SECURITY, CONTRIBUTING, templates) | **this repo** | inherited org-wide |
| CODEOWNERS, dependabot.yml (non-inheritable) | **this repo** | one-time seed |
| Which capabilities a repo class receives | **this repo** | `policies/repo-classes.yml` |
| How a repository is born | `l9-repo-template` | `make new-repo` — declares its class, this repo decides what that class gets |
| Org rulesets, secret scanning posture | **this repo** | advisory / evaluate mode |
| Cross-repo governance *reporting* | **this repo** | read-only weekly report |

## The rule

If a proposed addition here would run a test, parse a build log, or decide whether
code is correct, it belongs in `l9-ci-sdk` / `l9-ci-core` / `l9-ci-debt-resolver`.
This repo only ever asks: *is the governance metadata present and coherent?*
Distributing the locked `biome.json` contract from `l9-ci-core
presets/typescript/` is in-bounds (same as shipping lint callers). Reimplementing
the Biome scanner is not.

## Explicitly rejected additions

- **Reusable CI callees for pytest/ruff/pyright/semgrep/biome.** `l9-ci-sdk` /
  `l9-ci-core` own execution **and** delivery. This repo no longer distributes
  callers, governance packs, or the formatter contract: `l9-ci-core`'s
  `.l9/org-runtime-contract.yaml` lists "CI distribution from Quantum-L9/.github"
  as prohibited. The `l9-ci-pack/` directory is frozen reference material and
  its seed category fails closed.
- **Any code-scanning engine.** `l9-ci-core` already runs CodeQL / analysis.
  Seeding the Core caller is distribution, not a second scanner.
- **Any CI-failure triage or auto-fix.** `l9-ci-debt-resolver` owns bounded recovery.

## Interface, not duplication

Where governance needs a CI signal, it **references** the owning component rather
than recomputing it. `templates/governance-caller.yml` contains only governance
jobs. Canonical CI is `Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml`, enforced by a GitHub organization required-workflow ruleset — no file in the consumer, no
consumer-selected Core pin. This repo ships no CI and does not run ruff,
pytest, or semgrep itself. The retired refresh path (`make sync-ci` /
`scripts/sync_ci_from_pack.py`) is gone,
not the first-install path.
