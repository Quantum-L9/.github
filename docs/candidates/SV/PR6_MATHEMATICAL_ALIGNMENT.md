# PR #6 mathematical model alignment | reduced canonical candidate

Donor: open `Quantum-L9/l9-wip#6@fb0ae95620cea0dc3f48aa009056ddb755d69640`. Frozen `.github` target: `020a94bea86e7c5c5e4107da7014ec259508f397`.

The five-term decomposition remains an **accounting identity**, not a new numerical engine:

`SV(a) = IEV(a) + SFV(a) - DC(a) - ERL(a) - OC(a)`.

It requires **exhaustive, mutually exclusive coverage** of all material effects. Net future utility that already contains DC, ERL or OC may not have the same effect subtracted again. The conditional future expression supplied in PR #6 is one supported valuation formulation:

`SFV(a) = E[ sum_(tau=t+1)^H d(tau-t) * (U_flow(S_tau | do(a)) - U_flow(S_tau | do(baseline))) ]`.

A declared geometric special case uses `d(k)=gamma^k`. Different future distributions require supported causal assumptions/conditioning, not arbitrary paired trajectories. Uncertainty and nonidentified effects remain conditional or Unknown.

The bounded `Q/V` belief-state recurrence from PR #6 is a **supported method** for questions where sequential actor responses are material and the Numerical/Probabilistic/Formal owners select it. It is **not a universal algorithm**: bounded scenarios, robust optimization or another appropriate owner-admitted method may suffice. No new reasoning sibling or standalone Q/V requirement is introduced.

| Donor concern | Retained semantic destination | Scope |
| --- | --- | --- |
| `docs/STRATEGIC_VALUE_FRAMEWORK.md` | `model.valuation`, `model.counterfactual_mathematics`, `SV-001/002` | Only applicable value claims |
| `docs/CAUSAL_ATTRIBUTION_AND_PROPAGATION.md` | `model.causal_accounting` and partition ledger | Conditional on causal path/feedback claim |
| `docs/STRATEGIC_LOOKAHEAD.md` | `model.strategic_interaction_lookahead` | Method selected by owner for material actor-response decisions |
| `docs/BOUNDEDNESS_AND_CONVERGENCE.md` | `model.strategic_interaction_lookahead` and conditional completeness requirements | Applicable horizons, budgets and tails |
| `docs/NUMERICAL_REASONING.md` | `model.evaluation_integrity`, assessment method evidence | Independent numerical owner; no Planner-owned solver |
| `implementation/SYSTEMIC_FUTURE_VALUE_COMPONENTS.md` | effect/accounting ledger and model semantics | Functional obligations, not six new services |

The 20 candidate meanings are reduced to **two proposed global invariants (`L9-SV-001`, amended, and `L9-SV-002`) plus eighteen model/contract semantic placements** (twelve retained-former, six relocated); see `IRREDUCIBILITY_DISPOSITION.md`. The six relocated safeguards each keep an independent executable falsifier; see `ADMISSION_INVARIANT_REVIEW.md`. The accounting identity, the SFV expression and the Q/V recurrence above are unchanged by the reduction.

**No official source/schema compiler replay, numerical validation, or canonical admission occurred.**
