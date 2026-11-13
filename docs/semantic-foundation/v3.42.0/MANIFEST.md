# Semantic Foundation Manifest v3.42.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

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

The v3.41.0 inventory is preserved. No file is added, removed or renamed.

## Architecture decision records

The release contains **39** accepted ADRs plus the ADR index under `docs/adr/`.

v3.42.0 adds ADR-039 (factory-born repository registration), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/repository_registry.yaml#factory_born_entries`: the factory-born entry shape. `birth_provenance` has exactly `factory` (`Quantum-L9/l9-repo-template`), `receipt_schema` (`l9.birth-receipt/v1`), `receipt_digest`, `root_commit`, `template_sha`, `template_version`, `org_policy_sha`, `birth_profile` and `born_at`. The section also states the id rule, `lifecycle_at_registration: current`, the class rule (the single current admitted class, else fail closed), and that pinned entries never carry provenance. No repository entry is added or changed.
- `scripts/validate-semantics.py` RC-023: pinned entries are counted apart from entries carrying `birth_provenance`, and those entries are checked by shape (`rc023_factory_entry_problems`, `rc023_factory_repository_id`). RC-023-NEG grows from 57 to 70 cases.
- `ops/register-birth.py`, `ops/test-register-birth.py`, and a `register` job in `.github/workflows/repo-birth-bootstrap.yml` that opens the registration PR.
- ADR-039 (candidate).

No invariant, contract, term, capability, receipt family, lifecycle, RepositoryClass, projection or composition profile changes, and no derivation coordinate changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.41.0/` (candidate, not admitted), preserved unchanged.
