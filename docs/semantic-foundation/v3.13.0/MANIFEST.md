# Semantic Foundation Manifest v3.13.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **50** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
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
- `semantics/strategic_plan_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The inventory is unchanged from v3.12.0: no ledger is added or removed.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.13.0 adds no ADR. The existing authority law in `semantics/authority_model.yaml` (`admission_rules`, `escalation_rules`) and the existing ProductTopology contract (ADR-003) authorize the declaration. It names an authority role that `ProductTopology.admission.authority_ref` already references, and it creates no new admission doctrine.

## Product admission authority identity

v3.13.0 makes a semantic change to three canonical ledgers:

- `semantics/authority_model.yaml`: one declaration, `product_admission_authority` (`id: l9.authority/product-admission`), between `product_topology_authority` and `product_manifest_authority`. Its decision authority is `applicable_target_class_authority`, the owner of `l9.receipt/admission@1`. It inherits `admission_rules.global_requirements` by anchor and references `admission_rules` and `escalation_rules`, and it forbids self-admission. It declares the following consequences `false`: publication, runtime admission, runtime availability, capability invocation authorization, implementation conformance and consumer compatibility. Every other section of the ledger is unchanged.
- `semantics/projection_profiles.yaml`: the `authority_model` source of `l9.projection/stage-product-topology@1` gains the selectors `$.product_admission_authority`, `$.admission_rules` and `$.escalation_rules`, so ProductTopology intake receives the declaration it validates `admission.authority_ref` against, and the law that declaration inherits. No other profile changes.
- `semantics/semantic_dependency_model.yaml`: `dependency_rules.product_topology.depends_on` gains `authority_model`. ProductTopology intake already consumed the authority model through its stage projection, and now validates `admission.authority_ref` against it, so a change to the declaration must mark ProductTopology results stale (`invalidation_rules.source_digest_change`). No other dependency rule changes.

No derivation coordinate in any other ledger depends on the bytes of these files, so no mechanical refresh was required.

The release also adds RC-021 to `scripts/validate-semantics.py`, together with its negative-case batch, which fails closed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.12.0/`, which is unchanged.
