# ADR-007: Conformance requirements are derived before implementation

Status: Accepted

## Decision
`.github` owns the global semantics for deriving conformance requirements. `l9-conformance` owns fixture identity/admission, profile resolution, executable conformance, and conformance receipts.

Correctness criteria must preexist and be independent of the candidate implementation or its generation path. Fixtures/tests may realize governing law but may not invent it. Conformance evidence proves declared observations; it does not grant authority.
