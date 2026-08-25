# Agents

This document describes the automated agents (workflows) operating in this
repository and across the Quantum-L9 organization. Each agent has a defined
scope, schedule, permissions, and interaction model.

## Agent Registry

| Agent | Workflow | Schedule | Scope | Mode |
| --- | --- | --- | --- | --- |
| Governance Reporter | `governance-report.yml` | Weekly (Mon 08:00 UTC) | `.github` repo | Read-only issue |
| Label Syncer | `sync-labels-all.yml` | Weekly (Mon 09:30 UTC) | All repos | Additive (create/update) |
| Drift Remediator | `continuous-sync.yml` | Weekly (Tue 11:00 UTC) | All repos | PR-based |
| Policy Enforcer | `enforce-policies.yml` | Weekly (Wed 13:00 UTC) | All repos | Auto-correct settings |
| Preflight Monitor | `preflight-scheduled.yml` | Monthly (1st, 10:00 UTC) | Org-wide | Issue report |
| Pin Auditor | `audit-pins-org.yml` | Monthly (15th, 12:00 UTC) | All repos | Issue report |
| Auto-Seeder | `auto-seed-new-repo.yml` | Hourly (:20) + dispatch / repo creation | All repos | PR-based |
| Template Dispatcher | `dispatch-template-update.yml` | On push to templates/ | Seeded repos | Event dispatch |
| Governance PR | `governance-pr.yml` | On PR (workflow_call) | Calling repo | Advisory check |
| Governance Issue | `governance-issue.yml` | On issue (workflow_call) | Calling repo | Label-only |

## Permissions Model

All agents use a GitHub App token (`GOVERNANCE_APP_ID` / `GOVERNANCE_APP_PRIVATE_KEY`)
with the following scopes:

| Permission | Level | Used By |
| --- | --- | --- |
| `contents: read` | All repos | All agents |
| `contents: write` | All repos | Seeder, Drift Remediator, Dispatcher |
| `pull_requests: write` | All repos | Seeder, Drift Remediator |
| `issues: write` | `.github` only | Preflight, Pin Auditor, Reporter |
| `administration: write` | All repos | Policy Enforcer (settings correction) |

The App token is minted per-run via `actions/create-github-app-token` and expires
in one hour. No long-lived credentials exist.

## Interaction Model

Agents follow the advisory-first principle:

1. **Observe** — detect drift, missing files, floating refs, or policy violations
2. **Report** — create/update an issue or job summary with findings
3. **Remediate** — open a PR or correct a setting (never force-push to main)
4. **Never block** — all enforcement is in `evaluate` mode until explicitly promoted

## Opt-Out Mechanism

Consumer repos can opt out of specific agents:

| Marker File | Effect |
| --- | --- |
| `.l9/no-sync` | Drift Remediator skips this repo |
| `.l9/no-policy-enforcement` | Policy Enforcer skips this repo |

## Agent Contracts

Each agent guarantees:

- **Idempotency** — running twice produces the same result
- **Non-destructive** — never deletes files, branches, or data
- **Additive PRs** — PRs only add or restore content, never remove
- **Graceful degradation** — if a repo is inaccessible, the agent logs and continues
- **Summary output** — every run produces a GitHub Actions job summary table

### Seed-branch contract

The two seeders (`auto-seed-new-repo.yml`, `seed-governance.yml`) build their
PR as *"the consumer's current default branch + one seed commit"* and then move
the seed branch onto it. That construction discards anything else already on the
branch, so both gate every ref move through `ops/seed-branch-safety.js`:

| Consumer state | Seeder behavior |
| --- | --- |
| Seed branch absent | create the branch, open a PR |
| Seed PR open | **left alone** — the branch may carry review fixes |
| Branch holds only the seeder's own verified commit, no open PR | rebuilt on the current default branch |
| Branch holds any other commit | **left alone**, reported in the job summary |
| Branch state unprovable (comparison failed) | **left alone** — the gate fails closed |

Seeder authorship is proven, not assumed: the single ahead commit must carry
the seed subject **and** be committed by the identity the seeder runs as with
a GitHub-verified signature — an amended or rebased commit that preserves the
subject line fails the check and the branch is left alone.

The ref write is a server-side compare-and-swap: GraphQL `updateRefs` pins
`beforeOid` to the sha the verdict was computed from, so a branch that moves
between verdict and write is rejected atomically and left untouched.

`ops/test-seed-branch-safety.js` covers the gate; `ops/test-seed-workflow-branch-guard.js`
runs each workflow's real `script:` body against a stubbed API and asserts the
guarantee holds. Both run in `ops/validate-starters.sh`.

## Composite Actions (Shared Infrastructure)

These are not agents but reusable building blocks consumed by consumer repo CI:

| Action | Path | Purpose |
| --- | --- | --- |
| Immutable Checkout | `.github/actions/immutable-checkout/` | SHA-pinned git checkout without marketplace dependency |

## Copilot Governance

The `.github/copilot-instructions.md` file provides org-wide AI coding instructions.
Content exclusion policies are documented in `docs/copilot-exclusions.md` and
configured in Org Settings (not a file).

## Custom Properties

Repos are tagged with structured metadata via GitHub Custom Properties:

| Property | Type | Values | Purpose |
| --- | --- | --- | --- |
| `l9-ci-version` | single_select | v1, v2, none | CI migration tracking |
| `l9-tier` | single_select | critical, standard, experimental | Ruleset targeting |
| `l9-language` | multi_select | python, typescript, javascript, rust, go | CI template routing |
| `l9-seeded` | true_false | true, false | Governance seeding status |
| `l9-team` | single_select | platform, product, infra, external | Ownership routing |
