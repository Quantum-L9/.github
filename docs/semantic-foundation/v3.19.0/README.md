# Semantic Foundation v3.19.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.19.0 freezes the cognitive interface layer around the Strategic Plan Graph so Plan Keeper and Strategic Plan Metacognitive Reasoner runtimes can be implemented without inventing local packet shapes or collapsing reasoning into authoritative Strategy.

## Admitted delta

- Adds canonical `semantics/affected_strategic_closure.schema.yaml` as `l9.schema/affected-strategic-closure@1`.
- Adds canonical `semantics/strategic_planning_episode.schema.yaml` as `l9.schema/strategic-planning-episode@1`.
- Adds canonical `semantics/strategic_plan_revision_candidate.schema.yaml` as `l9.schema/strategic-plan-revision-candidate@1`.
- Adds canonical `semantics/strategic_plan_metacognitive_analysis.schema.yaml` as `l9.schema/strategic-plan-metacognitive-analysis@1`.
- Adds the minimum semantic anchors for those artifacts to the existing Strategic Cognition and Strategic Plan ledgers.
- Registers all four schemas in `semantics/canonical_sources.yaml`.
- Makes the generic compiler consume all four as semantic catalogs, never compiler-output authority.
- Adds ADR-018, which freezes the Planner / Meta-Planner cognitive handoff and authority boundaries.
- Adds RC-026 with hostile closure cases for reasoning/Strategy collapse, candidate self-admission, digest drift, Unknown coercion, metacognitive authority inflation, registration loss, and compiler misclassification.

## Cognitive interface stack

```text
Current Meta View
      |
      v
Affected Strategic Closure       derived, zero authority
      |
      v
Strategic Planning Episode       derived, zero authority
      |
      v
Strategic Plan Revision Candidate candidate, zero authority until admission
      |
      v
Strategic Authority
      |
      v
Strategic Plan Graph             authoritative Strategy

Planning Episodes + Plan revisions + evidence
      |
      v
Strategic Plan Metacognitive Analysis  derived / advisory
      |
      v
Planning cognition lessons -> Plan Keeper
```

## Planner boundary

The Plan Keeper may reason over exact current inputs and record observations, assumptions, candidate paths, evaluations, material Unknowns, and a recommendation in a Strategic Planning Episode. That episode is never Strategic Plan content merely because it was recorded.

A recommendation to revise Strategy must produce a separate Strategic Plan Revision Candidate bound to:

- exact predecessor revision and graph digest;
- exact proposed Strategic Plan Graph and graph digest;
- exact reasoning episode and digest; and
- applicable Strategic Authority reference.

Candidate existence is not admission. The candidate cannot approve or apply itself.

## Meta-Planner boundary

The Strategic Plan Metacognitive Reasoner may analyze exact planning episodes, Plan revisions, and outcome evidence and emit findings, recurring reasoning patterns, and advisory planning cognition lessons.

It may not modify the Strategic Plan, approve a revision candidate, become Strategic Authority, own external evidence truth, or convert a lesson directly into Strategy.

## Contraction decisions

v3.19.0 deliberately does **not** add:

- a generic `reasoning_artifact` authority class;
- a universal Planning Graph owner;
- runtime algorithms;
- prompts or model/provider bindings;
- memory implementation;
- confidence/probability/horizon/budget/schedule/progress fields;
- a hand-maintained Plan revision patch beside the exact proposed graph;
- a strategic hypothesis outcome-assessment schema;
- Delegation Graph or WorkState Graph schemas.

Existing `derived` and `candidate` authority classes are sufficient for the four admitted artifacts.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.18.0/`, which must be present with the exact v3.18 release inventory before this stacked successor is applied.
