# Semantic Foundation Manifest v3.32.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **85** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/affected_strategic_closure.schema.yaml`
- `semantics/architecture_break_test_composition.schema.yaml`
- `semantics/architecture_break_test_projection.schema.yaml`
- `semantics/architecture_intelligence_composition.schema.yaml`
- `semantics/architecture_intelligence_projection.schema.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_header_model.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/authority_resolution_composition.schema.yaml`
- `semantics/authority_resolution_projection.schema.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
- `semantics/coding_agent_execution_projection.schema.yaml`
- `semantics/compilation_profiles.yaml`
- `semantics/compiler_contract.yaml`
- `semantics/compiler_passes.yaml`
- `semantics/compiler_receipt.schema.yaml`
- `semantics/composed_projection.schema.yaml`
- `semantics/composition_engine_contract.yaml`
- `semantics/composition_profiles.yaml`
- `semantics/conformance_model.yaml`
- `semantics/contracts.yaml`
- `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml`
- `semantics/dependency_archetypes.yaml`
- `semantics/derivation_profiles.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/evidence_assessment_composition.schema.yaml`
- `semantics/evidence_assessment_projection.schema.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/globalization_assessment_composition.schema.yaml`
- `semantics/globalization_assessment_projection.schema.yaml`
- `semantics/hard_constraint_context_composition.schema.yaml`
- `semantics/hard_constraint_context_projection.schema.yaml`
- `semantics/identity_assertion.schema.yaml`
- `semantics/identity_assurance_composition.schema.yaml`
- `semantics/identity_assurance_projection.schema.yaml`
- `semantics/identity_model.yaml`
- `semantics/invariants.yaml`
- `semantics/ir_catalog.yaml`
- `semantics/lifecycle.yaml`
- `semantics/node_archetypes.yaml`
- `semantics/packet_catalog.yaml`
- `semantics/port_catalog.yaml`
- `semantics/pr_audit_composition.schema.yaml`
- `semantics/pr_audit_projection.schema.yaml`
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
- `semantics/semantic_change_context_composition.schema.yaml`
- `semantics/semantic_change_context_projection.schema.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/strategic_cognition_model.yaml`
- `semantics/strategic_metacognition_composition.schema.yaml`
- `semantics/strategic_metacognition_projection.schema.yaml`
- `semantics/strategic_plan_graph.schema.yaml`
- `semantics/strategic_plan_metacognitive_analysis.schema.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/strategic_plan_revision_candidate.schema.yaml`
- `semantics/strategic_planner_value_composition.schema.yaml`
- `semantics/strategic_planner_value_projection.schema.yaml`
- `semantics/strategic_planning_context_composition.schema.yaml`
- `semantics/strategic_planning_context_projection.schema.yaml`
- `semantics/strategic_planning_episode.schema.yaml`
- `semantics/strategic_value_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`
- `semantics/work_state_continuity_composition.schema.yaml`
- `semantics/work_state_continuity_projection.schema.yaml`

The v3.29.0 inventory is preserved. Three files are added: `semantics/strategic_value_model.yaml`, `semantics/strategic_planner_value_projection.schema.yaml`, `semantics/strategic_planner_value_composition.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **27** accepted ADRs plus the ADR index under `docs/adr/`.

v3.32.0 adds ADR-029 (strategic value foundation and catalog-declared composition provenance criteria), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/invariants.yaml`: `L9-SV-001`, `L9-SV-002` (D1: `L9-SV-001` is the original SV-001 then the original SV-015, verbatim).
- `semantics/contracts.yaml`: `l9.contract/strategic-value-assessment@1`; derivation digest and count rebound.
- `semantics/vocabulary.yaml`: 11 terms (`strategic_value`, `systemic_future_value`, `strategic_value_assessment`, `counterfactual_baseline`, `future_effect_identity`, `bidirectional_value_propagation`, `value_propagation_mesh`, `future_work_elimination`, `capability_unlock`, `decision_relevant_information_value`, `decision_boundary`).
- `semantics/strategic_value_model.yaml` (`l9.strategic.value@1`), registered in `canonical_sources.yaml`, `generic_compiler_manifest.yaml#requires.semantic_catalogs` and as source class `strategic_value_model`.
- `semantics/projection_profiles.yaml`: `l9.projection/strategic-planner-value@1` over `strategic_value_model`, `vocabulary`, `invariants`, `contracts`, `authority_model`.
- `semantics/composition_profiles.yaml`: `l9.compose/strategic-planner-value@1` (source-class namespace, exact coverage); `provenance_constraints` (`l9.provenance-constraint` v1, 4 definitions) and global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`.
- Payload schemas `semantics/strategic_planner_value_projection.schema.yaml` and `semantics/strategic_planner_value_composition.schema.yaml`, registered in `requires.artifact_schemas`.
- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`: derivation sha256 and item counts only (D3).
- `scripts/validate-semantics.py`: RC-033 (provenance-constraint closure) with 8 negative cases.
- `docs/adr/README.md`: indexes ADR-029.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.29.0/`, preserved unchanged.
