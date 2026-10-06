# ADR-015 — Strategic Plan Semantic Model

**Status:** Accepted for semantic-foundation v3.10.0

## Decision

`Quantum-L9/.github/semantics` owns the global meaning of Strategic Plan content in one canonical ledger, `semantics/strategic_plan_model.yaml` (`l9.strategic-plan-model/global@1`). The Strategic Plan is L9's authoritative maintained theory of which future conditions it seeks, which concrete conditions indicate progress toward them, why selected paths are believed capable of producing them, and which paths it has actually chosen. It owns strategy, not reality.

The ledger admits exactly four Plan-owned primitives — Strategic Goal, Strategic Target, Strategic Hypothesis, and Strategic Commitment — five strategic relations — `advances`, `enables`, `depends_on`, `conflicts_with`, and `supersedes` — and one strategic reasoning concept, Affected Strategic Closure. A change in authoritative reality may require reconsideration of dependent strategic claims, but never directly modifies or invalidates the Strategic Plan; Affected Strategic Closure identifies what requires reconsideration and neither decides strategy nor modifies the Plan.

A new canonical owner is necessary. Without it every future Plan Keeper, schema, or runtime would independently decide what a Goal, Target, Hypothesis, and Commitment are, which relations exist, whether causal belief equals truth, and whether reality may directly change strategy (ADR-010). No existing ledger owns that complete question without contamination:

- `strategic_cognition_model.yaml` states that it "does not define Strategic Plan content or structure" and declares `content_defined_here: false` and `structure_defined_here: false`. Absorbing the Plan's anatomy would contradict its admitted boundary.
- `requirement_model.yaml` requires every entry to carry `hardness` and `satisfaction_semantics`. A Strategic Goal is not a satisfaction obligation and a Strategic Hypothesis has no hardness; placing them there would conflate what must be satisfied with what L9 seeks and why it believes a path will work.
- `semantic_dependency_model.yaml` marks transitive dependents stale when a source changes. Placing strategy there would make a change in reality automatically invalidate strategy, collapsing dependency impact into strategic judgment.
- `vocabulary.yaml` defines terms and defers their models; `authority_model.yaml` resolves who owns the Plan, not what it means; `artifact_model.yaml` classifies artifacts; `lifecycle.yaml` owns revision; `contracts.yaml` operationalizes invariants; `product_topology.schema.yaml` describes products, not organizational strategy.

The ledger reuses existing law instead of restating it. It anchors once to the existing Strategic Plan concept (`strategic_cognition_model.yaml#concepts.strategic_plan`) and its authority resolution (`authority_model.yaml#strategic_cognition_authority`), so Plan Keeper ownership is inherited, not duplicated per primitive. It references canonical `objective` and Strategic Intent with `owned_here: false`. Its `supersedes` relation is `lifecycle.yaml#lifecycle_relations.supersedes`. Its boundaries are carried by existing invariants — `L9-STRATEGY-001`, `L9-AUTH-001`, `L9-OWNER-001`, `L9-SEM-001`, `L9-PROMOTION-001`, `L9-PROJECTION-001`, and `L9-UNKNOWN-001` — so no invariant is added.

`strategic_cognition_model.yaml` and `authority_model.yaml` are unchanged. No Strategic Cognition statement becomes unresolvable without a pointer to the new model, and Plan ownership already resolves through `strategic_plan_owner: plan_keeper`. `generic_compiler_manifest.yaml` classifies the ledger once as a semantic catalog; its existing `does_not_own: strategic_cognition` already covers the Strategic Plan as a concept of Strategic Cognition, so no further entry is added.

## Rejected alternatives

- Absorb the Plan into `strategic_cognition_model.yaml`. It contradicts that ledger's admitted content and structure disclaimers.
- Absorb the Plan into `requirement_model.yaml`, or add `strategic_objective`. Canonical `objective` already means an optimization criterion evaluated among feasible alternatives; a strategic duplicate would redefine it.
- Absorb the Plan into `semantic_dependency_model.yaml`. Automatic staleness would let reality change strategy without Plan Keeper reasoning.
- Absorb the Plan into `vocabulary.yaml`, `authority_model.yaml`, `artifact_model.yaml`, `lifecycle.yaml`, `contracts.yaml`, or `product_topology.schema.yaml`. Each would broaden a ledger beyond its admitted responsibility.
- Actual State, Capability, or Constraint as Plan primitives. Each fact belongs to the authority that owns it; the Plan may reference it, depend on it, or hold a belief about it.
- Flywheel or bottleneck as primitives. Both are structure discovered by reasoning over the Plan, not object classes.
- Mission, Campaign, or Task as primitives. They belong to delegation and execution.
- The relations `blocks`, `substitutes_for`, `invalidates`, `contradicts`, `supports`, `causes`, `realizes`, `measures`, `pursues`, `decomposes_into`, and `implements`. None proved irreducible against the admitted four primitives and five relations.
- A hypergraph requirement. A single Strategic Hypothesis can express a compound causal claim over several externally owned references.
- A relation endpoint type matrix, a Strategic Plan schema, or fields for confidence, horizon, dates, or identifiers. Representation follows semantic convergence in a later campaign.
- Separate ledgers per primitive or for causal relations. One Strategic Plan owner is sufficient.

## Consequence

`scripts/validate-semantics.py` RC-018 proves the ledger's single declaration, canonical ownership, registration, and classification; exactly the four primitives, each with a definition and characteristic question; exactly the five relations, with `supersedes` reused from lifecycle; the relation law that relations transfer no ownership or authority and that material causal `enables` claims remain attributable to a Strategic Hypothesis; Affected Strategic Closure as the single reasoning concept, unable to decide, modify, invalidate, or automatically mark strategy stale; `objective` and Strategic Intent reused without ownership; anchoring to the existing Strategic Plan concept and Plan Keeper authority with Strategic Cognition's content and structure disclaimers intact; the absence of representation keys; and the five vocabulary terms. Every criterion is evaluated on every run, so an absent section fails rather than skips (`l9.contract/validation-and-correctness@1`). A bounded negative-case batch proves each boundary fails closed for its intended reason.
