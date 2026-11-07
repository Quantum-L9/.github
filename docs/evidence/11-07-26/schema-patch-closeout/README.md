# Projection schema patch closeout: head-bound receipt

Contract: `L9-PROJECTION-SCHEMA-PATCH-CLOSEOUT-01`. This directory is appended evidence. It supersedes nothing in `../authority-resolution/` or `../projection-qualification/`. Those results, including the recorded `string_list` `min_items` capability **FAIL**, keep their original bytes and timestamps.

## Coordinates

| Item | Value |
|---|---|
| Authority commit qualified | `Quantum-L9/.github@453701a671b3c9acc3400c47c926d1235adfeffd` (PR #214 branch) |
| `semantics/` tree | `7c6f35ddc701e6913c78054745e1e2179775299f` |
| #211 head carrying its two schema patches | `8cfae84` (`semantics/authority_resolution_{projection,composition}.schema.yaml`) |
| #214 commits | `929edd9` merges `8cfae84` (no rebase); `453701a` patches the 18 derived schemas; `530fe93` updates the v3.28.0 release record (documentation only; `semantics/` tree unchanged) |
| Pre-patch #214 head | `1e9cb8b01fce2920aa999a25818c54d0ee70cff3`, `semantics/` tree `d955349ec6d9359687aa0323e3a9b26836c466ac` |
| Compiler | `Quantum-L9/l9-semantic-compiler-engine@943db9a462d35ba66771a700ece77c746295f591` (`git archive`, unmodified), `l9-semantic-compiler` 0.9.3, CPython 3.12.13 |

The compiler revision is unchanged from #210/#211. It was not modified, and `schema-derive` / `schema-synthesize` were not run.

## Files

| File | Content |
|---|---|
| `qualification-summary.json` | Positive, negative and PATCH-01 equivalence results for all ten pairs (run A) |
| `independent-replay-summary.json` | Positive-only run B, from a separate clone at the same revision, in a separate process and output root |
| `reproducibility.json` | Per-profile byte comparison of run A and run B emitted files |
| `patch01-ledger.json` | Every removed `string_list` `min_items` (file, YAML path, value) |
| `constraint-classification.json` | Every retained `required`/`const`/`enum`/array `min_items` constraint with its basis class |
| `exclusion-ledger.json` | The seven source-field exclusions, with artifact and receipt coordinates |
| `make-validate.log`, `make-check.log` | Gates at `530fe93` (PR #214 head) |
| `harness.zip` | `qualify.py`, `patch01.py`, `classify.py`, `scan.py`, byte-exact as run. Archived like the earlier harnesses in this directory, because they are diagnostic tools and not repository source |

Absolute paths inside the JSON files are the original sandbox paths. They are not repository paths.

## Results

| Gate | Outcome |
|---|---|
| A. Schema completeness | 20 of 20 registered schemas present, patched in place, none replaced |
| B. Validator truthfulness | 381 unenforced `string_list` minimums removed (18 hand-authored, 363 derived), each proven behavior-neutral. 0 unsupported descriptors remain. The 49 retained array `min_items` are enforced, with 33 negative cases |
| C. Source correctness | 7 of 7 exclusions accounted for. Every other field is selected in source order, and no payload carries the source `schema` value. Consumer impact is **Unknown**. Owner disposition is **UNRESOLVED** |
| D. Producer qualification | 10 of 10 pairs PASS: 53 projections and 10 compositions, independently re-verified, 63 receipts valid. 461 of 461 negatives as intended. 126 of 126 files byte-identical on independent replay |
| E. Release closure | `make validate` exit 0 (57 PASS, 0 FAIL); `make check` exit 0. Current-head CI is reported on the PRs |
| F. Governance | Candidate only. A blocking owner decision is open |

## Remaining Unknowns

- Whether any declared consumer (`l9-identity-assurance`, `strategic_plan_metacognitive_reasoner`, `plan_keeper`) needs the excluded `schema` marker.
- Independent consumer replay for all ten profiles.
- Whether any removed hand-authored authority-resolution minimum is governed.

## Disposition

**BLOCKED_SEMANTIC_DECISION.** The seven-field narrowing in `identity-assurance@1`, `strategic-metacognition@1` and `strategic-planning-context@1` (`semantics/projection_profiles.yaml`) needs semantic-owner acceptance. That acceptance is required by the contract's PATCH-03 and acceptance gate F. Producer qualification and validator truthfulness are not blocked.

## Upstream defect inventory (for the separate l9-semantic-compiler-engine assignment)

These are evidence only. No compiler change was made.

| # | Defect | Evidence | What must change |
|---|---|---|---|
| D1 | `schema-derive` emits `min_items` under `type: string_list` | 363 descriptors in the 18 derived schemas (`patch01-ledger.json`) | Stop emitting list cardinality on any list type the interpreter does not enforce |
| D2 | The v1 interpreter ignores unsupported descriptor keys silently | `passes/validate.py` `schema_violations` reads `min_items` only for `type == "array"`. The #210 capability check FAIL | Enforce cardinality for every list type, or reject a descriptor key it does not implement (fail closed) |
| D3 | `schema-derive` emits observation-only constraints with no per-constraint basis | 3,970 pinned-snapshot constraints, recorded only by one document-level `derivation.basis` | Distinguish governed constraints (profile output, selectors, composition classes) from observed ones, or emit only governed ones by default |
| D4 | Wholly selected arrays get an `enum` of today's ids | `identity_assurance_*` `actors`/`surfaces`, `architecture_break_test_*` `rules` | Emit an `id` enum only when membership is fixed by id-filter selectors |
| D5 | v1 dispatch by `properties.schema.const` collides with a selected source's own `schema` field | Seven `$` selections had to be narrowed (`exclusion-ledger.json`) | A dispatch rule that does not share the payload's `schema` key, decided upstream and by the semantic owner |
| D6 | No item shape can be derived for an array that is empty at the derivation revision | 12 hand-authored constraints not reproduced in the earlier #214 control | Report these as unresolved instead of omitting them silently |
