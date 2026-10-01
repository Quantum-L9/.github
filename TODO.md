# TODO

## Deprecate `policies/` when the semantic compiler is online

`policies/repo-classes.yml`, `policies/repo-settings.yml`, and
`policies/mandatory-files.yml` are a second classification of what a
repository receives. Product kind, ownership, and distribution already live
in `semantics/product_kinds.yaml`, `semantics/authority_model.yaml`, and
`semantics/lifecycle.yaml`. The compiler contract is
`semantics/compiler_contract.yaml`.

When that compiler is online, retire this policy set and the workflows that
apply it:

- `repo-birth-bootstrap.yml` — remote apply at `l9-repo-template` `make new-repo`
- `auto-seed-new-repo.yml` — file materialize
- `enforce-policies.yml` — weekly settings and mandatory-file sweep
- `ops/repo-class-profile.js` — the class resolver

A repository should receive capabilities from its ProductTopology and
ProductKind, not from `.l9/org-birth-profile.yaml` plus a birth class.
`.github/workflows/governance.yml` in `policies/mandatory-files.yml` is
already stale and goes away with this set.

## Audit the boundary with `l9-repo-template`

`docs/BOUNDARIES.md` says `Quantum-L9/l9-repo-template` `make new-repo` births
a repository and this repo applies what the organization requires. Confirm
that split and remove the overlap.

Check:

- `make new-repo` creates the repository and dispatches `repo-birth-bootstrap.yml`. Remote apply (labels, settings) stays here. File materialize stays with `auto-seed-new-repo.yml`. One owner per capability.
- The class marker `.l9/org-birth-profile.yaml` is declared by the template. `policies/repo-classes.yml` is the only map of what that class receives.
- `l9-repo-template` `scripts/inventory_check.py` `DENY_CI_DISTRIBUTION` and the FORBID lists in `policies/repo-classes.yml` name the same paths. One list should be the authority.
- `docs/BOUNDARIES.md` still cites `policies/CODEOWNERS` and `policies/governance-caller.yml`. Those paths are not the files in this tree.

## Audit the boundary with `l9-ci-core`

`docs/BOUNDARIES.md` says this repo does not execute, lint, test, scan, or decide whether code is correct. Canonical CI is `Quantum-L9/l9-ci-core` `.github/workflows/org-ci.yml`, required by the organization ruleset **L9 canonical CI required**. Confirm that split and remove the leftover distribution.

Check:

- Nothing in `policies/` should install a consumer CI workflow.
- `policies/mandatory-files.yml` still requires `.github/workflows/governance.yml` from `templates/governance-caller.yml`. That caller is not canonical CI.
- This repository was excluded from ruleset `21895545` because `org-ci.yml` rejects the repository name `.github` in `build-artifact-manifest`. Decide whether `.github` is a governed CI target or stays outside that ruleset on purpose.
- Workflows in this repo that lint or validate (`actionlint.yml`, `validate-starters.yml`, `sha-pin-audit.yml`) are either organization-plane checks or work that belongs in `l9-ci-core`. Name which is which.
