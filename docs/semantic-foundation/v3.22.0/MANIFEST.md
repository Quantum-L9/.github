# Semantic Foundation Manifest v3.22.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **57** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/affected_strategic_closure.schema.yaml`
- `semantics/architecture_intelligence_composition.schema.yaml`
- `semantics/architecture_intelligence_projection.schema.yaml`
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
- `semantics/strategic_plan_metacognitive_analysis.schema.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/strategic_plan_revision_candidate.schema.yaml`
- `semantics/strategic_planning_episode.schema.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The v3.21.0 inventory is preserved. Two schema ledgers are added: `semantics/architecture_intelligence_projection.schema.yaml` and `semantics/architecture_intelligence_composition.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **19** accepted ADRs plus the ADR index under `docs/adr/`.

v3.22.0 adds ADR-019 (architecture intelligence projection and source-namespaced composition), accepted for this candidate; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/projection_profiles.yaml`:
  - adds `l9.projection/architecture-intelligence@1` (consumer `l9-global-architect`, 24 sources, `successor_of: l9.projection/gar-architecture-observer@1`, output `l9.projection.architecture-intelligence/v1`), byte-for-byte as supplied;
  - adds `forbidden_constraints` (criterion language `l9.forbidden-constraint` v1) defining `provider_implementation_details` and `target_rendering_details` by `payload_excludes`, and `unrelated_domain_payloads` by `source_authority`;
  - adds PROJECTION-016;
  - every existing profile, including `l9.projection/gar-architecture-observer@1`, is unchanged.
- `semantics/composition_engine_contract.yaml`: adds `placement_strategies` (`deep_merge`, unchanged behavior; `source_class_namespace`). The ordered pipeline is unchanged.
- `semantics/composition_profiles.yaml`: adds `l9.compose/architecture-intelligence@1`. `l9.compose/consumer-view@1` and `l9.compose/stage-context@1` are unchanged.
- `semantics/architecture_intelligence_projection.schema.yaml`: `l9.schema/architecture-intelligence-projection@1`, defining `l9.projection.architecture-intelligence/v1`.
- `semantics/architecture_intelligence_composition.schema.yaml`: `l9.schema/architecture-intelligence-composition@1`, defining `l9.composed-projection.architecture-intelligence/v1`.
- `semantics/generic_compiler_manifest.yaml`: registers both schemas under `requires.artifact_schemas`.
- `scripts/validate-semantics.py`: adds RC-030 and 17 fail-closed negative cases.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.21.0/`, preserved unchanged.
