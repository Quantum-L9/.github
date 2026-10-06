# Semantic Foundation Manifest v3.9.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **49** canonical semantic YAML files:
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
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The inventory is unchanged from v3.8.0: no ledger is added or removed.

## Architecture decision records

The release contains **14** accepted ADRs plus the ADR index under `docs/adr/`.

v3.9.0 adds no ADR. The change is a bounded strengthening of an existing contract and a repair of an existing projection profile, both already supported by accepted law (ADR-002, ADR-007, ADR-009) and by the existing constitutional invariants `L9-ASSURANCE-001`, `L9-UNKNOWN-001`, `L9-VALIDATION-001`, `L9-CORRECTNESS-001`, and `L9-EVIDENCE-001`.

## Validation-completeness extension

v3.9.0 modifies two canonical ledgers semantically:

- `semantics/contracts.yaml`: `l9.contract/validation-and-correctness@1` gains the validation-completeness source invariant, guarantees, prohibitions, and a `satisfied` outcome bound to complete evaluation of every applicable required criterion. The contract count remains 26.
- `semantics/projection_profiles.yaml`: `l9.projection/cursor-governance-operating-plane@1` carries the operative contract fields and the canonical global invariants. The profile count remains 23.

Three further ledgers change only in derivation coordinates (`semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`).

The release also extends `scripts/validate-semantics.py` with RC-017 and its fail-closed negative-case batch.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.8.0/`, preserved unchanged.
