# ADR-029 — Strategic Value Foundation and Catalog-Declared Composition Provenance Criteria

**Status:** Candidate for semantic-foundation v3.32.0. The repository owner approved decisions D1-D5 on 2026-11-08 as an explicit instruction in governed Claude Code session `session_017xwbxytavCYavKdhRr9a6n`. Owner approval of the decisions is not admission. Admission of v3.32.0 is the acceptance gate, after the preceding numbered releases (v3.30.0:ADR-027, v3.31.0:ADR-028) are admitted; this record does not admit itself.

## Context

Strategic Planning needs exact admitted Strategic Value semantics: objective-relative valuation against a feasible counterfactual baseline, an exhaustive causal accounting partition, and the evidence, uncertainty and authority boundaries of a quantitative Strategic Value claim. The candidate (Quantum-L9/.github#212, reduced in #215, closed out in #220) carried twenty candidate meanings. The reduction keeps two as new global invariants. The other eighteen are kept as traceable model text with unchanged contract obligations, governed by existing law.

Its composition profile declares four `required_provenance` tokens. The Semantic Compiler had no admitted criterion for any `required_provenance` token, so every composition declaring them (this one and `l9.compose/stage-context@1`) was reported `unknown` although each named fact was intact.

## Decision

1. **D1 — `L9-SV-001`.** The original SV-001 statement followed by the original SV-015 statement, both verbatim:

   > For an assessment asserting quantified Strategic Value, declare the objective, compatible utility units, feasible counterfactual baseline, bounded horizon, applicable discount and utility-flow basis, model/evidence coordinates and material uncertainty. Unknown or incompatible inputs cannot establish a complete Strategic Value ranking. For a Strategic Value claim, a counterfactual comparison must identify the same decision-relevant initial conditions, utility measure, exogenous context and time basis across intervention and baseline worlds, or explicitly quantify their divergence. A convenient scenario pairing or historical correlation is not evidence of an identifiable causal intervention effect.

   `L9-SV-002` is the second and only other new invariant. `L9-SV-015` merges into `L9-SV-001`; `L9-SV-016..018` relocate to the assessment contract; `L9-SV-019` reuses `L9-UNKNOWN-001`; `L9-SV-020` reuses the evidence, assurance, provenance and coordinate invariants. The twelve earlier meanings `L9-SV-003..014` stay as model text.
2. **D2 — composition provenance (R2).** Keep the four required_provenance declarations and make them mechanically verified. Establish the governing source of each requirement and whether a governed .github criterion is needed in addition to compiler enforcement; never invent authority in the compiler or mark an unsupported criterion satisfied. Bind components to exact source artifacts, composition profile and revision; keep tamper controls; cover l9.compose/stage-context@1; pin the exact compiler revision behind the final receipts. Realized as `composition_profiles.yaml#provenance_constraints` in `l9.provenance-constraint` v1, defining `source_projection_refs`, `source_projection_digests`, `composition_profile_ref`, `composition_profile_digest`, and the global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`. RC-033 validates the closure.
3. **D3.** capabilities.yaml, lifecycle.yaml and receipt_catalog.yaml take derivation-coordinate updates only, provided the freshly pinned source and native validation confirm no substantive change; fail closed on any mismatch.
4. **D4.** Independent successor release numbered at admission. Do not fold into v3.29.0, reserve v3.30.0 or v3.31.0, or hardcode v3.32.0. Select release number and ADR identity from the authoritative merged state when the admission branch is cut; preserve predecessor releases and hashes. Computed, not typed in, by `docs/candidates/SV/tools/prepare_successor_release.py` (Quantum-L9/.github#220): the merged state at this branch's base gives v3.30.0 and ADR-027, which earlier-queued PRs claim, so this candidate is provisionally v3.32.0 and ADR-029. The tool re-selects from the merged state when the branch is refreshed after those PRs land.
5. **D5.** Sequential admission in actual merge order: preceding numbered releases first, then SV in its own successor release, then GT core on the remediated #216 candidate and the admitted SV foundation, then the GT+SV dependent contract once its dependencies are satisfied. SV is not coupled to unrelated GT work; SV/GT compatibility is preserved.

## Options considered

- **D1 Option A** (development-pack wording) narrowed the ranking consequence to causally attributed rankings, the safeguard to claimed causal effects, and "quantify" to "identify and justify". Independent review classified it as a weakening. Rejected.
- **D2 R1** (remove the four declarations) would have produced a PASS by deleting normative text and left `l9.compose/stage-context@1` unresolved. Kept only as a controlled contingency; not used.

## Consequences

- The compiler evaluates a `required_provenance` token only through the catalog's declared criterion; an undefined token stays unresolved, and an unknown language, criterion or parameter fails closed. No authority is created in the compiler (`Quantum-L9/l9-semantic-compiler-engine@33e4c5832bf73c7d9b0b70854af011e9582f1ab2`).
- `l9.compose/stage-context@1` gains the same mechanical evaluation.
- Consumers bind only through their own release process after admission and trusted replay.

## Evidence

See `docs/semantic-foundation/v3.32.0/RELEASE_VALIDATION.md` and the candidate pack evidence on Quantum-L9/.github#220 (`docs/candidates/SV/evidence/admission/`).
