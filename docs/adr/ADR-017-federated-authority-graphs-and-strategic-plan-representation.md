# ADR-017 — Federated Authority Graphs and Strategic Plan Graph Representation

**Status:** Accepted for semantic-foundation v3.18.0 candidate

## Context

L9 now has canonical Strategy, Strategic Cognition, Strategic Intent, Strategic Authority, and Strategic Plan semantics. ADR-015 intentionally stopped before representation. The next operating-model requirement is to connect Strategy to delegation, durable work, execution, evidence, and authoritative reality without creating a central mega-graph that steals ownership from those domains.

The organization already has the required derivation primitives: canonical-source projections, non-authoritative read models, provenance-preserving composed projections, and `l9.compose/consumer-view@1`. What is missing is a global architecture rule for graph-shaped domain federation and the minimum representation of the Strategic Plan itself.

This ADR admits those two pieces and nothing else.

## Decision 1 — Federated authority graphs

Admit `l9.pattern/federated-authority-graphs@1` in `semantics/architecture_patterns.yaml`.

A federated authority graph is **not** one graph database, one canonical graph, or one new authority. It is a composition architecture in which each semantic domain preserves its own owner and exact source coordinates while exposing typed references that may be projected and composed into derived cross-domain views.

The operating-model direction is:

```text
Strategic Intent
      │
      ▼
Strategic Plan Graph
owns current Strategy
      │
      │ typed downstream → upstream references
      ▼
Delegation Graph
owns bounded delegation grants / authority assignments
      │
      ▼
WorkState Graph
owns work meaning + campaign continuity
      │
      ▼
Execution Graph
owns or derives execution structure under its own governing contract
      │
      ▼
Evidence + authoritative reality sources
own observations and domain truth in their respective domains
      │
      ▼
Derived management / reasoning views
authority = zero
```

This diagram is an ownership topology, not an instruction to colocate storage or assign all runtime responsibilities now.

### Reference direction law

The canonical direction of cross-domain realization references is **downstream to upstream**:

```text
Delegation Grant → Strategic Commitment
Work Unit        → Delegation Grant / governing strategic subject
Execution        → governing Work Unit
Evidence         → exact Execution or other observed subject
```

Upstream authorities do not maintain inventories of downstream consumers. Reverse traversal is derived from projected references.

Therefore:

```text
WHY traversal
Execution → Work → Delegation → Commitment → Target → Goal → Intent

HOW traversal
Goal → derived reverse adjacency → Target → Commitment
     → Delegation → Work → Execution → Evidence
```

WHY can follow authoritative forward references. HOW may use a derived reverse index. Neither traversal transfers authority.

### Ownership preservation

Every participating graph retains its own semantic owner. A typed cross-domain reference:

- does not copy the target object into local ownership;
- does not authorize mutation of the target;
- does not elevate a derived view into authority;
- does not make the graph/index provider the semantic owner;
- must resolve to an exact typed coordinate or remain explicitly Unknown.

A composed management view is disposable and rebuildable. Loss of Graphiti, Neo4j, Redis, a vector index, or any other materialization must never redefine authoritative truth.

## Decision 2 — Operating-model graph boundaries

This ADR formalizes the intended graph family without admitting future domain schemas prematurely.

| Graph / surface | Owns | Status after v3.18.0 |
| --- | --- | --- |
| Strategic Plan Graph | the Strategy represented by one Strategic Plan revision | schema admitted here |
| Delegation Graph | bounded delegation grants / authority assignments | semantic realization intentionally unresolved pending Gate / Gate_SDK audit |
| WorkState Graph | work meaning, dependencies, continuity, claims, outcomes | domain boundary formalized; schema/owner not admitted here |
| `l9-state` | durable revision / claim / journal / receipt persistence mechanics | persistence substrate, never owner of work meaning |
| Execution Graph | execution structure according to its governing execution contract | existing runtime realization may be consumed later; no new global ownership admitted here |
| Evidence | observed outcomes bound to exact subjects | evidence, never semantic authority by itself |
| Reality sources | domain facts | remain with each applicable authoritative owner |
| Management / reasoning view | nothing | derived composition only |

### No universal Reality graph

L9 does not admit a universal `Reality` owner. Facts remain authoritative where their domain semantics place them. A consumer may project and compose those facts, but projection and composition do not absorb ownership.

### Delegation default

Until a separate product boundary is proven necessary, missing **global delegation semantics belong in `Quantum-L9/.github`**. Runtime realization may live elsewhere. The Lane B audit of Gate / Gate_SDK must determine whether existing runtime delegation can faithfully realize the future canonical Delegation Graph. The audit must not code or pre-decide a new repository.

## Decision 3 — Strategic Plan Graph v1

Admit `semantics/strategic_plan_graph.schema.yaml` as the minimum machine-readable representation of one immutable Strategic Plan revision.

The schema is intentionally one file. A family of separate Goal, Target, Hypothesis, Commitment, and Relation schemas is not justified.

### Local node set

Exactly four Plan-owned node kinds exist:

1. `strategic_goal`
2. `strategic_target`
3. `strategic_hypothesis`
4. `strategic_commitment`

`strategy` is not a fifth node kind. Strategy is the integrated theory represented by the graph.

The following are not local Plan node kinds and remain externally owned: Strategic Intent, Objective, Capability, Constraint, Evidence, Architecture, Execution, Work, Delegation, environmental truth, and other domain facts.

### Strategic relations

Exactly five relation kinds exist:

- `advances`
- `enables`
- `depends_on`
- `conflicts_with`
- `supersedes`

No sixth relation is admitted for convenience.

At least one endpoint of every strategic relation must resolve to a local Plan-owned node. This prevents the Strategic Plan from becoming a universal world graph while still allowing Plan-owned claims to reference external semantics.

### `enables` attribution

An `enables` edge is a causal belief of Strategy, not authoritative reality. Every `enables` relation therefore requires `hypothesis_ref`, and that reference must resolve to a local `strategic_hypothesis`.

Example:

```text
Capability X ──enables──► Commitment C
                 │
                 └── attributed to Hypothesis H
```

This preserves future falsification and metacognitive analysis without adding confidence or probability fields.

### `supersedes` lineage

`supersedes` preserves history. Its source must be a local Plan node. Its target must resolve to the same primitive kind within the same Strategic Plan lineage and may be a node from a prior immutable Plan revision.

A Commitment may supersede a Commitment. A Target may supersede a Target. A Commitment does not supersede an Objective, Capability, or Goal merely because an implementation finds that convenient.

### External references

Non-local relation endpoints are semantic references. They remain externally owned. The representation does not copy external objects into Plan ownership.

This supports, for example:

```text
Commitment C depends_on Capability X
Hypothesis H conflicts_with Constraint Q
Target T advances Goal G
```

where `Capability X` and `Constraint Q` remain authoritative elsewhere.

### Compound causal claims

No hypergraph is admitted. A Strategic Hypothesis is the first-class causal proposition. Joint conditions remain expressible through the hypothesis statement plus ordinary strategic relations.

### Revision semantics

A Strategic Plan is maintained through immutable revisions:

```text
Plan P
  revision R1
      ↓ successor
  revision R2
      ↓
  revision R3
```

The schema therefore carries stable Plan identity, exact revision identity, optional predecessor revision, exact Strategic Authority reference, provenance, and graph digest. Content change requires a new revision identity. Historical revision content remains addressable and immutable.

The schema deliberately does not freeze a URI syntax. `semantic_ref` remains the coordinate abstraction.

### Affected Strategic Closure is not serialized

`affected_strategic_closure` remains a reasoning concept. It is computed when authoritative inputs change. It is not Plan content and does not appear as a graph field or node.

The legal flow remains:

```text
authoritative reality change
→ affected reasoning analysis
→ Affected Strategic Closure
→ Plan Keeper reasoning under Strategic Authority
→ Plan remains or a new revision is authorized
```

Reality does not directly mutate the Plan.

## Decision 4 — Computational management is derived

The federation enables computational management but does not create a management authority.

Examples of derived analyses include:

### Orphan strategic work

```text
work explicitly declared as strategy-realization
AND no reachable current Strategic Commitment / Target / Goal
→ ORPHAN_STRATEGIC_WORK candidate
```

Routine operational work is not automatically orphaned merely because it lacks a Goal.

### Zombie work

```text
active work
→ bound Strategic Commitment
→ Commitment superseded
→ RECONSIDERATION candidate
```

This does not automatically cancel work.

### Unrealized commitment

```text
current Strategic Commitment
AND no current delegation / work realization path
→ UNREALIZED_COMMITMENT observation
```

This may be intentional queueing and is not automatically a defect.

### Unsupported execution

```text
execution requires delegated authority
AND no valid current delegation reference resolves
→ fail closed
```

### Hypothesis reconsideration

```text
Hypothesis H attributes A enables B
Evidence shows A occurred and B materially did not
→ HYPOTHESIS_RECONSIDERATION candidate
```

Evidence does not mechanically rewrite the Strategic Plan. Plan Keeper owns the strategic decision.

## Decision 5 — Representation is provider-neutral

The Strategic Plan Graph schema defines semantic representation, not storage. It does not choose Graphiti, Neo4j, PostgreSQL, Qdrant, Redis, JSON files, or another provider.

A provider may materialize, index, search, visualize, or cache the graph under applicable contracts. Provider failure must not erase or redefine authoritative Strategy.

## Deferred decisions

v3.18.0 explicitly does **not** admit:

- Delegation Graph schema;
- WorkState Graph schema;
- universal execution semantics;
- universal Reality Graph;
- a management mega-graph repository;
- Graphiti / Neo4j / database bindings;
- Plan Keeper runtime;
- Metacognitive Reasoner runtime;
- confidence or probability;
- horizon / date / deadline fields;
- budget, priority, resource allocation, or progress fields;
- actor/executor/task/campaign fields inside Strategic Plan Graph;
- an Affected Strategic Closure serialization;
- a sixth Strategic Plan relation;
- a fifth Strategic Plan primitive.

## Lane B handoff

After v3.18.0 admission, audit Gate and Gate_SDK against the required Delegation Graph semantics. The audit question is narrowly:

> Can the current Gate / Gate_SDK delegation surfaces faithfully realize an authoritative, bounded Delegation Grant model while preserving the distinction between governing delegation and transport lineage?

The audit must inspect at minimum:

1. first-class grant identity;
2. delegator identity;
3. delegatee identity;
4. upstream authority source;
5. governed subject reference;
6. bounded scope;
7. validity / expiry;
8. revocation / supersession;
9. runtime projection preserving exact grant identity;
10. transport lineage versus governing authority;
11. Gate validation versus authority manufacture;
12. typed binding from Work / Execution to the grant.

Only after that audit may L9 choose among reuse, a small `.github` semantic addition, or a separately justified product.

## Consequences

L9 gains a durable operating-model spine without centralizing truth:

```text
Strategy → Delegation → Work → Execution → Evidence
```

while preserving the stronger law:

```text
many authoritative owners
        + typed references
        + provenance-preserving projections
        + derived composition
        = computational management without a mega-authority
```

That architecture is the basis for future WHY/HOW traversal, orphan-work detection, zombie-work detection, strategic realization analysis, hypothesis/outcome learning, and selective re-reasoning.
