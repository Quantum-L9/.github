# ADR-011: ProductKind is defined by canonical consumption and deployment

Status: Accepted

## Decision
`ProductKind` is the primary architectural participation form of an L9 product. It is determined by the product's canonical consumption and deployment model, not by repository shape, package format, provider identity, semantic complexity, or the mere presence of a process.

Two ProductKinds are admitted in this foundation:

- `node`: canonical consumption is `remote_invocation`; canonical deployment is `independent_runtime`.
- `dependency`: canonical consumption is `local_composition`; canonical deployment is `consumer_bound_artifact`.

SDK is intentionally unresolved and is not admitted by this decision.

## Archetypes
Archetypes specialize a ProductKind without redefining it or acquiring domain semantic ownership. Node archetypes live in `node_archetypes.yaml`. Dependency archetypes live in the sibling `dependency_archetypes.yaml`.

## Consequences
A Node and Dependency may both own rich semantics, ports, adapters, policies, receipts, provider integrations, and complex internal architecture. Those properties do not classify the product. The canonical consumption/deployment boundary does.
