# Release Validation v3.16.0

Candidate status: **corrective successor candidate**.

## Defect closed

The current strategic semantic family has no independent canonical definition of Strategy. Strategic Cognition and Strategic Plan are instead described using `strategic direction`, while Strategic Intent and Strategic Authority also rely on unexplained strategic terminology. That leaves the family semantically circular even though the downstream architecture is otherwise coherent.

## Validator delta

- RC-016 is updated only for the corrected Plan Keeper permission names, the `strategic_authority` source coordinate, and the newly explicit Strategy / Strategic Intent vocabulary roots.
- RC-018 is updated only to reuse Strategy and the corrected global rule name.
- RC-024 adds Strategy semantic-root closure and five isolated fail-closed negative cases.
- RC-001 through RC-023 otherwise remain in force.

## RC-024 Strategy semantic-root closure

RC-024 requires:

- one Strategy root at `strategic_cognition_model.yaml#concepts.strategy`;
- the Strategy definition matches the admitted meaning and contains neither `strategy` nor `strategic`;
- Strategic Intent constrains Strategy and resolves Strategic Authority;
- Strategic Plan is the authoritative maintained record of current Strategy;
- Strategic Authority is explicitly defined in `authority_model.yaml`, references the Strategy root, and must be explicitly granted;
- Strategic Plan authority resolves to `strategic_authority`;
- `strategic_plan_model.yaml` reuses Strategy with `owned_here: false`;
- vocabulary definitions for Strategy, Strategic Intent, Strategic Plan, and Strategic Authority mirror their canonical owners;
- retired `maintained_strategic_direction`, `revise_strategic_direction_*`, `strategic_plan_owns_strategy_not_reality`, and `semantic_class: strategic_direction` remain absent from current canonical strategy ledgers.

The negative cases restore a circular Strategy definition, remove Strategic Authority, restore the ghost Plan Keeper permission, detach Strategic Plan content from Strategy, and drift vocabulary away from the root. Each must fail at its intended field.

## Preserved closure

The four Plan-owned primitives and five relations are unchanged. No relation endpoint typing, schema, graph representation, runtime, probability, confidence, horizon, actor binding, memory behavior, or execution semantics is admitted. Plan Keeper / metacognitive separation, Current Meta View authority, Objective meaning, and external truth ownership remain unchanged.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all 16 accepted ADRs plus the ADR index, and this release record. `docs/semantic-foundation/v3.15.0/` and every earlier release record remain unchanged.

## Admission state

v3.16.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
