# ADR-003: NodeSpec is the minimal declarative node-birth interface

Status: Accepted

## Decision
A new node begins from `l9.node-spec/v1`: node identity/archetype, purpose, project invariants, desired capabilities, and technology intent/constraints. Authors declare genuine semantic decisions; L9 derives consequences already determined by canonical law.

## Boundary
Authors MUST declare semantic intent that cannot be inferred without inventing policy. The compiler MUST derive inherited contracts, requirement closure, capability dependencies, architecture obligations, ports, compatible bindings, conformance requirements, and implementation constraints where canonical semantics are sufficient.

The compiler MUST NOT invent project invariants, authority, or missing semantic meaning.
