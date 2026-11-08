# ADR-031 — Strategic Value and Game Theory Interaction Composition Contract

**Status:** Accepted for semantic-foundation v3.34.0. The repository owner admitted v3.34.0 on 2026-11-08 as the second, separate admission of the GT campaign. The decision was given as explicit instructions in a governed Claude Code session (`session_017xwbxytavCYavKdhRr9a6n`): the campaign contract L9-GT-SEAM-CAMPAIGN-CLOSEOUT-CONTRACT/v1 ("Complete GT core admission, then admit the GT×SV dependent contract"), "The GT candidate IS to be admitted that’s the point of this close out", and "I want this closed out meaning PR’s merged". Owner decision G4 records the separate approval. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when Quantum-L9/.github#229 merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.34.0**, additive successor to v3.33.0 |
| Pull request | Quantum-L9/.github#229. The dependent-stage binding reaches `main` through #228. |
| Admitted foundations | SV v3.32.0 / ADR-029 (`64d8b85`) and GT core v3.33.0 / ADR-030 (`a4bb461`). The contract was applied on `a4bb461`, which carries both. |
| Approved semantic tree | `semantics/` tree `252ec0adcc6e62202a4b82d5bb2bbec3dcd67e34`. It is identical at the qualified commit `b09162876bcb40765c8cb21c5e56766b781fce73` and at #229's head. |
| Contract text | `docs/candidates/GT/overlays/contracts_sv_dependent.yaml` as aligned in #226: the SV assessment contract applies by reference, and no SV obligation is restated. |
| Producer | `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891` |
| Effective revision | The `main` commit that merges #229. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

## Context

With Strategic Value (v3.32.0, ADR-029) and the Game Theory core admitted, a planner needs the contract that joins them without double counting or redefining either foundation.

## Decision

1. **G4 — `l9.contract/strategic-value-interaction-composition@1`.** Admitted only in its own successor release after GT core is admitted, bound to the revision carrying both foundations. A consumer envelope may claim an evaluated result only with a genuine Numerical Reasoning receipt; none is admitted, so evaluated consumer mode stays unavailable.
2. The contract cites `L9-GT-001`, `L9-SV-001`, `L9-SV-002`, `L9-AUTH-002`, `L9-HARD-001`, `L9-UNKNOWN-001`, `L9-PROJECTION-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-PROV-001`, `L9-COORD-001`. It redefines neither foundation: a GT-conditioned Strategic Value assessment is one canonical SV assessment evaluated over GT-conditioned futures, never a standalone value plus a GT uplift.

## Consequences

- Consumers bind only through their own release process after admission and trusted replay.
- No projection, composition or receipt is evidence of a numerical valuation or of an executed game solver.
- Neither foundation grants plan admission, strategic commitment, execution, publication or deployment authority.

## Evidence relied on

Owner decisions: `docs/candidates/GT/evidence/admission/gt-owner-decision.yaml`. Producer: `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891`. See `docs/semantic-foundation/v3.34.0/RELEASE_VALIDATION.md`.

## What admission does not establish

- An active numerical evaluator. No Numerical Reasoning receipt type is admitted, so a consumer envelope claiming an evaluated GT×SV result is refused, and evaluated consumer mode stays unavailable.
- Any equilibrium, Nash or Q/V claim, any game-solver execution, plan admission, execution, publication or deployment authority.
- Independent consumer replay or consumer binding.
