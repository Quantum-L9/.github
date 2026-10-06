# Semantic Foundation Manifest v3.11.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **50** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
- `semantics/compilation_profiles.yaml`
- `semantics/compiler_contract.yaml`
- `semantics/compiler_passes.yaml`
- `semantics/compiler_receipt.schema.yaml`
- `semantics/composed_projection.schema.yaml`
- `semantics/composition_engine_contract.yaml`
- `semantics/composition_profiles.yaml`
- `semantics/conformance_model.yaml`
- `semantics/contracts.yaml`
- `semantics/dependency_archetypes.yaml`
- `semantics/derivation_profiles.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/identity_assertion.schema.yaml`
- `semantics/identity_model.yaml`
- `semantics/invariants.yaml`
- `semantics/ir_catalog.yaml`
- `semantics/lifecycle.yaml`
- `semantics/node_archetypes.yaml`
- `semantics/packet_catalog.yaml`
- `semantics/port_catalog.yaml`
- `semantics/product_kinds.yaml`
- `semantics/product_manifest.schema.yaml`
- `semantics/product_topology.schema.yaml`
- `semantics/projection_artifact.schema.yaml`
- `semantics/projection_engine_contract.yaml`
- `semantics/projection_profiles.yaml`
- `semantics/receipt_catalog.yaml`
- `semantics/repository_classes.yaml`
- `semantics/repository_registry.yaml`
- `semantics/requirement_model.yaml`
- `semantics/resolution_model.yaml`
- `semantics/selector_model.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/strategic_cognition_model.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The inventory is unchanged from v3.10.0: no ledger is added or removed.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.11.0 adds no ADR. The profile is authorized by existing projection law (ADR-009) and identity law (ADR-012, ADR-013): a projection profile selects canonical semantics for a named consumer and creates no authority.

## Cursor-Governance identity projection extension

v3.11.0 modifies one canonical ledger semantically:

- `semantics/projection_profiles.yaml`: one consumer profile added, `l9.projection/cursor-governance-identity@1`, with sources `actor_registry` and `surface_registry` and output schema `l9.projection.cursor-governance-identity/v1`. The profile count rises from 23 to 24. Every other profile, including `l9.projection/cursor-governance-operating-plane@1`, is unchanged.

No derivation coordinate in any other ledger depends on `projection_profiles.yaml`, so no mechanical refresh was required.

The release also extends `scripts/validate-semantics.py` with RC-019 and its fail-closed negative-case batch.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.10.0/`, preserved unchanged.
