# Semantic Foundation Manifest v3.6.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **48** canonical semantic YAML files:
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
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

## Architecture decision records

The release contains **13** accepted ADRs plus the ADR index under `docs/adr/`.

## Identity registry extension

v3.6.0 adds the canonical identity-name layer referenced by `identity_model.yaml`:

- `semantics/actor_registry.yaml` (`l9.actor-registry/global@1`)
- `semantics/surface_registry.yaml` (`l9.surface-registry/global@1`)
- `ADR-013-global-actor-and-surface-identity-registries.md`
- `scripts/validate-semantics.py` RC-014 identity registry closure

ActorIdentity and SurfaceIdentity remain distinct dimensions with separately typed aliases. The registries name identity only; runtime evidence resolution, credential provisioning, governance-profile selection, and provider or adapter binding stay outside them.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.5.0/` (corrected successor candidate, preserved unchanged). Every v3.5.0 ledger is carried forward byte-identical except `canonical_sources.yaml` and `generic_compiler_manifest.yaml`, which register and classify the two new ledgers.
