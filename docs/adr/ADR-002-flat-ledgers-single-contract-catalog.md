# ADR-002: Flat canonical ledgers and one global contract catalog

Status: Accepted

## Decision
Canonical semantic concerns live as peer YAML ledgers under `semantics/`. Global cross-boundary contracts remain entries in the single `semantics/contracts.yaml` catalog. New semantic models reference contract IDs; they do not create hidden mini-contract systems.

## Rationale
The organism needs many semantic concerns but few authority surfaces. A flat catalog preserves discoverability, canonical ownership, projection, digest addressing, and dependency analysis without creating recipe folders or shadow law.

## Consequences
- `requirement_model.yaml`, `architecture_rules.yaml`, and related files define models, not alternate contract authorities.
- Contract references are by canonical ID and coordinates.
- If the contract catalog later becomes operationally unwieldy, physical sharding may be introduced only if canonical identity and single logical authority remain intact.
