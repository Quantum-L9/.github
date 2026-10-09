# Semantic Foundation Manifest v3.17.0

Release status: **CORRECTIVE SUCCESSOR CANDIDATE**

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

The release contains **16** accepted ADRs plus the ADR index under `docs/adr/`.

v3.17.0 adds ADR-016, which establishes Strategy as the non-circular semantic root for the admitted Strategic Cognition / Strategic Plan family.

## Strategy semantic-root correction

Four canonical ledgers change semantically:

- `semantics/strategic_cognition_model.yaml`: adds Strategy, grounds Strategic Cognition / Intent / Plan, grounds Plan Keeper permissions, and retires the current ghost `strategic direction` concept.
- `semantics/authority_model.yaml`: adds the explicit `strategic_authority` definition and binds Strategic Plan authority to it.
- `semantics/strategic_plan_model.yaml`: reuses Strategy without ownership transfer and grounds the already-admitted primitives, relation meanings, and Affected Strategic Closure.
- `semantics/vocabulary.yaml`: adds Strategy / Strategic Intent / Strategic Authority terms and aligns current strategy-family definitions with their canonical models.

`scripts/validate-semantics.py` updates RC-016 / RC-018 only where corrected identifiers require it and adds RC-024. No canonical source, invariant, contract, schema, artifact class, capability, projection profile, repository membership, conformance profile, or derivation source is added or removed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.16.0/`, preserved unchanged.
