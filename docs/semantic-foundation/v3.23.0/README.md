# Semantic Foundation v3.23.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.23.0 gives the coding-agent execution projection the mechanical closure v3.22.0 gave the architecture-intelligence projection: a registered payload schema and a criterion for every `forbidden` category, so the producer can receipt it `pass` and the coding agent can bind it without weakening its gate.

## Bounded delta

- `semantics/coding_agent_execution_projection.schema.yaml` (`l9.schema/coding-agent-execution-projection@1`) defines `l9.projection.coding-agent-execution/v1` and is registered under `requires.artifact_schemas`.
- `forbidden_constraints.definitions` gains the five categories `l9.projection/coding-agent-execution@1` declares: one `source_authority` and four `payload_excludes` over declared source classes, in the existing `l9.forbidden-constraint` v1 language. PROJECTION-016 is unchanged.
- ADR-020.
- `l9.projection/coding-agent-execution@1` is byte-for-byte as admitted at v3.20.0; RC-028 keeps pinning it. Every other profile, contract, schema, and criterion is unchanged.

## Evidence

With this tree and the producer at `Quantum-L9/l9-semantic-compiler-engine` PR #13 (`7e516b6d`, the forbidden-criterion engine), `project` emits three artifacts for the profile, one per source, each receipted `operation: projection`, `result: pass`, `unresolved_criteria: []`, with `payload_schema` and all five `declared_constraint:forbidden:*` criteria `pass`. The same producer at `main` (`37e6758b`) receipts the same tree `unknown`, because it evaluates no forbidden criterion; the closure is therefore proven only with the forbidden-criterion engine.

## Outstanding Unknowns and findings

- `obligation_not_admitted_in_a_selected_source` through `source_authority` restates a property the canonical loader already enforces and cannot fail on its own (the finding ADR-019 recorded for `unrelated_domain_payloads`).
- The port catalog holds no records at this revision, so its exclusion in `skill_command_or_routing_semantics` is proven by compiler tests only; the packet catalog (seven packet records) and the `invocability_contract` exclusion are live data.
- No RC-031 validator check exists yet for the registration and the five criteria; RC-028 and SC-008 are the checks this candidate relies on.
- The `semantic_digest` canonicalization is still not declared in a ledger.

## Authority

`Quantum-L9/.github` owns the profile, the schema, and the criteria. The compiler (`l9-semantic-compiler`) realizes them, and consumers verify. This candidate does not admit itself.
