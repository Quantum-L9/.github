# Semantic Foundation v3.22.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.22.0 gives the L9 Global Architect a source-bound architecture-intelligence projection and a composition that keeps every source whole. It also gives a profile's `forbidden` categories mechanical criteria.

## Bounded delta

- `l9.projection/architecture-intelligence@1`: 24 sources, a superset of the observer under PROJECTION-014. The observer is unchanged and stays resolvable by its exact identity.
- `l9.compose/architecture-intelligence@1` under the new `source_class_namespace` placement: exact coverage, duplicate components conflict, and cross-source identity-bearing records must be equivalent. Nothing is merged across sources.
- Two payload schemas: one per source projection, and one for the composed view with exactly one namespace per declared source class.
- `forbidden_constraints` with `payload_excludes` and `source_authority`; PROJECTION-016.
- ADR-019 and RC-030.

## Outstanding Unknowns and findings

- `unrelated_domain_payloads` is not independently restrictive. `source_authority` duplicates the loader's ownership check. A criterion tied to the consumer's purpose needs a canonical domain classification of sources, which is a new primitive, so it is escalated.
- `provider_implementation_details` has no live canonical matches: all four bindings are `target` class.
- The `semantic_digest` canonicalization is still not declared in a ledger. Producer and validator pins use canonical JSON (sorted keys, compact separators, UTF-8).

## Authority

`Quantum-L9/.github` owns the profiles, the contract, the schemas and the criteria. The compiler (`l9-semantic-compiler`) realizes them, and consumers verify. This candidate does not admit itself.
