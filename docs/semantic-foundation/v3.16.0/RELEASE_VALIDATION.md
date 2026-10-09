# Release Validation v3.16.0

Candidate status: **additive successor candidate**.

This release keeps the v3.15.0 semantic-foundation inventory. It admits repository `l9-conformance` and records the reachable published profile `l9.fixture-profile/core@1`. It adds no ledger, schema, invariant, contract, receipt family, vocabulary term, ProductKind, or ADR.

v3.15.0 remains unchanged.

## The Unknown being closed

Global law requires ProductKind `dependency` / archetype `l9.dependency-archetype/semantic-subsystem@1` to satisfy conformance class `core`, and assigns profile resolution to `l9-conformance`. No admitted publication surface provided a profile id. Downstream product manifests that consume `conformance.profile_refs` stayed unresolved.

v3.16.0 is the admission of that coordinate. The profile bytes live in `Quantum-L9/l9-conformance` and hash to `sha256:3d2cb01a2b872215a3e2298b4e3b3d7ae99ecf867d6486f5730a3f98aba2bb2f`.

## Semantic changes

Modified canonical ledgers:

- `semantics/projection_profiles.yaml`:
  - `source_classes.conformance_profiles.canonical_owner` stays `l9-conformance`.
  - `admitted_profiles` lists exactly `l9.fixture-profile/core@1`, class `core`, distribution repository `Quantum-L9/l9-conformance`, path `catalog/fixture-profile-core-1.yaml`, and the digest above.
- `semantics/repository_registry.yaml`:
  - adds `l9-conformance` with `provider: github`, `organization: Quantum-L9`, `repository: l9-conformance`, `lifecycle: current`, `class_ref: l9.repository-class/l9@1`.
  - the census is 33. Every other entry is unchanged.

`scripts/validate-semantics.py` pins that census in RC-023, including the negative cases that reject an unlisted repository.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.15.0/`, unchanged.
