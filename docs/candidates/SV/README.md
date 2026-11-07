# Strategic Value @1: irreducible `.github` admission candidate

**Status:** LOCAL CANDIDATE, not canonically admitted (`LOCAL_CANDIDATE_NOT_CANONICALLY_ADMITTED`). **Target:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397`, exact pinned revision. **Donor:** `Quantum-L9/l9-wip#6@fb0ae95620cea0dc3f48aa009056ddb755d69640`.

## Decision realized in this package

The proposal retains **eight** candidate global invariants: foundational `L9-SV-001` and `L9-SV-002`, plus `L9-SV-015..020`. The twelve remaining original candidate meanings (`003..014`) survive, with exact original statements and placement, as conditionally applicable `strategic_value_model.yaml#retained_former_candidate_semantics` and assessment-contract obligations. **These were candidate IDs, not existing admitted laws.** See `IRREDUCIBILITY_DISPOSITION.md`.

The contract `l9.contract/strategic-value-assessment@1` now applies **only** to an assessment making a material, applicable, objective-relative quantitative **Strategic Value claim**. It does not impose Strategic Value mathematics on unrelated Numerical Reasoning, generic decision evaluations or unrelated planning tasks. Probability and Q/V-specific obligations apply only when that method is selected and material to the claim.

The mathematical accounting identity is preserved:

`SV = ImmediateExpectedValue + SystemicFutureValue - DirectCost - ExpectedRiskLoss - OpportunityCost`, with one exclusive, exhaustive causal accounting partition across material consequences. A supported discounted counterfactual future-utility formulation and optional bounded Q/V lookahead are specified in `PR6_MATHEMATICAL_ALIGNMENT.md`.

## Canonical projection and composition definitions

**One value source model:** `l9.strategic.value@1`.

**Projection profile:** `l9.projection/strategic-planner-value@1`, selecting five independently authoritative source classes (`strategic_value_model`, `vocabulary`, `invariants`, `contracts`, `authority_model`).

**Projection payload schema:** `semantics/strategic_planner_value_projection.schema.yaml`, identifying payload version **`l9.projection.strategic-planner-value/v1`**. The schema describes the allowed bounded shape for one selected source class, not one super-projection of all five. It has typed bounded record structures. True source selection equivalence and compiler provenance require a real producer replay.

**Composition profile:** `l9.compose/strategic-planner-value@1`, a `source_class_namespace` exact-coverage composition of the five source projections.

**Composition payload schema:** `semantics/strategic_planner_value_composition.schema.yaml`, version **`l9.composed-projection.strategic-planner-value/v1`**. Namespacing preserves independent source identity; it does not grant numerical, canonical, planning, or execution authority.

Both schema names are added to `.github`'s existing `generic_compiler_manifest.yaml` **artifact_schemas** inventory. No parallel schema registry or solver is introduced.

## Proposed `.github` edits (10 destination paths)

| Action | Proposed repository path |
| --- | --- |
| NEW | `semantics/strategic_value_model.yaml` |
| NEW | `semantics/strategic_planner_value_projection.schema.yaml` |
| NEW | `semantics/strategic_planner_value_composition.schema.yaml` |
| UPDATE | `semantics/invariants.yaml` (eight candidate IDs only) |
| UPDATE | `semantics/contracts.yaml` (claim-scoped assessment contract and invariant derivation digest) |
| UPDATE | `semantics/vocabulary.yaml` (eleven terms) |
| UPDATE | `semantics/canonical_sources.yaml` (one value-model source) |
| UPDATE | `semantics/projection_profiles.yaml` (value source class and projection profile) |
| UPDATE | `semantics/composition_profiles.yaml` (one versioned composition profile) |
| UPDATE | `semantics/generic_compiler_manifest.yaml` (model and both schema registrations) |

The archive contains candidate source overlays, schema files, application utility, decision ledger and executable tests; not a modified live repository checkout. No Skill is included.

## Runnable checks

`python tests/run_strategic_value_falsifiers.py` executes six independent bad/control pairs (one by one with `--case SV015` through `SV020`). Failing a negative witness or a positive control exits nonzero. `python -m unittest discover -s tests -v` executes the full local candidate structural, schema, overlay and falsification tests. Python's standard library runs the falsifier; `PyYAML` is required by the YAML/schema/overlay tests and patch script.

The local tests prove only asserted candidate semantics and finite falsification discriminability, **not** official schema-compiler acceptance, real source freshness, forecasts or empirical adequacy. A new native-compiler regression runner fails closed when `l9_semantic_compiler` is unavailable; see `SCHEMA_QUALIFICATION_REVIEW.md`. The two schema definitions bind all 21 normative booleans to exact source constants and convert 31 minimum-length string-list declarations in each schema to dialect-enforced typed arrays.

## Apply only in a clean, pinned local checkout

```bash
python apply_to_pinned_checkout.py --checkout /path/to/Quantum-L9/.github
python apply_to_pinned_checkout.py --checkout /path/to/Quantum-L9/.github --apply
```

The script demands the exact frozen `BASE_SHA` and clean worktree, rejects ID and schema collisions and writes locally only. If main moves, re-resolve authority and review before proposing a new patch. Never weaken the pin to get a green run.

## Qualification status and remaining findings

See `SCHEMA_QUALIFICATION_REVIEW.md` for resolved schema weaknesses, current native interpreter evidence and outstanding producer/consumer proof. `IRREDUCIBILITY_OWNER_REVIEW.md` challenges all eight pending constitutional candidates, especially SV-019 and SV-020 against existing global Unknown/evidence/assurance law. The complete ZIP contains six purpose-built executable falsifiers; **these are not numerical-consumer integration tests**.

## Gates still requiring the authorized canonical owner

1. Resolve semantic owner and independently adjudicate irreducibility of the eight retained invariant candidate IDs, including whether `015` overlaps `001` or `019` overlaps existing uncertainty law.
2. Validate the new source, projection/composition profile selectors, schema matching/selection equivalence, inventory and required semantic-foundation release metadata with `.github` native tools.
3. Publish only through the repository-governed PR path. Do not claim admission, self-merge, publisher bypass, five real compiler PASS receipts or live Planner binding from this ZIP.
4. After formal admission and exact successor revision, compile **five** real per-source projections and the composition, obtain valid provenance/receipts, independently replay, then permit the downstream consumer to bind.
5. Any strong numerical forecast claim separately requires applicable, **independently reviewable model-validation evidence**, not mathematical proof of empirical adequacy.

**No remote GitHub changes, PR, merge, canonical admission, production deployment, official producer projection, or genuine PASS receipts are claimed.**
