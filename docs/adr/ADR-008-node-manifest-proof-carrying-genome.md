# ADR-008: NodeManifest is the proof-carrying semantic genome of a build

Status: Accepted

## Decision
`l9.node-manifest/v1` is the derived artifact that binds the exact semantic closure used to build a node: NodeSpec, invariants, contracts, requirements, capabilities, architecture, ports, technology, bindings, conformance obligations, compiler profile, provenance, and unresolved gaps.

Implementation lowering may consume only a NodeManifest that passes the resolved-manifest gate. The manifest remains derived and does not become the domain semantic owner. Material upstream changes make the prior manifest non-current unless compatibility explicitly preserves applicability.
