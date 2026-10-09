# Release Validation v3.18.0

Candidate status: **additive successor candidate**.

## Objective

Close the representation gap deliberately left by ADR-015 without allowing Strategic Plan representation to become a universal world graph, project-management schema, runtime implementation, or semantic mega-authority.

## RC-025 — Federated authority graphs + Strategic Plan Graph closure

RC-025 must prove:

1. `l9.pattern/federated-authority-graphs@1` exists exactly once.
2. The pattern remains a projection/composition architecture, not a new authority class.
3. Authoritative cross-domain reference direction is downstream → upstream.
4. Reverse adjacency is derived.
5. Cross-graph composition reuses `l9.compose/consumer-view@1` and remains `derived`.
6. Mega-graph authority, ownership transfer, upstream consumer inventories, source mutation, provider ownership, and silent Unknown coercion are explicitly forbidden.
7. `l9.schema/strategic-plan-graph@1` is canonical and owned by `Quantum-L9/.github` for the declared schema scope.
8. Top-level required fields remain the minimum Plan/revision/authority/scope/intent/objective/nodes/relations/provenance/digest closure.
9. Exactly four local Plan-owned node kinds are admitted.
10. Strategy itself is not a local node kind.
11. Exactly five strategic relation kinds are admitted.
12. Every strategic relation must touch at least one local Plan node.
13. `enables` requires attribution to a local Strategic Hypothesis.
14. `supersedes` preserves same-kind Plan lineage and may address a prior revision.
15. External references remain externally owned and unresolved references preserve `unknown`.
16. Plan revision identity, predecessor lineage, historical immutability, and graph digest binding remain explicit.
17. Deferred fields such as confidence, probability, horizon, schedule, budget, priority, execution state, storage IDs, and Affected Strategic Closure remain absent.
18. The schema is registered exactly once in `canonical_sources.yaml`.
19. The generic compiler consumes it as a semantic catalog and does not misclassify it as a compiler-output schema.

## Hostile negative cases

RC-025 carries **16** isolated negative cases. They deliberately attempt to:

- add a fifth local primitive;
- add a sixth strategic relation;
- turn Strategy into a local node;
- make Strategic Authority optional;
- add confidence to Plan content;
- serialize Affected Strategic Closure;
- allow relations with no local Plan endpoint;
- remove Hypothesis attribution from `enables`;
- attribute `enables` to the wrong primitive;
- allow cross-kind supersession;
- absorb external ownership;
- coerce Unknown to resolved;
- promote the management view to canonical authority;
- reverse the authoritative reference direction;
- misclassify the Plan Graph schema as compiler output;
- remove canonical-source registration.

Every case must fail at its intended RC-025 field. A crash, skip, default success, or unrelated failure is not a pass.

## Preserved closure

RC-001 through RC-024 remain in force. In particular:

- Strategy remains independently grounded by RC-024.
- Strategic Plan semantic content remains the four primitives, five relations, and Affected Strategic Closure governed by RC-018.
- `strategic_plan_model.yaml` remains semantics-only and is not widened with representation fields.
- Current Meta View remains derived and non-authoritative.
- Reality change may trigger reconsideration but never directly mutates the Strategic Plan.
- Plan Keeper / Metacognitive Reasoner authority separation remains unchanged.

## Release integrity

`HASHES.sha256` must bind the final canonical semantic bytes, all 17 ADRs plus the ADR index, and this release record. Earlier release directories remain immutable.

## Admission state

v3.18.0 is a candidate and does not self-admit. Passing validation produces evidence only. Applicable authority must admit the exact candidate bytes.
