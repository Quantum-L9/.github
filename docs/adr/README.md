# L9 `.github` Product-Compilation Architecture ADR Pack

Status: **REPLACEMENT CANDIDATE / RELEASE-READY**

This ADR pack formalizes how `Quantum-L9/.github` acts as the organization-level semantic authority for product topology, product compilation, and shared architecture semantics. It governs canonical meaning and compiler inputs, not product runtime implementation.

## North-star equation

```text
ProductTopology
    -> ProductKind + Archetype Resolution
    -> Requirement Closure
    -> Semantic Resolution
    -> Contracts / Laws / Conformance
    -> Architecture / Ports / Adapters / Relationships
    -> Technology / Provider Bindings
    -> ProductManifest
    -> Implementation IR
    -> Target Artifacts
```

## ADRs

- ADR-001: `.github` as the L9 global semantic authority
- ADR-002: One flat canonical semantic surface and one global contract catalog
- ADR-003: ProductTopology as the first-class product contract
- ADR-004: Requirement and resolution algebra
- ADR-005: Capability -> architecture -> port semantic resolution
- ADR-006: Technology binding after semantic resolution
- ADR-007: Conformance requirements and independent correctness
- ADR-008: ProductManifest as proof-carrying resolved realization
- ADR-009: Contract wiring, projections, compilation profiles, and invalidation
- ADR-010: Ownership boundaries and anti-recipe constraint
- ADR-011: ProductKind from canonical consumption and deployment

- `ADR-012-identity-topology-first-class-primitive.md` — identity dimensions, canonical resolution, typed assertions, and governance-profile separation.

---

# Architecture Decision Records (ADRs)

This directory holds the org-wide ADR template. ADRs record significant,
hard-to-reverse technical or architectural decisions — not routine changes.

## When to write an ADR

Write one when a decision:

- Changes a public contract (kernel API, CLI, schema, workflow interface)
- Introduces, replaces, or retires a dependency, provider, or kernel
- Establishes a convention other repos/teams are expected to follow
- Reverses or supersedes a prior decision

Skip it for routine bug fixes, dependency bumps, or anything reversible with a
single PR revert.

## How to use this template

1. Copy [`template.md`](./template.md) into **your repository's own**
   `docs/adr/` directory (this `.github` repo only hosts the template; ADRs
   themselves are recorded per-repo, next to the code they govern).
2. Name the file `docs/adr/NNNN-short-title.md`, using the next sequential
   4-digit number for that repo.
3. Fill in every section. Leave `Considered Options` even if only one option
   was viable — record *why* alternatives were rejected.
4. Set `Status: Proposed` and open a PR. Reviewers should not approve a
   status change to `Accepted` without discussion of the tradeoffs section.
5. If a later ADR reverses this one, do not delete the old file — set its
   status to `Superseded by ADR-NNNN` and link both directions.

## Relationship to CANONICAL_LAW.md

ADRs are decision *history* (why we chose X over Y, and when). They do not
replace or override [`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md),
which is the current, binding policy source of truth. If an ADR's outcome
changes a rule in `CANONICAL_LAW.md`, that document must be updated in the
same PR — the ADR records the reasoning, `CANONICAL_LAW.md` records the rule.
