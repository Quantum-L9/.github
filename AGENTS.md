# Agents

This document describes the automated agents (workflows) operating in this
repository and across the Quantum-L9 organization. Each agent has a defined
scope, schedule, permissions, and interaction model.

## Agent Registry

| Agent | Workflow | Schedule | Scope | Mode |
| --- | --- | --- | --- | --- |
| Governance Reporter | `governance-report.yml` | Weekly (Mon 08:00 UTC) | `.github` repo | Read-only issue |
| Label Syncer | `sync-labels-all.yml` | Weekly (Mon 09:30 UTC) | All repos | Additive (create/update) |
| Policy Enforcer | `enforce-policies.yml` | Weekly (Wed 13:00 UTC) | All repos | Auto-correct settings |
| Preflight Monitor | `preflight-scheduled.yml` | Monthly (1st, 10:00 UTC) | Org-wide | Issue report |
| Pin Auditor | `audit-pins-org.yml` | Monthly (15th, 12:00 UTC) | All repos | Issue report |
| Governance PR | `governance-pr.yml` | On PR (workflow_call) | Calling repo | Advisory check |
| Governance Issue | `governance-issue.yml` | On issue (workflow_call) | Calling repo | Label-only |

The CI distribution agents (Seeder, Drift Remediator, Template Dispatcher) were
retired in campaign l9-dot-github-ci-boundary-v1 and are listed here only as
history; the boundary validator rejects their reintroduction.

## Permissions Model

The org-wide agents use a GitHub App token (`GOVERNANCE_APP_ID` /
`GOVERNANCE_APP_PRIVATE_KEY`) with the following scopes:

| Permission | Level | Used By |
| --- | --- | --- |
| `contents: read` | All repos | All agents |
| `issues: write` | `.github` only | Preflight, Pin Auditor, Reporter |
| `administration: write` | All repos | Policy Enforcer (settings correction) |
| Labels write | All repos | Label Syncer |

The App token is minted per-run via `actions/create-github-app-token` and expires
in one hour. No long-lived credentials exist. No agent holds `contents: write`
or `pull_requests: write` on other repositories.

## Interaction Model

Agents follow the advisory-first principle:

1. **Observe** — detect drift, missing files, floating refs, or policy violations
2. **Report** — create/update an issue or job summary with findings
3. **Remediate** — correct a setting (never force-push to main)
4. **Never block** — all enforcement is in `evaluate` mode until explicitly promoted

## Opt-Out Mechanism

Consumer repos can opt out of specific agents:

| Marker File | Effect |
| --- | --- |
| `.l9/no-policy-enforcement` | Policy Enforcer skips this repo |

## Agent Contracts

Each agent guarantees:

- **Idempotency** — running twice produces the same result
- **Non-destructive** — never deletes files, branches, or data
- **Additive PRs** — PRs only add or restore content, never remove
- **Graceful degradation** — if a repo is inaccessible, the agent logs and continues
- **Summary output** — every run produces a GitHub Actions job summary table

## Composite Actions (Shared Infrastructure)

These are not agents but reusable building blocks consumed by consumer repos:

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
| `l9-tier` | single_select | critical, standard, experimental | Ruleset targeting |
| `l9-language` | multi_select | python, typescript, javascript, rust, go | Repository taxonomy |
| `l9-team` | single_select | platform, product, infra, external | Ownership routing |
