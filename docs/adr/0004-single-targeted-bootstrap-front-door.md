# ADR-0004: Single targeted bootstrap front door

## Status

Accepted

**Date:** 2026-09-25
**Deciders:** Human owner
**Related:** campaign `dotgithub-governance-compiler-v1` (integration branch `campaign/dotgithub-governance-compiler-v1`); [ADR-0001](./0001-one-governance-brain.md), [ADR-0002](./0002-versioned-governance-plan-compiler.md), [ADR-0003](./0003-immutable-authority-binding.md)

---

## Context and Problem Statement

Targeted governance of one repository used to take two public calls: seed
files (`auto-seed-new-repo.yml` with `target_repo`, `make birth-seed`) and apply
remote state plus attest (`repo-birth-bootstrap.yml`, `make birth-bootstrap`).
Callers had to know the internal capability topology and order the calls, and
a partial run left a half-governed repository with no single result saying so.

## Decision Drivers

- one transaction, one terminal result
- one place to verify authority SHA and plan digest before mutation
- reuse the internal capability executors without making callers coordinate them
- remote read-back attestation after every applicable action

## Considered Options

1. Keep multiple public targeted calls and document the required order.
2. Add an external orchestrator.
3. Make `.github` expose one public targeted bootstrap workflow that applies
   every plan capability and attests them.

## Decision Outcome

**Chosen option:** "3 — one front door", because it is the only option that
verifies the plan once and reports one result for the whole transaction.

`repo-birth-bootstrap.yml` (`make birth`) receives the target, an exact
`authority_sha`, and an `expected_plan_digest`. It checks out that authority,
compiles the plan from the target's remote facts, refuses before any mutation
unless the recomputed digest matches, then materializes plan files as a seed PR,
applies labels and settings, reads the remote back, and attests. With
`dry_run` and no digest it only compiles and reports the digest — the first
half of the two-step call.

Materialization reuses the auto-seed executor (`ops/seed-plan-pr.js`) and its
seed branch, so `ops/seed-branch-safety.js` arbitrates between a birth and the
hourly sweep. `auto-seed-new-repo.yml` remains the org-wide repair sweep; it is
no longer a targeted entry point.

**Implementation:** `.github/workflows/repo-birth-bootstrap.yml`,
`ops/seed-plan-pr.js`, `Makefile` target `birth`; proofs in
`ops/test-birth-front-door.js` and `ops/test-one-governance-brain.js`.

### Consequences

- Good, because a birth either completes or refuses as a whole, with one summary
  naming the authority SHA and plan digest.
- Good, because internal capability executors can change without caller churn.
- Bad, because callers must run twice (plan, then apply with the digest) and
  carry the SHA and digest between runs.
- Bad, because existing callers that dispatch `repo_birth` without
  `authority_sha` and `expected_plan_digest` (Quantum-L9/l9-repo-template
  `make new-repo`) are refused until they are updated.

## Pros and Cons of the Options

### Option 1 — multiple documented calls

- Good, because no workflow changes.
- Bad, because ordering and partial failure stay the caller's problem.

### Option 2 — external orchestrator

- Bad, because it adds a second owner of governance orchestration outside this
  repository.

## Links

- Invariants: GOV-020, GOV-021 — see [`docs/INVARIANTS.md`](../INVARIANTS.md).
