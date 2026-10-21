# Semantic Foundation Manifest v3.23.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **58** canonical semantic YAML files:
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

The v3.22.0 inventory is preserved. One schema ledger is added: `semantics/coding_agent_execution_projection.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **20** accepted ADRs plus the ADR index under `docs/adr/`.

v3.23.0 adds ADR-020 (coding-agent execution projection payload schema and forbidden-constraint criteria), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/projection_profiles.yaml`:
  - adds five `forbidden_constraints.definitions` entries, one per category `l9.projection/coding-agent-execution@1` declares: `obligation_not_admitted_in_a_selected_source` by `source_authority`; `skill_command_or_routing_semantics`, `adapter_host_or_surface_specific_semantics`, `repository_local_policy_as_global_law`, and `execution_publication_or_merge_authority_grant` by `payload_excludes` over declared source classes;
  - the criterion language (`l9.forbidden-constraint` v1), PROJECTION-016, the three v3.22.0 criteria, and every profile, including `l9.projection/coding-agent-execution@1`, are unchanged.
- `semantics/coding_agent_execution_projection.schema.yaml`: `l9.schema/coding-agent-execution-projection@1`, defining `l9.projection.coding-agent-execution/v1`.
- `semantics/generic_compiler_manifest.yaml`: registers the schema under `requires.artifact_schemas`.
- `scripts/validate-semantics.py`: unchanged.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.22.0/`, preserved unchanged.
