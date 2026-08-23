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
| `on-org-update.yml` | `.github/workflows/on-org-update.yml` | **Opt-in** — not in default `all` |
| `labels.yml` | `.github/labels.yml` | **Opt-in** — org `sync-labels-all.yml` fans labels |
| `community-health/` | `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md` | No LICENSE / FUNDING / SUPPORT in default seed |
| `issue-templates/` | `.github/ISSUE_TEMPLATE/` | Numbered chooser + ci/seed-ci/gov + config; no `bug_report` / `feature_request` |
| `pr-templates/` | `pull_request_template.md` + `PULL_REQUEST_TEMPLATE/agent.md` | Human + agent/chore variants |
| `../l9-ci-pack/workflows/` | `.github/workflows/` | Core hub callers (`l9-analysis.yml`, lint templates). Missing-only. |
| `../l9-ci-pack/governance/` | `.github/governance/` | Governance YAMLs the Core resolver reads. |
| `../l9-ci-pack/biome.json` | `biome.json` | Locked Biome 2.5.8 contract. Missing-only; never overwrite. |
| `../l9-ci-pack/.biomeignore` | `.biomeignore` | Path exclusions companion. Missing-only. |
| `../l9-ci-pack/.editorconfig` | `.editorconfig` | Editor indent/newline contract. Missing-only. |
| `../l9-ci-pack/.vscode/extensions.json` | `.vscode/extensions.json` | Recommends `biomejs.biome`. Missing-only. |

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
