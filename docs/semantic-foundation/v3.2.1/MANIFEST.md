# Semantic Foundation Manifest v3.2.1

Release status: **ACTIVE / CANONICAL**

## Install surface

The release contains 40 files under `semantics/`:
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
- `semantics/derivation_profiles.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/invariants.yaml`
- `semantics/ir_catalog.yaml`
- `semantics/lifecycle.yaml`
- `semantics/node_archetypes.yaml`
- `semantics/node_manifest.schema.yaml`
- `semantics/node_spec.schema.yaml`
- `semantics/packet_catalog.yaml`
- `semantics/port_catalog.yaml`
- `semantics/projection_artifact.schema.yaml`
- `semantics/projection_engine_contract.yaml`
- `semantics/projection_profiles.yaml`
- `semantics/receipt_catalog.yaml`
- `semantics/requirement_model.yaml`
- `semantics/resolution_model.yaml`
- `semantics/selector_model.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

## Architecture decision records

The release also contains the canonical architecture rationale under `docs/adr/`.

## Removed from the candidate

- `compilation_artifacts.yaml` (formerly under `semantics/`) — duplicate artifact-model authority. `artifact_model.yaml` is the single canonical artifact model (registered in `canonical_sources.yaml`, required by `generic_compiler_manifest.yaml`); no canonical file referenced the removed ledger.

## Integrity machinery

Not part of the canonical semantic surface; verifies it:
- `ops/validate-semantic-foundation.py`
- `ops/test-validate-semantic-foundation.py`

## Provenance

- Supersedes: unmerged v3.2.0 candidate, `Quantum-L9/.github@12ddcfd0b155a8956ff9130e835ad610de416699`
- v3.2.0 candidate `HASHES.sha256` digest: `d6fe8933451f7e7692b817505999f57a1c78ae958efef307395c5aa88ebd6e11`
- v3.2.1 digests: `HASHES.sha256` in this directory (repository-root-relative paths)
