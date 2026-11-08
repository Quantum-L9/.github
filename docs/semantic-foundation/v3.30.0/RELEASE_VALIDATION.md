# Release Validation v3.30.0

Candidate status: **additive successor candidate**.

## ImplementationIR structural contract closure

- **SC-001** parses 83 canonical sources as YAML mappings, `semantics/implementation_ir.schema.yaml` among them.
- **SC-003** finds 83 unique `artifact_id` values, including `l9.schema/implementation-ir@1`.
- **RC-006** classifies the new ledger exactly once.
- **RC-027** resolves 229 typed cross-ledger references (223 before). Each of the schema's six `governed_by.contracts` names a declared contract.
- **SC-008** proves this release record:
  - the manifest lists all **83** canonical sources;
  - the ADR count is **27**;
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.

## Qualification through the existing compiler mechanism

Run at `Quantum-L9/.github@d9cdb8a5f054a0481ede27a09493b875ecccdfbc`, with `Quantum-L9/l9-semantic-compiler-engine@18215ae2cd948ff8c9cc8992785d2f72f8b53310` exported unmodified (`l9-semantic-compiler` 0.9.3).

- **Resolution.** `CanonicalAuthority(...).schema_defining("l9.implementation-ir/v1")` returns `l9.schema/implementation-ir@1`.
- **Positive.** A State instance passes the v1 interpreter (`passes/validate.py` `schema_violations`) with no violation. It was lowered by hand from the resolved `l9.state` ProductManifest (`sha256:a8303f93…d1d2c`, Quantum-L9/l9-wip#37) and the topology's `interfaces` and `effects`. It is a structural qualification fixture, not compiler output, with:
  - 13 actions, 8 of them consequential;
  - 2 forbidden actions;
  - 4 ports and 4 adapters;
  - the optional ScopeAuthorization port as `unresolved`.
- **Shape negatives: 15 of 15 rejected at the intended field.**

| Case | Interpreter result |
|---|---|
| Missing manifest provenance | `$.provenance.manifest_digest: required field missing` |
| Malformed manifest digest | `$.subject.manifest_digest: expected semantic_digest` |
| Missing subject | `$.subject: required field missing` |
| Wrong IR schema const | `$.schema: expected const 'l9.implementation-ir/v1'` |
| Wrong compilation profile | `$.authority.compilation_profile_ref: expected const` |
| Fourth disposition (`best_effort`) | `…behavior.disposition: value not in declared enum` |
| Behavior without disposition | `…behavior.disposition: required field missing` |
| Consequential not boolean | `…consequential: expected boolean` |
| Action without request contract | `…request_contract_ref: required field missing` |
| Port without contracts | `$.ports[0].contract_refs: fewer than 1 items` |
| Port direction outside enum | `$.ports[0].direction: value not in declared enum` |
| Adapter without realized port | `$.adapters[0].realizes_port_ref: required field missing` |
| Unresolved entry without reason | `$.unresolved[0].reason: required field missing` |
| Missing composition root | `$.composition.root: required field missing` |
| Missing forbidden actions | `$.interfaces.forbidden_actions: required field missing` |

## Not mechanically checked

These cross-field controls pass the shape by construction. Each is stated as a named rule that `implementation-contract-validator/v1` must enforce. The Semantic Compiler at `18215ae` does not implement that solver yet (unit R4-B).

| Control | Shape result | Assigned rule |
|---|---|---|
| Wrong product identity | not a shape violation | `subject_product_kind_and_archetype_equal_the_manifest_product` |
| Non-Node selecting Node-only binding | not a shape violation | `target_binding_is_admitted_and_its_applies_to_and_source_ir_admit_the_subject` |
| Undeclared action | not a shape violation | `interface_actions_are_exactly_the_manifest_interfaces_actions_with_no_addition_omission_or_reordering_of_identity` |
| Unknown technology capability | not a shape violation | `target_binding_is_admitted_and_its_applies_to_and_source_ir_admit_the_subject` |
| Invented provider identity | not a shape violation | `no_optional_port_receives_an_invented_adapter_or_provider` |
| Behavior resolved without specification or binding | not a shape violation | `generable_requires_a_behavior_contract_ref_or_a_target_binding_map_that_determines_the_obligation` |
| Manifest digest mismatch | not a shape violation | `subject_and_provenance_manifest_digest_are_the_consumed_manifest_digest` |
| Unbound required port | caught only when `implementation_ref` has the wrong type | `bound_requires_an_admitted_implementation_ref_preserved_exactly_from_the_manifest` |

Also not checked: the nineteen rules as a whole, and that no release check pins the schema.

## Amendment: behavior-contract dependency, typed unresolved results, no operation_ref

Run at `Quantum-L9/.github@004a49b2a0ac155f838b9e1fec6a27f06bd64f16` (the semantic amendment before this record), with the unmodified `Quantum-L9/l9-semantic-compiler-engine@18215ae2cd948ff8c9cc8992785d2f72f8b53310`.

- **Resolution.** `schema_defining("l9.implementation-ir/v1")` returns `l9.schema/implementation-ir@1` with 19 `semantic_rules`.
- **Positive.** The hand-lowered State fixture passes. It is a structural qualification fixture, not compiler output, with 13 actions (8 consequential), 2 forbidden, 4 ports, 4 adapters, `provenance.behavior_contracts: []` and the optional ScopeAuthorization port `unresolved` with `result: unresolved`. Each of `unresolved`, `incompatible`, `unsat` and `ambiguous` is accepted as a result.
- **Shape negatives: 21 of 21 rejected at the intended field.** These are the 15 above re-run against the amended schema, plus the following:

| Case | Interpreter result |
|---|---|
| Provenance without `behavior_contracts` | `$.provenance.behavior_contracts: required field missing` |
| Behavior-contract entry without digest | `$.provenance.behavior_contracts[0].digest: required field missing` |
| Behavior-contract malformed digest | `$.provenance.behavior_contracts[0].digest: expected semantic_digest` |
| Unresolved entry without result | `$.unresolved[0].result: required field missing` |
| Unresolved result `resolved` | `$.unresolved[0].result: value not in declared enum` |
| Unresolved result `unknown` | `$.unresolved[0].result: value not in declared enum` |

- **Behavior-contract invalidation: structural fixture proof only.**
  - A shape-valid IR claims `generable` behavior through `example.behavior/x@1` and lists `{ref, digest}` with the compiler's canonical digest of content v1.
  - The digest rule holds for v1.
  - After a one-field content change (v2), the digests differ. The retained claim fails the rule, so it is stale.
  - `example.behavior/x@1` is an illustrative coordinate with no authority. No behavior-contract kind is admitted, so a live end-to-end invalidation of generated behavior is not demonstrable at this release.
- **operation_ref.** It is absent from `interfaces.actions[].behavior.properties`. The v1 interpreter does not reject undeclared fields, so its absence is a contract statement, enforced by `implementation_ir_adds_no_product_meaning_and_is_never_semantic_authority`.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 57 PASS lines and no FAIL, including:

- the negative-case batches;
- SC-001 to SC-010;
- every RC check it runs: RC-001 to RC-007, RC-009, RC-011 to RC-030 and RC-032.

No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.30.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
