# Semantic Foundation Manifest v3.26.0

Release status: **SUCCESSOR CANDIDATE WITH ONE DECLARED MAJOR BREAK**

## Install surface

The release contains **61** canonical semantic YAML files:
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
- `semantics/generic_compiler_manifest.yaml`
- `semantics/identity_assertion.schema.yaml`
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

The v3.25.0 inventory is preserved. One schema ledger is added: `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **23** accepted ADRs plus the ADR index under `docs/adr/`.

v3.26.0 adds ADR-023 (operating-plane @2 as a declared major-version successor, and PROJECTION-014 exact selection removal), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/projection_profiles.yaml`:
  - adds `l9.projection/cursor-governance-operating-plane@2` (`class: consumer`, `consumer: Cursor-Governance`, `successor_of: l9.projection/cursor-governance-operating-plane@1`): the 32 predecessor selectors in `vocabulary`, `capabilities`, `authority_model`, `lifecycle`, `invariants`, `contracts`, `error_taxonomy`, and `receipt_catalog`, plus 23 added selectors in those classes (55 total); `output.schema: l9.projection.cursor-governance-operating-plane/v2`; `breaking_changes.removed_selections` names exactly `conformance_profiles` `$.published_profiles[*].id`, `.digest`, and `.status`, with `consumer_migration: explicit` and a rationale;
  - amends PROJECTION-014 to `successor_profile_keeps_class_and_consumer_and_either_preserves_all_selections_or_declares_exact_major_version_removals_with_explicit_consumer_migration` and renames the `global_rules` key `profile_successor_declares_successor_of_and_preserves_every_predecessor_selection` to `profile_successor_preserves_selections_or_declares_exact_major_break`;
  - `l9.projection/cursor-governance-operating-plane@1`, the criterion language, `forbidden_constraints.definitions`, PROJECTION-001 to PROJECTION-013 and PROJECTION-015 to PROJECTION-016, and every other profile are unchanged.
- `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml`: `l9.schema/cursor-governance-operating-plane-v2-projection@1`, defining `l9.projection.cursor-governance-operating-plane/v2` through `properties.schema.const`.
- `semantics/generic_compiler_manifest.yaml`: registers the schema under `requires.artifact_schemas`.
- `docs/adr/README.md`: indexes ADR-023.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.25.0/`, preserved unchanged.
