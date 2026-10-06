# ADR-014 — Strategic Cognition in the Reasoning Plane

**Status:** Accepted for semantic-foundation v3.8.0

## Decision

`Quantum-L9/.github/semantics` owns the global meaning of Strategic Cognition in one canonical ledger, `semantics/strategic_cognition_model.yaml` (`l9.strategic-cognition-model/global@1`). Without it every future strategic-reasoning consumer would independently decide what Strategic Cognition, the Current Meta View, the Plan Keeper, and the Strategic Plan Metacognitive Reasoner mean (ADR-010). No existing ledger owns that complete question: vocabulary defines terms, invariants state constitutional law, `authority_model.yaml` resolves authority, and `artifact_model.yaml` and the projection/composition schemas own view mechanics, but none of them defines the reasoning concern and its roles without being contaminated by it.

Runtime cognition belongs outside `.github`, in the Reasoning Plane. This repository defines the semantics only; it defines no Plan Keeper or Reasoner runtime, prompts, model or provider selection, actor binding, memory behavior, or Strategic Plan content or structure.

The Plan Keeper and the Strategic Plan Metacognitive Reasoner are authority-separated. One constitutional invariant, `L9-STRATEGY-001`, states the separation: Plan Keeper owns the Strategic Plan. Strategic Plan Metacognitive Reasoner owns analysis of the reasoning processes that produce the Strategic Plan. The latter may teach the former but may never modify, supersede, or become strategic authority. `authority_model.yaml` `strategic_cognition_authority` makes the separation machine-resolvable.

Strategic Plan Metacognition is advisory to strategic authority. Its subject is the reasoning that produces and revises the Strategic Plan, not L9 reasoning in general. Its lessons are consumed by the Plan Keeper; they carry no authority and do not become strategic decisions by being emitted, repeated, or validated (L9-PROMOTION-001).

The Semantic Compiler remains independent of Reasoning Plane cognition (`vocabulary.yaml` `stage_rules.reasoning_plane_rule`). The ledger is a semantic catalog the compiler may read; `generic_compiler_manifest.yaml` lists `strategic_cognition` under `does_not_own`.

The Current Meta View reuses existing projection and composition law. It is a `composed_projection` of `projection_artifact` components under `l9.schema/composed-projection@1`: derived, disposable, non-authoritative, provenance-preserving, and invalidated when source truth changes. No artifact class is added and projection is not redefined (L9-PROJECTION-001, L9-DERIVED-001).

Strategic Cognition semantics make no realization component the owner of strategy. Graphiti, a model provider, the Semantic Compiler, or any other component that stores, computes, or transports strategic reasoning does not thereby own the Strategic Plan or its semantics (L9-OWNER-001, L9-SEM-001). The Plan Keeper and the Reasoner are semantic roles, not ActorIdentities; reasoning capability confers no strategic authority (L9-AUTH-002).

## Rejected alternatives

- A new top-level `.github/cognition/` authority plane. It would be a second semantic authority beside `semantics/` (ADR-001, ADR-002).
- Semantic Compiler ownership of Strategic Cognition. It contradicts the existing Reasoning Plane independence rule and the compiler's `does_not_own: global_semantic_law`.
- The Strategic Plan Metacognitive Reasoner as strategic authority. Analysis of planning would become planning, collapsing the separation the invariant exists to preserve.
- Graphiti as Strategic Plan semantic authority. Storage or memory realization does not confer semantic ownership.
- A Strategic Plan Graph schema in this release. Constitutional meaning and the authority boundary come before a data model.
- Runtime cognition in this release. Runtime belongs to the Reasoning Plane, outside `.github`, and follows the semantics.

## Consequence

`scripts/validate-semantics.py` RC-016 proves the ledger's single declaration, canonical ownership, registration, and classification; the single `L9-STRATEGY-001` invariant; Plan Keeper ownership of the Strategic Plan; Reasoner ownership of Strategic Plan reasoning analysis and its denial of mutation, supersession, and strategic authority; the Current Meta View as a non-authoritative reuse of existing projection/composition law; that Plan Keeper acquires no truth-source ownership; that the Semantic Compiler does not own Strategic Cognition; and that the Reasoning Plane separation is intact. A bounded negative-case batch proves each boundary fails closed for its intended reason.
