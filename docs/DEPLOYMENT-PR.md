## Problem

Quantum-L9 needs organization-wide governance defaults, advisory security posture,
and consistent issue intake without duplicating CI owned by `l9-ci-sdk` or
`l9-ci-core`.

## Fix

Deploys `.github` pack v3.1: inherited community-health files, reusable advisory
governance, evaluate-only rulesets, alert-only secret scanning setup, one-time
CODEOWNERS/caller/Dependabot seeding, issue forms, and weekly posture reporting.

## Risk

- [x] Low — advisory, additive, reversible
- [ ] Medium — shared code, config, or public interface
- [ ] High — breaking, migration, IAM/network, irreversible

Blast radius: organization governance metadata; no application runtime.
Rollback: repoint `v1`, disable evaluate rulesets, revert this PR.

## Evidence

```text
Paste scripts/verify-pack.sh and scripts/preflight.sh output here.
```

## Gates

- [x] No blocking controls enabled
- [x] Push protection remains off
- [x] Rulesets are evaluate-only
- [x] No CI execution duplicated from l9-ci-sdk/l9-ci-core
- [x] GitHub App secrets are not committed

## Reviewer focus

Verify real CODEOWNERS team slugs, advisory defaults, and CI ownership boundary.
