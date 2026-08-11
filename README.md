# Quantum-L9 — org defaults & governance v4.0

Advisory-first governance control plane for the Quantum-L9 constellation. Everything
here **reports and remediates**; nothing blocks until explicitly promoted. See
`docs/ADVISORY.md` for the promotion ladder and `docs/BOUNDARIES.md` for what this
repo deliberately does not do.

## Scope boundary (read this first)

This repo owns **governance metadata, advisory reporting, policy enforcement, and
org-wide automation**. It does not run tests, lint, typecheck, scan code, or
diagnose CI failures.

| Concern | Owner |
| --- | --- |
| Test / lint / build execution | `l9-ci-sdk`, `l9-ci-core` |
| CI failure diagnosis and bounded remediation | `l9-ci-debt-resolver` |
| CI debt measurement | `l9-ci-debt-intelligence` |
| PR/issue metadata, community health, org posture, policy enforcement | **this repo** |
| AI coding governance (Copilot instructions, content exclusion) | **this repo** |
| Cross-repo orchestration and dispatch | **this repo** |

## What ships

| Capability | Implementation | Mode | Blocks? |
| --- | --- | --- | --- |
| Org rulesets | `rulesets/*.json` | `evaluate` | No |
| Required analysis workflow | `rulesets/org-required-analysis.json` | `evaluate` | No |
| Secret scanning | `ops/activate-all.sh` → org API | alerts only | No |
| Governance seeding | `auto-seed-new-repo.yml` | PR-based | No |
| Label sync | `sync-labels-all.yml` (weekly) | additive | No |
| Drift remediation | `continuous-sync.yml` (weekly) | PR-based | No |
| Policy enforcement | `enforce-policies.yml` (weekly) | auto-correct settings | No |
| SHA-pin audit | `audit-pins-org.yml` (monthly) | report only | No |
| Preflight check | `preflight-scheduled.yml` (monthly) | report only | No |
| Template dispatch | `dispatch-template-update.yml` | event-driven | No |
| Copilot governance | `.github/copilot-instructions.md` | advisory | No |
| Custom properties | `ops/properties-schema.json` | metadata | No |

## Layout

```
.github/
├── copilot-instructions.md              org-wide AI coding governance
├── pull_request_template.md             inherited org-wide
├── CODEOWNERS                           this repo only
├── labels.yml                           org label taxonomy
├── ISSUE_TEMPLATE/                      inherited org-wide
├── actions/
│   └── immutable-checkout/              reusable: SHA-pinned checkout
└── workflows/
    ├── governance-pr.yml                workflow_call, strict=false
    ├── governance-issue.yml             labels only, never fails
    ├── governance-report.yml            weekly read-only posture issue
    ├── seed-governance.yml              dispatch-only, dry-run default
    ├── auto-seed-new-repo.yml           seeds new/unseeded repos via PR
    ├── sync-labels-all.yml              weekly label fan-out
    ├── preflight-scheduled.yml          monthly drift detection
    ├── continuous-sync.yml              weekly drift remediation
    ├── audit-pins-org.yml               monthly SHA-pin audit
    ├── dispatch-template-update.yml     notifies consumers on change
    └── enforce-policies.yml             weekly policy enforcement
policies/
├── repo-settings.yml                    declarative repo settings
└── mandatory-files.yml                  required files (managed/seeded/present)
rulesets/
├── org-advisory-pr.json                 evaluate: PR + governance check
├── org-advisory-hygiene.json            evaluate: branch deletion + force-push
└── org-required-analysis.json           evaluate: requires l9-analysis workflow
templates/
├── CODEOWNERS.repo                      seeded into consumer repos
├── dependabot.yml                       seeded into consumer repos
├── governance-caller.yml                seeded into consumer repos
├── on-org-update.yml                    receiver for cross-repo dispatch
├── community-health/                    LICENSE, CONTRIBUTING, etc.
├── issue-templates/                     full issue template set
└── pr-templates/                        PR template
ops/
├── activate-all.sh                      one-shot: enables everything
├── set-repo-properties.sh              bulk-set custom properties
├── properties-schema.json               custom properties definition
├── sync-v2-starters.sh                  syncs from l9-ci-core
├── sync-org-files.sh                    seeds templates into consumers
├── apply-rulesets.sh                    applies org rulesets
├── validate-starters.sh                 validates pack integrity
├── pin-actions-sha.sh                   pins floating action refs
└── audit-sha-pins.sh                    audits this repo's pins
docs/
├── ADVISORY.md                          promotion ladder
├── BOUNDARIES.md                        scope constraints
├── DISTRIBUTION.md                      distribution model
├── copilot-exclusions.md                content exclusion source of truth
└── adr/                                 architecture decision records
scripts/
├── preflight.sh                         comprehensive org health check
├── enable-secret-scanning.sh            alerts only
├── sync-labels.sh                       per-repo label sync
└── bootstrap.sh                         local inheritance check
```

## Automation schedule

After running `ops/activate-all.sh`:

| Day | Time (UTC) | Workflow | Action |
| --- | --- | --- | --- |
| Monday | 09:30 | `sync-labels-all.yml` | Syncs label taxonomy to all repos |
| Tuesday | 11:00 | `continuous-sync.yml` | Detects drift, opens remediation PRs |
| Wednesday | 13:00 | `enforce-policies.yml` | Corrects repo settings, reports missing files |
| Weekly | 08:00 | `governance-report.yml` | Measures org governance coverage |
| 1st | 10:00 | `preflight-scheduled.yml` | Detects org-wide config drift |
| 15th | 12:00 | `audit-pins-org.yml` | Reports floating action refs |
| On push | — | `dispatch-template-update.yml` | Notifies consumers of template changes |
| On create | — | `auto-seed-new-repo.yml` | Seeds governance into new repos |

## Quick start

```bash
# 1. First-time activation (run once after initial setup)
ops/activate-all.sh

# 2. Set custom properties on all repos
ops/set-repo-properties.sh --apply

# 3. Everything else is automated from this point
```

## Consumer repos

Consumer repos receive governance automatically. No action required. They can:

- **Opt out of sync:** Create `.l9/no-sync` in the repo
- **Opt out of policy enforcement:** Create `.l9/no-policy-enforcement` in the repo
- **Receive template updates:** Add `templates/on-org-update.yml` to `.github/workflows/`
- **Use composite actions:** Reference `Quantum-L9/.github/actions/<name>@<sha>`

## Advisory guarantees

All controls are advisory by default. The promotion path is:

1. **Evaluate** (4 weeks) — observe, report, measure
2. **Advisory** (4 weeks) — warn on PR, never block
3. **Active** — block on violation (requires explicit promotion decision)

`ops/activate-all.sh` refuses to set anything above `evaluate`. Promotion is a
deliberate, documented decision recorded in `docs/adr/`.
