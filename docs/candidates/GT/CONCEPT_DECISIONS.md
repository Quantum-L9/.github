# GT admission semantics: bounded decisions

## Accepted design in this conversation

- A single canonical SV meaning and five-bucket value assessment; GT never redefines SV.
- GT adds **endogenous actor response**, not a fourth reasoning sibling.
- GT-only returns a conditional strategic assessment; SV-only remains independent.
- When combined, one numerical owner evaluates canonical SV over GT-conditioned paths, not `SV + GT uplift`.
- The value change can be positive, negative, zero, or Unknown; combined assessment has no authorization effect.
- Strategic Planner is the first consumer; its native Plan authority remains elsewhere.

## Irreducibility adjudication

- One proposed global invariant L9-GT-001: adaptive response must not be silently modeled as passive.
- Twelve GT-only definitions, each needed to distinguish specific game or response semantics; no StrategicValue, SystemicFutureValue, causal-value buckets, utility calculation, or approval vocabulary is redefined.
- One GT assessment contract, independently useful without the SV dependency.
- One **dependent** GT+SV composition contract, requiring admitted SV contract and projection, not self-admitting.
- One GT-specific consumer profile with three existing canonical source classes.
- One GT-only mechanical composition profile with existing source_class_namespace placement; it assembles source selections, never numbers.
- Two GT-only native schema candidates for source and composed payloads. A consumer-owned reference-envelope JSON Schema is not registered as a new canonical value model.
- Existing `l9.pattern/canonical-source-derived-projections@1` and existing Formal/Probabilistic/Numerical owners suffice. New architecture pattern, reasoning node, global SV model, or source ledger is not justified.

## Explicitly rejected from global additions

- Five SV valuation buckets or a GameTheoryStrategicValue numeric formula.
- GT uplift as an additive bucket, reputation effect automatically counted again, or 'compounding' as a promise of higher value.
- Solver implementation mandates (`softmax`, `einsum`, `best_response` as a universal algorithm).
- Treating a Nash solution as verified behavior, a stable fixed point as Nash proof, or a forecast as execution authority.
- Broker-specific reservation-price policies, Graphiti storage layout, or AgentOS execution wiring.

## Source lineage and status

Donor: `l9-wip#6` pinned head `fb0ae95620cea0dc3f48aa009056ddb755d69640` and Dropbox September 27 original discussion plus the July solver notes. The previous two GT harvests and prior SV candidate were compared for duplication; neither is admitted by inclusion. The current `.github` ledger already owns the Plan `strategic_commitment` term; GT now uses `incentive_bearing_commitment` instead. PR #212 stages SV as documentation only; PR #215 reduces it to two new invariants (`L9-SV-001`, `L9-SV-002`) and keeps SV-015..020 as model/contract lineage. The other GT entries are candidate additions. Global admission is a separate exact-digest decision.
