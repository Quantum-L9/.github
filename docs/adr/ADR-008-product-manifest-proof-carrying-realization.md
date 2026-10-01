# ADR-008: ProductManifest is the proof-carrying resolved realization

Status: Accepted

## Decision
`l9.product-manifest/v1` is the derived artifact binding one exact ProductTopology to its resolved ProductKind, archetype, requirements, capabilities, architecture, ports, adapters, product relationships, technology/provider bindings, admission obligations, conformance obligations, compiler coordinates, provenance, and unresolved gaps.

Implementation lowering may consume only a ProductManifest that passes the resolved-manifest gate. ProductManifest remains derived evidence-bearing realization state and never becomes product or domain semantic authority.

## Currentness
Material upstream change to ProductTopology, ProductKind law, archetype law, governing contracts, required capabilities, bindings, or conformance makes the prior ProductManifest non-current unless an applicable compatibility contract proves continued applicability.
