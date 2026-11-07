# Game Theory (GT) `.github` candidate, aligned to the reduced Strategic Value candidate

**Status:** LOCAL CANDIDATE, not canonically admitted. **Canonical target:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397`. **SV dependency:** PR #215 at `a64d05a152b5920dad577cead26618a6f05fef09`, the two-invariant reduction (`L9-SV-001`, `L9-SV-002`) of PR #212. **Remediation record:** `REMEDIATION_LEDGER.md`.

GT governs conditional strategic interaction. SV governs value. Numerical Reasoning evaluates. Strategic Authority decides. This pack makes GT's actor-response semantics valid without SV, and shows that a GT result can be an input to exactly one canonical SV assessment, never an additive uplift.

## What the pack proposes

| Kind | Content |
| --- | --- |
| Invariant | `L9-GT-001` (owner adjudication pending) |
| Vocabulary | twelve GT terms, disjoint from the eleven SV terms |
| GT-only contract | `l9.contract/strategic-interaction-assessment@1`, governed by six invariants: `L9-GT-001`, `L9-AUTH-002`, `L9-HARD-001`, `L9-UNKNOWN-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001` |
| GT+SV contract (release B only) | `l9.contract/strategic-value-interaction-composition@1`, citing `L9-SV-001`, `L9-SV-002` and the assurance, provenance and coordinate laws |
| Projection | `l9.projection/strategic-planner-interaction@1`: vocabulary, invariants (exactly the six governing IDs) and contracts (the GT core contract only) |
| Forbidden criterion | `sv_semantic_records_excluded_from_gt_projection` (`payload_excludes` over the eleven SV terms, both SV invariants and the SV contract) |
| Composition | `l9.compose/strategic-planner-interaction@1`, `source_class_namespace`, exact coverage |
| Payload schemas | `strategic_interaction_projection.schema.yaml` and `strategic_interaction_composition.schema.yaml`, each with its `properties.schema.const` output discriminator |

The GT and SV compositions stay separate (three and five sources). The consumer envelope `schemas/gt_sv_consumer_assessment.candidate.schema.json` references both verified views plus an owner-produced numerical result. It is a candidate consumer contract, not a compiler composition schema; `tools/verify_consumer_envelope.py` checks what the schema cannot (receipt-backed digests, equal coordinates, real numerical evidence).

## Runnable checks

```bash
python -m unittest discover -s tests -v     # 77 local tests (PyYAML, jsonschema)
python apply_to_pinned_checkout.py --checkout <clone at 020a94b with SV #215 applied>   # dry run
```

## Integrated rehearsal (how the evidence was produced)

```bash
git clone https://github.com/Quantum-L9/.github reh              # HEAD 020a94b
python <SV pack @ a64d05a>/apply_to_pinned_checkout.py --checkout reh --apply --disposable
python apply_to_pinned_checkout.py --checkout reh --apply --disposable
git -C reh add -- semantics && git -C reh commit -m REHEARSAL      # local only, never pushed
python reh/scripts/validate-semantics.py
python tools/run_integrated_qualification.py --authority-root reh --revision <commit> \
    --compiler-src <l9-semantic-compiler-engine>/src --out <dir>
python tools/gt_producer_negative_controls.py --authority-root reh --revision <commit> \
    --compiler-src <engine>/src --run1 <dir>/run1 --out controls.json
```

The core stage refuses unless HEAD is `020a94b` and the dirty paths are exactly the thirteen SV-applied files with their pinned digests. The dependent stage refuses until `admitted_foundation_revision` is recorded in `evidence/sv_alignment_binding.json` by a reviewed commit.

## Qualification status (`evidence/integration-v1/`)

- Native `.github` validator on the integrated candidate: 54 checks pass. Only SC-008 and SC-010 fail, because the v3.27.0 release inventory does not list the new files. That needs a successor release record, which this pack does not invent.
- Real compiler `3bf1a82` (0.9.3): GT three projections and the composition **pass**; SV five projections **pass**; SV composition **unknown**, because its four `required_provenance` declarations have no mechanical criterion (owner decision recorded in #215). Two runs were byte-identical.
- The forbidden criterion was evaluated against 11 vocabulary, 2 invariant and 1 contract selections, and passed.
- 19 GT producer controls each produced their asserted exit code, typed failure and criterion.

**No canonical admission, merge, release, canonical producer receipt or consumer binding is claimed.** Producer receipts bind to a local rehearsal commit that was never pushed. `PR212_*.md` and the `evidence/prior_*`, `pr212_*` and `authority_binding.json` files are the historical PR #212 record, left unchanged.
