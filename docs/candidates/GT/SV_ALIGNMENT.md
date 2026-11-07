# GT alignment with the reduced Strategic Value candidate

**SV candidate:** PR #215 at `a64d05a152b5920dad577cead26618a6f05fef09`, stacked on PR #212 at `85531616cee2da94bbb7154418a78537549a4d76`. **Canonical target:** `020a94bea86e7c5c5e4107da7014ec259508f397`. **Machine record:** `evidence/sv_alignment_binding.json`.

| Coordinate | Value |
| --- | --- |
| New SV invariants | `L9-SV-001`, `L9-SV-002` |
| Lineage only (not invariants) | `L9-SV-015` … `L9-SV-020`, carried as model/contract obligations |
| SV governing set | twelve IDs (two new plus ten existing) |
| SV vocabulary | eleven terms |
| SV model | `l9.strategic.value@1` |
| SV contract | `l9.contract/strategic-value-assessment@1` |
| SV projection / composition | `l9.projection/strategic-planner-value@1` / `l9.compose/strategic-planner-value@1` |
| SV source classes | five: `strategic_value_model`, `vocabulary`, `invariants`, `contracts`, `authority_model` |
| Authority status | candidate, not admitted (both SV and GT) |

## How the binding is enforced

- The GT applier never resolves `main` or `HEAD`. Its core stage requires HEAD `020a94b` and a dirty set equal to the thirteen files the SV applier at `a64d05a` writes, each matching its pinned SHA-256. Those digests were reproduced in this session and equal the source digests in #215's own projection requests.
- The assembled candidate must contain exactly the two SV invariants, the SV contract, all eleven SV terms, the SV model and the five-class SV profile. A target carrying the eight-invariant PR #212 set is refused (`test_old_eight_invariant_sv_assumption_is_rejected`).
- No GT normative artifact (overlay, schema or consumer envelope) names `L9-SV-015`…`L9-SV-020`.
- The GT core contract cites no SV invariant. The dependent contract cites `L9-SV-001` and `L9-SV-002`.

## When #215 moves

Re-run the SV applier at the new head on a clean clone of the target, re-record `pack_blobs` and `sv_applied_target_sha256`, re-run the integrated rehearsal, and re-qualify. Never weaken the pin to obtain a green run.
