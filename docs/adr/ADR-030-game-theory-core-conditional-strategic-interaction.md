# ADR-030 — Game Theory Core: Conditional Strategic Interaction

**Status:** Accepted for semantic-foundation v3.33.0. The repository owner admitted v3.33.0 on 2026-11-08. The decision was given as explicit instructions in a governed Claude Code session (`session_017xwbxytavCYavKdhRr9a6n`): the campaign contract L9-GT-SEAM-CAMPAIGN-CLOSEOUT-CONTRACT/v1 ("Complete GT core admission"), then "The GT candidate IS to be admitted that’s the point of this close out". This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when Quantum-L9/.github#225 merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.33.0**, additive successor to v3.32.0 |
| Pull request | Quantum-L9/.github#225. The candidate pack reaches `main` through #216 → #213. |
| Approved semantic tree | `semantics/` tree `3ce1adaf6da7f5eea8c47414bffc86145906505c`. It is identical at the qualified commit `f03f85981a7bd8249bc5998ee04535f53608fd73` and at #225's head; the later commits change only this ADR, its index and the v3.33.0 release documents. |
| Producer | `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891` |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Owner decisions | `docs/candidates/GT/evidence/admission/gt-owner-decision.yaml` (G1 KEEP, G2 subject, G3 native schemas retained, G4 dependent contract later) |
| Effective revision | The `main` commit that merges #225. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admission is scoped to the v3.33.0 delta. The v3.29.0, v3.30.0 and v3.31.0 deltas, merged to `main` as candidates, are not admitted by this record.

## Context

Strategic planning needs admitted semantics for conditional strategic interaction: how other actors respond to a focal action, under their information, incentives and versioned assumptions. Without them a planner silently treats the world as passive. The candidate (Quantum-L9/.github#213, remediated in #216) was aligned with Strategic Value, which v3.32.0 (ADR-029) admitted on its own first.

## Decision

1. **G1 — `L9-GT-001` (KEEP).** No admitted invariant states conditional modeling of other actors' responses. L9-UNKNOWN-001 governs how Unknown is carried, not when adaptive response must be modeled. L9-SV-001 governs counterfactual comparability for value claims, not actor response; the L9-IDENTITY-* invariants that mention actors govern identity, not behavior (checked against main c9bbfaf, 33 invariants). docs/candidates/GT/evidence/sv_collision_report.json records zero shared GT/SV terms, invariant, contract and profile IDs; docs/candidates/GT/evidence/pr212_break_test.json records LOCAL_FALSIFICATION_SURVIVED.

   > For an assessment that asserts strategic interaction, model other actors' consequential responses as conditional on the focal action, their information available at each decision point, incentives and version-bound response assumptions, or preserve missing conditional behavior as Unknown. A passive-world approximation is only an explicit model assumption, never silently equivalent to adaptive response. This obligation does not by itself assert a quantified Strategic Value claim.

2. **G2 — GT-only subject.** `l9.contract/strategic-interaction-assessment@1` over exactly `L9-GT-001`, `L9-AUTH-002`, `L9-HARD-001`, `L9-UNKNOWN-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001`; 12 vocabulary terms; `l9.projection/strategic-planner-interaction@1` over `vocabulary`, `invariants`, `contracts`; `l9.compose/strategic-planner-interaction@1`; and the forbidden criterion `sv_semantic_records_excluded_from_gt_projection`. It excludes every SV-owned term, invariant and contract from the GT projection. The GT core stays valid without Strategic Value; it cites no SV invariant.
3. **G3 — payload schemas.** The native YAML payload schemas that pass the real producer and the 19 controls are the admitted descriptors. The compiler-generated JSON candidates and drafted grammars under docs/candidates/GT/synthesis/ stay supporting evidence and are not admitted (campaign contract Article 4, preferred route).
4. **Not in this release.** `l9.contract/strategic-value-interaction-composition@1` is admitted separately, after this release (G4).

## Consequences

- Consumers bind only through their own release process after admission and trusted replay.
- No projection, composition or receipt is evidence of a numerical valuation or of an executed game solver.
- Neither foundation grants plan admission, strategic commitment, execution, publication or deployment authority.

## Evidence relied on

Owner decisions: `docs/candidates/GT/evidence/admission/gt-owner-decision.yaml`. Producer: `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891`. See `docs/semantic-foundation/v3.33.0/RELEASE_VALIDATION.md`.

## What admission does not establish

- Admission of `l9.contract/strategic-value-interaction-composition@1`; it is a separate subject in its own release.
- Independent consumer replay or consumer binding.
- Admission of the compiler-generated candidate schemas or drafted grammars under `docs/candidates/GT/synthesis/`.
- Any game-solver execution, equilibrium claim, numerical valuation, plan admission, execution, publication or deployment authority.
