# ADR-031 — Strategic Value and Game Theory Interaction Composition Contract

**Status:** Candidate for semantic-foundation v3.34.0.

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
