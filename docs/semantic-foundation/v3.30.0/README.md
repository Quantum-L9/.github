# Semantic Foundation v3.30.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.30.0 gives `l9.implementation-ir/v1`, the output of compilation Stage 14 and the only input of Stage 15, a canonical structure. Before this release the IR had an identity, a purpose and transitions, but no admitted structure. Stage 14's required structural validation (`implementation-contract-validator/v1`) therefore had nothing to check against. A compiler that defined the shape itself would have become the owner of ImplementationIR semantics.

This is unit R4-A (`R4-A-IMPLEMENTATION-IR-QUALIFICATION`) of campaign `L9-COMPILER-R4-EXECUTABLE-NODE-001`.

## Bounded delta

- `semantics/implementation_ir.schema.yaml` (`l9.schema/implementation-ir@1`) is an `l9.schema-definition/v1` artifact schema whose `properties.schema.const` is `l9.implementation-ir/v1`. It uses the existing artifact-schema mechanism:
  - it is listed under `generic_compiler_manifest.yaml#requires.artifact_schemas`;
  - it is resolved by the Semantic Compiler's `CanonicalAuthority.schema_defining`;
  - it is checked by its v1 schema interpreter.
- Required sections: `subject`, `authority`, `target`, `interfaces`, `ports`, `adapters`, `composition`, `conformance`, `unresolved` and `provenance`. Every value is lowered from a resolved ProductManifest and an admitted target binding.
- Exactly three dispositions for every realizable obligation:
  - `generable`: fully determined, so it may be emitted;
  - `bound`: existing product code named by an admitted `implementation_ref`, verified and never regenerated;
  - `unresolved`: recorded and never realized.
- Sixteen `semantic_rules` for the cross-field obligations the shape cannot express. They are assigned to `implementation-contract-validator/v1`.
- ADR-027. `semantics/ir_catalog.yaml` is unchanged.

## Evidence

Qualification ran at commit `d9cdb8a5f054a0481ede27a09493b875ecccdfbc` (this change before its release record), with the unmodified `Quantum-L9/l9-semantic-compiler-engine@18215ae2cd948ff8c9cc8992785d2f72f8b53310`:
- The contract resolves through `schema_defining("l9.implementation-ir/v1")`. No compiler change was needed.
- A State instance passes the shape. It was lowered by hand from the resolved `l9.state` ProductManifest (`manifest_digest sha256:a8303f93…d1d2c`) and its topology's `interfaces` and `effects`, as a structural qualification fixture, not compiler output. It has 13 actions, 8 consequential, 2 forbidden, 4 ports, 4 adapters, and `urn:l9:state:port:ScopeAuthorization:1.0` optional and `unresolved`.
- 15 of 15 shape-level negative controls are rejected at the intended field (`RELEASE_VALIDATION.md`).

## Outstanding Unknowns and findings

- **Cross-field rules are declared, not yet enforced.** Eight cross-field negative controls are not shape violations: wrong product identity, non-Node binding selection, undeclared action, unknown technology, invented provider, behavior without contract or binding, manifest digest mismatch, and unbound required port. They are enforced only once the Semantic Compiler implements `implementation-contract-validator/v1` (unit R4-B).
- `behavior_contract_ref` names a coordinate kind that no ledger defines yet. `generable` therefore covers only target-binding maps, such as registration and composition, never product algorithms.
- No release check pins the schema or its rules.
- No independent second Node instance was constructed at this structural stage.
- The open findings recorded by v3.29.0 remain open.

## Authority

`Quantum-L9/.github` owns the schema. A compiler produces and validates ImplementationIR against it, but does not own its meaning. This candidate does not admit itself, and it grants no producer, compiler or consumer any mutation, publication, merge, admission, deployment, or runtime authority.
