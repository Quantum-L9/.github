# Semantic Foundation Manifest v3.24.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **60** canonical semantic YAML files:
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

The v3.23.0 inventory is preserved. Two schema ledgers are added: `semantics/pr_audit_projection.schema.yaml` and `semantics/pr_audit_composition.schema.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **21** accepted ADRs plus the ADR index under `docs/adr/`.

v3.24.0 adds ADR-021 (PR-audit projection, source-namespaced composition, payload schemas, and validator closure), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/projection_profiles.yaml`:
  - adds `l9.projection/pr-audit@1` (`class: consumer`, `consumer: l9-pr-audit`): 24 global invariants, 16 global contracts, 7 `authority_model` sections, 2 `artifact_model` sections, 1 architecture rule, 6 architecture patterns, 2 `capabilities` sections, 2 `conformance_model` sections, 4 `receipt_catalog` selections, 3 `lifecycle` selections, `semantic_dependency_model.invalidation_rules`, `error_taxonomy.result_domains`, and 27 vocabulary terms; `output.schema: l9.projection.pr-audit/v1`; `forbidden` is exactly the five ADR-020 categories;
  - the criterion language (`l9.forbidden-constraint` v1), `forbidden_constraints.definitions`, PROJECTION-001 to PROJECTION-016, and every other profile are unchanged.
- `semantics/composition_profiles.yaml`: adds `l9.compose/pr-audit@1` composing `l9.projection/pr-audit@1` under `source_class_namespace` with exact source coverage; `output.schema: l9.composed-projection.pr-audit/v1`.
- `semantics/pr_audit_projection.schema.yaml`: `l9.schema/pr-audit-projection@1`, defining `l9.projection.pr-audit/v1`.
- `semantics/pr_audit_composition.schema.yaml`: `l9.schema/pr-audit-composition@1`, defining `l9.composed-projection.pr-audit/v1` with one namespace per declared source class.
- `semantics/generic_compiler_manifest.yaml`: registers both schemas under `requires.artifact_schemas`.
- `scripts/validate-semantics.py`: adds RC-031 and its negative cases; registers `check_rc031` after `check_rc030`.
- `docs/adr/README.md`: indexes ADR-021.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.23.0/`, preserved unchanged.
