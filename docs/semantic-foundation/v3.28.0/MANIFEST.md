# Semantic Foundation Manifest v3.28.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **82** canonical semantic YAML files:
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
- `semantics/strategic_planning_context_composition.schema.yaml`
- `semantics/strategic_planning_context_projection.schema.yaml`
- `semantics/strategic_planning_episode.schema.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`
- `semantics/work_state_continuity_composition.schema.yaml`
- `semantics/work_state_continuity_projection.schema.yaml`

The v3.27.0 inventory is preserved. 20 payload schemas are added; no ledger is removed or renamed.

## Architecture decision records

The release contains **24** accepted ADRs plus the ADR index under `docs/adr/`.

v3.28.0 adds no ADR.

## Semantic changes

- `semantics/projection_profiles.yaml`: adds ten projection profiles, `l9.projection/authority-resolution@1`, `l9.projection/evidence-assessment@1`, `l9.projection/semantic-change-context@1`, `l9.projection/architecture-break-test@1`, `l9.projection/globalization-assessment@1`, `l9.projection/work-state-continuity@1`, `l9.projection/hard-constraint-context@1`, `l9.projection/identity-assurance@1`, `l9.projection/strategic-metacognition@1`, `l9.projection/strategic-planning-context@1`. In `identity-assurance`, `strategic-metacognition`, `strategic-planning-context`, each selected source is selected field by field, excluding only its own top-level `schema` field.
- `semantics/composition_profiles.yaml`: adds the ten matching `l9.compose/<name>@1` profiles, each composing exactly its projection under source-class namespaces.
- `semantics/generic_compiler_manifest.yaml`: lists the 20 payload schemas below under `requires.artifact_schemas`.
- Added payload schemas:
  - `semantics/architecture_break_test_composition.schema.yaml`
  - `semantics/architecture_break_test_projection.schema.yaml`
  - `semantics/authority_resolution_composition.schema.yaml`
  - `semantics/authority_resolution_projection.schema.yaml`
  - `semantics/evidence_assessment_composition.schema.yaml`
  - `semantics/evidence_assessment_projection.schema.yaml`
  - `semantics/globalization_assessment_composition.schema.yaml`
  - `semantics/globalization_assessment_projection.schema.yaml`
  - `semantics/hard_constraint_context_composition.schema.yaml`
  - `semantics/hard_constraint_context_projection.schema.yaml`
  - `semantics/identity_assurance_composition.schema.yaml`
  - `semantics/identity_assurance_projection.schema.yaml`
  - `semantics/semantic_change_context_composition.schema.yaml`
  - `semantics/semantic_change_context_projection.schema.yaml`
  - `semantics/strategic_metacognition_composition.schema.yaml`
  - `semantics/strategic_metacognition_projection.schema.yaml`
  - `semantics/strategic_planning_context_composition.schema.yaml`
  - `semantics/strategic_planning_context_projection.schema.yaml`
  - `semantics/work_state_continuity_composition.schema.yaml`
  - `semantics/work_state_continuity_projection.schema.yaml`

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.27.0/`, preserved unchanged.
