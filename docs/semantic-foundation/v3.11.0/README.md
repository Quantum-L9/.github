# Semantic Foundation v3.11.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor closes one upstream semantic dependency: the canonical projection profile through which Cursor-Governance derives its ActorIdentity and SurfaceIdentity projection from the two canonical identity registries. Without it the downstream deterministic projector has no canonical profile to resolve and the Cursor-Governance identity projection stays ungenerated.

## Bounded delta

- Adds exactly one consumer projection profile to `semantics/projection_profiles.yaml`: `l9.projection/cursor-governance-identity@1`, consumer `Cursor-Governance`, sources `actor_registry` and `surface_registry` only, output schema `l9.projection.cursor-governance-identity/v1` (the existing downstream consumer contract). It projects the canonical actor and surface entries, their bounded kind and status vocabularies, and their typed historical aliases, and declares the ownership boundaries it does not carry (identity ownership, credentials, roles and grants, actor-to-surface assignment, adapter, provider, or governance-profile selection, runtime-marker or runtime-evidence interpretation, execution authority).
- Adds RC-019 to `scripts/validate-semantics.py`, a closure check for this exact profile coordinate, with a fail-closed negative-case batch. RC-019 does not define an identity profile family by name and does not cap how many Cursor-Governance profiles may exist.

## Non-goals

v3.11.0 adds no actor, surface, alias, or identity dimension; no invariant, contract, schema, semantic ledger, projection framework, or ADR. It does not interpret runtime identity evidence and carries no credential, role, or permission semantics. It does not modify `semantics/actor_registry.yaml`, `semantics/surface_registry.yaml`, the existing `l9.projection/cursor-governance-operating-plane@1` profile, the Strategic Plan or Strategic Cognition models, ProductKind, ProductTopology, or repository identity. It does not modify Cursor-Governance; generating and binding the projection remain downstream work.

## Authority

`Quantum-L9/.github` owns canonical ActorIdentity and SurfaceIdentity and this projection profile. Cursor-Governance owns the generated projection, its local governing binding, actor-to-surface assignment, roles, principals, adapters, credential and environment coordinates, and runtime identity interpretation. The projection is derived, non-canonical, provenance-bearing, and invalidated by any material change to either registry.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.10.0/` (Strategic Plan semantic model). The predecessor release record remains immutable.
