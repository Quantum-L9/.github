# GT alignment with the admitted Strategic Value foundation

**SV foundation:** admitted as Semantic Foundation **v3.32.0** (ADR-029, Quantum-L9/.github#222, merge commit `64d8b8598300f94c3201f26866f73be6895dab60`). **Canonical target:** `main` at `c9bbfaf61bd0f7444b1a617876a031c2fba75406`, whose `semantics/` tree `251bb3d9238f93f0207b1f8443c80359e034595b` is the admitted tree. **Machine record:** `evidence/sv_alignment_binding.json` (schema v3).

| Coordinate | Value |
| --- | --- |
| SV invariants | `L9-SV-001` (the original SV-001 statement followed by the original SV-015 statement, verbatim; ADR-029 D1) and `L9-SV-002` |
| Lineage only (not invariants) | `L9-SV-015` … `L9-SV-020`, carried as model text and contract obligations |
| SV governing set | twelve IDs (two new plus ten existing) |
| SV vocabulary | eleven terms |
| SV model | `l9.strategic.value@1` |
| SV contract | `l9.contract/strategic-value-assessment@1` |
| SV projection / composition | `l9.projection/strategic-planner-value@1` / `l9.compose/strategic-planner-value@1`; `required_provenance` is evaluated through `composition_profiles.yaml#provenance_constraints` (ADR-029 D2) |
| SV source classes | five: `strategic_value_model`, `vocabulary`, `invariants`, `contracts`, `authority_model` |
| Authority status | SV admitted (v3.32.0); GT candidate, not admitted |

## How the binding is enforced

- The GT applier never resolves `main` or `HEAD`. Its core stage requires:
  - HEAD `c9bbfaf` and a clean tree;
  - the `semantics/` tree equal to the admitted tree;
  - the three SV-owned files (`strategic_value_model.yaml` and both SV payload schemas) at their pinned digests.
- The assembled candidate must contain exactly the two SV invariants, the SV contract, all eleven SV terms, the SV model and the five-class SV profile. A target carrying the eight-invariant PR #212 set is refused.
- No GT normative artifact (overlay, schema or consumer envelope) names `L9-SV-015`…`L9-SV-020`.
- The GT core contract cites no SV invariant.
- The dependent GT+SV contract cites `L9-SV-001` and `L9-SV-002`. It applies `l9.contract/strategic-value-assessment@1` **by reference**: every `requires` entry is satisfied by reference, and every `forbidden` entry is respected by reference. Restating, paraphrasing or weakening SV obligations in GT contracts is itself forbidden.
  - Before alignment, this contract restated five SV obligations in its own words: counterfactual identification, welfare aggregation, nonanticipativity, once-only weighting and preference reversal.
  - One of those restatements had drifted: "declared" welfare aggregation where SV says "authorized".
  - `test_dependent_contract_reuses_sv_obligations_by_reference` keeps the paraphrases out.

## Evidence on the admitted foundation (`evidence/integration-v2/`)

- **Rehearsal:** GT core applied to clean `c9bbfaf` changes eleven canonical files and none of the SV-owned files.
- **Native validator:** 56 checks pass. Only SC-008 and SC-010 fail, because the v3.32.0 release inventory does not list GT's files; that needs GT's own successor release record.
- **Real compiler `33e4c58`** (the revision ADR-029 pins): all ten results pass. These are GT's three projections plus its composition, and SV's five projections plus its composition, now with the provenance criteria verified. Two runs were byte-identical.
- **Producer controls:** all 19 GT controls matched their asserted mechanism.

## When main moves

Re-record `canonical_target` and `canonical_target_semantics_tree` from the new `main`. Confirm the admitted SV-owned files are unchanged, then re-run the rehearsal, qualification, controls and synthesis. Never weaken the pin to obtain a green run.

## History

`superseded_bindings[0]` keeps the v2 binding to the unadmitted SV candidate, PR #215 at `a64d05a`, on `020a94b`, together with its 13 SV-applied digests and `evidence/integration-v1/`. The SV-owned files admitted in v3.32.0 are byte-identical to that candidate's. `invariants.yaml` differs because ADR-029 D1 rejected the development-pack amendment of `L9-SV-001`.
