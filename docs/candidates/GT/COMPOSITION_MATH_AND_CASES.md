# GT + SV: minimal mathematical expression

This file explains the contracts. It is **not** a second canonical valuation formula, an executable solver, or proof of actor-model accuracy.

## 1. GT supplies a model-conditioned response law

Given focal action or strategy `a`, current belief state `b`, declared game/actor model `M`, and evidence/revision context `c`, GT may propose a **joint** distribution over subsequent response/state trajectories:

```text
D_GT(W[0:T] | a, b, M, c)
```

It may also provide deterministic candidate responses, conditional best responses, exploitability metrics or other solution-concept diagnostics when their assumptions are explicitly declared. No particular numerical algorithm, probabilistic inference engine or storage provider is mandated. Correlated actors and events must be represented jointly or remain Unknown. A partial probability mass is not silently normalized.

## 2. Numerical Reasoning invokes the *existing* SV definition once

```text
SV_interaction(a)
    := SV_canonical(
           candidate_action=a,
           counterfactual_world_distribution=D_GT(W[0:T] | a,b,M,c),
           comparable_baseline=B,
           objective_and_beneficiary=O,
           time_basis_and_horizon=H,
           admitted_value_contract=SV_contract_ref)
```

`SV_canonical` means the **eventual independently admitted** Strategic Value calculation; the SV candidate (PR #212 as reduced by PR #215 to `L9-SV-001` and `L9-SV-002`) is staged under `docs/candidates/SV/` and is not yet admitted. It proposes the mandatory exhaustive mutually exclusive immediate/future/cost/risk/opportunity accounting partition, beneficiary/welfare aggregation and counterfactual identification. The GT candidate references those semantics without copying the valuation model. This definition deliberately does *not* reproduce that decomposition, introduce another GT value bucket, or take ownership of numerical methods.

When a canonical SV implementation exposes conditional scenario valuations rather than a distribution argument, the *same* meaning may be calculated as an appropriately coupled expectation over response-conditioned scenarios, **provided the inner SV value has not already integrated the same uncertainty**. Nested expectations are not allowed to apply a response probability twice.

For a comparable passive-world baseline, an optional **diagnostic** is:

```text
Delta_SV_interaction(a) = SV_interaction(a) - SV_passive(a)
```

This is a comparison between two valuations under the same objective/units/horizon/baseline, never a sixth or additive SV component. The diagnostic can be positive, negative, zero or Unknown. A separate historical value estimate with an already-modeled actor response is not a passive-world baseline.

## 3. Exact counterexamples

- **No adaptive response:** if the GT-conditioned and passive joint distributions are the same, the value is the same. Neither projection generates an automatic compounding premium.
- **Ranking reversal:** an A option worth 1000 under a static successful-response assumption is worth 0.6(1000)+0.4(400)=760 under the declared GT-conditioned two-scenario model. A feasible option B worth 800 is preferred by this simplified value measure. Do not report 1000+760.
- **Repeated benefit already counted:** if the canonical SV value of 500 includes a distinct 200 future reputation effect, a GT model may change the distribution of that effect but must not append the same 200 again.
- **Conflicting objective/unit/horizon:** `SV(A)` in USD for 4 weeks and `SV(B)` in EUR for 12 weeks cannot be ranked as comparable unless a separately justified conversion and harmonized baseline exist. If missing, preserve Unresolved.
- **Unknown response mass:** a declared response distribution with total probability 0.8 cannot be treated as complete or silently renormalized; unresolved paths and their potential decision impact remain explicit.
- **Correlated counterparties:** buyer and supplier responses that share a market shock cannot be multiplied as independent marginal probabilities without evidence.
- **Stale model revision:** changing the ActorModel revision invalidates only calculations depending on it, not unrelated facts or accepted plan authority.
- **Unadmitted SV:** the GT standalone assessment can still be reported. The dependent GT+SV composed assessment remains Unresolved without invented SV references.
- **Hard constraint:** no expected value or equilibrium diagnostic makes a formally prohibited action admissible.

## 4. Equilibrium is a distinct mathematical claim

For a finite normal-form game with admissible action sets `A_i`, player strategies `pi`, and payoff model `u_i`, the unilateral deviation gain is:

```text
gap_i(pi) = max_{a_i in A_i} E[u_i(a_i, pi_-i)] - E[u_i(pi)]
```

An epsilon-Nash claim requires a method-appropriate proof that all declared deviation gains are bounded by `epsilon`, with soundly bounded approximation/numerical error. A small change between adjacent solver iterations is **not** the same test. For example, an exact stationary softmax response at temperature 1 for player utility `[2,0]` can leave positive `gap > 0.2`. Refer to the numerical method owner and independent conformance for verification.

## 5. Ownership and outputs

- Global GT contract defines conditional interaction meaning; it does not implement a solver.
- Probabilistic Reasoning owns calibrated belief updates and uncertain actor responses.
- Numerical Reasoning owns payoff and canonical SV evaluation methods and receipts.
- The Semantic Compiler selects/merges semantics only, never computes a value.
- Strategic Planner owns its planning question, candidate framing and advisory recommendation; Strategic Authority retains any plan revision decision.
- A GT-only projection, SV-only projection and derived GT+SV numerical assessment are distinct, digest-bound artifacts with different producers and authority scopes.

## SV method scope
The SV model permits question-appropriate methods, including bounded scenario evaluation and conditional Q/V; Q/V is not universally mandatory. This GT composition does not force a Q/V algorithm, equate a fixed-point with Nash, or treat local projection validation as independent evidence of empirical adequacy. A combined numerical SV claim additionally requires the counterfactual comparability, nonanticipativity, effect-identity, evidence and uncertainty obligations of the reduced SV candidate: `L9-SV-001` (counterfactual identification), `L9-SV-002` (exhaustive five-bucket partition) and the assessment-contract obligations that now carry the former SV-015..020 meanings.
