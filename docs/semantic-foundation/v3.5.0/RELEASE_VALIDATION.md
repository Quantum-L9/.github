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

## Residual semantic closure (second pass)

Additional checks in the same validator, run on the residual-closure candidate:

- RC-001 `capabilities.yaml` derivation matches the bytes and record counts of `invariants.yaml` (30) and `contracts.yaml` (25): PASS
- RC-002 `lifecycle.yaml` derivation matches the bytes of `invariants.yaml`, `contracts.yaml`, and `capabilities.yaml`: PASS
- RC-003 every projection profile class resolves to `profile_classes`: not enforced in this pass (enforced in the third pass below)
- RC-004 every projection source resolves to `source_classes` (140 references, 22 profiles): PASS
- RC-005 profile shape compatible with its declared class: not enforced in this pass (enforced in the third pass below)
- RC-006 `canonical_sources.yaml` equals the `semantic_catalogs` class of `generic_compiler_manifest.yaml` (32 = 32) and every other ledger is classified exactly once: PASS
- RC-007 every registered path resolves to a ledger declaring `canonical: true`: PASS
- RC-008 registered ids and paths unique (SC-002): PASS
- RC-009 `artifact_model.yaml` ProductManifest required fields contain no duplicate (16 fields): PASS
- RC-010 manifest install-surface count equals enumerated entries (SC-008): PASS

Corrections in this pass:

1. `capabilities.yaml` derivation: invariants sha256 767a5786… → c6e4d355… (count 24 → 30); contracts sha256 9a79b1ba… → f05239b7… (count 21 → 25).
2. `lifecycle.yaml` derivation: invariants → c6e4d355…, contracts → f05239b7…, capabilities 97759b02… → 959acf1e….
3. `projection_profiles.yaml`: `identity_model` registered as a source class (`identity_model.yaml`) so the product identity projection's sources resolve.
4. `artifact_model.yaml`: duplicate `provider_bindings` removed from `artifacts.product_manifest.required` (structural; semantic effect none).
5. `HASHES.sha256` regenerated over the same inventory.
6. `receipt_catalog.yaml` derivation: invariants → c6e4d355…, contracts → f05239b7…, capabilities → 959acf1e…. RC-011 checks that ledger on every `make validate`.

## Final semantic reference closure (third pass)

Checks added to the same validator, run on the reference-closure candidate:

- RC-003 every projection profile class resolves to `profile_classes` (22 profiles, 6 classes, no allowlist): PASS
- RC-005 `l9.projection/product-identity-topology@1` uses source-local selectors (`product_topology` exactly `$.identity`, `$.governance`, `$.product.id`, `$.product.kind`; `identity_model` explicitly `$`), carries no profile-level `selects`, and every `stage` profile binds `semantic_build_stage.<stage>` to a stage declared in `vocabulary.semantic_build_stages` (14 profiles): PASS
- RC-012 `architecture_patterns.yaml` patterns declare obligations as `architecture_obligations` (7 values, lists of non-empty strings), no `required_capabilities` field or include remains, and no projection selector targets `$.patterns[*].required_capabilities` (4 profiles select `$.patterns[*].architecture_obligations`): PASS

Corrections in this pass:

1. `architecture_patterns.yaml`: pattern field `required_capabilities` renamed to the existing semantic concept `architecture_obligations` on `l9.pattern/semantic-core-provider-adapter@1` and `l9.pattern/runnable-node@1`; the seven obligation values are unchanged and are not resolved as capability identities. The same-file projection include lists follow the rename.
2. `projection_profiles.yaml`: the four selectors `$.patterns[*].required_capabilities` (semantic-compiler-core, stage-architecture, stage-ports, stage-provider-bindings) now select `$.patterns[*].architecture_obligations`.
3. `projection_profiles.yaml`: `l9.projection/product-identity-topology@1` is class `runtime` (identity resolution is evidence-bound to a runtime context and consumed by memory, bootstrap, governance, and receipt components; `stage` is excluded because `vocabulary.semantic_build_stages` declares no identity stage, `consumer` because no existing consumer coordinate names it, and `governance` because governance profile is not identity). Its sources use the catalog's source-local selector mapping; the ProductTopology selectors and the three rules are unchanged; no profile class was added.
4. `HASHES.sha256` regenerated over the same inventory.

Left unchanged in this pass: `pytest/v1` keeps its coordinate until a binding-ID grammar is declared; `compilation_profiles.yaml` declared the stage `identity_topology_resolution` while `vocabulary.semantic_build_stages` did not list it (outside this pass's lock; closed in the fourth pass below).

## Final stage-domain closure (fourth pass)

Check added to the same validator, run on the stage-domain-closure candidate:

- RC-013 `vocabulary.semantic_build_stages` equals the stage domain of the single canonical compilation profile `l9.compilation/product-build@1`: same stage ids, same list order, same ordinals, ordinals follow list position in both ledgers, exactly one profile in the `canonical: true` ledger (15 stages): PASS

Correction in this pass:

1. `vocabulary.yaml`: `identity_topology_resolution` added to `semantic_build_stages` at ordinal 2, the position `compilation_profiles.yaml` establishes. Its `consumes` (`product_topology_ir`, `identity_model`, `applicable_identity_contracts`, `product_kind_resolution`, `product_archetype_resolution`), `operations` (`projection`, `derivation`, `resolution`), and `produces` (`identity_topology_ir`, `identity_binding_requirements`) reproduce the profile's stage verbatim; `validation` uses the vocabulary's existing shape (`required: true`, `solver_source: canonical_compilation_profile`, the solver itself stays `identity-topology-validator/v1` in `solver_catalog.yaml`); the label `Identity Topology Resolution` is the stage id rendered in the vocabulary's label convention. The thirteen following stages keep every field and shift ordinal 2–14 → 3–15. No stage was redesigned, renamed, or removed; `compilation_profiles.yaml`, `identity_model.yaml`, `projection_profiles.yaml`, and `solver_catalog.yaml` are unchanged.
2. `HASHES.sha256` regenerated over the same inventory.

Left unchanged in this pass: `pytest/v1` keeps its coordinate until a binding-ID grammar is declared; for nine of the fourteen pre-existing stages the vocabulary's `consumes` or `operations` lists differed from the canonical profile's (twelve field differences), which this pass's RC-013 did not judge because the stage-domain contract covered ids, order, and ordinals only (closed in the fifth pass below); no `stage` projection profile exists for `identity_topology_resolution` (RC-005 binds stage consumers to declared stages, not the reverse, and projection edits were outside this pass's lock).

## Canonical stage semantic parity (fifth pass)

RC-013 strengthened in the same validator, run on the stage-parity candidate:

- RC-013 `vocabulary.semantic_build_stages` equals the single canonical compilation profile `l9.compilation/product-build@1` on stage ids, list order, ordinals, and, per stage, the exact `consumes`, `operations`, and `produces` lists (same values, same order; 15 stages, 45 field comparisons). A mismatch fails with file, stage id, field, vocabulary value, and canonical value: PASS

Correction in this pass:

1. `vocabulary.yaml`: twelve stage lists replaced with the canonical profile's exact values; no other byte of the file changed. `operations`: `product_topology` (`validation, resolution` → `projection, validation`), `architecture` (adds `resolution`), `provider_bindings` (`binding_selection` → `projection, binding_selection, resolution, synthesis`), `conformance` (adds `synthesis`), `product_manifest` (`derivation, validation` → `synthesis, validation`). `consumes`: `global_baseline` (adds `product_kind_resolution`, `product_archetype_resolution`), `requirement_resolution` (adds the same two and `identity_topology_ir`), `semantic_resolution` (adds `capability_resolution`, `node_archetypes`, `dependency_archetypes`), `ports` (adds `applicable_conformance_projection`), `provider_bindings` (`technology_capabilities, provider_constraints` → `technology_profile, technology_capabilities, binding_catalog`), `conformance` (adds `product_kind_resolution`, `product_archetype_resolution`, `conformance_model`, `selected_pattern_refs`, `adapter_requirement_ir`, `product_relationship_ir`, `fixture_profiles`), `product_manifest` (adds `identity_topology_ir`). No `produces` list differed. Stage ids, order, ordinals, labels, and `validation` blocks are unchanged; the vocabulary's `solver_source: canonical_compilation_profile` indirection is kept and the profile's `solver_ref` and `subjects` are not copied.
2. `HASHES.sha256` regenerated over the same inventory.

Left unchanged, recorded as successor concerns: `pytest/v1` keeps its coordinate until a binding-ID grammar is declared; no `stage` projection profile exists for `identity_topology_resolution` (14 stage profiles for 15 stages; whether canonical law requires total stage projection coverage is an open authority question, not a synchronization defect).

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
