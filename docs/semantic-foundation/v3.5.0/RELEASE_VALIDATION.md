# Release Validation v3.5.0

Candidate status: **corrected successor candidate**.

This release preserves the v3.4 ProductTopology, ProductKind, ProductManifest, Dependency, and IdentityTopology architecture while restoring the mechanical closure properties established by PR #146 v3.2.1.

## Closure gates

- YAML parse and artifact-id uniqueness: PASS
- Single canonical artifact authority (`artifact_model.yaml`): PASS
- Canonical compiler-operation algebra: PASS
- Compiler pass operation closure: PASS
- Receipt operation domain equality: PASS
- Canonical `provider_bindings` stage identity: PASS
- Stage solver identity closure: PASS
- Validation subject is produced by its stage: PASS
- Validation subject is handled by its solver: PASS
- ProductTopology/ProductManifest retained: PASS
- IdentityTopology/IdentityAssertion retained: PASS
- SDK remains unresolved/unadmitted: PASS
- Successor validation monotonicity invariant: PASS
- Release hash integrity: PASS after packaging

## Corrective changes from v3.4

1. Removed duplicate `compilation_artifacts.yaml`; `artifact_model.yaml` is the sole artifact authority.
2. Unified compiler operations to `projection`, `derivation`, `resolution`, `synthesis`, `binding_selection`, `lowering`, `rendering`, `composition`, and `validation`.
3. Closed compiler receipt operation domain over the canonical operation algebra, including `resolution`.
4. Canonicalized the build-stage identity to `provider_bindings`.
5. Reconciled stale `project_contracts` stage coordinates to `product_contracts`.
6. Closed stage validation subjects against both stage outputs and selected solver handles.
7. Preserved explicit Unknown for unadmitted ProductKinds such as SDK.
8. Added monotonic validation-strength law for successor foundations.

**Overall: PASS**, subject to final delivered-byte hash verification.
