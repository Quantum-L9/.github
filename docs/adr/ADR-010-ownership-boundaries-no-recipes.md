# ADR-010: Formalize reusable law, not node recipes

Status: Accepted

## Decision
`.github` will add canonical ledgers only when they remove a recurring semantic decision across future nodes without stealing a decision from the domain semantic owner. It will not become a catalog of database recipes, framework recipes, per-node blueprints, or provider-specific architecture templates.

## Ownership matrix
- `.github`: global law, models, catalogs, schemas, profiles, resolution semantics.
- Domain repo: domain invariants, domain contracts, domain ports/capabilities.
- Semantic Compiler: deterministic transformation and candidate synthesis within canonical profiles.
- `l9-conformance`: executable proof system.
- Providers/technologies: realization facts, never semantic ownership by implementation alone.

The design target is a small formal kernel with large compositional leverage.
