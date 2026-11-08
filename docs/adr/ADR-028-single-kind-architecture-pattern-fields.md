# ADR-028 — Single-Kind Architecture Pattern Fields

**Status:** Candidate for semantic-foundation v3.31.0, stacked on v3.30.0 (ADR-027, Quantum-L9/.github#218). Drafted on 2026-11-08 at the repository owner's instruction ("Normalize"), after candidate schema synthesis for `l9.projection/architecture-intelligence@1` could not describe `semantics/architecture_patterns.yaml`. Admission of v3.31.0 is the acceptance gate; this record does not admit itself.

## Context

Candidate payload-schema synthesis (`schema-synthesize` in `Quantum-L9/l9-semantic-compiler-engine`) types a selected source through a closed source-field grammar algebra. That algebra has no union, so one field cannot be a string in some entries and a list in another, or a list in one entry and an object in another. `l9.projection/architecture-intelligence@1` selects `$.patterns` whole, so every pattern field must have one kind across all patterns.

An exhaustive scan of the 24 sources that profile selects, at `Quantum-L9/.github@9488d8f`, found exactly two such fields. Both are in `architecture_patterns.yaml`, and both were on `main` before v3.29.0:

1. **Edge `to`.** In every edge of every pattern, `to` is one node name, except in `l9.pattern/reference-model-conformance@1`. There, the edge `conformance_runner compares` has a list `to`: `[reference_model, candidate_implementation]`.
2. **Pattern `lifecycle`.** `l9.pattern/dependency-package@1` declares `lifecycle` as an object holding a constraint `expression`, the same form as its `runtime_identity` and as `admission_rule` elsewhere. `l9.pattern/authority-candidate-admission@1` declares `lifecycle` as a bare list of states.

## Options considered

### Option A — Normalize the two fields in the ledger

- Edge `to`: split the list-valued edge into one edge per compared side.
- `lifecycle`: hold the state list under `stages`, the key `semantics/lifecycle.yaml` uses for an ordered state list, so `lifecycle` is an object in both patterns.
- Pros: two entries change. The `dependency-package@1` lifecycle that RC-029 pins is untouched. Nodes, relations, states and their order are unchanged.
- Cons: the split edge no longer states in one place that the two compared sides are compared with each other. The pattern's `purpose` and `guarantees` (`candidate_does_not_define_its_own_correctness`) still say so.

### Option B — Make every `to` a list, and every `lifecycle` a list

- Pros: one edge can name several targets.
- Cons: every edge of every pattern changes, for a feature one edge uses. A constraint expression is not a state list, so `dependency-package@1`, which RC-029 pins, would change meaning.

### Option C — Admit a union operator in the candidate grammar dialect

- Pros: no ledger changes.
- Cons: it widens a closed, owner-reviewed algebra for two entries. It does not stop mixed kinds from recurring in other ledgers.

## Decisions

Option A.

1. In `l9.pattern/reference-model-conformance@1`, the edge `conformance_runner compares [reference_model, candidate_implementation]` becomes two edges: `conformance_runner compares reference_model` and `conformance_runner compares candidate_implementation`.
2. In `l9.pattern/authority-candidate-admission@1`, `lifecycle: [candidate, admission_evaluated, awaiting_authority, admitted, published]` becomes `lifecycle: {stages: [candidate, admission_evaluated, awaiting_authority, admitted, published]}`. The states and their order are unchanged.
3. Both patterns keep their identifiers `@1`. Their nodes, relations, states, purpose, preconditions, guarantees, forbidden lists and `compatible_with` lists are unchanged, so the meaning does not change. Only the representation of two fields changes.
4. No other ledger, rule, profile, criterion, contract or invariant changes. No RC check is added.

## Review findings (recorded, not resolved)

- No release check pins that a pattern field has one kind across patterns. The convention is enforced only by the absence of a counterexample, and by candidate grammars where they are drafted.
- If the owner judges either change material, the pattern needs a successor `@2` instead of an amended `@1` (L9-REVISION-001). This record takes the position that both are changes of representation only.
- Both patterns are selected by `l9.projection/architecture-intelligence@1`. `authority-candidate-admission@1` is also selected whole by `l9.projection/pr-audit@1`, and its id is referenced by `node_archetypes.yaml` and the strategic-planning schemas. None of those reads the `lifecycle` list or the edge shape, and RC-030 and RC-032 still pass. A consumer outside this repository that read either field must now read the new form.

## Consequences

- Every field of every pattern in `architecture_patterns.yaml` has one kind, so a closed grammar can describe the ledger.
- Candidate schema synthesis for `architecture-intelligence@1` is no longer blocked by this ledger. It still requires owner-reviewed grammars, and a compiler able to project the profile's `vocabulary` selections within its work budget.
- This grants no publication, admission, deployment or runtime authority.
