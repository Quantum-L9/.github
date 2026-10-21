# Semantic Foundation v3.25.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.25.0 admits a candidate projection for a revision-bound pull-request audit consumer, with the mechanical closure v3.22.0 gave the architecture-intelligence projection and v3.23.0 gave the coding-agent execution projection, on the producer-emitted projection contract v3.24.0 declares: a consumer profile, a source-namespaced composition, two registered payload schemas, a criterion for every `forbidden` category, and a validator check that pins all four artifacts.

## Bounded delta

- `semantics/projection_profiles.yaml` gains `l9.projection/pr-audit@1` (`class: consumer`, `consumer: l9-pr-audit`). It selects, by exact id or whole canonical section, from thirteen registered ledgers: 24 global invariants, 16 global contracts closed over their `source_invariants`, 7 `authority_model` sections, the artifact model's authority classes and derivation rules, 1 architecture rule, 6 architecture patterns, the capability state dimensions and rules, the conformance model's global rules and requirement shape, the receipt kernel with the validation and admission families, the lifecycle rules, state semantics and published-artifact lifecycle, the invalidation rules, the validation result domain, and 27 vocabulary terms. Its `forbidden` list is exactly the five categories ADR-020 gave criteria. `forbidden_constraints.definitions` is unchanged.
- `semantics/composition_profiles.yaml` gains `l9.compose/pr-audit@1`, composing the profile under `source_class_namespace` placement with exact source coverage.
- `semantics/pr_audit_projection.schema.yaml` (`l9.schema/pr-audit-projection@1`) defines `l9.projection.pr-audit/v1`; `semantics/pr_audit_composition.schema.yaml` (`l9.schema/pr-audit-composition@1`) defines `l9.composed-projection.pr-audit/v1`. Both are registered under `requires.artifact_schemas`.
- `scripts/validate-semantics.py` gains RC-032, pinning the profile, the composition profile, and both schemas by canonical-JSON digest, with 36 negative cases that fail closed.
- ADR-022.
- Every previously admitted profile, contract, schema, criterion, and the v3.24.0 `binding_conventions` are unchanged. RC-028 and RC-030 keep pinning their profiles.

## Evidence

With the semantic bytes of this candidate and the producer at `Quantum-L9/l9-semantic-compiler-engine` `8bbd882f6a84c55449b9706c39a62e98eec1057b`, `projection-coordinates` resolves the profile at digest `sha256:f38e47275f08cfe0d14af80d470a7e90af645d9e4612860062c16cbc57812941` with thirteen source pins; `project` emits thirteen `l9.projection-artifact/v1` artifacts, each receipted `operation: projection`, `result: pass`, `unresolved_criteria: []`, with `payload_schema` resolving to `l9.schema/pr-audit-projection@1` and all five `declared_constraint:forbidden:*` criteria `pass`; `compose` emits one `l9.composed-projection/v1` artifact under `l9.compose/pr-audit@1` receipted `operation: composition`, `result: pass`, `unresolved_criteria: []`, composition digest `sha256:6731ada90b400b1d311857809ecd86539852454319e3734fd1e7b219d1354591`. The run was repeated against the candidate commit that carries the v3.24.0 `binding_conventions` (`02e4556fb721b94bee6266b23776dbd0c0851e44`) with identical results and digests.

## Outstanding Unknowns and findings

- `obligation_not_admitted_in_a_selected_source` through `source_authority` restates a property the canonical loader already enforces and cannot fail on its own (the finding ADR-019 and ADR-020 recorded).
- The projection schema types `global_rules` as a bare object because three selected ledgers declare a section of that name and one artifact carries one source; the composed schema pins each one's keys under its namespace, and selection equivalence proves the per-source key set.
- The RC-031 check that v3.23.0 anticipated for the coding-agent schema registration and criteria remains unwritten; v3.25.0 numbers its own check RC-032 so that number stays free for it.
- The v3.24.0 findings on unkeyed producer attestation and the undefined form of the admission decision record are unchanged.

## Authority

`Quantum-L9/.github` owns the profile, the composition, the schemas, and the criteria. The compiler (`l9-semantic-compiler`) realizes them, consumers verify, and replay attests. This candidate does not admit itself and grants the consumer no mutation, publication, merge, admission, or execution authority.
