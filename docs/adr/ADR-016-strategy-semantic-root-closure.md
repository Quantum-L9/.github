# ADR-016 — Strategy Semantic Root Closure

**Status:** Accepted for semantic-foundation v3.16.0 candidate

## Decision

The L9 strategic semantic family must terminate in one independently defined root concept: **Strategy**.

**Strategy** is an integrated theory of intended change that identifies desired future conditions, causal beliefs about how relevant conditions and actions may influence those conditions, and chosen courses of action under uncertainty.

The definition deliberately does not use the words "strategy" or "strategic". The adjective "strategic" describes a concept's relationship to Strategy; it is not itself a semantic definition and grants no authority or ownership.

`semantics/strategic_cognition_model.yaml` owns the Strategy root because it already owns the concern joining Strategic Cognition, Strategic Intent, Strategic Plan, Plan Keeper, and the metacognitive separation. A new ledger would split one concern and is not justified.

`semantics/authority_model.yaml` defines Strategic Authority explicitly: the explicitly granted authority to create, revise, or supersede the Strategy represented by the Strategic Plan within a bounded scope. Plan Keeper authority resolves to that definition.

The corrected dependency chain is:

```text
Strategic Intent constrains Strategy
Strategy is represented authoritatively by the Strategic Plan
Plan Keeper maintains the Strategic Plan under Strategic Authority
Strategic Cognition determines whether the Plan should remain unchanged or be revised
```

The four Plan-owned primitives and five relations admitted by ADR-015 remain exactly the same. Their definitions are grounded in Strategy rather than undefined `strategic direction`. Affected Strategic Closure is grounded in Plan-owned claims. External truth ownership, Current Meta View semantics, Objective semantics, Plan Keeper ownership, and the metacognitive authority separation are unchanged.

The unowned ghost concept `strategic direction` is retired from current canonical semantics before a runtime binds to it. Organization-wide code search at the v3.15.0 baseline found the retired identifiers only inside `.github`.

## Rejected alternatives

- Add `strategy_model.yaml`. Existing Strategic Cognition semantics already own the root concern; another ledger would create a needless ownership seam.
- Preserve `strategic direction` as a compatibility alias. No downstream consumer was found, and preserving an undefined concept would codify the defect.
- Reopen the four primitives or five relations. Their distinctions survived the adversarial architecture tests; the defect was above them.
- Add another invariant or contract. Existing authority, ownership, projection, validation, and Strategy separation law is sufficient once the root concepts resolve.
- Add schema or runtime representation. Representation remains a later campaign.

## Consequence

`scripts/validate-semantics.py` RC-024 fails closed unless Strategy has the admitted non-circular root definition; Strategic Intent, Strategic Plan, and Strategic Authority resolve through it; the Plan model reuses it without ownership transfer; strategy-family vocabulary mirrors canonical owners; and retired strategic-direction identifiers remain absent from current canonical strategy ledgers.

Historical release records remain immutable. v3.16.0 is the corrective successor.
