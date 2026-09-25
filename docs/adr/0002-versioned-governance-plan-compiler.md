# ADR-0002: Versioned deterministic governance-plan compiler

## Status

Accepted

**Date:** 2026-09-25
**Deciders:** Human owner
**Related:** campaign `dotgithub-governance-compiler-v1` (integration branch `campaign/dotgithub-governance-compiler-v1`); [ADR-0001](./0001-one-governance-brain.md), [ADR-0003](./0003-immutable-authority-binding.md)

---

## Context and Problem Statement

A single policy owner still permits drift if consumers receive only raw source
files and each derives its own effective answer. Consumers need one versioned,
deterministic machine contract that describes the effective governance state
for a target.

## Decision Drivers

- identical interpretation across seed, remote apply, enforcement,
  reconciliation, and attestation
- machine-verifiable provenance
- no new external parser dependency merely for policy compilation
- pure compilation from explicit facts, so it can be tested

## Considered Options

1. Keep raw policy files as the consumer API.
2. Publish several per-capability helper APIs.
3. Compile one `l9.org-governance-plan/v1` document containing the complete
   effective answer.

## Decision Outcome

**Chosen option:** "3 — one versioned plan document", because a single complete
answer is the only consumer API that cannot be partially reinterpreted.

`ops/compile-repo-governance.js` is the canonical compiler. The plan is
schema-validated and carries the effective class, materialization, inheritance,
prohibition, mandatory-file state, labels, repository settings, attestation
expectations, authority identity, and a deterministic digest.

**Implementation:** compiler at `ops/compile-repo-governance.js`, schema at
`ops/schemas/repo-governance-plan.schema.json`, tests in
`ops/test-compile-repo-governance.js`. Consumers migrate in G2–G5 of campaign
`dotgithub-governance-compiler-v1` (integration branch
`campaign/dotgithub-governance-compiler-v1`).

### Consequences

- Good, because consumers become thin adapters.
- Good, because one plan can be stored as transaction evidence.
- Good, because parity can be golden-tested.
- Bad, because the plan schema becomes a compatibility surface that needs
  version discipline.
- Neutral, because existing helpers become compiler internals rather than
  disappearing.

## Pros and Cons of the Options

### Option 1 — raw policy files as the API

- Good, because nothing new is introduced.
- Bad, because every consumer must reinterpret the files, which is the drift
  this decision exists to remove.

### Option 2 — per-capability helper APIs

- Bad, because consumers still assemble the effective answer themselves, and
  no single artifact describes a whole transaction.

## Links

- Invariants created: GOV-017, GOV-018, GOV-019, GOV-025, GOV-027, GOV-028,
  GOV-029 — see [`docs/INVARIANTS.md`](../INVARIANTS.md).
- Plan contract: [`docs/REPO_BIRTH_PROFILES.md`](../REPO_BIRTH_PROFILES.md#governance-plan-compiler).
