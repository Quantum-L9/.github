> **Historical (PR #212 @ `85531616`).** Superseded by `SV_ALIGNMENT.md`, which binds GT to the reduced SV candidate in PR #215 @ `a64d05a`. Kept unchanged below as the record of the first alignment.

# PR #212 alignment: bounded break-test results

**Local outcome:** 12/12 selected attacks pass local synthetic controls. **Formal status:** BLOCKED pending independent invariant-owner decisions, real current-source checkout and compiler validation; this is not an independent Break Tester producer receipt.

- **GT212-01** Canonical vocabulary identity collision: Repaired by distinct incentive_bearing_commitment; canonical Plan strategic_commitment unchanged (`test_canonical_plan_commitment_collision_repaired`)
- **GT212-02** SV term and invariant duplication: Zero exact GT/SV terms and global invariant IDs intersect (`test_sv_specific_terms_and_invariants_not_copied`)
- **GT212-03** Three-source GT vs five-source SV profiles: Independent source-namespaced semantic views; no profile mixing (`test_gt_profile_and_sv_profile_are_separate_named_views`)
- **GT212-04** GT-only hidden SV dependency: Unquantified GT claims do not need admitted SV (`test_gt_contract_independent_of_value_and_non_universal`)
- **GT212-05** SV-dependent assessment falsely activated at PR212: No evaluated output without admitted SV and real references (`test_unresolved_sv_does_not_fabricate_sourcerefs_or_numbers`)
- **GT212-06** False synthetic evaluated claim without accounting: Structured consumer candidate rejects missing SV accounting receipt (`test_evaluated_requires_accounting_and_compatible_refs`)
- **GT212-07** Canonical Plan action authority escape: Source contract disallows GT-driven plan revision and execution (`test_no_new_valuer_or_permission`)
- **GT212-08** Source-class omission or profile source collision: Missing GT source class invalid in local schema (`test_composition_fails_closed_without_namespace`)
- **GT212-09** Manipulated source identity in consumer envelope: Consumer references two composed views with exact expected identities (`test_consumer_refs_compositions_not_single_per_source_projections`)
- **GT212-10** Passive-world value not affected: Expected value unchanged in degenerate response distribution (`test_passive_world_matches_sv_only`)
- **GT212-11** Response reverses plan ranking: A action changes 1000 to 760, B 800 wins; no additive GT uplift (`test_gt_response_can_reverse_plan_ranking`)
- **GT212-12** Stable softmax misrepresented as Nash: Stationary update not sufficient for near-zero unilateral deviation gap (`test_softmax_fixed_point_is_not_nash_proof`)

## Owner gates before canonical admission

- Resolve SV PR #212 global-invariant irreducibility and exact admitted successor first; new GT global invariant may specialize an existing SV requirement and is not admitted by this test.
- Run real native schema interpreter against two GT schema YAMLs (the local JSON Schema tests are not equivalent), source selector equality and exact 3-source GT composition.
- Compile real GT source projections and valid composition, and independently validate receipts and source provenance.
- Admit GT alone separately; only after SV is independently admitted may a GT+SV dependent contract and combined numerical assessment be accepted.
- Prove numerical method and consumer behavior separately from semantic projection.
