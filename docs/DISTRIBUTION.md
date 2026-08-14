# Distribution model — what the token actually blocks

## Short answer

**No. The missing token does not block pushing the current version of
`Quantum-L9/.github` to org repos — because most of it is never pushed at all.**

GitHub *inherits* community health files by reference. There is no copy, no sync,
and no token involved. Repos read the latest `main` of `Quantum-L9/.github` live.
Merge a fix to `SECURITY.md` and all 29 repos reflect it on the next page load.

The token gated exactly three files, and only for a **one-time seed** — not for
ongoing updates.

## The three distribution mechanisms

| Mechanism | Files | Token needed? | Update propagation |
| --- | --- | --- | --- |
| **Inheritance** (automatic) | `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `FUNDING.yml`, `pull_request_template.md`, `ISSUE_TEMPLATE/*` | No | Instant, live from `main` |
| **Reference** (`workflow_call`) | governance workflow *logic* | No | Instant, on tag move |
| **Physical copy** (seed) | Full `templates/` bundle (CODEOWNERS, caller, dependabot, labels, community-health, issue/PR templates, on-org-update) | **Yes, once** (or when new surfaces are added) | Re-run seed / consumer `make sync-ci` |

### Inheritance covers most of the repo

Any repo without its own copy falls back to the org default automatically. Caveats:

- The `.github` repo must be **public** — a private one disables inheritance entirely.
- Files must sit in the repo root, `.github/`, or `docs/`; issue templates must be
  in `.github/ISSUE_TEMPLATE/`.
- Override is **all-or-nothing per file**. One local `SECURITY.md` in a repo means
  that repo ignores the org default for that file. There is no merging.

### Reference covers workflow logic

Workflows are *not* community health files and are never inherited. But they do not
need copying either. `governance-pr.yml` and `governance-issue.yml` live here as
`workflow_call` callees; each repo has a caller pinned to `@v1`. Cross-repo
`workflow_call` requires the callee repo be accessible — public satisfies this,
which the inheritance requirement already forces.

**Consequence**: to change a governance rule org-wide, edit `governance-pr.yml`
here and move the `v1` tag. All 29 repos pick it up on their next PR. Zero token
use, zero fan-out, zero PRs.

### Physical copy covers the full `templates/` bundle

Org inheritance is convenient for repos that stay inside Quantum-L9, but it is the
wrong distribution model for **repo templates**, forks, and contributors who need
files visible in-tree. `templates/` is therefore the SSOT for a **physical** seed:

1. **`CODEOWNERS`**, **`dependabot.yml`**, **governance caller**, **labels**
2. **Community health** (`CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`,
   `SUPPORT.md`, `LICENSE`, `.github/FUNDING.yml`)
3. **Issue + PR templates** and the **`on-org-update`** receiver workflow
4. **`l9-ci-pack/`** — Core hub callers (`l9-analysis.yml`, lint templates) and
   `.github/governance/*.yaml`. This repo distributes the pack; `l9-ci-core`
   executes CI. See `docs/BOUNDARIES.md`.

`seed-governance.yml` (and `auto-seed-new-repo.yml`) seed these once per repo via
PR using `ops/build-seed-payload.js`, matching `ops/sync-org-files.sh`. Existing
files are left untouched (missing-only). Root `CODEOWNERS` is never overwritten by
`.github/CODEOWNERS`. New repos from `l9-dependency-template` inherit the pack
because it is in the template tree; `make sync-ci` is refresh-only.

## Corrected assessment of the earlier claim

The previous statement — "does not open PRs yet, needs a token with write scope
across 29 repos" — was **true but badly framed**. It implied governance updates were
blocked pending a token decision. They are not:

- Findings 1, 3, 4 (PR template path, SECURITY.md, CONTRIBUTING.md) propagate on
  merge with **no token whatsoever**.
- Finding 2 (CODEOWNERS) needs the one-time seed.
- Finding 5's real deliverable was never fan-out — it is the `workflow_call`
  indirection that makes fan-out unnecessary. The earlier version proposed
  recurring distribution, which was the wrong architecture: it would have required
  standing write access to 29 repos forever, to solve a problem that a pinned tag
  solves with none.

## Credential recommendation

Do **not** use a PAT. Use a **GitHub App** installed on the org, scoped to
`contents: write` and `pull_requests: write`:

- No human owner; survives offboarding.
- Installation token expires in one hour.
- `create-github-app-token` mints it per run — nothing long-lived in secrets.
- The workflow is `workflow_dispatch`-only and pinned to a protected
  `governance-distribution` environment, so a required reviewer approves each run.

Since seeding runs roughly once ever, App credentials can be uninstalled afterward
and reinstalled only if a new repo needs seeding.

## Order of operations

1. `./scripts/preflight.sh` — verify team slugs resolve, `.github` is public, list
   which repos already have local overrides blocking inheritance.
2. Fix any placeholder team slug that preflight flags as nonexistent.
3. Merge to `main`. **Findings 1, 3, 4 are live at this point, no token.**
4. Tag `v1` so callers have something to pin:

   ```bash
   # immutable release tag + moving alias
   git tag v1.0.0
   git push origin v1.0.0
   git tag -f v1 v1.0.0
   git push origin v1 --force
   ```

   Callers pin `@v1`. To ship a governance change later, repeat with a new
   immutable tag and re-point the alias:

   ```bash
   git tag v1.1.0 && git push origin v1.1.0
   git tag -f v1 v1.1.0 && git push origin v1 --force
   ```

   Never delete `v1`; force-move it. Deleting breaks every caller until it reappears.
5. Install the GitHub App; configure `governance-distribution` environment reviewers.
6. Run `seed-governance.yml` with `mode: dry-run`, `repo_filter: l9-` — inspect the
   summary table.
7. Re-run with `mode: seed` on the filtered subset, review those PRs, then drop the
   filter.
8. Optionally uninstall the App.

## Ongoing steady state

| Change | Action | Token? |
| --- | --- | --- |
| Security policy text | Edit `SECURITY.md`, merge | No |
| PR template structure | Edit `pull_request_template.md`, merge | No |
| A governance gate rule | Edit `governance-pr.yml`, move `v1` tag | No |
| Code ownership routing | Edit `templates/CODEOWNERS.repo`, re-run seed | Yes |
| New repo from `l9-dependency-template` | Files already in the template tree | No |
| Blank repo (no template) | `workflow_dispatch` `seed-governance.yml` or `auto-seed-new-repo.yml` | Yes |
| New repo joins the org (legacy) | Run seed filtered to that repo | Yes |

Only the last two rows ever need it.


---

## Appendix A — `secrets: inherit`

Both callees currently use only the automatic `GITHUB_TOKEN`, so callers pass
nothing. The token is minted per job with the `permissions:` block declared in the
callee, and expires when the job ends.

The moment a governance job needs a real secret, that changes. Secrets are **not**
visible to a called workflow automatically — the caller must pass them explicitly:

```yaml
jobs:
  pr:
    uses: Quantum-L9/.github/.github/workflows/governance-pr.yml@v1
    secrets: inherit          # passes all caller secrets
    # or, preferred, be explicit:
    # secrets:
    #   SEMGREP_TOKEN: ${{ secrets.SEMGREP_TOKEN }}
```

`inherit` works for callers in the same organization. Prefer named passing where
practical — `inherit` hands the callee every secret the caller can see, which is
broader than least privilege.

Failure mode if forgotten: the callee sees an empty string rather than an error, so
it fails at the point of use with a confusing auth message rather than at the call.

## Appendix B — Actions access policy (the rollout trap)

Cross-repo `workflow_call` is subject to the **consumer** repo's Actions policy, not
just this repo's visibility. Under a repo or org setting of *Allow OWNER actions and
reusable workflows* — or a narrower allow-list — a caller referencing
`Quantum-L9/.github/...@v1` fails before any step runs.

Because both repos are in the same org and this one is public, the default
*Allow all* and *Allow OWNER* settings both work. It breaks when:

- Actions are **disabled** entirely on a consumer repo.
- `allowed_actions` is `selected` with an allow-list that omits `Quantum-L9/*`.
- An **enterprise-level** policy overrides the org. Note the settings hierarchy:
  enterprise → org → repo. If the setting appears locked at repo level, it is set
  at org level; if locked there, it is set at the enterprise level.

Diagnose per repo:

```bash
gh api repos/Quantum-L9/<repo>/actions/permissions
# -> {"enabled": true, "allowed_actions": "all"}          OK
# -> {"enabled": false}                                    caller will never run
# -> {"allowed_actions": "selected"}                       check the allow-list:
gh api repos/Quantum-L9/<repo>/actions/permissions/selected-actions
```

Remediate:

```bash
gh api -X PUT repos/Quantum-L9/<repo>/actions/permissions \
  -F enabled=true -f allowed_actions=all
```

Or at org level once, which is the higher-leverage fix:

```bash
gh api -X PUT orgs/Quantum-L9/actions/permissions \
  -f enabled_repositories=all -f allowed_actions=all
```

`scripts/preflight.sh` now checks this for every repo (section 5) so the trap is
caught before seeding rather than after.
