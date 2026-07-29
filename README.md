# Quantum-L9 — org defaults & governance v3.1

Advisory-first governance for the Quantum-L9 constellation. Everything here
**reports**; nothing blocks. See `docs/ADVISORY.md` for the promotion ladder and
`docs/BOUNDARIES.md` for what this repo deliberately does not do.

## Scope boundary (read this first)

This repo owns **governance metadata and advisory reporting**. It does not run
tests, lint, typecheck, scan code, or diagnose CI failures.

| Concern | Owner |
| --- | --- |
| Test / lint / build execution | `l9-ci-sdk`, `l9-ci-core` |
| CI failure diagnosis and bounded remediation | `l9-ci-debt-resolver` |
| CI debt measurement | `l9-ci-debt-intelligence` |
| PR/issue metadata quality, community health, org posture | **this repo** |

A reusable CI callee was the third-ranked gap before this constraint was known. It
is now **explicitly rejected** — `l9-ci-sdk` owns it. `preflight.sh` section 7
fails if any workflow here starts referencing pytest, ruff, pyright, or semgrep.

## What ships

| Gap | Fix | Mode | Blocks? |
| --- | --- | --- | --- |
| Enforcement layer absent | `rulesets/*.json` | `evaluate` | No |
| Secret detection absent | `scripts/enable-secret-scanning.sh` | alerts only | No |
| CI duplication | *rejected* — replaced by `governance-report.yml` (read-only) | advisory | No |
| Frozen SHA pins | `templates/dependabot.yml` | PRs only | No |
| Issue forms undeployed | `.github/ISSUE_TEMPLATE/*` | inherited | No |

## Layout

```
.github/
├── pull_request_template.md         inherited org-wide
├── CODEOWNERS                       this repo only
├── labels.yml
├── ISSUE_TEMPLATE/                  inherited org-wide
│   ├── config.yml                   routes CI issues to l9-ci-debt-resolver
│   ├── 1-bug.yml  2-feature.yml  3-task.yml
└── workflows/
    ├── governance-pr.yml            workflow_call, strict=false
    ├── governance-issue.yml         labels only, never fails
    ├── governance-report.yml        weekly read-only posture issue
    └── seed-governance.yml          dispatch-only, dry-run default
rulesets/                            all enforcement=evaluate
templates/                           CODEOWNERS.repo, dependabot.yml, caller
docs/  ADVISORY.md  BOUNDARIES.md  DISTRIBUTION.md  AUDIT.md
scripts/  preflight.sh  apply-rulesets.sh  enable-secret-scanning.sh
          sync-labels.sh  bootstrap.sh
```

## Agent deployment

Follow `docs/AGENT-DEPLOYMENT-RUNBOOK.md` exactly. It activates every capability to the maximum non-blocking extent, stages seeding through a one-repo pilot, and requires a deployment evidence artifact.

## Order of operations

```bash
./scripts/preflight.sh                      # read-only; 7 sections
./scripts/enable-secret-scanning.sh         # alerts only, no push protection
# merge, then:
git tag v1.0.0 && git push origin v1.0.0
git tag -f v1 v1.0.0 && git push origin v1 --force
DRY_RUN=1 ./scripts/apply-rulesets.sh       # evaluate mode preview
# Actions -> Seed non-inheritable governance -> mode: dry-run, repo_filter: l9-
```

Then let `governance-report.yml` run for four weeks before promoting anything.

## Advisory guarantees

Exactly one hard failure exists anywhere in this pack: `apply-rulesets.sh` refuses
to run if a ruleset says anything other than `evaluate`. It fails toward advisory.

`preflight.sh` section 6 asserts posture has not drifted: strict defaults false,
all rulesets evaluate, push protection off, issue triage cannot fail a run.
