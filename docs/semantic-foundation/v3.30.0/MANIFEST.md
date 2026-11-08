# Semantic Foundation Manifest v3.30.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **83** canonical semantic YAML files:
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

The v3.29.0 inventory is preserved. One ledger is added: `semantics/implementation_ir.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **27** accepted ADRs plus the ADR index under `docs/adr/`.

v3.30.0 adds ADR-027 (structural contract for `l9.implementation-ir/v1`), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/implementation_ir.schema.yaml` (`l9.schema/implementation-ir@1`, `l9.schema-definition/v1`): the structure of `l9.implementation-ir/v1` (`properties.schema.const`).
  - Required sections: `subject`, `authority`, `target`, `interfaces`, `ports`, `adapters`, `composition`, `conformance`, `unresolved` and `provenance`.
  - Every realizable obligation carries one of three dispositions: `generable`, `bound` or `unresolved`.
  - Sixteen `semantic_rules` state the cross-field obligations, which `enforcement` assigns to `implementation-contract-validator/v1`.
  - It is governed by `l9.contract/product-manifest@1`, `technology-binding@1`, `derived-artifact@1`, `provenance-and-coordinate@1`, `unknown-and-degradation@1` and `validation-and-correctness@1`.
- `semantics/generic_compiler_manifest.yaml`: lists `implementation_ir.schema.yaml` under `requires.artifact_schemas`.
- `docs/adr/README.md`: indexes ADR-027.

No other ledger, rule, profile, criterion, contract or invariant changes. `semantics/ir_catalog.yaml` is unchanged.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.29.0/`, preserved unchanged.
