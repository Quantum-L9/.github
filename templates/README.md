# Org-level templates for consumer repos

Everything in this directory is **physically seeded** into consumer repositories
by:

1. **Actions seeder** — `.github/workflows/seed-governance.yml` (org App, opens PRs)
2. **Org CLI** — `ops/sync-org-files.sh` (local checkout sync)
3. **Consumer sync** — `templates/sync_ci_from_pack.py` (copied to consumer as
   `scripts/sync_ci_from_pack.py` / `make sync-ci`)

Payload map SSOT for Actions: `ops/build-seed-payload.js` (must stay aligned with
`ops/sync-org-files.sh`).

These files are NOT reliably GitHub-inheritable for template/fork use — they must
live in each repo's tree to take effect.

## Layout

| Directory / File | Destination in consumer repo | Notes |
|---|---|---|
| `CODEOWNERS.repo` | `.github/CODEOWNERS` | Not inheritable; must be physical |
| `dependabot.yml` | `.github/dependabot.yml` | Not inheritable; must be physical |
| `governance-caller.yml` | `.github/workflows/governance.yml` | Calls org reusable workflows |
| `on-org-update.yml` | `.github/workflows/on-org-update.yml` | Receiver for org template sync PRs |
| `labels.yml` | `.github/labels.yml` | Used by `gh label sync` or labeler |
| `community-health/` | repo root + `.github/FUNDING.yml` | Physical copy overrides org inherit |
| `issue-templates/` | `.github/ISSUE_TEMPLATE/` | Not inheritable; must be physical |
| `pr-templates/` | `.github/pull_request_template.md` | Not inheritable from org `.github/` nested path |

## Inheritance vs. physical copy

GitHub's "community health" inheritance (from the org `.github` repo) only
applies when a consumer repo **lacks** its own copy. Physical seeding is
preferred because:

1. **Visibility** — contributors see the files without navigating to the org repo.
2. **Determinism** — the version is pinned at sync time, not floating.
3. **Forkability** — forks outside the org still carry the files.
4. **CI gates** — `CODEOWNERS`, `dependabot.yml`, issue/PR templates are never
   inherited by GitHub; they must be physical regardless.

## Updating

Edit files here (in `Quantum-L9/.github/templates/`), then consumer repos pull
the update on their next `make sync-ci` run. The sync script reads these files
at the pinned `ORG_GITHUB_SHA` from the consumer's `.l9/ci-pin`.

## What stays inherited (not seeded)

- `FUNDING.yml` at org root — GitHub reads it org-wide automatically.
- Community health files that the consumer has **not** opted into physical copy
  mode for — they fall back to org-level inheritance silently.
