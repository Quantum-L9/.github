# Semantic Foundation v3.45.0
Release status: **admitted additive successor** (ADR-042, 2026-11-21). Admission takes effect at the `main` commit that merges the pull request carrying ADR-042.
## What this release adds
One canonical source changes: `semantics/domain_consumer_bindings.yaml` gains `l9.domain-consumer-binding/manus@1` and a consumer count correction in its `purpose`. Nothing is removed, renamed or redefined.
`manus@1` is the first binding for the Manus consumer. `semantics/actor_registry.yaml` has declared `manus` (`kind: agent`, `status: current`) and `semantics/surface_registry.yaml` has declared `manus-cloud` (`status: current`) across earlier admitted releases; what was missing was a declaration of which domain projections that host requires. Until this release the only statement of that requirement was repository-local, in `Quantum-L9/Cursor-Governance` `governance/host-bindings/manus.yaml`, which binds the operating plane and `coding-agent-execution@1` by owner decision and records `canonical_binding_ref: null` because there was nothing canonical to name.
## Shape
| | Profiles |
|---|---|
| `requires` | `governance@1`, `identity-attribution@1`, `capabilities-dependencies@1`, `contracts-conformance@1`, `evidence-provenance@1` |
| `conditional` | `architecture@1` (`hosted_skill_requirement`); `strategic-value@1` and `signals@1` (`explicit_task_requirement`) |
One surface, `manus-cloud`. No `successor_of`, because no Manus binding precedes this one. `binding_grants_permissions: false`, `action_authority: externally_resolved`, `unresolved: []`.
## What this release does not establish
No credential, role, grant, merge, publication, deployment or execution authority. No capability breadth: the Manus adapter's Infisical capability manifest is a separate artifact and still renders one capability with seven named exclusions. No memory admission. No replacement of `l9.projection/cursor-governance-operating-plane@2`, which the adapter continues to bind at session start; whether a future `manus@2` absorbs it is undecided. No downstream migration: consumers re-project, and this record does not mutate another repository.
## Outstanding unknowns
- The canonical subject digest was not computed for this cut: `check_admission_closure.py` is not present in this tree, so the digest is recorded as Unknown rather than substituted with a different measure. The approved `semantics/` tree is named in `RELEASE_VALIDATION.md` and in ADR-042.
- `Quantum-L9/Cursor-Governance` still carries `canonical_binding_ref: null` and a validator that tolerates it. Moving that repository to `manus@1` is a separate change with its own review.
## Authority
`Quantum-L9/.github` owns these ledgers. Nothing here grants mutation, publication, merge, admission, deployment or execution authority beyond the admission recorded above, which takes effect only at the merge commit.
