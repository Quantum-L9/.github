# Semantic Foundation Manifest v3.42.1

Release status: **REGISTRY-ONLY SUCCESSOR CANDIDATE**

## Install surface

The release contains **117** canonical semantic YAML files:
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
- `semantics/conformance_ir.schema.yaml`
- `semantics/conformance_model.yaml`
- `semantics/contracts.yaml`
- `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml`
- `semantics/dependency_archetypes.yaml`
- `semantics/derivation_profiles.yaml`
- `semantics/domain_architecture_composition.schema.yaml`
- `semantics/domain_architecture_projection.schema.yaml`
- `semantics/domain_capabilities_dependencies_composition.schema.yaml`
- `semantics/domain_capabilities_dependencies_projection.schema.yaml`
- `semantics/domain_consumer_bindings.yaml`
- `semantics/domain_contracts_conformance_composition.schema.yaml`
- `semantics/domain_contracts_conformance_projection.schema.yaml`
- `semantics/domain_evidence_provenance_composition.schema.yaml`
- `semantics/domain_evidence_provenance_projection.schema.yaml`
- `semantics/domain_governance_composition.schema.yaml`
- `semantics/domain_governance_projection.schema.yaml`
- `semantics/domain_identity_attribution_composition.schema.yaml`
- `semantics/domain_identity_attribution_projection.schema.yaml`
- `semantics/domain_projection_model.yaml`
- `semantics/domain_signals_composition.schema.yaml`
- `semantics/domain_signals_projection.schema.yaml`
- `semantics/domain_strategic_value_composition.schema.yaml`
- `semantics/domain_strategic_value_projection.schema.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/evidence_assessment_composition.schema.yaml`
- `semantics/evidence_assessment_projection.schema.yaml`
- `semantics/fixture_ir.schema.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/globalization_assessment_composition.schema.yaml`
- `semantics/globalization_assessment_projection.schema.yaml`
- `semantics/hard_constraint_context_composition.schema.yaml`
- `semantics/hard_constraint_context_projection.schema.yaml`
- `semantics/harness_surface.schema.yaml`
- `semantics/identity_assertion.schema.yaml`
- `semantics/identity_assurance_composition.schema.yaml`
- `semantics/identity_assurance_composition_v2.schema.yaml`
- `semantics/identity_assurance_projection.schema.yaml`
- `semantics/identity_assurance_projection_v2.schema.yaml`
- `semantics/identity_model.yaml`
- `semantics/implementation_ir.schema.yaml`
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
- `semantics/strategic_interaction_composition.schema.yaml`
- `semantics/strategic_interaction_projection.schema.yaml`
- `semantics/strategic_metacognition_composition.schema.yaml`
- `semantics/strategic_metacognition_composition_v2.schema.yaml`
- `semantics/strategic_metacognition_projection.schema.yaml`
- `semantics/strategic_metacognition_projection_v2.schema.yaml`
- `semantics/strategic_plan_graph.schema.yaml`
- `semantics/strategic_plan_metacognitive_analysis.schema.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/strategic_plan_revision_candidate.schema.yaml`
- `semantics/strategic_planner_value_composition.schema.yaml`
- `semantics/strategic_planner_value_projection.schema.yaml`
- `semantics/strategic_planning_context_composition.schema.yaml`
- `semantics/strategic_planning_context_composition_v2.schema.yaml`
- `semantics/strategic_planning_context_projection.schema.yaml`
- `semantics/strategic_planning_context_projection_v2.schema.yaml`
- `semantics/strategic_planning_episode.schema.yaml`
- `semantics/strategic_value_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technical_coordination_composition.schema.yaml`
- `semantics/technical_coordination_projection.schema.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`
- `semantics/work_state_continuity_composition.schema.yaml`
- `semantics/work_state_continuity_projection.schema.yaml`

## Decision records

The release contains **39** accepted ADRs under `docs/adr/` (unchanged).

## Semantic changes

- `semantics/repository_registry.yaml#repositories[l9-state]` — `Quantum-L9/l9-state`, class `l9.repository-class/l9@1`, lifecycle `current`, factory receipt `sha256:dcf1d70fc8390e6729f2f962b595fb35f19535b25171ba2875bd0a45ec0011a0` (root commit `6cbe0fe16231eb9f347c64643dea6362c0e9d838`, template `923ae91457ea5fb1d0099bbf2a6b4128a7eb42bb`).

No other ledger changes. Generated by `ops/register-birth.py` from the factory-attested birth record (ADR-039); no field was typed by an operator.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.42.0/`, preserved unchanged.
