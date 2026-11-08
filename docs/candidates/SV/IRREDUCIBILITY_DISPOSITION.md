# Strategic Value candidates: irreducibility reduction (twenty meanings, two invariants)

**Decision status:** proposed pre-admission classification, not canonical authority.  
**Beneficiary frozen for this candidate:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397`.  
**Donor:** `Quantum-L9/l9-wip#6@fb0ae95620cea0dc3f48aa009056ddb755d69640`.

The original fourteen candidate meanings are **not erased**. Only two are proposed as new global invariant IDs. The other twelve are now expressed in `strategic_value_model.yaml#retained_former_candidate_semantics`, their primary model sections, and the conditionally applicable Strategic Value assessment contract. These were **candidate IDs**, never admitted global IDs, so no existing canonical invariant is being retired or rewritten.

| Former candidate | Proposed disposition | Semantic owner and destination | Why not a separate unconditional global law |
| --- | --- | --- | --- |
| `L9-SV-001` | **KEEP** invariant | `invariants.yaml` + `model.valuation` | Foundational comparability and declared model basis for a complete quantitative Strategic Value claim |
| `L9-SV-002` | **KEEP** invariant | `invariants.yaml` + `model.valuation.accounting_partition_contract` | Foundational exclusive and exhaustive five-term accounting; cannot be replaced by vague deduplication |
| `L9-SV-003` | MOVE | `model.forecast_and_realization`; contract `separate_predicted_and_realized_outcomes` | Specializes existing provenance/evidence/unknown obligations, not a new general evidence constitution |
| `L9-SV-004` | MOVE | `model.causal_accounting`; contract `no_novelty_echo_or_circular_value_inflation` | Recurrence/feedback valuation detail, conditional on claimed causal propagation |
| `L9-SV-005` | MOVE | `model.causal_accounting`; contract `negative_propagation_and_coordinating_drag_where_material` | Bilateral direction and sign detail is model semantics |
| `L9-SV-006` | MOVE | `model.causal_accounting`; contract `bounded_tail_and_early_stop_coverage_or_explicit_unresolved_consequences` | Mesh/loop unrolling is conditional model methodology, not universal graph law |
| `L9-SV-007` | MOVE | `model.valuation.explanatory_dimensions`; effect-identity contract | Future work elimination is a value dimension, never a bonus multiplier |
| `L9-SV-008` | MOVE | `model.valuation.explanatory_dimensions`; effect-identity contract | Capability/dependency unlocks are counterfactual value dimensions, not autonomous credits |
| `L9-SV-009` | MOVE | `model.valuation.explanatory_dimensions`; uncertainty contract | Information/option value is conditional on relevance to a decision, not automatic from entropy reduction |
| `L9-SV-010` | MOVE | `model.comparisons.relevant_meta_action_kinds`; relevant alternatives contract | ACT/LEARN/COMPUTE/WAIT/STOP matter only when feasible and relevant; not universally mandatory |
| `L9-SV-011` | MOVE | `model.strategic_interaction_lookahead`; actor-response contract | Q/V is supported when selected; bounded scenarios, robust or other owner-admitted methods can suffice |
| `L9-SV-012` | MOVE | `model.comparisons.may_return`; result-shape guarantee | Specializes general uncertainty/result-shape preservation, dependent on the actual decision question |
| `L9-SV-013` | MOVE | `model.strategic_interaction_lookahead.qv_only_stopping_conditions`; conditional marginal-computation requirement | Additional computation/learning is an alternative only when material; no universal Q/V optimization obligation |
| `L9-SV-014` | MOVE | `model.strategic_interaction_lookahead.selection_requirements`; actor-response contract | Responsive actors trigger conditional methods, not blanket game-theoretic state recursion |

**Remaining candidate global laws (after `SV-CONSTITUTIONAL-REDUCTION-DEV-PACK-v1`):** `L9-SV-001` and `L9-SV-002` only. The six further candidates `L9-SV-015..020` are dispositioned below; their meanings are preserved, not admitted.

## Additional candidates `L9-SV-015..020`: reduction disposition

| Former candidate | Disposition | Governing invariants | Model destination | Unchanged contract obligation | Applies when |
| --- | --- | --- | --- | --- | --- |
| `L9-SV-015` | **MERGE** into amended `L9-SV-001` | `L9-SV-001` | `evaluation_integrity.counterfactual_identification` | `counterfactual_worlds_share_defensible_initial_conditions_time_basis_and_identification_assumptions` | a causal intervention effect is claimed |
| `L9-SV-016` | **CONTRACT** | `L9-SV-001`, `L9-SV-002`, `L9-AUTH-001` | `evaluation_integrity.beneficiary_scope` | `beneficiary_scope_and_welfare_aggregation_when_cross_actor_effects_material` | material cross-actor valuation |
| `L9-SV-017` | **CONTRACT** | `L9-SV-001`, `L9-PROV-001` | `evaluation_integrity.nonanticipativity` | `nonanticipative_conditional_policies_when_sequential_actions_are_evaluated` | sequential policy value is claimed |
| `L9-SV-018` | **CONTRACT** | `L9-SV-002`, `L9-HARD-001` | `evaluation_integrity.joint_portfolio_valuation` | `joint_portfolio_counterfactual_and_resource_interactions_for_nonadditive_actions` | joint or portfolio value is claimed |
| `L9-SV-019` | **REUSE** existing law | `L9-UNKNOWN-001`, `L9-SV-001` | `evaluation_integrity.uncertainty_aware_selection` | `uncertainty_sensitivity_or_conditional_frontier_when_preference_can_flip` | material preference-sensitive uncertainty |
| `L9-SV-020` | **REUSE** existing law | `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-PROV-001`, `L9-COORD-001` | `evaluation_integrity.independent_method_assurance` | `method_identity_input_lineage_executed_method_evidence_and_applicable_independently_reviewable_model_validation_evidence_for_strong_numerical_claims` | a model-derived or independently verified claim is made |

Each record in `strategic_value_model.yaml#relocated_additional_candidate_semantics` carries the original PR #212 statement verbatim (`meaning`), checked byte-for-byte against the frozen donor in `evidence/reduction-v1/donor/`, and `authority_status: not_admitted_as_independent_invariant`. The record is lineage, not an invariant.

All 20 candidate meanings are therefore traceable: 2 proposed invariants, 12 retained-former model/contract placements, 6 relocated model/contract placements.

Existing source obligations such as `L9-PROV-001`, `L9-UNKNOWN-001`, `L9-HARD-001`, `L9-PROJECTION-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-COORD-001` and authority/strategy separation remain owned by the existing `.github` ledgers and are **projected**, not copied as new value-specific laws.

## Exact closure checks

The model's `governed_by.invariants`, the assessment contract's `source_invariants`, the projection profile's invariant selectors, and both payload-schema enums each contain exactly the twelve governing IDs (`L9-SV-001`, `L9-SV-002` and ten existing invariants), each once. `L9-SV-015..020` appear only inside the relocation lineage section and its schema descriptor (and in falsifier lineage and documentation); `tests/test_reduction_closure.py` and `apply_to_pinned_checkout.py` enforce this mechanically.

This is a **candidate architecture reduction**. The ledger's `owner_decision_ref` is `null` for all eight decisions. Formal adjudication remains with the owner.
