# Semantic Foundation Manifest v3.36.0

Release status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-033, 2026-11-11)

## Install surface

The release contains **112** canonical semantic YAML files:
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

The v3.35.0 inventory is preserved. Eighteen files are added; no ledger is removed or renamed.

## Architecture decision records

The release contains **33** accepted ADRs plus the ADR index under `docs/adr/`.

v3.36.0 adds ADR-033, which admits it.

## Semantic changes

- `semantics/invariants.yaml`: `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`, `L9-SIGNAL-002`, `L9-SIGNAL-003` and `L9-SIGNAL-004`, record-equal to the Quantum-L9/.github#234 candidates.
- `semantics/vocabulary.yaml`: terms `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`, `signal_feedback_episode` and `signal_consumption` (record-equal to #234), and `domain_projection` and `domain_consumer_binding`.
- `semantics/contracts.yaml`: `l9.contract/domain-composition-compatibility@1` and `l9.contract/domain-composition-provenance@1`.
- `semantics/projection_profiles.yaml`: profile class `domain` and eight domain profiles `l9.projection/<name>@1` for `architecture`, `strategic-value`, `signals`, `governance`, `evidence-provenance`, `contracts-conformance`, `capabilities-dependencies` and `identity-attribution`, each declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`.
- `semantics/composition_profiles.yaml`: the eight `l9.compose/<name>@1` compositions, source-class namespaced, declaring the same protocol.
- New ledgers `semantics/domain_projection_model.yaml` (`DOMAIN-001`..`DOMAIN-010`) and `semantics/domain_consumer_bindings.yaml` (six bindings, `BINDING-001`..`004`, `COMPOSE-001`..`005`), registered in `semantics/canonical_sources.yaml` and `semantics/generic_compiler_manifest.yaml#requires.semantic_catalogs`.
- Sixteen registered payload schemas of type `l9.source-class-payload-schema/v1` (one projection and one composition schema per domain, each named domain_NAME_projection or domain_NAME_composition with suffix .schema.yaml under semantics/), listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`.
- Derived coordinates rebound from final bytes: `semantics/contracts.yaml#derivation` (40 invariants), and the `source_artifacts` of `semantics/capabilities.yaml` (40 invariants, 31 contracts), `semantics/lifecycle.yaml` and `semantics/receipt_catalog.yaml`.
- `scripts/validate-semantics.py`: RC-034 and RC-034-NEG.

No existing projection or composition profile changes; RC-034 pins both predecessor catalogs by canonical-JSON digest.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.35.0/`, preserved unchanged.
