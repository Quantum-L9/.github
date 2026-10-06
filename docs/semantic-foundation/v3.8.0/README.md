# Semantic Foundation v3.8.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor admits the global semantics of L9 Strategic Cognition: a canonical language and authority boundary for strategic cognition, before strategic cognition has a data model or a runtime.

## Bounded delta

- Adds one canonical ledger, `semantics/strategic_cognition_model.yaml` (`l9.strategic-cognition-model/global@1`), defining Strategic Cognition, the Strategic Plan, the Current Meta View, the Plan Keeper, and the Strategic Plan Metacognitive Reasoner.
- Adds one constitutional invariant, `L9-STRATEGY-001`: Plan Keeper owns the Strategic Plan; the Strategic Plan Metacognitive Reasoner owns analysis of the reasoning that produces it, may teach the Plan Keeper, and may never modify, supersede, or become strategic authority.
- Makes that separation machine-resolvable in `authority_model.yaml` `strategic_cognition_authority`.
- Models the Current Meta View through existing projection and composition law (`composed_projection`, `l9.schema/composed-projection@1`): derived, disposable, non-authoritative, provenance-preserving, invalidatable.
- Adds ADR-014 and RC-016 Strategic Cognition closure with seven fail-closed negative cases.

## Non-goals

v3.8.0 adds no Strategic Plan Graph schema, node or edge fields, hypergraph representation, Strategic Plan values or horizons, Plan Graph storage, APIs, lifecycle or invalidation semantics, reasoning-plane runtime, Plan Keeper or Reasoner implementation, prompts, agent definitions, actor identities, model or provider selection, Graphiti integration, memory schema change, Gate transport or registration change, capability admission or global capability identity, projection profile or strategic selector, artifact class, receipt class, contract, incentive or promotion scoring, deletion policy, autonomy scoring, cognition allocation, learned orchestration, machine learning, training, runtime observability, or execution workflow.

## Authority

`Quantum-L9/.github` owns the global meaning of Strategic Cognition. Runtime cognition belongs to the Reasoning Plane outside this repository. The Semantic Compiler remains independent of the Reasoning Plane and does not own Strategic Cognition.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.7.0/`. The predecessor release record remains immutable.
