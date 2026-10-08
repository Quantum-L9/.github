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
- `.github/ISSUE_TEMPLATE/*` (`config.yml` advisory URL rewritten to the consumer)
- `.github/pull_request_template.md` and `.github/PULL_REQUEST_TEMPLATE/release.md` (`pr-templates`, named files, never a directory copy)

`community-health` copies `SECURITY.md` only. It is the one community-health
file whose bytes differ per consumer. `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`,
`SUPPORT.md`, `FUNDING.yml` and `VULNERABILITY_REPORT.yml` are inherited and a
seeded copy would create a second owner. CI is never in the payload; the
`on-org-update` and `l9-ci-pack` categories throw.

`continuous-sync.yml` is the exception to missing-only. It restores
`.github/CODEOWNERS` and `.github/dependabot.yml` when they drift, unless the
repo has `.l9/no-sync`. That workflow uses the governance GitHub App
(`GOVERNANCE_APP_ID`), not `GH_TOKEN`.

The `.github` repository must be public. A private one disables inheritance,
and cross-repo `workflow_call` needs the callee to be readable.

## Credentials

`seed-governance.yml` and `auto-seed-new-repo.yml` read the org secret
`GH_TOKEN`. A token that can write `.github/workflows/*` is required for the
governance caller. The governance App can request that permission, but an org
install only gains it after a browser approval, so seed does not depend on
that click.

Those workflows, and `repo-birth-bootstrap.yml`, run in the
`governance-distribution` environment.

## Steady state

| Change | What to do |
| --- | --- |
| Contributing guide, code of conduct, support, funding, vulnerability report form | Edit the file and merge. Every repo with no local copy inherits it live. Nothing to seed. |
| Security policy | Edit `SECURITY.md` and merge. `self_governed` repos inherit it. Repos that were seeded a copy keep the old file; seed will not overwrite it. |
| PR or issue template | Edit and merge. The seed sources are `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE/release.md`, and `.github/ISSUE_TEMPLATE/*`. Seeded copies are not overwritten. |
| Governance gate rule | Edit `governance-pr.yml` or `governance-issue.yml`, then re-pin the SHA in `policies/governance-caller.yml` and update consumers that already have a caller. |
| CODEOWNERS or dependabot | Edit `policies/CODEOWNERS` or `.github/dependabot.yml`. `continuous-sync.yml` opens a restore PR where those files drifted. |
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
