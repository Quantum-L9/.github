# Semantic Foundation v3.16.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor makes one published conformance profile reachable and admits the repository that owns it.

`l9.dependency-archetype/semantic-subsystem@1` already requires conformance class `core`. Profile resolution is owned by `l9-conformance`, not by this repository. Until this release, no admitted repository published a profile id that global semantics could resolve, so a dependency product could not close `conformance.profile_refs`.

## Bounded delta

- `Quantum-L9/l9-conformance` publishes `l9.fixture-profile/core@1` at `catalog/fixture-profile-core-1.yaml` with digest `sha256:3d2cb01a2b872215a3e2298b4e3b3d7ae99ecf867d6486f5730a3f98aba2bb2f`. Membership is the normative fixture `l9.fixture/semantic-subsystem-requires-core@1`, which witnesses the existing archetype requirement. It does not create law and it does not describe memory behavior.
- `semantics/projection_profiles.yaml` records that coordinate under `source_classes.conformance_profiles.admitted_profiles`. `canonical_owner` remains `l9-conformance`.
- `semantics/repository_registry.yaml` admits `l9-conformance` as repository class `l9.repository-class/l9@1`. The census is 33. RC-023 pins the new id and count.

## Non-goals

v3.16.0 adds no invariant, contract, schema, vocabulary term, receipt family, ProductKind, or ADR. It does not copy fixture bodies into `.github`. It does not admit a memory release.

## Authority

`l9-conformance` owns the profile. `Quantum-L9/.github` owns repository identity and the reachable coordinate. A consumer binds the coordinate by reference. It does not invent a second profile id.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.15.0/`. That release record is unchanged.
