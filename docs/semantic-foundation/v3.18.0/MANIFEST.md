# Semantic Foundation Manifest v3.18.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **51** canonical semantic YAML files:
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
- `semantics/strategic_plan_graph.schema.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The v3.17.0 inventory is preserved and extended by exactly one canonical schema: `semantics/strategic_plan_graph.schema.yaml`. No prior canonical ledger is removed or renamed.

## Architecture decision records

The release contains **17** accepted ADRs plus the ADR index under `docs/adr/`.

v3.18.0 adds ADR-017, which admits federated authority graphs as the operating-model composition pattern and Strategic Plan Graph v1 as the first authoritative graph representation in that family.

## Semantic changes

- `semantics/architecture_patterns.yaml`: adds `l9.pattern/federated-authority-graphs@1` with downstream-to-upstream typed reference law, derived reverse traversal, derived consumer-view composition, provider neutrality, and explicit anti-mega-authority constraints.
- `semantics/strategic_plan_graph.schema.yaml`: adds the minimum representation for one immutable Strategic Plan revision.
- `semantics/canonical_sources.yaml`: registers the Strategic Plan Graph schema exactly once as a canonical source.
- `semantics/generic_compiler_manifest.yaml`: consumes `strategic_plan_graph.schema.yaml` as a semantic catalog.
- `scripts/validate-semantics.py`: adds RC-025 and its negative-case suite.
- `docs/adr/README.md`: registers ADR-017.

No invariant, contract, capability, artifact class, product kind, repository class, projection profile, composition profile, technology binding, provider binding, actor registry entry, or runtime admission is added.

## Operating-model boundary

The intended family is Strategy → Delegation → WorkState → Execution → Evidence / authoritative reality, with each domain retaining its own semantic owner. v3.18.0 admits only the generic federation law and the Strategic Plan Graph representation. Delegation and WorkState schemas remain future authority-resolved decisions.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.17.0/`, preserved unchanged.
