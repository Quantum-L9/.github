# Semantic Foundation Manifest v3.21.0

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

The v3.20.0 inventory is preserved exactly. No canonical ledger is added, removed, or renamed.

## Architecture decision records

The release contains **18** accepted ADRs plus the ADR index under `docs/adr/`.

v3.21.0 adds no ADR. Instead it appends a dated amendment, "Amendment 2026-10-14: Memory hosted-service exception", to ADR-011. The original ADR-011 decision text is preserved byte-for-byte above the amendment.

## Semantic changes

- `semantics/product_kinds.yaml`:
  - adds `kind_exception_model` (binding requirements including the release floor, rules, protected requirements, and protected prohibitions);
  - adds exactly one `kind_exceptions` entry, `l9.product-kind-exception/memory-hosted-service@1`, bound to `l9-graphiti-memory:product/l9-graphite-memory` in `Quantum-L9/l9-graphiti-memory`;
  - renames the global rule `product_kind_is_determined_by_canonical_consumption_and_deployment_model` to its qualified form `…_unless_an_admitted_product_kind_exception_binds_the_exact_product`, and adds three global rules that scope kind law to the exact product and to owner-only admission;
  - is now additionally governed by `l9.contract/monotonic-subordination@1` and `l9.contract/admission-and-promotion@1`.
- `semantics/contracts.yaml`:
  - `l9.contract/product-kind@1` qualifies its purpose, the Dependency guarantee, and the `resolved` and `invalid` outcomes by an exactly bound admitted exception;
  - it adds one `requires`, two guarantees, four forbidden uses, the applies-to subject `product_kind_exception_claims`, and the source invariant `L9-MONOTONIC-001`;
  - `l9.contract/product-topology@1` qualifies `product_kind_constrains_consumption_and_deployment`;
  - no contract is added or removed.
- `semantics/architecture_rules.yaml`: adds global rule `kind_rule_obligations_apply_unmodified_unless_an_admitted_product_kind_exception_binds_the_exact_product` and rule `l9.arch-rule/product-kind-exception@1`.
- `semantics/architecture_patterns.yaml`: adds global rule `pattern_obligations_apply_unmodified_unless_an_admitted_product_kind_exception_displaces_them_for_its_exact_product`. No pattern changes.
- `semantics/dependency_archetypes.yaml`: adds global rule `archetype_obligations_apply_unmodified_unless_an_admitted_product_kind_exception_displaces_them_for_its_exact_product`. No archetype changes.
- `semantics/vocabulary.yaml`: adds the term `product_kind_exception` and an exact-product qualifier rule on `dependency`.
- `semantics/product_topology.schema.yaml`: adds the claim field `product.kind_exception_ref`, the semantic rule `product_kind_exception_is_claimed_only_by_explicit_reference_and_exact_subject_binding`, and `kind_resolution.exception_rule` / `exception_catalog`. The rule states where the release floor is enforced.
- `semantics/product_manifest.schema.yaml`:
  - adds typed `product.fields`, including `kind_exception_ref`;
  - adds the resolved-manifest gate items `product_kind_exception_absent_or_exactly_bound_and_admitted` and `product_kind_exception_release_floor_satisfied_when_claimed`;
  - adds the semantic rule `manifest_preserves_the_exact_applied_product_kind_exception_coordinate`.
- `semantics/projection_profiles.yaml`:
  - the ProductTopology stage now selects `$.kind_exception_model` and `$.kind_exceptions`;
  - the semantic-resolution stage now selects `$.kind_exceptions`;
  - the identity projection now selects `$.product.kind_exception_ref`.
- `semantics/solver_catalog.yaml`: the product-topology validator declares `applies_admitted_product_kind_exceptions_only_by_exact_subject_binding`.
- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`: derivation source digests are refreshed for the new `contracts.yaml` and `capabilities.yaml` bytes. Item counts and derived content are unchanged.
- `scripts/validate-semantics.py`:
  - adds RC-029, with 3 positive ProductTopology witnesses, field-and-digest pins of the exception and its model, and 71 hostile negative cases;
  - RC-005 pins the identity projection selection, including `$.product.kind_exception_ref`.

Nothing else is added: no ProductKind, archetype, pattern, contract, invariant, capability, artifact authority class, repository class, technology, actor or surface identity, service, or generalized waiver mechanism.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.20.0/`, the `l9.projection/coding-agent-execution@1` candidate delivered by open PR #179 (head `aedf271d6a401c3515637bb70339a49e7cc92319`). That record is preserved unchanged and is the exact stacked baseline. This release must merge after #179.
