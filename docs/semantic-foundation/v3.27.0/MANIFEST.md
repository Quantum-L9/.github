# Semantic Foundation Manifest v3.27.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **62** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/affected_strategic_closure.schema.yaml`
- `semantics/architecture_intelligence_composition.schema.yaml`
- `semantics/architecture_intelligence_projection.schema.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_header_model.yaml`
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

The v3.26.0 inventory is preserved. One ledger is added: `semantics/artifact_header_model.yaml`. No ledger is removed or renamed.

## Architecture decision records

The release contains **24** accepted ADRs plus the ADR index under `docs/adr/`.

v3.27.0 adds ADR-024 (artifact header field semantics as source declarations), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/artifact_header_model.yaml`: `l9.artifact-header-model/global@1` defines the native `L9_META` artifact header.
  - Every field is a source declaration (evidence class `declared`, authority `source`).
  - Field meanings apply under a recognized `l9_schema` (`1`, `2`).
  - It defines 30 fields (11 identity, 6 classification, 5 governance, 8 retrieval), each with a category, a value kind, a definition and an explicit `does_not_establish`.
  - `status` is the one field with declared values: `active`, `deprecated`, `candidate`, `stub`.
  - `projection_boundary.canonical_relations` is `none`.
  - It lists in `does_not_own` the carrier syntax, parsing, predicate names, projection policy, open vocabularies, identity and ownership resolution, and relation types.
- `semantics/canonical_sources.yaml`: registers `l9.source/artifact-header-model@1` (`canonical: true`, `projection_allowed: true`, `derivation_allowed: false`).
- `semantics/generic_compiler_manifest.yaml`: lists `artifact_header_model.yaml` under `requires.semantic_catalogs`.
- `semantics/vocabulary.yaml`: adds the terms `artifact_header` and `header_declaration`, each with `detailed_model: artifact_header_model.yaml`.
- `docs/adr/README.md`: indexes ADR-024.

No other ledger, rule, profile, criterion, contract or invariant changes.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.26.0/`, preserved unchanged.
