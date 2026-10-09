# Semantic Foundation Manifest v3.19.0

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

The v3.18.0 inventory is preserved and extended by exactly four canonical schema definitions for the Strategic Planning cognition interface. No prior canonical ledger is removed or renamed.

## Architecture decision records

The release contains **18** accepted ADRs plus the ADR index under `docs/adr/`.

v3.19.0 adds ADR-018, which freezes the canonical representations for Affected Strategic Closure, Strategic Planning Episode, Strategic Plan Revision Candidate, and Strategic Plan Metacognitive Analysis.

## Semantic changes

- `semantics/strategic_cognition_model.yaml`: adds the minimum semantic anchors for Planning Episode, Revision Candidate, and Metacognitive Analysis, plus role permissions/prohibitions needed to preserve the Planner / Meta-Planner authority boundary.
- `semantics/strategic_plan_model.yaml`: binds Affected Strategic Closure to its canonical representation schema while preserving derived/non-authoritative semantics and explicit algorithm deferral.
- `semantics/affected_strategic_closure.schema.yaml`: adds the minimum derived reconsideration-frontier representation.
- `semantics/strategic_planning_episode.schema.yaml`: adds the minimum immutable Plan Keeper reasoning-record representation.
- `semantics/strategic_plan_revision_candidate.schema.yaml`: adds the digest-bound candidate bridge from reasoning to a possible authorized Plan revision.
- `semantics/strategic_plan_metacognitive_analysis.schema.yaml`: adds the advisory Meta-Planner analysis representation.
- `semantics/canonical_sources.yaml`: registers all four schema definitions exactly once.
- `semantics/generic_compiler_manifest.yaml`: consumes all four as semantic catalogs.
- `scripts/validate-semantics.py`: adds RC-026 and its 20 hostile negative cases.
- `docs/adr/README.md`: registers ADR-018.

No invariant, contract, capability, artifact authority class, ProductKind, repository class, projection profile, composition profile, technology/provider binding, actor identity, runtime admission, prompt/model binding, memory behavior, confidence model, or execution semantic is added.

## Planner / Meta-Planner boundary

The Plan Keeper may produce a Strategic Planning Episode and optionally a Strategic Plan Revision Candidate. Neither is Strategy. Only admission of the exact candidate/proposed-graph bytes under applicable Strategic Authority may produce a new authoritative Strategic Plan Graph revision.

The Strategic Plan Metacognitive Reasoner may produce advisory Strategic Plan Metacognitive Analysis and planning cognition lessons. It may not modify the Plan, approve a revision candidate, become Strategic Authority, or absorb evidence ownership.

## Representation contraction

The revision candidate does not carry a separately maintained Plan mutation patch. The change is mechanically derivable from the exact predecessor graph and exact proposed graph. This prevents duplicate representations from drifting.

No generic `reasoning_artifact` class is admitted because existing `derived` and `candidate` authority classes are sufficient.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.18.0/`, preserved unchanged and required as the exact stacked baseline.
