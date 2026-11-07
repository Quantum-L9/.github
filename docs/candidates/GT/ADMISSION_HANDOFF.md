# Admission handoff: SV + GT core, then the GT+SV contract

**This pack is a candidate. It makes no canonical change and admits nothing.**

## Successor release A — SV + GT core

Contents: the reduced SV candidate (PR #215) plus `L9-GT-001`, twelve GT terms, the GT core contract, the GT projection and composition profiles, the GT forbidden-criterion definition, and both GT payload schemas with their manifest registration. The GT+SV dependent contract is **not** in release A.

Canonical destination paths, as derived from the resolved target (`evidence/integration-v1/rehearsal.json`), are **15**, not the 12 the remediation spec estimated. The extra three are the derived ledgers `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml`, whose recorded digests of `invariants.yaml` and `contracts.yaml` must be rebound (as Semantic Foundation v3.8.0 did in `2ae5dfa`):

`invariants.yaml`, `contracts.yaml`, `vocabulary.yaml`, `canonical_sources.yaml`, `projection_profiles.yaml`, `composition_profiles.yaml`, `generic_compiler_manifest.yaml`, `strategic_value_model.yaml`, `strategic_planner_value_projection.schema.yaml`, `strategic_planner_value_composition.schema.yaml`, `strategic_interaction_projection.schema.yaml`, `strategic_interaction_composition.schema.yaml`, `capabilities.yaml`, `lifecycle.yaml`, `receipt_catalog.yaml`.

Gates the canonical owner must close:

1. Adjudicate `L9-GT-001` independently: it must not duplicate an existing global meaning. This is not done here.
2. Close the SV owner decisions listed in #215, including the amended `L9-SV-001` wording and whether `required_provenance` stays on `l9.compose/strategic-planner-value@1`. While it stays, the SV composition is `unknown` under compiler 0.9.3, so no GT+SV result can be evaluated.
3. Confirm that the three derived ledgers need digest rebinding only.
4. Prepare a successor semantic-foundation release record so SC-008 and SC-010 pass. The version is not chosen here.
5. Re-run the integrated rehearsal at the exact successor revision, and replay it under trust.

## Successor release B — GT+SV cross-boundary contract

1. Record the admitted release-A revision in `evidence/sv_alignment_binding.json#admitted_foundation_revision` through a reviewed commit.
2. Run `apply_to_pinned_checkout.py --stage dependent` on a clean checkout at exactly that revision. It refuses otherwise, and checks that the admitted SV model, SV contract, both SV invariants and GT core are present.
3. Separately authorize admission of `l9.contract/strategic-value-interaction-composition@1`.
4. Verify the combined Numerical Reasoning and consumer contract. `tools/verify_consumer_envelope.py` accepts an evaluated envelope only with receipt-backed view digests at equal coordinates and a numerical-evaluation receipt over both views. No Numerical Reasoning receipt type is admitted yet, so that part remains Unknown.

Admitting the dependent contract in release A, alongside the SV contract it depends on, would need the canonical authority to establish first that same-release dependency satisfaction is allowed. That permission cannot be inferred from the current contract.

## Consumer activation

Independent producer and consumer evidence is still required. A projection or composition receipt is never evidence of a numerical valuation or of an executed GT solver.
