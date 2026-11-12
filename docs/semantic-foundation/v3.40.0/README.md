# Semantic Foundation v3.40.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.40.0 gives `l9.fixture-ir/v1` (Stage 8, `fixtures`) and `l9.conformance-ir/v1` (Stage 12, `conformance`) canonical structures, and gives the product-authored harness surface its own structure (`l9.harness-surface/v1`). Before this release both IRs had an identity, a purpose and transitions in `ir_catalog.yaml`, but no admitted structure, so the required validations under `fixture-derivation-validator/v1` and `reference-conformance/v1` had nothing to check against.

Successor to v3.39.0. This is contract `L9-GH-R5-F1-001` of campaign R5 (conformance-first), first drafted as v3.37.0 / ADR-034 on v3.36.0 and renumbered when v3.37.0 to v3.39.0 were admitted on `main` first; the delta is unchanged from the audited tip `agent/r5/F1@15faa586ae2c`. ADR-037 is its candidate decision record and does not admit itself. The candidate was amended in place, before admission, by the operator-approved package of 2026-11-12 (items 1–8 and D-OBLIGATIONS, ADR-037 decisions 12–20).

## Bounded delta

- `semantics/fixture_ir.schema.yaml` (`l9.schema/fixture-ir@1`): `l9.schema-definition/v1` whose `properties.schema.const` is `l9.fixture-ir/v1` (Stage 8 output). Fixture cases with non-empty `source_law_refs`, contract-typed `given` setup (interface actions, port fixtures, declared harness controls, a flat `{path: literal}` precondition), a single `when.operation` or a declared sequence/parallel group, a literal Gate invocation `context` per Gate action step and per interface-action observation, and `expect` over result contracts, declared read observations and declared harness observations only. The interface surface declares forbidden actions, harness controls (`clock`, `journal_retention`, `fault_injection`, `authorization_policy`, `internal_setup`) and harness observations. Evaluation semantics are pinned: presence predicates treat an absent path as a value, relational predicates on an absent path are an error, and `count_where {where: [{path, predicate, operand?}], count}` counts exactly. `subject`/`provenance` bind the pre-manifest `closure_digest`. `law_index` entries carry the law `statement` and a closed `verification_class`. 38 `semantic_rules` enforced by `fixture-derivation-validator/v1`.
- `semantics/conformance_ir.schema.yaml` (`l9.schema/conformance-ir@1`): const `l9.conformance-ir/v1` (Stage 12 output). One obligation per `law_index` entry, derived from the law (governing ref, law kind, statement, verification class, citing cases), with disposition, a target-neutral execution plan for executable-class obligations, verdicts `pass | fail | error | unresolved`, `fixture_profile` and typed `unknowns`. Only `fixture_replay` can make an obligation executable; `static_inspection` and `external_runtime_evidence` obligations are unresolved and never pass. 19 `semantic_rules` enforced by `reference-conformance/v1`.
- `semantics/harness_surface.schema.yaml` (`l9.schema/harness-surface@1`): const `l9.harness-surface/v1`, the product-authored harness surface `{schema, product_ref, owner, revision?, harness_controls, harness_observations}`. Entries reuse the fixture-IR entry shapes and add a required, verified-never-regenerated `implementation_ref`. Stage 8 consumes it as `product_harness_surface`. 6 `semantic_rules` enforced by `fixture-derivation-validator/v1`.
- **Interim law input** (part of the admission subject, not canonical until admitted): `fixture_ir.schema.yaml#interim_law_input` and `law_index` substitute for Stage 8's `semantic_law_ir` and `law_provenance` until an owner-admitted `l9.law-ir/v1` schema exists. No law-ir schema is authored.
- `semantics/product_topology.schema.yaml#properties.conformance`: optional `fixture_case_refs: [{ref, digest}]` and `harness_surface_ref: {ref, digest}`; `product_file_resolution` (raw-bytes digests, resolution to exactly one RepositorySpec authoritative source entry by `coordinate`, confinement to the repository, four typed refusals); six `semantic_rules`. `conformance.required` is unchanged; existing topologies stay valid.
- `semantics/product_manifest.schema.yaml`: optional `closure_digest` and `conformance.compilation {fixture_ir_digest, conformance_ir_digest}`, `closure_digest_definition` (the semantic digest of the manifest without `manifest_digest`, `closure_digest` and `conformance.compilation`), two `semantic_rules`. `required` is unchanged.
- `semantics/ir_catalog.yaml`: adds `l9.harness-surface/v1` so the harness-surface schema registers through the same IR-schema route as the two IR schemas.
- `semantics/compilation_profiles.yaml` (`l9.compilation/product-build@1` stage 8) and `semantics/vocabulary.yaml#semantic_build_stages` (RC-013 parity): stage 8 consumes `product_fixture_cases` and `product_harness_surface`.
- `semantics/binding_catalog.yaml`: `pytest/v2`, `successor_of: pytest/v1`, mapping groups, observations, harness controls and observations, context (including observation context), exact `count_where`, presence checks and unresolved cases. `pytest/v1` is unchanged.
- `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas` lists the three schemas.
- `scripts/validate-semantics.py`: RC-035 and RC-035-NEG; `scripts/fixture_conformance_ir.py` and `ops/fixtures/fixture-conformance-ir/` (6 positive witness files, 110 falsifying fixtures).
- ADR-037 (candidate).

## Evidence

Candidate pack: `docs/candidates/R5-F1/` (design, rule → validator → falsifying-fixture table, State language test, `pytest/v1` alignment and the `pytest/v2` successor, Unknowns, step-0 admission verdicts). Language test: five State cases from `Quantum-L9/l9-wip@ce0c4973af31aa68741014febef1364ba58f3e3f` encode with no State-specific field and all are executable after the amendment; each `law_index` statement is State's invariant `assertion` verbatim. State's harness refs and its closure digest are stand-ins until State declares its harness surface and a manifest is compiled.

## Outstanding Unknowns

- U0: no `l9.law-ir/v1` structural schema; `law_index` is the interim substitution (owner-owned follow-up).
- RepositorySpec authoritative source entries do not yet carry `coordinate`; `product_topology.schema.yaml#product_file_resolution.consumer_requirement` states what resolution reads, and the RepositorySpec schema is owned outside this repository.
- No compiler run has consumed the amended schemas yet; the compiler agent re-locks to this candidate and its rehearsal is separate evidence.

U4 (no admitted `verification_class` domain) is closed by the closed `verification_class` enum.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants mutation, publication, merge, admission, deployment or execution authority. Admission of v3.40.0 requires the repository owner's explicit decision for this exact subject.
