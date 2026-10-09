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
- ADR-012: Identity as a first-class topology primitive
- ADR-013: Global actor and surface identity registries
- ADR-014: Strategic Cognition in the Reasoning Plane
- ADR-015: Strategic Plan semantic model
- ADR-016: Strategy semantic root closure
- ADR-017: Federated authority graphs and Strategic Plan Graph representation

ADR-001 through ADR-017 are the global semantic decisions. They live in this
directory because this repository owns that law.

## Domain decisions

[`template.md`](./template.md) is for a decision a domain repository makes
about its own capability. Copy it into that repository's `docs/adr/` and
number it in that repository's sequence. A domain record sits next to the
code it governs. It does not replace a ledger in `semantics/`.

When the same decision would otherwise be remade in every product, it belongs
here as global law ([ADR-010](./ADR-010-ownership-boundaries-no-recipes.md)),
registered in `semantics/canonical_sources.yaml`.

Write a domain ADR when a decision:

- Changes a public contract that repository owns
- Introduces, replaces, or retires a dependency, provider, or kernel
- Establishes a convention other teams are expected to follow inside that boundary
- Reverses or supersedes a prior decision in that repository

Skip it for a routine bug fix, a dependency bump, or anything a single revert
undoes.

1. Copy [`template.md`](./template.md) to `docs/adr/NNNN-short-title.md` in the
   repository that owns the decision.
2. Fill in every section. Leave `Considered Options` even when only one option
   was viable, and record why the others were rejected.
3. Set `Status: Proposed` and open a pull request. Acceptance follows discussion
   of the tradeoffs.
4. When a later ADR reverses an earlier one, keep the old file. Set its status
   to `Superseded by ADR-NNNN` and link both directions.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
