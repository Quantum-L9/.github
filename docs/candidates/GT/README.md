# Game Theory (GT) `.github` candidate, aligned to the admitted Strategic Value foundation

**Status:** LOCAL CANDIDATE, not canonically admitted. **Canonical target:** `Quantum-L9/.github@c9bbfaf61bd0f7444b1a617876a031c2fba75406` (`main`), carrying the **admitted** SV foundation v3.32.0 (ADR-029, #222). **SV dependency:** `L9-SV-001`, `L9-SV-002`, `l9.contract/strategic-value-assessment@1` and `l9.strategic.value@1` as admitted. **Alignment record:** `SV_ALIGNMENT.md`. **Remediation record:** `REMEDIATION_LEDGER.md`.

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
python -m unittest discover -s tests -v     # 94 local tests (PyYAML, jsonschema)
python apply_to_pinned_checkout.py --checkout <clean clone at c9bbfaf>   # dry run
```

## Integrated rehearsal (how the evidence was produced)

```bash
git clone https://github.com/Quantum-L9/.github reh && git -C reh checkout c9bbfaf   # admitted SV v3.32.0
python apply_to_pinned_checkout.py --checkout reh --apply --disposable
git -C reh add -- semantics && git -C reh commit -m REHEARSAL      # local only, never pushed
python reh/scripts/validate-semantics.py
python tools/run_integrated_qualification.py --authority-root reh --revision <commit> \
    --compiler-src <l9-semantic-compiler-engine@33e4c58>/src --out <dir>
python tools/gt_producer_negative_controls.py --authority-root reh --revision <commit> \
    --compiler-src <engine@33e4c58>/src --run1 <dir>/run1 --out controls.json
```

The core stage refuses unless HEAD is `c9bbfaf` and the tree is clean, the `semantics/` tree is the ADR-029 admitted tree, and the SV-owned files match their pinned digests. The dependent stage refuses until `admitted_foundation_revision` is recorded in `evidence/sv_alignment_binding.json` by a reviewed commit.

## Qualification status (`evidence/integration-v2/`, on the admitted SV foundation)

- Native `.github` validator on GT core over `c9bbfaf`: 56 checks pass. Only SC-008 and SC-010 fail, because the v3.32.0 release inventory does not list GT's files. That needs GT's own successor release record, which this pack does not invent.
- Real compiler `33e4c58` (the revision ADR-029 pins): GT's three projections and composition **pass**, and SV's five projections and composition **pass**, with all four `required_provenance` criteria now verified. All ten results are unconditional passes. Two runs were byte-identical.
- `evidence/integration-v1/` is the superseded record against the unadmitted SV #215 candidate on `020a94b`.
- The forbidden criterion was evaluated against 11 vocabulary, 2 invariant and 1 contract selections, and passed.
- 19 GT producer controls each produced their asserted exit code, typed failure and criterion.

## Compiler-generated candidate schemas (`synthesis/`)

`tools/synthesize_candidate_schemas.py` runs the real compiler's `schema-synthesize` (`l9-semantic-compiler-engine@33e4c58`) on GT core over the admitted SV foundation (`c9bbfaf`). It emits:

- `synthesis/generated/strategic_planner_interaction_projection.candidate.schema.json`
- `synthesis/generated/strategic_planner_interaction_composition.candidate.schema.json`

On two runs the compiler exited 0 with byte-identical output, and `schema-candidate-check` reported `candidate_digests_consistent`. The drafted source-field grammars are candidates for owner review. `--check` reproduces every output. See `synthesis/README.md`.

**No canonical admission, merge, release, canonical producer receipt or consumer binding is claimed.** Producer receipts bind to a local rehearsal commit that was never pushed. `PR212_*.md` and the `evidence/prior_*`, `pr212_*` and `authority_binding.json` files are the historical PR #212 record, left unchanged.
