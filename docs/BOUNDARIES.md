# Boundaries — what this repo does not do

`Quantum-L9/.github` owns org-level governance metadata and advisory reporting.
It does not execute, lint, test, scan, or remediate code.

## Ownership map

| Concern | Owner | This repo's role |
| --- | --- | --- |
| Test execution, lint, typecheck, code scanning | `l9-ci-core` (`org-ci.yml`, organization required workflow) and `l9-ci-sdk` | none. The `on-org-update` seed category fails closed. |
| CI failure diagnosis | `l9-ci-debt-resolver` | none |
| CI debt measurement | `l9-ci-debt-intelligence` | consume as a link, never recompute |
| PR and issue description quality | **this repo** | advisory gates |
| Community health files | **this repo** | inherited when the consumer has no local copy; otherwise seeded missing-only |
| CODEOWNERS, dependabot, governance caller | **this repo** | `policies/CODEOWNERS`, `.github/dependabot.yml`, `policies/governance-caller.yml` |
| Which capabilities a class receives | **this repo** | `policies/repo-classes.yml` |
| How a repository is born | `l9-repo-template` | `make new-repo` declares the class; this repo applies it |
| Org rulesets, secret scanning posture | **this repo** | advisory / evaluate |
| Cross-repo governance reporting | **this repo** | read-only weekly report |

## The rule

If a proposed addition would run a test, parse a build log, or decide whether
code is correct, it belongs in `l9-ci-core`, `l9-ci-sdk`, or
`l9-ci-debt-resolver`. This repo only asks whether the governance metadata is
present and coherent.

## Explicitly rejected

- Copied CI workflows as an enforcement mechanism. Canonical CI is
  `Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml`, reached through an
  organization required-workflow ruleset. No copied workflow, no
  consumer-selected Core pin.
- Seeding `on-org-update`. That category throws.
- A second code scanner. `l9-ci-core` already runs analysis.
- CI-failure triage or auto-fix. `l9-ci-debt-resolver` owns bounded recovery.

## What this repo does ship

`policies/governance-caller.yml` is a thin `workflow_call` caller for
`governance-pr.yml` and `governance-issue.yml`. It is governance metadata. The
`default` class materializes it. `self_governed` and `non_constellation_python`
forbid `.github/workflows/governance.yml`.
