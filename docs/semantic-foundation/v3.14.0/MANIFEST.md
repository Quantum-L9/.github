# Semantic Foundation Manifest v3.14.0

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

The inventory is unchanged from v3.13.0: no ledger is added or removed.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.14.0 adds no ADR. The existing authority law in `semantics/authority_model.yaml` (`admission_rules.global_requirements`) and the existing global contract catalog (ADR-002) authorize the correction. The contract already consumed that requirement set; this release makes the consumption exact and creates no new admission doctrine.

## Admission contract alignment

v3.14.0 makes a semantic change to one canonical ledger, and a mechanical digest refresh to three:

- `semantics/contracts.yaml`: `l9.contract/admission-and-promotion@1` only. Its `requires` sequence now equals `semantics/authority_model.yaml#admission_rules.global_requirements` exactly: `exact_subject_identity`, `exact_subject_revision_or_digest_when_revisioned`, `target_semantic_or_authority_class`, `target_class_authority`, `explicit_decision_record`, `explicit_compatibility_contract_when_reusing_prior_decision_after_material_change`. The prior list carried the stale spelling `explicit_compatibility_contract_when_reusing_a_prior_decision_after_material_change` and the unconditional entry `independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence`; both are gone from the base list. `id`, `purpose`, `scope`, `owner`, `source_invariants`, `applies_to`, `guarantees`, `forbidden` and `outcomes` are unchanged, so the conditional cross-domain recurrence law stays declared in `guarantees` and `forbidden` and the contract keeps citing `L9-GLOBALIZATION-001`. The contract count remains 26; no other contract changes.
- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`: only the `derivation.source_artifacts[].sha256` coordinates that pin the bytes of `contracts.yaml`, and then of `capabilities.yaml`, are refreshed (RC-001, RC-002, RC-011). No semantic payload changes.

`semantics/authority_model.yaml` is unchanged: it is the authority side, already pinned by RC-021, and the stale consumer was the contract.

The release also adds RC-022 to `scripts/validate-semantics.py`, together with its negative-case batch, which fails closed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.13.0/`, which is unchanged.
