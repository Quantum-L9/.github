# Rulesets

Two kinds of ruleset live here, and the difference is the whole point.

## The canonical CI ruleset — `active`

`l9-canonical-ci-required.json` is **L9 canonical CI required** (org ruleset
id `21895545`, active since 2026-08-31). It binds the default branch of every
non-archived repository except `.github` to the required workflow
`Quantum-L9/l9-ci-core` / `refs/heads/main` / `.github/workflows/org-ci.yml`
and requires the status check `Analyze (central Core)` with
`strict_required_status_checks_policy: true`, so a green check only counts
when it evaluated the head against the current base
(`l9-ci-core/.l9/release-plane.yaml` `admission_freshness`).

It is recorded here so that a change to it is a reviewed PR, not a UI click.
`scripts/apply-rulesets.sh` applies it exactly as recorded and refuses it in
any state but `active`; `scripts/verify-pack.sh` asserts the binding, the
strict policy and the check context. `.github` is excluded because
`org-ci.yml` rejects the repository name `.github` in
`build-artifact-manifest`.

What it blocks: a merge whose head has no current passing
`Analyze (central Core)`. What that check contains is decided in
`l9-ci-core` (`docs/ACTIVATION.md` there): Semgrep technical gate, Core's
Biome check, and the repository's own `make setup/validate/check/test` once
it declares the Repository Execution V2 contract.

## The advisory rulesets — `evaluate`

| File | Targets | Rules |
| --- | --- | --- |
| `org-advisory-pr.json` | default branch, all repos except `.github` | PR required, `Governance / pr` reported |
| `org-advisory-hygiene.json` | all branches | deletion + force-push observed |

In evaluate mode a rule runs and reports to Insights **without blocking
anyone**. `evaluate` requires GitHub Enterprise Cloud; on lower plans
`apply-rulesets.sh` skips them rather than silently falling back to `active`.

### Promotion is a deliberate, dated decision

```bash
# observe for at least 4 weeks, then review Insights before touching this
jq '.enforcement = "active"' rulesets/org-advisory-pr.json > /tmp/r.json
```

Do not promote an advisory ruleset that has not produced 4 weeks of clean
evaluate data. See `docs/ADVISORY.md`.

## Warning

Never add `required_status_checks` to a ruleset that targets branch
**creation** — an org-wide rule doing so can block repository creation
entirely. The canonical ruleset sets `do_not_enforce_on_create: true` on both
rules for this reason.
