# ADR-0003: Immutable authority binding

## Status

Accepted

**Date:** 2026-09-25
**Deciders:** Human owner
**Related:** campaign `dotgithub-governance-compiler-v1` (integration branch `campaign/dotgithub-governance-compiler-v1`); [ADR-0001](./0001-one-governance-brain.md), [ADR-0002](./0002-versioned-governance-plan-compiler.md)

---

## Context and Problem Statement

A governance transaction can compile against one policy revision and later
apply or attest against a different, moving `main`. Both stages are then
individually valid but do not describe the same authority.

## Decision Drivers

- reproducible governance transactions
- auditable provenance
- fail-closed handling of a stale plan
- deterministic replay

## Considered Options

1. Always use current `main` at every step.
2. Record the SHA as evidence but keep applying current policy.
3. Bind the transaction to an exact authority SHA and expected plan digest;
   recompute and verify before mutation.

## Decision Outcome

**Chosen option:** "3 — bind to authority SHA and plan digest", because it is
the only option under which stale input cannot silently mutate a target.

Every production plan records an exact 40-character authority SHA. Targeted
bootstrap receives the expected SHA and plan digest, loads policy at that
revision, recomputes the plan from remote target facts, and refuses mutation if
either differs.

**Implementation:** compiler at `ops/compile-repo-governance.js`, schema at
`ops/schemas/repo-governance-plan.schema.json`, tests in
`ops/test-compile-repo-governance.js`. Consumers migrate in G2–G5 of campaign
`dotgithub-governance-compiler-v1` (integration branch
`campaign/dotgithub-governance-compiler-v1`); the bootstrap-side SHA and digest
check lands with the G5 cutover.

### Consequences

- Good, because plan, apply, and attest become one reproducible transaction.
- Good, because stale input cannot silently mutate a target.
- Bad, because callers must carry two additional pieces of evidence.
- Neutral, because a moving `main` no longer changes an already-authorized
  transaction.

## Pros and Cons of the Options

### Option 1 — current `main` at every step

- Good, because callers carry no extra evidence.
- Bad, because plan and apply can silently describe different policy.

### Option 2 — record the SHA, apply current policy

- Bad, because the recorded evidence then describes a revision that was not
  the one applied.

## Links

- Invariants created: GOV-017, GOV-018, GOV-019, GOV-020 — see
  [`docs/INVARIANTS.md`](../INVARIANTS.md).
