# ADR-004: Requirements and resolvers share one formal algebra

Status: Accepted

## Decision
All product-compilation resolution uses typed requirements and the common result domain defined by `requirement_model.yaml` and `resolution_model.yaml`. Hard requirements are non-compensable. Soft objectives only rank already feasible candidates.

Canonical resolution states are `resolved`, `unresolved`, `incompatible`, `unsat`, and `ambiguous`. Resolver-specific prose MUST NOT redefine these meanings.

## Consequences
Capability, architecture, port, technology, and conformance resolution can compose mechanically. UNKNOWN or ambiguity does not disappear because another stage prefers progress.
