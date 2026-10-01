# ADR-003: ProductTopology is the first-class L9 product contract

Status: Accepted

## Decision
Every L9 product is authored through `l9.product-topology/v1`. ProductTopology is the authoritative product contract once admitted. It uses one universal topology vocabulary for identity, purpose, semantic boundary, requirements, capabilities, consumption, deployment, contracts, architecture, interfaces, ports, adapters, relationships, bindings, providers, runtime, security, state, failures, receipts, observability, admission, lifecycle, conformance, distribution, provenance, and explicit Unknowns.

`NodeSpec` and other kind-specific specification inputs are not part of the canonical build path. Product kind and archetype specialize the shared topology without creating a second product-description language.

## Compiler boundary
The product owner declares semantic decisions that cannot be derived without inventing policy. The compiler may validate, resolve references, derive governed consequences, select admitted patterns and bindings, and synthesize lower-level realization artifacts. It MUST NOT invent product purpose, ownership, authority, ProductKind, semantic boundary, or missing meaning.

## Consequence
All L9 product compilation begins from ProductTopology. A kind-specific build language is forbidden when ProductKind and archetype projection can faithfully constrain the universal topology.
