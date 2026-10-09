# Semantic Foundation v3.18.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.18.0 lays the graph foundation of the L9 operating model. It admits one global federation pattern for independently owned authority graphs and the minimum provider-neutral Strategic Plan Graph representation that ADR-015 deliberately deferred.

## Admitted delta

- Adds `l9.pattern/federated-authority-graphs@1` to `semantics/architecture_patterns.yaml`.
- Adds canonical `semantics/strategic_plan_graph.schema.yaml` as `l9.schema/strategic-plan-graph@1`.
- Registers the schema in `semantics/canonical_sources.yaml`.
- Makes the generic compiler consume the schema as a semantic catalog, not as compiler-output authority.
- Adds ADR-017, which formalizes the graph-family ownership boundaries, downstream-to-upstream reference direction, derived WHY/HOW composition, Strategic Plan Graph v1, provider neutrality, and the bounded Lane B delegation audit handoff.
- Adds RC-025 with hostile closure cases for ontology inflation, relation inflation, authority drift, world-graph expansion, loss of hypothesis attribution, cross-kind supersession, ownership absorption, Unknown coercion, composition authority inflation, reference-direction reversal, compiler misclassification, and registry loss.

## Strategic Plan Graph v1

Exactly four local Plan-owned node kinds remain:

- `strategic_goal`
- `strategic_target`
- `strategic_hypothesis`
- `strategic_commitment`

Exactly five strategic relations remain:

- `advances`
- `enables`
- `depends_on`
- `conflicts_with`
- `supersedes`

Strategy is the integrated meaning of the graph, not a fifth node kind. Strategic Intent and Objective remain referenced upstream concepts. Capability, Constraint, Evidence, Execution, Work, Delegation, and reality objects remain externally owned.

## Federation law

Authoritative domains remain separate. Cross-domain realization references point downstream → upstream. Reverse traversal is derived. `l9.compose/consumer-view@1` may compose projections into a management/reasoning view, but that view has zero semantic authority and may not mutate its sources.

## Non-goals

v3.18.0 does not admit Delegation Graph schema, WorkState Graph schema, universal execution semantics, a universal Reality graph, Graphiti/Neo4j/storage bindings, Plan Keeper runtime, Metacognitive Reasoner runtime, planning confidence/probability/horizon/schedule/budget/progress fields, or a new management-graph product.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.17.0/`, preserved unchanged.
