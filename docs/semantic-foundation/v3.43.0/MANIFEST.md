# Semantic Foundation Manifest v3.43.0

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

## Decision records

The release contains **40** accepted ADRs under `docs/adr/` (ADR-040 added, candidate).

## Semantic changes

Only `semantics/repository_registry.yaml` changes (ADR-040):

- `global_rules`: `organization_hosting_does_not_imply_l9_membership` is superseded and removed; `organization_hosted_repositories_must_be_registered`, `membership_is_conferred_by_registry_entry_never_by_organization_hosting`, `registry_membership_does_not_imply_product_kind` and `registry_membership_does_not_imply_constellation_participation` are added, all `true`. Every other global rule is unchanged.
- `purpose`: states organization completeness and that membership is organization membership only.
- `organization_completeness` (new): decision record, scope (github / Quantum-L9, archived and forked repositories included), `archived_repository_lifecycle: retired`, the id rule with the one grandfathered id `dot-github`, the enforcement and admission paths, and the `organization_admission` field set.
- `downstream_obligations`: `registry_is_organization_complete_from_v3_43_0`, `reproject_on_every_registry_release`, `registry_membership_is_not_product_kind_or_node_admission`.
- `repositories`: 27 entries admitted, each class `l9.repository-class/l9@1`, no ProductKind, ids folded from the case-sensitive repository name:

| id | coordinate | lifecycle |
| --- | --- | --- |
| `splitwisely-ai` | `Quantum-L9/SplitWisely.ai` | `current` |
| `llm-router` | `Quantum-L9/LLM-Router` | `current` |
| `cognitive-engine-graphs` | `Quantum-L9/Cognitive.Engine.Graphs` | `current` |
| `enrichment-inference-engine` | `Quantum-L9/Enrichment.Inference.Engine` | `current` |
| `constellation-gate` | `Quantum-L9/Constellation.Gate` | `current` |
| `gate-sdk` | `Quantum-L9/Gate_SDK` | `current` |
| `safehavenrr-site` | `Quantum-L9/safehavenrr-site` | `current` |
| `quantum-website-cursor` | `Quantum-L9/Quantum-Website-Cursor` | `current` |
| `odoo-enterprise` | `Quantum-L9/odoo-enterprise` | `current` |
| `clawdbot` | `Quantum-L9/clawdbot` | `current` |
| `ideaos` | `Quantum-L9/IdeaOS` | `current` |
| `sm-microbidlocal` | `Quantum-L9/SM-MicroBidLocal` | `current` |
| `mack-5-0` | `Quantum-L9/Mack-5.0` | `current` |
| `quantum-dashboard` | `Quantum-L9/quantum-dashboard` | `current` |
| `sustainabilitysolutions1` | `Quantum-L9/SustainabilitySolutions1` | `current` |
| `infisical-config` | `Quantum-L9/infisical-config` | `current` |
| `l9-cto` | `Quantum-L9/l9-cto` | `current` |
| `platform-state-service` | `Quantum-L9/platform-state-service` | `current` |
| `venture-forge-toolbox` | `Quantum-L9/venture-forge-toolbox` | `current` |
| `openclaw` | `Quantum-L9/openclaw` | `current` |
| `ib-identityos` | `Quantum-L9/IB-IdentityOS` | `current` |
| `deckhouseodoo` | `Quantum-L9/DeckhouseOdoo` | `current` |
| `emma-v1-0` | `Quantum-L9/emma_v1.0` | `current` |
| `governance-active` | `Quantum-L9/Governance-Active` | `current` |
| `golden-repo` | `Quantum-L9/golden-repo` | `retired` |
| `ib-founderos-runtime` | `Quantum-L9/IB-Founderos-Runtime` | `current` |
| `deckhouse` | `Quantum-L9/Deckhouse` | `current` |

The registry holds 61 entries: the 60-entry pinned census plus the factory-born `l9-state`. No existing entry, id or coordinate changes. `semantics/repository_classes.yaml`, including the derived view `l9.repository-view/memory-namespace-l9@1`, is unchanged.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.42.1/`, preserved unchanged.
