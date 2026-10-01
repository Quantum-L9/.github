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

## Semantic-foundation closure validator

`scripts/validate-semantics.py` runs inside `make validate`. It is read-only
and fails closed with file, field, and offending value. Result on the
surgical-alignment candidate (post-#148):

- SC-001 canonical sources parse as YAML mappings (44 files): PASS
- SC-002 `canonical_sources.yaml` ids and paths unique, every path exists (32 registered): PASS
- SC-003 `artifact_id` present and unique across ledgers (44): PASS
- SC-004 `contracts.yaml` derivation matches `invariants.yaml` bytes (sha256 `c6e4d355…`, 30 invariants): PASS
- SC-005 capability model closed; typed capability references resolve; pattern traits are not resolved as capabilities: PASS
- SC-006 every binding technology target is registered in `technology_capabilities.yaml`: PASS
- SC-007 binding identifiers unique; no ledger declares a binding-ID grammar, so grammar conformance is not enforced: PASS
- SC-008 release inventory lists every canonical source and every accepted ADR; `HASHES.sha256` matches delivered bytes: PASS
- SC-009 validation is observational (no file written): PASS
- SC-010 unresolved references fail closed: PASS

## Surgical alignment corrections (post-#148)

1. `contracts.yaml` derivation provenance repaired to the actual invariant corpus: `source_invariant_count` 24 → 30, `source_digest_sha256` 767a5786… → c6e4d355… (invariant meaning unchanged).
2. `json-schema` registered in `technology_capabilities.yaml` (class `target`) so `l9.binding/json-schema-2020-12@1` resolves under `technology_must_be_registered_before_mechanical_binding`.
3. `MANIFEST.md` install-surface count corrected from 45 to the 44 files it lists.
4. `HASHES.sha256` regenerated from delivered bytes over the same inventory.

Left unchanged, recorded as successor concerns: derivation digests in `capabilities.yaml`, `lifecycle.yaml`, and `receipt_catalog.yaml` still record the pre-#147 invariant/contract digests; architecture-pattern `required_capabilities` is still untyped pending a coordinated rename with the `projection_profiles.yaml` selectors; `pytest/v1` keeps its coordinate until a binding-ID grammar is declared.

## Corrective changes from v3.4

1. Removed duplicate `compilation_artifacts.yaml`; `artifact_model.yaml` is the sole artifact authority.
2. Unified compiler operations to `projection`, `derivation`, `resolution`, `synthesis`, `binding_selection`, `lowering`, `rendering`, `composition`, and `validation`.
3. Closed compiler receipt operation domain over the canonical operation algebra, including `resolution`.
4. Canonicalized the build-stage identity to `provider_bindings`.
5. Reconciled stale `project_contracts` stage coordinates to `product_contracts`.
6. Closed stage validation subjects against both stage outputs and selected solver handles.
7. Preserved explicit Unknown for unadmitted ProductKinds such as SDK.
8. Added monotonic validation-strength law for successor foundations.

**Overall: PASS**; delivered-byte hashes are verified mechanically by SC-008 on every `make validate`.
