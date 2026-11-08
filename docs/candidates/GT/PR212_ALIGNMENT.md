> **Historical (PR #212 @ `85531616`).** Superseded by `SV_ALIGNMENT.md`, which binds GT to the reduced SV candidate in PR #215 @ `a64d05a`. Kept unchanged below as the record of the first alignment.

# Game Theory candidate aligned to Strategic Value PR #212

**Scope:** GT-only repo candidate, no skill. **Source read:** [Quantum-L9/.github PR #212](https://github.com/Quantum-L9/.github/pull/212) at `85531616cee2da94bbb7154418a78537549a4d76`.
**Canonical baseline:** `.github/main@020a94bea86e7c5c5e4107da7014ec259508f397`. All PR #212 changes are documentation under `docs/candidates/SV/`; SV is **not admitted** and no SV source bytes are copied into this package.

## Material revisions versus previous GT candidate

1. **Identity collision repaired.** Previously GT added `strategic_commitment`, but canonical `semantics/vocabulary.yaml` already defines that as an authorized Plan commitment. New GT-only term `incentive_bearing_commitment` means the *game model's binding response-changing commitment*, not a Plan-owned commitment. GT selectors and strict schemas updated accordingly.
2. **GT claim-scoped, SV-independent.** `L9-GT-001` now applies only to an assessment asserting actor-adaptive interaction. The GT core contract can be evaluated without SV; generic numerical or passive-world analyses are not globally forced to use GT.
3. **PR #212 SV is the sole valuation owner.** Dependent contract references `l9.strategic.value@1`, `l9.contract/strategic-value-assessment@1`, `l9.projection/strategic-planner-value@1`, `l9.compose/strategic-planner-value@1`. Its dependency is **unresolved until independently admitted**. No copy of SV 11 terms, eight proposed laws, model, five-bucket formula, or two strict SV schemas.
4. **Same projection pattern as SV.** GT compiles exactly three independent source classes and GT-only `source_class_namespace` composition. The SV pack compiles five source classes. The two derived semantic views are consumed by the Planner; the canonical composition engine does not numerically combine them.
5. **Tighter source-schema shape.** GT per-source/composed schema candidates require selected term records, exact GT invariant/contract identities, typed record arrays, and non-empty required collections. Native interpreter and selector replay are still external proof obligations.
6. **Math and claim scope.** The SV model retains a mandatory exhaustive mutually exclusive IEV/SFV/DC/ERL/OC partition; GT only supplies action-conditioned response models. It does not add an uplift term or force a universal Q/V algorithm.
7. **Tooling pinned to PR head.** The local preparation script now requires exact `85531616cee2da94bbb7154418a78537549a4d76` plus the nine observed SV candidate blob IDs and exact original canonical source blobs. It prepares GT *core* on a clean checkout only with optional `--apply`; it never admits dependent GT+SV.

## Staging and admission order

- **Stage A**: Review GT-only overlay under a sibling `docs/candidates/GT/` documentation pack, as PR #212 did for SV. Do not revise PR #212 or apply either overlay into canonical `semantics/` in the current task.
- **Stage B**: Independently qualify GT global-invariant irreducibility, contracts, 3 source selections, 2 schemas, and source provenance against exact successor.
- **Stage C**: Independently admit SV (including any modified/retired proposed laws). Only then bind GT+SV dependent contract against the exact admitted SV revision and validate end-to-end method/consumer evidence.

## Break-test cases

1. **SV existing law collision**: GT copy of `strategic_commitment` would redefine Plan commitment -> **rejected and repaired**.
2. **Fake SV receipt from PR candidate** -> **blocked**, explicit Unknown.
3. **GT-only assessment without SV** -> **permitted**.
4. **Infeasible highest-payoff action** -> formal hard constraint wins.
5. **Missing response mass or correlated joint responses** -> conditional/Unknown, never invented or renormalized.
6. **Already valued reputation effect** -> no second uplift; one SV ledger after response model conditions.
7. **Multiple actors' benefits** -> beneficiary/welfare authorization required as PR #212 requires.
8. **Lookahead future-observation leakage** -> rejected under conditional SV-017; GT response model respects information at move.
9. **Softmax stable fixed point with nonzero Nash gap** -> do not assert Nash.
10. **SV-only consumer** -> unaffected by GT's 3-source projection.

**Evidence limit:** The tests are local structural and synthetic checks; a real producer schema interpreter, native compilation with 3 GT + 5 SV source projection receipts, actual empirical calibration, and owner admission were not performed. Local break-testing does not certify these stronger claims.
