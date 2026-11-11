# DRAFT: decision record for Semantic Foundation v3.36.0 (Domain Projection Architecture v1)

**This is not an ADR and decides nothing.** It is the text an accepted ADR would copy into `docs/adr/` only after the
repository owner gives an explicit decision for the exact subject below. Until then v3.36.0 is an
`ADDITIVE SUCCESSOR CANDIDATE`. No field below is filled by an agent.

## Status

Proposed. **Decision:** _owner only — not given._ **Decider reference:** _none._

## Subject

| Field | Value |
| --- | --- |
| Release | `docs/semantic-foundation/v3.36.0/` |
| Approved semantic tree | _`git rev-parse <candidate commit>:semantics` at the commit the owner approves_ |
| Target class (and authority) | Canonical global semantics; `Quantum-L9/.github` (`semantics/authority_model.yaml#admission_rules`) |
| Predecessor | v3.35.0 (ADR-032) |

## Context

Consumer profiles each re-select overlapping canonical semantics (GAR, Strategic Planner, Cursor-Governance,
coding agent). PR #234 proposed qualitative Strategic Value and Signal law that no profile can select until it is
canonical. This subject introduces reusable domain projections that consumers bind instead of re-deciding
selection, without changing any existing profile.

## Admitted definitions (proposed)

- Invariants `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`, `L9-SIGNAL-002`, `L9-SIGNAL-003`, `L9-SIGNAL-004`.
- Terms `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`,
  `signal_feedback_episode`, `signal_consumption`, `domain_projection`, `domain_consumer_binding`.
- Contracts `l9.contract/domain-composition-compatibility@1`, `l9.contract/domain-composition-provenance@1`.
- Profile class `domain`.
- Projection profiles `l9.projection/architecture@1`, `l9.projection/strategic-value@1`, `l9.projection/signals@1`,
  `l9.projection/governance@1`, `l9.projection/evidence-provenance@1`, `l9.projection/contracts-conformance@1`,
  `l9.projection/capabilities-dependencies@1`, `l9.projection/identity-attribution@1`.
- Composition profiles `l9.compose/<same eight names>@1`.
- Ledgers `l9.domain-projection-model/global@1` (sources `l9.source/domain-projection-model@1`) and
  `l9.domain-consumer-binding-catalog/global@1` (source `l9.source/domain-consumer-bindings@1`), with bindings
  `l9.domain-consumer-binding/{gar, strategic-planner, cursor, coding-agent, simple-plan, claude-code}@1`.
- Sixteen payload schemas `l9.schema/domain-<name>-{projection,composition}@1`.

## Decision options for the owner

1. Admit the whole subject.
2. Admit the PR #234 records and the domain architecture, but withhold one or more bindings (for example
   `strategic-planner@1`, whose consumer is unresolved). A withheld item is removed from `semantics/` and the release
   re-cut before admission, not left as a nominated-but-unadmitted record.
3. Admit only the PR #234 SVQ/Signal records. The domain profiles that select them then move to a later release.
4. Reject.

## Accepted limitations (if admitted)

- Bindings are declarations. Compiler 0.10.0 projects and composes each domain; it does not yet evaluate the two
  composition contracts over a binding's domain set.
- No consumer migrates: every binding with predecessors carries an explicit `consumer_migration` blocker.
- `strategic-planner@1` is blocked for activation (no repository or entrypoint).

## What admission would not establish

No consumer is switched, no plan, execution, publication, merge or deployment authority is granted, and a binding
grants no permission. Downstream usability needs the post-merge producer run on `main`.
