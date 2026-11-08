# Admission handoff: SV + GT core, then the GT+SV contract

**This pack is a candidate. It makes no canonical change and admits nothing.**

## Done: Strategic Value admitted (v3.32.0)

SV was admitted on its own as Semantic Foundation v3.32.0 (ADR-029, #222, `64d8b85`), following ADR-029 D5's sequential order. GT is now bound to that admitted foundation (`SV_ALIGNMENT.md`, `evidence/sv_alignment_binding.json` v3). The superseded plan to admit SV and GT core together as "release A" no longer applies.

## Next successor release — GT core on the admitted SV foundation

Contents: `L9-GT-001`, twelve GT terms, the GT core contract, the GT projection and composition profiles, the GT forbidden-criterion definition, and both GT payload schemas with their manifest registration. The GT+SV dependent contract is **not** in this release.

Canonical destination paths on `c9bbfaf`, derived from the rehearsal (`evidence/integration-v2/rehearsal.json`): **11**. These are `invariants.yaml`, `contracts.yaml`, `vocabulary.yaml`, `projection_profiles.yaml`, `composition_profiles.yaml`, `generic_compiler_manifest.yaml`, `strategic_interaction_projection.schema.yaml` and `strategic_interaction_composition.schema.yaml`, plus the derived ledgers `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml`, whose recorded digests are rebound. No admitted SV-owned file changes.

Gates the canonical owner must close:

1. Adjudicate `L9-GT-001` independently: it must not duplicate an existing global meaning. Independent review recommends moving it into the GT core contract, governed by `L9-UNKNOWN-001`, `L9-EVIDENCE-001` and `L9-ASSURANCE-001`, the same test SV applied to SV-015..020. This is not done here.
2. Confirm that the three derived ledgers need digest rebinding only, as ADR-029 D3 did for SV.
3. Prepare a successor semantic-foundation release record so SC-008 and SC-010 pass. Number it from the merged state, as ADR-029 D4 does; the version is not chosen here.
4. Re-run the rehearsal at the exact successor revision, and replay it under trust.
5. Review the compiler-generated candidate schemas and their drafted grammars in `synthesis/` (`schema-synthesize` at `33e4c58`, exit 0, deterministic). Approve, amend or reject the grammars, and decide whether the candidate schemas replace or accompany `semantics/strategic_interaction_*.schema.yaml`. Then re-run `tools/synthesize_candidate_schemas.py` against the admitted revision with the approved grammars.

## The release after — GT+SV cross-boundary contract

1. Record the revision that admits GT core in `evidence/sv_alignment_binding.json#admitted_foundation_revision` through a reviewed commit.
2. Run `apply_to_pinned_checkout.py --stage dependent` on a clean checkout at exactly that revision. It refuses otherwise, and checks that the admitted SV model, SV contract, both SV invariants and GT core are present.
3. Separately authorize admission of `l9.contract/strategic-value-interaction-composition@1`.
4. Verify the combined Numerical Reasoning and consumer contract. `tools/verify_consumer_envelope.py` accepts an evaluated envelope only with receipt-backed view digests at equal coordinates and a numerical-evaluation receipt over both views. No Numerical Reasoning receipt type is admitted yet, so that part remains Unknown.

Admitting the dependent contract in release A, alongside the SV contract it depends on, would need the canonical authority to establish first that same-release dependency satisfaction is allowed. That permission cannot be inferred from the current contract.

## Consumer activation

Independent producer and consumer evidence is still required. A projection or composition receipt is never evidence of a numerical valuation or of an executed GT solver.
