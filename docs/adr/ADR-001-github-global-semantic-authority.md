# ADR-001: `.github` is the L9 global semantic authority

Status: Accepted

## Decision
`Quantum-L9/.github/semantics` is the canonical organization-level owner for global L9 vocabulary, invariants, cross-boundary contracts, capability semantics, resolution models, architecture rules, catalogs, schemas, profiles, authority rules, and semantic dependency law.

Domain repositories continue to own domain semantics. The Semantic Compiler consumes canonical semantics and transforms them. `l9-conformance` owns executable conformance semantics and evidence. Consumers may project or specialize global semantics but do not become their owners.

## Consequences
- Global meaning has one source.
- Domain semantics remain separately owned.
- Derived artifacts and implementation repositories cannot silently redefine global law.
- `.github` is a semantic/control/distribution plane, not the implementation of every L9 capability.
