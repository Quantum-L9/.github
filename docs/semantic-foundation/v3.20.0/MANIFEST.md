# Semantic Foundation Manifest v3.20.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **55** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/affected_strategic_closure.schema.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
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

The v3.19.0 inventory is preserved unchanged. No canonical ledger is added, removed, or renamed.

## Architecture decision records

The release contains **18** accepted ADRs plus the ADR index under `docs/adr/`.

v3.20.0 adds no ADR. Adding a projection profile to the existing catalog needs no new architecture decision.

## Semantic changes

- `semantics/projection_profiles.yaml`: adds `l9.projection/coding-agent-execution@1`, a runtime profile for consumer `Cursor-Governance`. It selects 19 global invariants and 10 global contracts by exact id, closed over the contracts' `source_invariants`, plus the `agent_authority`, `human_authority`, `escalation_rules`, and `admission_rules` sections of `semantics/authority_model.yaml`. It emits `l9.projection.coding-agent-execution/v1`. The profile count rises from 24 to 25.
- `scripts/validate-semantics.py`: adds RC-028 and its 34 fail-closed negative cases.

No invariant, contract, schema, source registration, vocabulary term, capability, artifact authority class, ProductKind, repository class, composition profile, technology/provider binding, actor or surface identity, producer, or execution semantic is added.

## Coding-execution boundary

The profile is a bounded view of law that is already admitted. It carries no repository-local coding policy, skill, command, adapter, host, or surface semantics, and it grants no execution, publication, or merge authority. Coding-specific refinements that no global record states remain subordinate policy for their owner under `l9.contract/monotonic-subordination@1`.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.19.0/`, preserved unchanged.
