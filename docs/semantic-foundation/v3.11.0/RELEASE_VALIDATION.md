# Release Validation v3.11.0

Candidate status: **additive successor candidate**.

This release preserves the v3.10.0 semantic-foundation inventory and adds one consumer projection profile. No actor, surface, alias, identity dimension, invariant, contract, schema, ledger, projection framework, or ADR is added.

## Semantic changes

Modified canonical ledger:

- `semantics/projection_profiles.yaml`, one profile appended after `l9.projection/cursor-governance-operating-plane@1`:
  - `id: l9.projection/cursor-governance-identity@1`, `class: consumer`, `consumer: Cursor-Governance`.
  - `sources.actor_registry.selectors`: `$.schema`, `$.artifact_id`, `$.actor_kinds`, `$.actor_statuses`, `$.actors`, `$.aliases`.
  - `sources.surface_registry.selectors`: `$.schema`, `$.artifact_id`, `$.surface_statuses`, `$.surfaces`, `$.aliases`.
  - `output.schema: l9.projection.cursor-governance-identity/v1`, the existing downstream consumer contract.
  - `forbidden`: `identity_ownership_transfer`, `credential_token_or_signing_key_semantics`, `role_permission_or_grant_semantics`, `actor_to_surface_assignment`, `adapter_provider_or_governance_profile_selection`, `runtime_marker_or_runtime_evidence_interpretation`, `execution_authority`.

Every selector reads a top-level section of its canonical registry through the existing plain-field selector grammar of `semantics/selector_model.yaml`. The profile carries the complete `actors`, `surfaces`, and `aliases` collections, so the downstream deterministic projector selects the referenced identities from canonical entries rather than reconstructing identity locally. It carries no `global_rules`, `does_not_own`, `alias_rules`, or `downstream_obligations` sections; those are law the registries state about themselves, not identity entries.

Explicitly unchanged: `semantics/actor_registry.yaml` (6 actors, 2 aliases), `semantics/surface_registry.yaml` (11 surfaces, 5 aliases), `semantics/identity_model.yaml`, `semantics/identity_assertion.schema.yaml`, `semantics/contracts.yaml`, `semantics/invariants.yaml` (31), `semantics/strategic_cognition_model.yaml`, `semantics/strategic_plan_model.yaml`, every other projection profile, every schema, every capability, artifact class, and ADR, and all prior release records. The profile count is 24; the contract count remains 26.

## Mechanical derivation refreshes

None. `projection_profiles.yaml` is not a declared derivation source of any other ledger, and the validator reported no stale coordinate after the change; the only pre-release failure was SC-008 against the v3.10.0 hash inventory, which this record supersedes.

## Validator delta

- `scripts/validate-semantics.py`: RC-019 Cursor-Governance identity projection closure plus an isolated negative-case batch, each case required to fail at its intended field. RC-018 (Strategic Plan semantic closure, v3.10.0) and every earlier check are unchanged.

## RC-019 Cursor-Governance identity projection closure

RC-019 governs the exact coordinate `l9.projection/cursor-governance-identity@1` and proves:

- the profile exists exactly once;
- its class is `consumer` and its consumer is exactly `Cursor-Governance`;
- its sources are exactly `actor_registry` and `surface_registry`, each resolving through `source_classes` to the canonical ledger that declares `l9.actor-registry/global@1` or `l9.surface-registry/global@1` with `canonical: true`, so no other ledger is substituted for or added beside the registries;
- the actor source carries `$.actors` and `$.aliases`; the surface source carries `$.surfaces` and `$.aliases`;
- every selector on either source resolves to a top-level section that the registry actually declares;
- the output schema is exactly `l9.projection.cursor-governance-identity/v1`;
- the profile declares the seven ownership boundaries it does not carry.

RC-019 does not define an identity profile family by name and does not limit how many projection profiles may serve Cursor-Governance; whether another profile may be admitted is a decision for canonical authority, not for the validator (GAR-F-161001, `L9-VALIDATION-001`).

The negative-case batch proves fail-closed behavior, each at its intended field, for: target profile missing; target profile duplicated; wrong consumer; wrong profile class; `actor_registry` source missing; `surface_registry` source missing; `identity_model` substituted for `actor_registry`; incomplete actor projection (aliases dropped); incomplete surface projection (entries dropped); a selector naming a section the actor registry does not have; wrong output schema; and an ownership boundary dropped.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-018. v3.11.0 adds RC-019 without weakening or replacing predecessor checks.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.11.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion. Generating the Cursor-Governance projection from this profile is downstream work in Cursor-Governance.
