# Agent Runbook — Quantum-L9 `.github` deployment surface

## Mission

Deploy changes to `Quantum-L9/.github` and prove them. This repository now
holds GitHub-native org defaults and advisory non-CI governance only; the CI
distribution, seeding, sync, and versioning machinery documented by the
previous v3.1 runbook was retired in campaign l9-dot-github-ci-boundary-v1.

## Invariants

The agent MUST preserve all of these:

1. `governance-pr.yml` has `strict.default: false`.
2. `governance-issue.yml` never calls `core.setFailed`.
3. Every JSON ruleset has `"enforcement": "evaluate"`.
4. Push protection remains off. Secret-scanning alerts are on.
5. Dependabot may open PRs but nothing auto-merges them.
6. No workflow here runs pytest, Ruff, Pyright, Semgrep, CodeQL, tests, lint,
   build, or CI remediation. Those belong to `l9-ci-sdk`, `l9-ci-core`, and
   `l9-ci-debt-resolver`.
7. No workflow here seeds, syncs, or dispatches CI files into other
   repositories; `ops/validate-starters.sh` fails the build if a retired
   CI-distribution surface reappears.
8. Never push directly to `main`; use one deployment PR.
9. Never print the GitHub App private key or installation token.
10. If any invariant fails, stop and report. Do not improvise an enforcing fallback.

## Pre-flight

```bash
make validate   # boundary validation + SHA-pin audit (must be green)
make preflight  # org health check (read-only)
```

## Deploy

Open one PR against `main`, get the required checks green, and merge only with
operator authorization. Surviving org automation (label sync, policy
enforcement, reporting, pin audit) runs on its own schedules; no deployment
steps are needed for it.
