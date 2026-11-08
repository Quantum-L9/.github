# Game Theory seam campaign closeout — 2026-11-08

Evidence for `L9-GT-SEAM-CAMPAIGN-CLOSEOUT-CONTRACT/v1`. Terminal states reached: **GT_CORE_ADMITTED_AND_VERIFIED**, **GT_SV_CONTRACT_ADMITTED_AND_VERIFIED**, **GT_SEAM_CAMPAIGN_COMPLETE**.

- **GT core:** Semantic Foundation v3.33.0 (ADR-030), effective at `a4bb461` (Quantum-L9/.github#225).
- **GT×SV contract:** v3.34.0 (ADR-031), effective at `05031a2` (#229).
- **Foundation:** both bind to the admitted Strategic Value foundation, v3.32.0 (ADR-029, `64d8b85`).

This directory records evidence and grants nothing. The admissions themselves are the ADRs and the release status lines on `main`.

| Record | What it shows |
|---|---|
| [`authority-resolution.json`](authority-resolution.json) | Who admitted, by what instruction, and the merge authority |
| [`pr-merge-ledger.json`](pr-merge-ledger.json) | #216, #226, #213, #225, #228 and #229: heads, merge commits, times |
| [`schema-authority-disposition.json`](schema-authority-disposition.json) | Native YAML schemas admitted; the synthesized JSON candidates stay evidence |
| [`canonical-diff-census.json`](canonical-diff-census.json) | Every file each admission brought to `main` |
| [`negative-controls-matrix.json`](negative-controls-matrix.json) | The 19 producer controls at four revisions, plus each Article 9 case and its mechanism |
| [`gt-core/`](gt-core/) | Producer qualification at `f03f859`; post-merge producer, controls, native validation and the `--require downstream` gate at `a4bb461` |
| [`gt-sv/`](gt-sv/) | Qualification and controls at `b091628`, consumer-envelope evidence, and the post-merge replay, validation and gate at `05031a2` |
| [`campaign-final-receipt.json`](campaign-final-receipt.json) | Identities, coordinates, verification results, numerical-evaluator status and outstanding dependencies |

The owner-decision record is [`../admission/gt-owner-decision.yaml`](../admission/gt-owner-decision.yaml). The bindings are [`../admitted_sv_binding.json`](../admitted_sv_binding.json) (release A) and [`../admitted_foundation_binding.json`](../admitted_foundation_binding.json) (release B). The historical records (`../integration-v1/`, `../sv_alignment_binding.json`, `../pr212_*`) are retained and are not admission evidence.

Producer of record for every run here: `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891`. The gate JSONs contain sandbox paths that are not portable.

**Numerical evaluator: not active.** No Numerical Reasoning receipt type is admitted, so a GT×SV consumer envelope that claims an evaluated result is refused.
