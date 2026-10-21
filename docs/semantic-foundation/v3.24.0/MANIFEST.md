# Semantic Foundation Manifest v3.24.0

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

The v3.23.0 inventory is preserved byte for byte in count and names. No ledger is added, removed, or renamed.

## Architecture decision records

The release contains **21** accepted ADRs plus the ADR index under `docs/adr/`.

v3.24.0 adds ADR-021 (producer-emitted projection contract and consumer-committed bundles), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/projection_engine_contract.yaml`: adds `binding_conventions` (`l9.projection-binding-conventions/v1`) declaring canonical JSON, `semantic_digest`, `source_digest`, `projection_digest`, `receipt_identity`, `receipt_digest`, the `<profile_ref>#<source_ref>` subject and output form, multi-selector support, and the consumer-committed bundle transport. `inputs`, `pipeline`, `output`, `guarantees`, and `forbidden` are unchanged.
- `semantics/composition_engine_contract.yaml`: adds `binding_conventions` (`l9.composition-binding-conventions/v1`) for `composition_digest`, the composed subject, and component records. Pipeline and placement strategies are unchanged.
- Every profile, schema, criterion, catalog, and registry is unchanged; RC-028 and RC-030 pins hold.
- `scripts/validate-semantics.py`: unchanged.
- Removed outside the canonical surface: `scripts/publish-projection.py`, `scripts/test-publish-projection.py`, and their `validate-starters.yml` step. `docs/PROJECTION_PUBLICATION.md` is rewritten to the bundle architecture.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.23.0/`, preserved unchanged.
