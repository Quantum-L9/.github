# Strategic Value schema qualification: bounded evidence and admission gate

**Status (reduction-v1, current):** `NATIVE_SCHEMA_QUALIFICATION_PASS@3bf1a82; FIVE_PROJECTIONS_PASS; COMPOSITION_UNKNOWN; NOT_ADMITTED` — see the successor section at the end.  
**Status (PR #212, historical):** `LOCAL_SCHEMA_HARDENING_PASSED; NATIVE_COMPILER_QUALIFICATION_BLOCKED`  
**Beneficiary:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397` (read-only).  
**Interpreter inspected:** `Quantum-L9/l9-semantic-compiler-engine@943db9a462d35ba66771a700ece77c746295f591`, `src/l9_semantic_compiler/passes/validate.py` lines 190-243.  
**Admission/remote mutation:** NONE.

## Resolved schema enforcement defects

| Finding | Evidence | Change | Status |
|---|---|---|---|
| Fixed normative truths accepted false | Both schemas used `type: boolean` for source-true obligations | Bind 21 boolean fields per schema to exact source values with **both** `type: boolean` and `const: true`; protects against false and integer `1` | LOCAL STRUCTURE PASS; native behavior pending |
| `string_list.min_items` silently ineffective | Native `schema_violations` checks `min_items` only in its `declared_type == "array"` branch, not the `string_list` branch | Convert 31 list declarations per schema to `type: array`, `items.type: string`, retained `min_items` | LOCAL STRUCTURE PASS; native behavior pending |
| `terms.fields` may be unsupported | Native `schema_violations` prefers `descriptor.fields` over `properties`, and descends to child descriptors | No dialect change; add actual nested term mutation witness in native qualification runner | SOURCE CONTRACT CONFIRMED; native behavior pending |
| Per-source root has no `required` namespace | One projection schema applies to five heterogeneous source classes | Retain permissive root; native producer *must* independently prove selected source class and exact selected-ID equivalence; composition requires all five source namespaces | ACCEPTED CONDITIONAL ON ACTUAL PRODUCER PROOF |
| ID enum + minimum does not establish identity uniqueness | Native schema dialect does not enforce exact coverage/uniqueness through those fields | Do not add an unsupported uniqueness keyword to manufacture PASS; require source selection equivalence and source-identity replay | EXTERNAL VALIDATION REQUIRED |

The field `schema` identifies the *derived payload* version, not the original source document's schema identity; the source model selector intentionally excludes `$.schema`. The projection artifact envelope and producer receipt still independently bind source ref/digest/profile.

## Runnable native-compiler qualification

The package includes `tests/run_native_schema_qualification.py`. Run with the **actual** `l9_semantic_compiler` installed and importable in the exact compiler checkout:

```bash
PYTHONPATH=/path/to/l9-semantic-compiler-engine/src python tests/run_native_schema_qualification.py
```

It fails closed with exit 2 if the real package is unavailable, and tests: (1) a selected model payload positive control; (2) false and integer-as-boolean mutations; (3) a required minimum-length list changed to empty; (4) a nested vocabulary term positive control; (5) non-string nested `definition`; and (6) a composition missing four required source namespaces. This is native schema-dialect verification only; it does **not** generate a real projection receipt or prove that the profile selects the correct records.

Local execution in this environment returned `BLOCKED / REAL_COMPILER_NOT_IMPORTABLE` (exit 2). No native PASS was inferred from reading the implementation source.

## Independent falsifier evidence

The **complete previous package already contained** `tests/run_strategic_value_falsifiers.py`, `tests/falsification_cases.json`, all six per-case receipts, and `evidence/local_candidate_tests.log`. Their absence from an individually supplied upload set is a visibility limitation, not a missing-archive fact. They run as dedicated, purpose-built contract assertions and **do not** invoke a production Strategic Value numerical method. Their success must never be used to claim the Numerical Reasoning implementation enforces SV-015..020.

For substantive admission, integrate the same bad/good counterexamples into the real consumer or numerical contract evaluator, with exact source IDs, response status, and numerical model revisions. Do not replace that independent proof by rewriting the local test function.

## Dependency closure before canonical admission

1. Qualified owner decisions for the eight dispositions (two kept invariants, six relocations), including the amended SV-001 wording (see `IRREDUCIBILITY_OWNER_REVIEW.md`).
2. A **real** clean `.github` checkout at the pinned/base successor revision, patch applied, native semantic checks, exact schema artifact registrations under `generic_compiler_manifest.yaml`, projection/composition catalog closure and source-digest verification.
3. Real compiled output for all five source projections plus one composition under the declared profile IDs; every artifact and receipt authentic, with source-selected identity equivalence, `payload_schema`, `selection_equivalence`, exact digest, namespace coverage and freshness criteria passing.
4. Consumer-side replay of producer provenance and real Numerical Reasoning validation, not just the five-source semantic-view receipt.
5. Authorized canonical admission and governed publication. A self-contained local ZIP cannot admit itself.

**Conclusion:** source-schema defects repaired and local tests passed; qualification is explicitly not admission-ready until the native compiler and independent evaluator evidence is produced.

## Successor qualification: two-invariant reduction (`evidence/reduction-v1/`)

**Compiler:** `Quantum-L9/l9-semantic-compiler-engine@3bf1a8241452332637ba0daffeee55c433f93e05` (0.9.3), imported from source with a clean `src/`. **Authority:** a local, never-pushed rehearsal commit `d723fe901bfdcfe13748f302f99db5eaa88c519e`. It is the applier's output on `020a94b`, committed in a disposable clone, because the compiler reads git objects at an exact revision.

| Gate | Result | Evidence |
|---|---|---|
| Schema changes | Invariant enum and `min_items` now 12 in both schemas; `governed_by.invariants.min_items` 12; typed `relocated_additional_candidate_semantics` descriptor (8 required fields, `const` candidate ID, disposition and authority status; non-empty `governing_invariants` restricted to the 12 selected IDs) in the projection schema and the composition model namespace. Boolean `const` pins stay 21 per schema; typed string arrays rise from 31 to 37 per schema. | `tools/reduce_to_two_invariants.py --check` |
| Native `schema_violations` | **PASS**, 24 checks: positive reduced model; false and integer booleans; empty and 11-item governance arrays; 7 lineage mutations, including a removed ID used as a governing ref; 12-record invariant positive; each of SV-015..020 rejected as an invariant record; nested vocabulary; missing composition namespaces; composition model namespace without lineage | `native-schema-results.json` |
| Five real source projections | **PASS** each: `source_identity`, `source_currentness`, `profile_currentness`, `selection_equivalence`, `payload_schema`. The invariants projection selected exactly the 12 IDs. | `projection-run1/`, `determinism-comparison.json` |
| Real composition | **UNKNOWN** (exit 3): `component_provenance`, `composition_equivalence` and `payload_schema` pass. The four `declared_constraint:required_provenance:*` criteria stay unresolved because compiler 0.9.3 has no mechanical criterion for them. | `projection-run1/receipts/313a7e77….json` |
| Determinism | Two independent output directories, 12 files, byte-identical | `determinism-comparison.json` |
| Producer negative controls | 16 negatives each fail through the intended mechanism (`REVISION_MISMATCH`, `INVALID_REQUEST`, `UNRESOLVED_REFERENCE`, `STRUCTURAL_VALIDATION_FAILED` on `payload_schema`, `INVALID_PROFILE` missing selector, `AMBIGUOUS_SEMANTICS` duplicate source, projection-digest binding). Both positive controls pass. | `producer-negative-controls.json` |

The composition `unknown` is not suppressed. The profile's `required_provenance` declaration is unchanged from PR #212. Removing it would drop a declared constraint to obtain a PASS, so that decision is left to the owner.

**No canonical producer receipt is claimed.** The receipts above are bound to the rehearsal revision. They must be regenerated from the admitted revision after admission.
