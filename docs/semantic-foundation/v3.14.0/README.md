# Semantic Foundation v3.14.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor repairs a pre-existing canonical inconsistency discovered after v3.13.0. The global contract `l9.contract/admission-and-promotion@1` in `semantics/contracts.yaml` operationalizes the universal admission prerequisites that `semantics/authority_model.yaml#admission_rules.global_requirements` owns, and that `l9.authority/product-admission` inherits. v3.13.0 shipped with the contract's base `requires` drifted from that authority list in two ways: one requirement carried a stale spelling (`…reusing_a_prior_decision…` where the authority model says `…reusing_prior_decision…`), and a conditional cross-domain evidence obligation (`independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence`) sat in the unconditional base list although no authority-model requirement admits it there.

v3.14.0 does not create the product admission authority. That happened in v3.13.0, which remains unchanged. This release aligns the contract that consumes the same base requirement set.

## Bounded delta

- `semantics/contracts.yaml`, `l9.contract/admission-and-promotion@1` only: its `requires` sequence now equals `authority_model.yaml#admission_rules.global_requirements` exactly, six requirements in the authority model's order. The stale spelling is replaced by the canonical identifier. The cross-domain witness entry is removed from the unconditional base `requires` list and preserved verbatim as the conditional guarantee `independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence`. No other guarantee changes, and `id`, `purpose`, `scope`, `owner`, `source_invariants`, `applies_to`, `forbidden` and `outcomes` are byte-identical to v3.13.0. A universal admission prerequisite is not the same thing as a conditional recurrence evidence obligation: the six prerequisites bind every admission, while independent domain witnesses remain required whenever cross-domain recurrence is asserted as admission evidence, and are not a prerequisite of an admission that asserts no recurrence. The relocated guarantee sits beside the existing `cross_domain_recurrence_claims_are_evidence_bound_when_used_to_support_higher_scope_admission` and `recurrence_or_validation_creates_no_implicit_promotion`, the prohibitions `treating_recurrence_as_global_admission` and `treating_hypothetical_reuse_repeated_assertion_or_single_domain_repetition_as_cross_domain_recurrence`, and the cited invariant `L9-GLOBALIZATION-001`.
- Adds RC-022 to `scripts/validate-semantics.py`. RC-022 proves the contract's base `requires` equals the live authority-model sequence exactly and that the conditional recurrence law, the relocated witness guarantee included, stays declared, with a negative-case batch that fails closed. The witness token therefore fails RC-022 if it re-enters `requires` and fails RC-022 if it leaves `guarantees`. RC-021 keeps ownership of the product-admission authority identity and the pinned inherited law.
- Refreshes only the derivation digests in `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, and `semantics/receipt_catalog.yaml` that the new `contracts.yaml` bytes made stale (RC-001, RC-002, RC-011). Their semantic payload is unchanged.

## Non-goals

v3.14.0 adds no invariant, contract, schema, semantic source, authority coordinate, ProductKind, vocabulary term, receipt family or ADR. It does not change `semantics/authority_model.yaml`, which is the side already pinned by RC-021 and consumed by the canonical product-admission declaration. It does not widen the product-admission subjects, redefine cross-domain recurrence, weaken globalization law, change lifecycle or identity law, or alter ProductTopology, ProductManifest, admission receipt ownership or admission decision authority. It modifies no downstream consumer: a consumer whose `admission.subject` names a subject the authority model does not declare aligns in separate downstream work.

## Authority

`Quantum-L9/.github` owns the global authority model and the global contract catalog. The authority model owns the universal admission prerequisites; the contract consumes them. Recurrence or pattern recognition may justify a globalization candidate but never creates global law (`L9-GLOBALIZATION-001`); evidence of cross-domain recurrence, from independent domain witnesses, is therefore an obligation only when such recurrence is actually asserted, not a prerequisite of every admission. This release preserves and correctly places that existing law; it creates no new globalization law.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.13.0/` (product admission authority identity). That release record is unchanged.
