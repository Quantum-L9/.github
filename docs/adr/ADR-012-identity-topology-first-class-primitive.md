# ADR-012 — Identity topology is a first-class product primitive

**Status:** Accepted for semantic-foundation v3.4.0

## Decision

Identity becomes a first-class ProductTopology primitive. Product, release, runtime, Constellation, actor, and surface identity are distinct semantic dimensions. GovernanceProfile, adapter identity, and provider identity are not identity substitutes.

Dynamic identity is resolved once from bounded runtime evidence under `l9.contract/identity-resolution@1` and propagated as `l9.identity-assertion/v1`. Downstream consumers validate or challenge the assertion; they do not independently re-derive identity from the same evidence.

Consequential memory authorship and receipts bind ActorIdentity when required. Unknown or ambiguous ActorIdentity fails closed for consequential authorship rather than being guessed from provider, adapter, surface, or governance-profile strings.

## Consequence

Cursor-Governance and memory adapters may project this law downstream, but this foundation does not mutate those repositories. Their remediation becomes a consumer convergence task against the upstream identity contracts.
