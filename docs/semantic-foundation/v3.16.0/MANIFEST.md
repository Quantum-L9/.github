# Semantic Foundation Manifest v3.16.0

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

The inventory is unchanged from v3.15.0: no ledger is added or removed.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.16.0 adds no ADR.

## Conformance profile reachability and repository admission

v3.16.0 records one reachable published fixture profile and admits the repository that owns it.

- `semantics/projection_profiles.yaml`: `source_classes.conformance_profiles` keeps `canonical_owner: l9-conformance` and adds `admitted_profiles` with exactly one coordinate, `l9.fixture-profile/core@1`, class `core`, distribution `Quantum-L9/l9-conformance` path `catalog/fixture-profile-core-1.yaml`, digest `sha256:3d2cb01a2b872215a3e2298b4e3b3d7ae99ecf867d6486f5730a3f98aba2bb2f`. The profile body is not copied into this repository.
- `semantics/repository_registry.yaml`: admits `l9-conformance` (`provider: github`, `organization: Quantum-L9`, `repository: l9-conformance`, `lifecycle: current`, `class_ref: l9.repository-class/l9@1`). The census is 33 repositories. No other entry changes.
- `scripts/validate-semantics.py`: RC-023 pins the census at 33 and includes `l9-conformance`.

No other canonical ledger changes. No derivation digest is refreshed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.15.0/`, which is unchanged.
