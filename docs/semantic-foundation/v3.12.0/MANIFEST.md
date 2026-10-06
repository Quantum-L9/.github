# Semantic Foundation Manifest v3.12.0

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

The inventory is unchanged from v3.11.0: no ledger is added or removed.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.12.0 adds no ADR. Existing technology-binding law (ADR-006, technology binding after semantics) and ownership-boundary law (ADR-010) authorize the admission. The technology catalog registers provider facts after semantic resolution and creates no semantic authority.

## Graphiti/Zep technology admission

v3.12.0 makes a semantic change to one canonical ledger:

- `semantics/technology_capabilities.yaml`: two technology registrations appended after `makefile`, `graphiti-mcp` and `zep`. Each has `class: datastore`, `provides` (`graph_episode_storage`, `graph_search`, `episode_deletion_by_locator`), `target_roles` (`persistence_provider`), and `semantic_ownership.implied: false`. The technology count rises from 9 to 11. The capability-class set (`language`, `framework`, `datastore`, `transport`, `target`), every existing registration, `global_rules`, `binding_rules`, and `registration_requirements` are unchanged.

No derivation coordinate in any other ledger depends on the bytes of `technology_capabilities.yaml`, so no mechanical refresh was required.

The release also adds RC-020 to `scripts/validate-semantics.py`, together with its negative-case batch, which fails closed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.11.0/`, which is unchanged.
