# Semantic Foundation Manifest v3.44.0

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

The release contains **40** accepted ADRs under `docs/adr/` (unchanged; no ADR is added by this candidate).

## Semantic changes

Owner decision (operator, 2026-11-20, in a governed Claude Code session): the `claude-code` actor has exactly two surfaces, `claude-code-cli` and `claude-code-web`. `claude-code-desktop` and `claude-code-ide` were registered in error, and a cloud session started from a phone is a Claude Code web session.

- `semantics/surface_registry.yaml` (`l9.surface-registry/global@1`):
  - `surfaces[claude-code-desktop]`: `status: current` → `retired`, no successor; description records the retirement.
  - `surfaces[claude-code-ide]`: `status: current` → `retired`, no successor; the command line run inside an IDE is `claude-code-cli`.
  - `surfaces[claude-code-mobile]`: `status: current` → `superseded`, `successor_refs: [l9.surface-registry/global@1#claude-code-web]` (`lifecycle.yaml#lifecycle_relations.successor_of`; the `successor_refs` field name follows `product_topology.schema.yaml` identity declarations).
  - `surfaces[claude-code-cli]` and `surfaces[claude-code-web]`: status unchanged (`current`); descriptions state that the CLI includes the command line run inside an IDE and that web covers any client starting a hosted cloud session, a phone included.
  - `aliases[claude-mobile]`: `canonical: claude-code-mobile` → `claude-code-web`. `claude-desktop` and `claude-ide` keep their retired coordinates; `claude-cli` and `claude-web` are unchanged.
  - `alias_rules.alias_kinds.historical_surface_alias`: an alias canonicalizes to exactly one canonical surface, a current one or the successor of a superseded one; an alias of a retired surface without a successor keeps that retired coordinate and admits no new use.
  - All eleven surface ids stay registered and addressable; nothing is removed or renamed.
- `semantics/actor_registry.yaml` (`l9.actor-registry/global@1`): `actors[claude-code].description` names its two surfaces. The historical actor aliases `claude-code-desktop` and `claude-code-mobile` → `claude-code` are kept; equal strings across dimensions stay unrelated.
- `semantics/domain_consumer_bindings.yaml` (`l9.domain-consumer-binding-catalog/global@1`): `l9.domain-consumer-binding/claude-code@1` is admitted (ADR-033) and unedited. New `l9.domain-consumer-binding/claude-code@2`, `successor_of: l9.domain-consumer-binding/claude-code@1`, identical to @1 except `surface_refs`: `l9.surface-registry/global@1#claude-code-cli` and `l9.surface-registry/global@1#claude-code-web`. Two global rules are added, both `true`: `a_successor_binding_names_its_predecessor_version_of_the_same_consumer` and `a_host_binding_without_a_successor_names_only_current_surfaces`.

No invariant, contract, vocabulary term, source class, projection or composition profile, or payload schema changes. No derivation coordinate changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.43.0/`, preserved unchanged.
