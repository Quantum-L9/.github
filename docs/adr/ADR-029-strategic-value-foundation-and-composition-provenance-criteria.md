# ADR-029 — Strategic Value Foundation and Catalog-Declared Composition Provenance Criteria

**Status:** Accepted for semantic-foundation v3.32.0. The repository owner admitted v3.32.0 on 2026-11-08. The decision was given as an explicit instruction in a governed Claude Code session (`session_017xwbxytavCYavKdhRr9a6n`: "I approve. Admit formally and close it out"), which also directed the merge of Quantum-L9/.github#222 into `main`. It follows the owner's approval of decisions D1-D5 in the same session. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when #222 merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.32.0**, additive successor to v3.31.0 |
| Pull request | Quantum-L9/.github#222. The candidate pack and its evidence were merged through #220 → #215 → #212 (`92c037a`); the compiler criteria through Quantum-L9/l9-semantic-compiler-engine#33 (`9ca8d0e`). |
| Approved semantic tree | `semantics/` tree `251bb3d9238f93f0207b1f8443c80359e034595b`. It is identical at the qualified authority commit `c4c4a1dd7275f50e8249168fc86aa5c5d1b14ee7` and at #222's head, which differs from `c4c4a1d` only in this ADR and the four v3.32.0 release documents. |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges #222. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Invariants `L9-SV-001` (the original SV-001 statement followed by the original SV-015 statement, verbatim) and `L9-SV-002` in `semantics/invariants.yaml`. No other `L9-SV-*` identity is admitted; SV-003..SV-014 and SV-015..SV-020 remain model and contract text with their lineage.
- `l9.contract/strategic-value-assessment@1` in `semantics/contracts.yaml`.
- `l9.strategic.value@1` (`semantics/strategic_value_model.yaml`), its canonical source `l9.source/strategic-value-model@1` and source class `strategic_value_model`.
- Eleven vocabulary terms in `semantics/vocabulary.yaml`.
- `l9.projection/strategic-planner-value@1`, `l9.compose/strategic-planner-value@1` and their payload schemas `l9.projection.strategic-planner-value/v1` and `l9.composed-projection.strategic-planner-value/v1`.
- `semantics/composition_profiles.yaml#provenance_constraints` (`l9.provenance-constraint` v1) and the global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`, with validator RC-033.
- The derivation-coordinate rebinding of `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml`.

Admission is scoped to the v3.32.0 delta. The v3.29.0, v3.30.0 and v3.31.0 deltas, merged to `main` as candidates before it, are not admitted by this record.

## Context

Strategic Planning needs exact admitted Strategic Value semantics: objective-relative valuation against a feasible counterfactual baseline, an exhaustive causal accounting partition, and the evidence, uncertainty and authority boundaries of a quantitative Strategic Value claim. The candidate (Quantum-L9/.github#212, reduced in #215, closed out in #220) carried twenty candidate meanings. The reduction keeps two as new global invariants. The other eighteen are kept as traceable model text with unchanged contract obligations, governed by existing law.

Its composition profile declares four `required_provenance` tokens. The Semantic Compiler had no admitted criterion for any `required_provenance` token, so every composition declaring them (this one and `l9.compose/stage-context@1`) was reported `unknown` although each named fact was intact.

## Decision

1. **D1 — `L9-SV-001`.** The original SV-001 statement followed by the original SV-015 statement, both verbatim:

   > For an assessment asserting quantified Strategic Value, declare the objective, compatible utility units, feasible counterfactual baseline, bounded horizon, applicable discount and utility-flow basis, model/evidence coordinates and material uncertainty. Unknown or incompatible inputs cannot establish a complete Strategic Value ranking. For a Strategic Value claim, a counterfactual comparison must identify the same decision-relevant initial conditions, utility measure, exogenous context and time basis across intervention and baseline worlds, or explicitly quantify their divergence. A convenient scenario pairing or historical correlation is not evidence of an identifiable causal intervention effect.

   `L9-SV-002` is the second and only other new invariant. `L9-SV-015` merges into `L9-SV-001`; `L9-SV-016..018` relocate to the assessment contract; `L9-SV-019` reuses `L9-UNKNOWN-001`; `L9-SV-020` reuses the evidence, assurance, provenance and coordinate invariants. The twelve earlier meanings `L9-SV-003..014` stay as model text.
2. **D2 — composition provenance (R2).** Keep the four required_provenance declarations and make them mechanically verified. Establish the governing source of each requirement and whether a governed .github criterion is needed in addition to compiler enforcement; never invent authority in the compiler or mark an unsupported criterion satisfied. Bind components to exact source artifacts, composition profile and revision; keep tamper controls; cover l9.compose/stage-context@1; pin the exact compiler revision behind the final receipts. Realized as `composition_profiles.yaml#provenance_constraints` in `l9.provenance-constraint` v1, defining `source_projection_refs`, `source_projection_digests`, `composition_profile_ref`, `composition_profile_digest`, and the global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`. RC-033 validates the closure.
3. **D3.** capabilities.yaml, lifecycle.yaml and receipt_catalog.yaml take derivation-coordinate updates only, provided the freshly pinned source and native validation confirm no substantive change; fail closed on any mismatch.
4. **D4.** Independent successor release numbered at admission. Do not fold into v3.29.0, reserve v3.30.0 or v3.31.0, or hardcode v3.32.0. Select release number and ADR identity from the authoritative merged state when the admission branch is cut; preserve predecessor releases and hashes. Computed, not typed in, by `docs/candidates/SV/tools/prepare_successor_release.py` (Quantum-L9/.github#220): the merged state at this branch's base gives v3.32.0 and ADR-029, which earlier-queued PRs claim, so this candidate is provisionally v3.32.0 and ADR-029. The tool re-selects from the merged state when the branch is refreshed after those PRs land.
5. **D5.** Sequential admission in actual merge order: preceding numbered releases first, then SV in its own successor release, then GT core on the remediated #216 candidate and the admitted SV foundation, then the GT+SV dependent contract once its dependencies are satisfied. SV is not coupled to unrelated GT work; SV/GT compatibility is preserved.

## Options considered

- **D1 Option A** (development-pack wording) narrowed the ranking consequence to causally attributed rankings, the safeguard to claimed causal effects, and "quantify" to "identify and justify". Independent review classified it as a weakening. Rejected.
- **D2 R1** (remove the four declarations) would have produced a PASS by deleting normative text and left `l9.compose/stage-context@1` unresolved. Kept only as a controlled contingency; not used.

## Consequences

- The compiler evaluates a `required_provenance` token only through the catalog's declared criterion; an undefined token stays unresolved, and an unknown language, criterion or parameter fails closed. No authority is created in the compiler (`Quantum-L9/l9-semantic-compiler-engine@33e4c5832bf73c7d9b0b70854af011e9582f1ab2`).
- `l9.compose/stage-context@1` gains the same mechanical evaluation.
- Consumers bind only through their own release process after admission and trusted replay.

## Evidence relied on

Producer qualification at the approved semantic tree, `l9-semantic-compiler-engine@33e4c5832bf73c7d9b0b70854af011e9582f1ab2` (on that repository's `main` through #33): five source projections pass, the composition passes with all four `required_provenance` criteria verified and no unresolved criterion, two runs reproduce 29 artifact, receipt and summary files byte for byte, 18 of 18 producer negative controls behave as intended, the compiler's 20 composition-provenance tests (tamper and fail-closed cases) pass at `33e4c58`, and native validation exits 0. See `docs/semantic-foundation/v3.32.0/RELEASE_VALIDATION.md` and the candidate pack evidence on Quantum-L9/.github#220 (`docs/candidates/SV/evidence/admission/`).

## What admission does not establish

- Independent consumer replay or consumer binding. Consumers bind through their own release process after trusted replay.
- Admission of the v3.29.0, v3.30.0 or v3.31.0 deltas.
- Any numerical result, strategic commitment, plan admission, execution, publication or deployment authority. Valuation stays derived and non-authoritative.
