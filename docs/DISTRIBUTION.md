# Distribution model — org defaults and non-CI governance

> **Retired (campaign l9-dot-github-ci-boundary-v1):** this repository no longer
> distributes, seeds, synchronizes, or versions L9 CI implementation. The
> `l9-ci-pack`, the Actions seeders (`auto-seed-new-repo.yml`,
> `seed-governance.yml`), the drift sync (`continuous-sync.yml`), the template
> dispatch (`dispatch-template-update.yml`), and the consumer sync script
> (`templates/sync_ci_from_pack.py`) have been removed. CI targeting,
> versioning, reconciliation, and enforcement belong to `l9-ci-core` (runtime
> execution) and the `l9-ci-control-plane` (policy); neither lives here.

## What still distributes from here

| Mechanism | Files | Token needed? | Update propagation |
| --- | --- | --- | --- |
| **Inheritance** (automatic) | `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `FUNDING.yml`, `pull_request_template.md`, `ISSUE_TEMPLATE/*` | No | Instant, live from `main` |
| **Reference** (`workflow_call`) | governance workflow *logic* (`governance-pr.yml`, `governance-issue.yml`) | No | Instant, on tag move |
| **Manual copy** | `templates/` files GitHub cannot inherit | No | Copy by hand, when a repo needs them |

### Inheritance covers most of the repo

Any repo without its own copy falls back to the org default automatically. Caveats:

- The `.github` repo must be **public** — a private one disables inheritance entirely.
- Files must sit in the repo root, `.github/`, or `docs/`; issue templates must be
  in `.github/ISSUE_TEMPLATE/`.
- Override is **all-or-nothing per file**. One local `SECURITY.md` in a repo means
  that repo ignores the org default for that file. There is no merging.

### Reference covers non-CI governance workflow logic

Workflows are *not* community health files and are never inherited. But they do not
need copying either. `governance-pr.yml` and `governance-issue.yml` live here as
`workflow_call` callees; each repo has a caller pinned to `@v1`. Cross-repo
`workflow_call` requires the callee repo be accessible — public satisfies this.

**Consequence**: to change a governance rule org-wide, edit `governance-pr.yml`
here and move the `v1` tag. Consumers pick it up on their next PR. Zero token
use, zero fan-out, zero PRs.

### Manual copy covers the non-inheritable `templates/` files

Org inheritance is convenient for repos that stay inside Quantum-L9, but some
files are **never** inherited (`CODEOWNERS`, `dependabot.yml`, labels, issue/PR
templates) and forks/templates need them visible in-tree. `templates/` is the
copy source; nothing here pushes it automatically. New repositories copy the
files they need by hand — see `templates/README.md`.

## Tag policy (governance callers)

Tag `v1` so callers have something to pin:

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
caught before rollout rather than after.
