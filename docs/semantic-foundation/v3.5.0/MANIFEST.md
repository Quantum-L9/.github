# Semantic Foundation Manifest v3.5.0

Release status: **REPLACEMENT CANDIDATE / RELEASE-READY**

## Install surface

The release contains **45** canonical semantic YAML files:
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
- `semantics/compilation_artifacts.yaml`
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
- `semantics/requirement_model.yaml`
- `semantics/resolution_model.yaml`
- `semantics/selector_model.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

## Architecture decision records

The release contains **12** accepted ADRs plus the ADR index under `docs/adr/`.

## Identity topology extension

v3.5.0 makes identity a first-class ProductTopology primitive through:

- `semantics/identity_model.yaml`
- `semantics/identity_assertion.schema.yaml`
- `l9.contract/identity-topology@1`
- `l9.contract/identity-resolution@1`
- `l9.contract/identity-assertion@1`
- `ADR-012-identity-topology-first-class-primitive.md`

ProductIdentity, ReleaseIdentity, RuntimeIdentity, ConstellationIdentity, ActorIdentity, and SurfaceIdentity are distinct. GovernanceProfile, adapter identity, and provider identity are explicitly non-substitutable for ActorIdentity.

## Replacement basis

Immediate predecessor: `PR-146-evolved-semantic-foundation-v3.3.0.zip`.
That predecessor was itself evolved from the exact user-supplied `PR 146-semantic-foundation-v3.2.0.zip`; neither replacement was reconstructed from GitHub file reads.
