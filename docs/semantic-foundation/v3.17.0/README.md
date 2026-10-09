# Semantic Foundation v3.17.0

Status: **CORRECTIVE SUCCESSOR CANDIDATE**

v3.17.0 repairs the semantic root of the Strategic Cognition / Strategic Plan family. The existing architecture correctly separated Goals, Targets, Hypotheses, Commitments, authority, metacognition, and external truth, but it never independently defined Strategy. Several current definitions therefore leaned on undefined `strategic direction` terminology.

## Bounded delta

- Defines Strategy once, non-circularly, in `semantics/strategic_cognition_model.yaml`.
- Grounds Strategic Cognition, Strategic Intent, Strategic Plan, and Plan Keeper permissions in that root.
- Defines Strategic Authority explicitly in `semantics/authority_model.yaml` and makes Plan Keeper authority resolve to it.
- Makes `semantics/strategic_plan_model.yaml` reuse Strategy with `owned_here: false` and grounds the existing four primitives, four local relation meanings, and Affected Strategic Closure without changing their identities.
- Adds root vocabulary terms `strategy`, `strategic_intent`, and `strategic_authority`; removes the undefined `strategic_direction` classification from current strategy terms.
- Adds ADR-016 and RC-024 Strategy semantic-root closure.

## Preserved architecture

Exactly four Plan-owned primitives remain: Strategic Goal, Strategic Target, Strategic Hypothesis, Strategic Commitment. Exactly five relations remain: `advances`, `enables`, `depends_on`, `conflicts_with`, `supersedes`. Objective remains the existing optimization criterion. Current Meta View remains derived and non-authoritative. Reality may trigger reconsideration but cannot directly mutate the Strategic Plan. Metacognition remains advisory.

## Non-goals

No new invariant, contract, canonical ledger, artifact class, primitive, relation, schema, runtime, graph representation, actor binding, confidence model, temporal model, or Graphiti integration is admitted.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.16.0/`, preserved unchanged.
