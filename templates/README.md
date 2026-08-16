# Org-level templates for consumer repos

These files are **manual copy sources** for files GitHub does not inherit.
The automated seeders, the org-CLI sync, and the consumer sync script that
formerly pushed this directory into consumer repositories were retired
(campaign l9-dot-github-ci-boundary-v1). Copy what a new repository needs by
hand; nothing in this directory is pushed automatically.

## Layout

| Directory / File | Destination in consumer repo | Notes |
|---|---|---|
| `CODEOWNERS.repo` | `.github/CODEOWNERS` | Not inheritable; must be physical |
| `dependabot.yml` | `.github/dependabot.yml` | Not inheritable; must be physical |
| `governance-caller.yml` | `.github/workflows/governance.yml` | Calls org reusable governance workflows |
| `labels.yml` | `.github/labels.yml` | Used by `gh label sync` or labeler |
| `community-health/` | repo root + `.github/FUNDING.yml` | Physical copy overrides org inherit |
| `issue-templates/` | `.github/ISSUE_TEMPLATE/` | Not inheritable; must be physical |
| `pr-templates/` | `.github/pull_request_template.md` | Not inheritable from org `.github/` nested path |

## Inheritance vs. physical copy

GitHub's "community health" inheritance (from the org `.github` repo) only
applies when a consumer repo **lacks** its own copy. Physical copying is
preferred when needed because:

1. **Visibility** — contributors see the files without navigating to the org repo.
2. **Determinism** — the version is pinned at copy time, not floating.
3. **Forkability** — forks outside the org still carry the files.
4. **CI gates** — `CODEOWNERS`, `dependabot.yml`, issue/PR templates are never
   inherited by GitHub; they must be physical regardless.

## What stays inherited (not copied)

- `FUNDING.yml` at org root — GitHub reads it org-wide automatically.
- Community health files that the consumer has **not** opted into physical copy
  mode for — they fall back to org-level inheritance silently.
