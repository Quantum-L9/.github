# ADR-018 — Strategic Planning Cognition Artifact Representations

**Status:** Accepted for semantic-foundation v3.19.0 candidate

## Context

ADR-014 established Strategic Cognition and the separation between the Plan Keeper and the Strategic Plan Metacognitive Reasoner. ADR-015 admitted the four Plan-owned primitives, five strategic relations, and Affected Strategic Closure while deliberately deferring representation. ADR-016 repaired Strategy as the non-circular semantic root. ADR-017 then admitted the provider-neutral Strategic Plan Graph representation and the federated-authority-graph pattern.

The next implementation boundary is now clear. A Planner runtime and an independent Meta-Planner runtime need stable machine-readable interfaces around the Strategic Plan Graph, but neither runtime may invent its own interpretation of:

- what selective reconsideration means;
- what a planning reasoning episode records;
- how reasoning becomes a candidate rather than an immediate Plan mutation;
- how a candidate is bound to an exact predecessor and exact proposed Plan Graph;
- what the Meta-Planner may observe and emit; or
- whether metacognitive output can become Strategy.

Without canonical representations, downstream implementations would be forced to create local packet shapes and would likely collapse reasoning workspace, candidate state, Strategic Plan state, and metacognitive advice into one mutable runtime object.

## Decision

Admit four canonical schema definitions in `Quantum-L9/.github`:

1. `l9.schema/affected-strategic-closure@1`
2. `l9.schema/strategic-planning-episode@1`
3. `l9.schema/strategic-plan-revision-candidate@1`
4. `l9.schema/strategic-plan-metacognitive-analysis@1`

These schemas define representation only. Existing Strategic Cognition and Strategic Plan ledgers remain the semantic owners. The schemas do not admit runtime algorithms, prompts, model/provider selection, memory behavior, storage layout, graph database technology, confidence/probability models, scheduling, or execution authority.

## Canonical cognitive flow

```text
Authoritative reality / evidence
            |
            v
     Current Meta View
       authority: derived
            |
            v
 Affected Strategic Closure
       authority: derived
            |
            v
 Strategic Planning Episode
       authority: derived
       strategic effect: none
            |
            v
 Plan Revision Candidate
       authority: candidate
       strategic effect: none until admitted
            |
      Strategic Authority
            |
            v
   Strategic Plan Graph
       authority: Strategy

Planning Episodes + Plan revisions + outcome evidence
            |
            v
Metacognitive Analysis
       authority: derived/advisory
            |
            v
 planning cognition lessons
            |
            v
        Plan Keeper
```

The flow is intentionally asymmetric. The Plan Keeper reasons about the world and Strategy. The Strategic Plan Metacognitive Reasoner reasons about the Plan Keeper's reasoning process. The latter never becomes a second strategic authority.

## Affected Strategic Closure

Affected Strategic Closure represents the bounded reconsideration frontier for one exact Plan revision and one exact set of changed authoritative inputs.

It binds:

- `plan_ref`;
- exact `plan_revision_ref`;
- exact `plan_graph_digest`;
- exact trigger source references and digests;
- the resulting set of affected Plan-owned claim references;
- unresolved references when applicable;
- provenance; and
- a closure digest.

The schema does **not** define the closure algorithm. Algorithm choice remains a later reasoning/runtime concern. The artifact may identify claims requiring reconsideration but may never decide Strategy, mutate the Plan, invalidate the Plan, or automatically mark claims false or stale.

An empty closure is valid when no Plan-owned claim materially depends on the changed input.

## Strategic Planning Episode

A Strategic Planning Episode is an immutable, non-authoritative record of one bounded Plan Keeper reasoning episode over exact inputs.

It binds the exact:

- Strategic Plan revision and graph digest;
- Strategic Authority reference;
- Strategic Intent references;
- Objective references;
- Current Meta View reference and digest;
- optional Affected Strategic Closure reference and digest; and
- trigger references.

Its workspace contains only reasoning-workspace objects:

- **Observation** — a statement tied to source references. Recording it does not transfer truth ownership.
- **Assumption** — a provisional proposition used during reasoning. It is not automatically a Strategic Hypothesis.
- **Candidate Path** — a possible path considered by the Planner. It is not a Strategic Commitment.
- **Evaluation** — a bounded assessment of a candidate or reasoning subject against referenced Objectives, Evidence, and exact inputs. It creates no Objective or Evidence authority.
- **Material Unknown** — unresolved material input that must remain Unknown rather than being coerced into a favorable answer.

The episode may recommend exactly one of three outcomes:

- retain the current Plan;
- propose a revision; or
- remain unresolved.

The recommendation has `authority_effect: none`. A `propose_revision` result requires a separate Strategic Plan Revision Candidate.

## Strategic Plan Revision Candidate

A Strategic Plan Revision Candidate is the sole bridge admitted here between Plan Keeper reasoning and a possible new authoritative Plan revision.

It binds:

- the exact current `plan_ref`;
- exact predecessor revision reference and graph digest;
- one exact proposed Strategic Plan Graph reference, schema identity, and digest;
- the exact Strategic Planning Episode reference and digest that produced it;
- optional Affected Strategic Closure reference and digest;
- Strategic Authority reference;
- rationale references;
- provenance; and
- candidate digest.

The candidate does **not** carry a separately maintained mutation patch. The delta is mechanically derivable from the exact predecessor graph and exact proposed graph. This avoids a second representation that could disagree with the candidate graph.

Candidate existence is not admission. `strategic_authority_ref` identifies the applicable authority but does not itself prove that authority was exercised. Admission must bind both the candidate digest and proposed graph digest. If either changes, prior approval does not float.

The proposed predecessor must still be current at admission time or admission fails closed.

## Strategic Plan Metacognitive Analysis

Strategic Plan Metacognitive Analysis is the canonical advisory output shape owned by the Strategic Plan Metacognitive Reasoner.

It binds:

- one Strategic Plan lineage (`plan_ref`);
- exact reasoning episodes with digests;
- Plan revision references;
- outcome evidence references;
- optional prior metacognitive analyses;
- findings;
- recurring reasoning patterns;
- planning cognition lessons;
- unresolved items;
- provenance; and
- analysis digest.

Findings are limited to reasoning-focused categories:

- reasoning strength;
- reasoning failure;
- expectation/outcome mismatch;
- revision pattern; or
- Unknown.

Recurring patterns are limited to:

- recurring reasoning strength;
- recurring reasoning failure;
- recurring expectation/outcome pattern; or
- Unknown.

A planning cognition lesson is advisory input to the Plan Keeper. It has `authority_effect: none`. A lesson may influence a future planning episode, but it may never directly modify the Strategic Plan or become a strategic decision.

## Artifact authority model

No new global artifact class is admitted in this release.

The four artifacts fit existing authority classes:

| Artifact | Instance authority | Strategic effect |
| --- | --- | --- |
| Affected Strategic Closure | derived | none |
| Strategic Planning Episode | derived | none |
| Strategic Plan Revision Candidate | candidate | none until separately admitted |
| Strategic Plan Metacognitive Analysis | derived / advisory | none |
| Strategic Plan Graph | authoritative within granted Strategic Authority after admission | represents current Strategy |

The existing `derived` and `candidate` authority classes are sufficient. A generic `reasoning_artifact` class is therefore not justified by this release.

## Planner implementation boundary

A conforming Plan Keeper implementation may consume:

- Current Meta View;
- Strategic Intent;
- current Strategic Plan Graph;
- applicable Objectives;
- optional Affected Strategic Closure; and
- advisory planning cognition lessons.

It may emit:

- Strategic Planning Episode; and
- optionally a Strategic Plan Revision Candidate.

It may not treat its workspace, recommendation, or candidate as Strategy before applicable Strategic Authority admits the exact candidate.

The schemas deliberately do not define how the Planner searches, optimizes, simulates, prompts, calls models, retrieves memory, or ranks candidate paths.

## Meta-Planner implementation boundary

A conforming Strategic Plan Metacognitive Reasoner may consume:

- exact Strategic Planning Episodes;
- Plan revision history;
- outcome evidence references;
- prior analyses; and
- other authority-resolved inputs needed to evaluate the reasoning process.

It may emit Strategic Plan Metacognitive Analysis and advisory planning cognition lessons.

It may not:

- modify or supersede the Strategic Plan;
- approve a revision candidate;
- become Strategic Authority;
- reinterpret external evidence into owned truth;
- turn a lesson into a strategic decision; or
- create an unbounded Meta-Meta authority chain.

## Why no separate reasoning graph authority

The reasoning artifacts are graph-shaped through typed references, but this release does not create a new `Planning Graph` semantic owner or a universal cognition graph.

The Strategic Plan remains the authoritative Strategy graph. Planning Episode and Metacognitive Analysis are bounded reasoning artifacts whose local typed references may later be indexed or projected into a graph provider without changing their semantic ownership.

Graphiti, Neo4j, relational storage, vector stores, model vendors, prompt formats, and memory providers remain implementation choices.

## Relationship to federated authority graphs

ADR-017 remains unchanged. The new reasoning artifacts participate through references rather than ownership absorption:

```text
Current Meta View -> Planning Episode -> Revision Candidate -> Strategic Plan Graph
                                           |
                                           +-- admitted only under Strategic Authority

Planning Episode / Plan Revision / Evidence -> Metacognitive Analysis -> Planner lesson
```

These reasoning artifacts do not create new nodes in the Strategy graph unless and until an exact revision candidate is admitted and becomes a new Strategic Plan Graph revision.

## Rejected alternatives

### Put Planner workspace directly in Strategic Plan Graph

Rejected. Workspace observations, assumptions, rejected paths, and evaluations are not Strategy. Serializing them into the Plan would destroy the boundary between reasoning and authoritative Strategy.

### Let Plan Keeper mutate the current Plan in place

Rejected. Historical Strategy must remain addressable. Reasoning produces a candidate; authorization produces a new immutable Plan revision.

### Store a hand-maintained revision patch beside the proposed graph

Rejected. The patch would become a second representation of the same change and could drift from the proposed graph. The delta is mechanically derivable from predecessor and proposed graph digests.

### Let metacognitive findings revise Strategy directly

Rejected. It would collapse the independent advisory cognition into Strategic Authority and violate the frozen Plan Keeper / Meta-Planner separation.

### Add confidence, probability, horizon, budget, priority, schedule, progress, or model/provider fields now

Rejected. None is required to represent the cognitive handoff. Their future admission requires separate semantic necessity and ownership proof.

### Add a generic `reasoning_artifact` authority class

Rejected for this release. Existing `derived` and `candidate` classes are sufficient. A new global class would be ontology inflation without demonstrated necessity.

### Admit a hypothesis-outcome assessment schema in this release

Rejected as premature. Its owner crosses Strategic belief evaluation and Evidence interpretation and should be resolved separately before representation is frozen.

## Validation

RC-026 must fail closed if the four schemas drift across authority, ownership, digest binding, candidate admission, workspace/Plan separation, Unknown preservation, metacognitive advisory law, canonical registration, compiler classification, or the semantic-model anchors admitted here.

## Consequence

After v3.18 and v3.19 are admitted, Planner and Meta-Planner implementations can be built against stable semantic interfaces without deciding their runtime algorithms in `.github`.

The downstream implementation problem becomes deliberately narrow:

```text
Planner runtime:
  exact inputs -> Strategic Planning Episode -> optional Revision Candidate

Admission:
  exact Revision Candidate + exact proposed Plan Graph -> authorized new Plan revision

Meta-Planner runtime:
  exact episodes + revisions + evidence -> advisory Metacognitive Analysis
```

That is the intended foundation for Strategic Cognition runtime realization.
