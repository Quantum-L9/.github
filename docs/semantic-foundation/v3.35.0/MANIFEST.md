# Semantic Foundation Manifest v3.35.0

Release status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-032, 2026-11-08)

## Install surface

The release contains **94** canonical semantic YAML files:
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
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`
- `semantics/work_state_continuity_composition.schema.yaml`
- `semantics/work_state_continuity_projection.schema.yaml`

The v3.34.0 inventory is preserved. Six files are added; no ledger is removed or renamed.

## Architecture decision records

The release contains **32** accepted ADRs plus the ADR index under `docs/adr/`.

v3.35.0 adds ADR-032 (Source-Class Payload Dispatch Successors for Three Projection Pairs), the owner's admission decision for this release. Admission is scoped to the v3.35.0 delta.

## Semantic changes

- `semantics/projection_profiles.yaml`: `l9.projection/identity-assurance@2`, `l9.projection/strategic-planning-context@2` and `l9.projection/strategic-metacognition@2`, each `successor_of` its @1 and declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`; validation rule `PROJECTION-017`.
- `semantics/composition_profiles.yaml`: `l9.compose/identity-assurance@2`, `l9.compose/strategic-planning-context@2` and `l9.compose/strategic-metacognition@2`, each composing its @2 projection and declaring the same protocol.
- `semantics/vocabulary.yaml`: terms `payload_validation_protocol`, `source_class_payload_schema` and `strict_descriptor_dialect`.
- Six registered payload schemas of type `l9.source-class-payload-schema/v1`, listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `semantics/identity_assurance_composition_v2.schema.yaml`
  - `semantics/identity_assurance_projection_v2.schema.yaml`
  - `semantics/strategic_metacognition_composition_v2.schema.yaml`
  - `semantics/strategic_metacognition_projection_v2.schema.yaml`
  - `semantics/strategic_planning_context_composition_v2.schema.yaml`
  - `semantics/strategic_planning_context_projection_v2.schema.yaml`
- No derived coordinate moves: no registered source's recorded digest or item count changes.

Withheld by the owner's decision, and still candidates in `docs/candidates/source-class-dispatch-v2/`: the composition global rule `source_class_dispatch_composition_is_source_namespaced_and_declares_the_protocol_of_its_projection_profile`, and the strict descriptor dialect document itself. The @1 profiles stay admitted and unchanged.
- `docs/adr/README.md`: indexes ADR-032.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.34.0/`, preserved unchanged.
