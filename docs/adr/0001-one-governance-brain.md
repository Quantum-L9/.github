# ADR-0001: One governance brain

## Status

Accepted

**Date:** 2026-09-25
**Deciders:** Human owner
**Related:** campaign `dotgithub-governance-compiler-v1` (integration branch `campaign/dotgithub-governance-compiler-v1`); [ADR-0002](./0002-versioned-governance-plan-compiler.md), [ADR-0003](./0003-immutable-authority-binding.md)

---

## Context and Problem Statement

Organization governance policy lives in one repository, but class-sensitive
behavior is interpreted in several workflows and scripts. Central file
ownership alone does not prevent semantic drift when each consumer recomputes
applicability for itself.

## Decision Drivers

- one durable owner per responsibility
- no shadow policy interpreters
- existing class semantics preserved
- maximum reuse of existing policy and helpers
- drift detectable by code search and contract tests

## Considered Options

1. Keep distributed interpreters and synchronize them with tests.
2. Move class policy into each operational consumer.
3. Keep `Quantum-L9/.github` as the single authority and compile one effective
   plan that every adapter consumes.

## Decision Outcome

**Chosen option:** "3 — single authority, one compiled plan", because it is the
only option that removes the second interpreter instead of policing it.

All organization governance policy interpretation stays in this repository and
is exposed through one canonical governance compiler. Operational workflows and
scripts execute compiled decisions; they do not create their own class-policy
semantics.

**Implementation:** compiler at `ops/compile-repo-governance.js`, schema at
`ops/schemas/repo-governance-plan.schema.json`, tests in
`ops/test-compile-repo-governance.js`. Consumers migrate in G2–G5 of campaign
`dotgithub-governance-compiler-v1` (integration branch
`campaign/dotgithub-governance-compiler-v1`).

### Consequences

- Good, because policy drift becomes structurally harder.
- Good, because one fix reaches every consumer once they have migrated.
- Good, because class-sensitive repair and birth-time behavior converge.
- Bad, because compiler correctness becomes critical infrastructure and needs
  strong tests and versioning.
- Neutral, because lower-level helpers remain useful, but their direct
  operational use is restricted.

## Pros and Cons of the Options

### Option 1 — distributed interpreters synchronized by tests

- Good, because it needs no consumer changes.
- Bad, because every interpreter is still a place semantics can diverge; tests
  only detect the divergence they were written for.

### Option 2 — class policy inside each consumer

- Bad, because it multiplies owners of the same decision.

## Links

- Invariants created: GOV-001, GOV-002, GOV-003, GOV-004, GOV-024, GOV-025 —
  see [`docs/INVARIANTS.md`](../INVARIANTS.md).
- Non-goal: this decision does not make `.github` an owner of CI execution or
  application correctness ([`docs/BOUNDARIES.md`](../BOUNDARIES.md)).
