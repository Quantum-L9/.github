# Distribution

Files leave this repository in three ways. CI does not. `on-org-update` is a
retired seed category and throws. Canonical CI is
`Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml`, enforced by an
organization required-workflow ruleset.

Which files a repository actually receives is `policies/repo-classes.yml`.
The mode names are `docs/REPO_BIRTH_PROFILES.md`.

## Mechanisms

| Mechanism | What moves | Credential | How an edit propagates |
| --- | --- | --- | --- |
| **Inheritance** | The passive community-health surfaces: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SUPPORT.md`, `.github/FUNDING.yml`, `.github/VULNERABILITY_REPORT.yml`. For `self_governed` repositories, `SECURITY.md` and the templates as well. | None | Live from `main`. These are never in the seed payload. One local copy blocks inheritance for that file. There is no merge. |
| **Reference** | `governance-pr.yml` and `governance-issue.yml`, called from the consumer's `.github/workflows/governance.yml` | None for the callee | The caller pins a full commit SHA (`policies/governance-caller.yml`). Moving a tag does not retarget a caller that already pins a SHA. Missing-only seed does not overwrite an existing caller. |
| **Physical copy** | `.github/CODEOWNERS`, `.github/dependabot.yml`, the governance caller where the class allows it, `SECURITY.md`, `.github/ISSUE_TEMPLATE/*`, `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/release.md`. Default categories: `codeowners`, `dependabot`, `governance`, `community-health`, `issue-templates`, `pr-templates`. `labels` is opt-in. | Org secret `GH_TOKEN` | Missing-only pull request. An existing file is left as-is. |
| **Remote apply** | Labels and repository settings | Org secret / governance App | API state, not a file. `sync-labels-all.yml`, `enforce-policies.yml`, `repo-birth-bootstrap.yml`. |

Seed sources that are also this repository's own files are read from those
files. Consumer-only files live in `policies/`:

- `policies/CODEOWNERS` → `.github/CODEOWNERS` (skipped when the consumer already has a root `CODEOWNERS`)
- `policies/governance-caller.yml` → `.github/workflows/governance.yml`
- `.github/dependabot.yml`, `.github/labels.yml` (opt-in)
- `SECURITY.md` (`community-health`; advisory URLs rewritten to the consumer)
- `.github/ISSUE_TEMPLATE/` — seven named forms (`1-bug.yml`, `2-feature.yml`, `3-task.yml`, `4-incident.yml`, `ci-failure.yml`, `gov-violation.yml`, `config.yml`), never a directory sweep; `config.yml` advisory URL rewritten to the consumer
- `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/release.md` (`pr-templates`, named files, never a directory copy)

`community-health` copies `SECURITY.md` only. It is the one community-health
file whose bytes differ per consumer. `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
`SUPPORT.md`, `FUNDING.yml` and `VULNERABILITY_REPORT.yml` are inherited and a
seeded copy would create a second owner. CI is never in the payload; the
`on-org-update` and `l9-ci-pack` categories throw.

Physical copy has three entrypoints and one decision. `auto-seed-new-repo.yml`
(hourly), `seed-governance.yml` (dispatch) and `ops/sync-org-files.sh`
(manual, local checkout) all resolve the target's class through
`ops/repo-class-profile.js` and build the payload through
`ops/build-seed-payload.js`. `all` means the class's categories. An explicit
category list is filtered by the class: INHERIT drops, FORBID is refused with
the class and path named. Every entrypoint is missing-only; the shell path
reports each existing file as kept and a second run is byte-identical.

Every source a requested category names is required: a missing one fails the
build before any consumer is touched, so the payload never shrinks silently.
Only a 404 reads as "absent" on a consumer; a 403, 409, 5xx, or a directory
where a file belongs fails that repository instead of planning a write or
falling back to `default`. Before writing, both seeders list the consumer's
other open PRs; one already changing a planned path (including a rename's
previous name) leaves the repository `BLOCKED_CONFLICT` with nothing written,
and a listing that cannot be read is `BLOCKED_PERMISSION` or `UNREACHABLE`.
Both seeders pin the default-branch commit before the first policy read; root
`CODEOWNERS`, the class marker and every destination are read at that commit,
and a branch that cannot be pinned plans nothing. The default branch is
re-read before the seed branch moves; if it moved, the
run stops for that repository (`BASE_MOVED`) and the next one replans. This
narrows the race with other writers; it does not close it. An empty repository
is reported `UNINITIALIZED_NOT_SEEDED` by the hourly sweep and retried; no
other 409 is treated that way.

`continuous-sync.yml` (Manual Update) is the exception to missing-only. It
restores `.github/CODEOWNERS` to the exact org bytes, and
`.github/dependabot.yml` to the render for the repository's root shape, when
they drift. It skips a repository with `.l9/no-sync`, and acts only where the
repository's class materializes the file: it resolves the class (and a root
`CODEOWNERS`, which wins) first and plans from the same class-filtered payload
the seeders build, so a `self_governed` repository gets neither file and a
malformed marker gets nothing. It runs only when dispatched: nothing
schedules it and no push starts it. `dry_run=true` (Preview, the default)
reports drift and writes nothing; `dry_run=false` (Apply) opens one reviewable
PR per drifted repository. Any value other than an explicit `false` previews.
That workflow uses the governance GitHub App (`GOVERNANCE_APP_ID`), not
`GH_TOKEN`.

`.github/dependabot.yml` is MANAGED-RENDERED
([ADR 0019](adr/0019-dependabot-managed-rendered.md)). `ops/render-dependabot.js`
renders it from:

- the fragments in `policies/dependabot/`;
- the repository root, read at the pinned base:
  - `github-actions` always;
  - `uv` when there is a `uv.lock`;
  - otherwise `pip` for a root `requirements*.txt` or a PEP 621 `pyproject.toml`;
  - `pre-commit` when there is a `.pre-commit-config.yaml`;
- Core's `core-owned-tools.json`, vendored at
  `policies/vendor/l9-ci-core/` and digest-checked.

The rendered file ignores Core-owned tools and the Core, SDK and `.github`
action pins. Every entrypoint passes the shape to the one builder. A root that
cannot be listed is `UNREACHABLE` (or `BLOCKED_PERMISSION`), never an
actions-only render.

**Rollout.** Do not run Apply until this renderer is merged. Before it, a
restore wrote actions-only bytes over legitimate `uv` / `pip` / `pre-commit`
entries. Until then, a repository with extra ecosystems opts out with
`.l9/no-sync`. After merge, the operator Previews one repository at a time
(`repo_filter` = `Cursor-Governance`, `l9-ci-sdk`, `gate_sdk`), reviews the
planned `dependabot.yml` restore, and Applies per repository only on explicit
approval.

The `.github` repository must be public. A private one disables inheritance,
and cross-repo `workflow_call` needs the callee to be readable.

## Credentials

`seed-governance.yml` and `auto-seed-new-repo.yml` read the org secret
`GH_TOKEN`. A token that can write `.github/workflows/*` is required for the
governance caller. The governance App can request that permission, but an org
install only gains it after a browser approval, so seed does not depend on
that click.

`continuous-sync.yml` mints a governance App installation token from
`GOVERNANCE_APP_ID` (variable) and `GOVERNANCE_APP_PRIVATE_KEY` (secret). Both
are defined on the `governance-distribution` environment, not the repository
or organization, so the job must run in that environment. Before it did, every
run failed at token minting with `Input required and not supplied: app-id`.
Branch provenance is checked against the App's own `<app-slug>[bot]` identity.
The App's workflows permission takes effect only after an org-owner browser
approval. Without it, an Apply cannot move a sync branch whose commit re-pins
`.github/workflows/governance.yml`: that repository is not updated and the run
summary reports it blocked (`BLOCKED_PERMISSION` for a new branch,
`BLOCKED_POLICY` for a rebuilt one).

Those workflows, and `repo-birth-bootstrap.yml`, run in the
`governance-distribution` environment.

## Steady state

| Change | What to do |
| --- | --- |
| Contributing guide, code of conduct, support, funding, vulnerability report form | Edit the file and merge. Every repo with no local copy inherits it live. Nothing to seed. |
| Security policy | Edit `SECURITY.md` and merge. `self_governed` repos inherit it. Repos that were seeded a copy keep the old file; seed will not overwrite it. |
| PR or issue template | Edit and merge. The seed sources are `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/release.md`, and `.github/ISSUE_TEMPLATE/*`. Seeded copies are not overwritten. |
| Governance gate rule | Edit `governance-pr.yml` or `governance-issue.yml`, then re-pin the SHA in `policies/governance-caller.yml` and update consumers that already have a caller. |
| CODEOWNERS or dependabot | Edit `policies/CODEOWNERS`, or the fragments in `policies/dependabot/` (then regenerate `.github/dependabot.yml` with `node ops/render-dependabot.js > .github/dependabot.yml`), and merge. A new Core list is vendored with its commit and sha256 in `policies/dependabot/core-owned-tools.source.json`. Then dispatch `continuous-sync.yml`: Preview to read the drift, Apply to open a restore PR where those files drifted. |
| New repository | `auto-seed-new-repo.yml`, or `workflow_dispatch` on `seed-governance.yml`. `l9-repo-template` `make new-repo` dispatches `repo-birth-bootstrap.yml` for one repo. |

## Appendix A — secrets and called workflows

`governance-pr.yml` and `governance-issue.yml` use the automatic `GITHUB_TOKEN`
only. `policies/governance-caller.yml` does not pass `secrets: inherit`. A
called workflow does not receive the caller's secrets unless the caller passes
them by name. Prefer a named `secrets:` entry.

If a secret is omitted, the callee sees an empty string and fails at the point
of use.

## Appendix B — Actions access policy (the rollout trap)

Cross-repo `workflow_call` is subject to the **consumer** repo's Actions
policy, not just this repo's visibility. Under *Allow OWNER actions and
reusable workflows*, or a narrower allow-list, a caller referencing
`Quantum-L9/.github/...` fails before any step runs.

Because both repos are in the same org and this one is public, the default
*Allow all* and *Allow OWNER* settings both work. It breaks when:

- Actions are **disabled** entirely on a consumer repo.
- `allowed_actions` is `local_only`.
- `allowed_actions` is `selected` and the allow-list omits `Quantum-L9/*`.
- An **enterprise-level** policy overrides the org. Enterprise, then org, then
  repo. A setting locked at repo level is set at org level; locked there, it
  is set at the enterprise level.

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

Or at org level once:

```bash
gh api -X PUT orgs/Quantum-L9/actions/permissions \
  -f enabled_repositories=all -f allowed_actions=all
```

`scripts/preflight.sh` checks this for every repo before seeding. The weekly
governance report names repos whose Actions policy would stop the caller, and
points here.

## Appendix C — PR template, PR body, and caller pins

The PR template is organization-managed: one canonical file,
`.github/pull_request_template.md` in this repository, and no divergent copy
anywhere else. `continuous-sync.yml` extends its exception to missing-only
(above) to two more paths, decided per repository by `policies/repo-classes.yml`:

| Path | Class rule | Sync action |
| --- | --- | --- |
| `.github/pull_request_template.md` | class seeds `pr-templates` | carry the canonical bytes; a divergent copy is replaced |
| `.github/pull_request_template.md` | class INHERITS it | carry no copy; a local copy byte-identical to the org template blocks inheritance and is removed; a divergent one is `BLOCKED_OWNERSHIP` and left in place |
| `.github/workflows/governance.yml` | class seeds `governance` | re-pin only: the `governance-pr.yml` / `governance-issue.yml` `uses:` SHAs follow `policies/governance-caller.yml`; everything else in the consumer's caller (e.g. `strict: true`) is kept |

Alternate templates (a `PULL_REQUEST_TEMPLATE/` directory, root or `docs/`
copies) are reported per repository and never edited. Each run's summary gives
every repository one status: `INHERITED`, `CANONICAL_COPY`, `UPDATE_PR_OPEN`,
`UPDATE_PENDING_MERGE`, `DRIFT` (Preview), `BLOCKED_PERMISSION`,
`BLOCKED_POLICY`, `BLOCKED_OWNERSHIP`, `BLOCKED_CONFLICT` (another open PR
changes a planned path), `BASE_MOVED`, `UNINITIALIZED` (no commits),
`OPTED_OUT`, `UNREACHABLE`, or `UNVERIFIED`. Every planning read, the
`.l9/no-sync` opt-out included, is pinned to the default-branch commit read
first, and that commit is re-checked before the sync branch moves, so an
opt-out committed mid-run stops publication (`BASE_MOVED`). A `.l9/no-sync`
that is a directory, like a class marker that is one, is `UNREACHABLE` with
nothing planned, never read as absent. Any repository
left `UNREACHABLE`, `BLOCKED_PERMISSION`, or `UNVERIFIED` fails the run. A
change to the template, the caller, CODEOWNERS, dependabot, or the class policy
reaches consumers only when an operator dispatches the workflow. Preview first,
then Apply. Each repository gets one
atomic commit, moved onto the sync branch through the seeders' guarded path
(`ops/seed-branch-safety.js`): only when the branch holds nothing but this
workflow's own verified commit (subject, `<app-slug>[bot]` committer,
signature), and as a server-side compare-and-swap on the inspected sha.

**PR body.** The template's machine-owned regions (`PROTECTED-ROOT-PATHS`,
`EVIDENCE`, `CHANGES-BY-INTENT`, `FILES-TOUCHED`) are filled by one renderer,
Cursor-Governance `ops/scripts/compose_pr_body.py`: at publication by `make pr`,
and on every later PR event by the `body` job in `governance-pr.yml`, which
runs that composer at the commit pinned in the job (`COMPOSER` and the checkout
`ref`, moved together). Reviewer text outside the regions is never rewritten;
an unchanged body is never PATCHed; a head no local gate measured is marked
`STALE` in Evidence, never claimed. On such a head the Protected-root paths are
remeasured with the repository's own `validate_root_file_protection.py` (or
marked not measured when it cannot run), and an Edit mode, Why or Proof that
described an earlier head's path set is withdrawn as unverified rather than
carried forward; a reviewer's own justification text is left as written. This
repository's own PRs get the same job through `pr-files.yml`.

The template's visible order puts the inventory first (Files touched, then
Changes by intent) and Protected-root last; the `L9_PROTECTED_ROOT_PR` stamp
stays the first line. It carries no placeholder the composer cannot honestly
complete: no bare `Closes #`, no sample paths, no sample evidence. The
composer marks each receipt `BOUND`, `STALE` or `UNVERIFIED` against the tree
it describes, ticks a Gate box only from a bound receipt that measured it, and
writes an explicit *unresolved* marker into fields that need the author's
judgment (Reviewer focus, an applicable Semantic change, an unevidenced Type of
Change). No PR needs a repository-wide manifest or per-file metadata header:
the body's regions are the inventory.

PRs the seeders and Manual Update open carry their own short body in the
sections the `gates` job checks — Problem, Fix, Risk (exactly one), Evidence
(source commit, exact base, class, and the changed paths), Gates — built from
what the run did. Consumer CI is left unchecked as unverified; nothing claims a
check the run did not observe. They are not a second composer: they have no
machine-owned regions, so the `body` job leaves them as written.

**Shipping a body or gate change to consumers.** Merge the
`governance-pr.yml` change, set the merged commit as the pin in
`policies/governance-caller.yml`, and merge that. Then dispatch
`continuous-sync.yml`: Preview lists the callers it would re-pin, and Apply
re-pins every eligible consumer caller through a reviewable PR. A consumer's
run still reflects its previous pin until that PR merges; the run summary lists
who is pending.
