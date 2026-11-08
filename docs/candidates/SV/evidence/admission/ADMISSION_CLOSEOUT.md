# Strategic Value admission closeout

## Statuses (kept separate)

| Status | State | Record |
| --- | --- | --- |
| Implementation | **COMPLETE** for the admission candidate | this file |
| Owner approval | **APPROVED** D1-D5, 2026-11-08 | `owner-decision.yaml` |
| Canonical admission | **NOT ADMITTED** — waits on the release queue (D5) | — |
| Post-merge trusted replay | **NOT RUN** — only possible after admission | — |

## Exact coordinates

| Coordinate | Value |
| --- | --- |
| Admission branch / PR | `Quantum-L9/.github` `agent/claude-code/sv-admission` — Quantum-L9/.github#222 (targets `main`; #218 merged, merge after #219 and the v3.29.0/v3.30.0 admissions) |
| Admission base (fetched `origin/main`) | `b085dba0533b22be24eebef80c99d8b520268afa` |
| Branch history | `f589e10` semantics and RC-033 on `9488d8f`; `7d9ca47` release record; `eeba4a1` RC-033 split for SonarCloud S3776; `5ec8d2d` merge of `main` after #218 landed (v3.30.0 / ADR-027; only `docs/adr/README.md` conflicted); `7f277aa` + `daca00e` release record regenerated from the refreshed merged state. Evidence first produced at `7d9ca47` and `eeba4a1` was regenerated at `daca00e` with identical results. The pack applier, re-pinned to `b085dba`, reproduces this `semantics/` tree byte for byte. |
| **Qualified candidate revision** | `daca00e0d03c2205ef1bf51753dff539093d3999` |
| `semantics/` tree at that revision | `f3c9c624db0905bd627a6a685eb5aa85477b981c` |
| Release candidate / ADR (provisional) | `v3.32.0` / `ADR-029`, selected by `tools/prepare_successor_release.py` from merged state at `b085dba` (next would be `v3.31.0` / `ADR-028`) skipping the claim of open #219; at `9488d8f` it skipped #218's and #219's |
| Producer | Quantum-L9/l9-semantic-compiler-engine#33, `agent/claude-code/required-provenance-criteria` at `33e4c5832bf73c7d9b0b70854af011e9582f1ab2` (base `18215ae`, version label 0.9.3) |

## Owner decisions realized

- **D1 (Option B).** `L9-SV-001` is the donor SV-001 statement followed by the donor SV-015 statement, both verbatim. `L9-SV-002` is unchanged. The six relocated safeguards and twelve earlier meanings keep their lineage and contract obligations. The regenerated outputs changed only `overlays/invariants_additions.yaml`. The two payload schemas carry no SV-001 text, so they are byte-identical, and the projection profile digest is unchanged (`sha256:0ccf2184…`).
- **D2 (R2).** Authority finding: the governing sources of the four tokens are `composition_profiles.yaml#global_rules.source_projection_provenance_required`, `composed_projection.schema.yaml` (`components[].projection_ref`, `projection_digest`; `composition_profile.ref`, `digest`) and `composition_engine_contract.yaml` (inputs `composition_profile_ref`, `composition_profile_digest`; guarantee `component_provenance_preserved`). By the established `forbidden_constraints` pattern, a declared constraint becomes mechanically evaluable only through a criterion its catalog declares. So R2 needs **both** a governed `.github` declaration and compiler enforcement:
  - `.github`: `composition_profiles.yaml#provenance_constraints` (`l9.provenance-constraint` v1, one criterion per token), the global rule `required_provenance_is_evaluated_only_through_declared_provenance_constraints`, and validator RC-033 with 8 negative cases. These ride in the SV successor release, so the authority dependency adds no delay. The R1 contingency was not invoked.
  - Compiler: evaluates only catalog-declared criteria. An undefined token stays unresolved, and an unknown language, criterion or parameter fails closed. Each criterion re-derives its fact from the verified components, the profile record and the authority revision.
- **D3.** On the freshly pinned base, `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml` changed only in derivation `sha256` and `item_count` (invariants 31→33, contracts 26→27). Native SC-004, RC-001, RC-002 and RC-011 pass.
- **D4.** An independent successor release, numbered from merged state by the tool and never typed in. Predecessor releases are byte-identical (checked by the tool and SC-008).
- **D5.** Merge order: v3.29.0 admission, #218 (v3.30.0, **merged 2026-11-08** as candidate; admission pending), #219 (v3.31.0, open), then SV, then GT core (#216), then the GT+SV dependent contract.

## Qualification at `daca00e` with compiler `33e4c58` (`qualification-daca00e/`)

| Check | Result |
| --- | --- |
| `make validate` / `make check` on the admission branch | exit 0 / exit 0; validator 59 PASS, no FAIL (SC-001..SC-010, RC-001..RC-033 incl. negative batches) |
| Five SV source projections | 5/5 **PASS** (`producer-summary.json`) |
| SV composition `l9.compose/strategic-planner-value@1` | **PASS**, exit 0, digest `sha256:7e93f3afe35bc5d628ac716952088bf02ddb1bef0c32fc6a1528f915108e38e7`; all 4 `required_provenance` criteria `pass` |
| Independent provenance verifier (no compiler imports) | **PASS**: all 8 checks; compiler result `pass`, no unresolved criteria; 5 PASS projection receipts at one revision (`provenance-verifier.json`) |
| Deterministic repeat | two runs, 29 artifact/composed/receipt/summary files byte-identical (`determinism.json`, `producer-run{1,2}.tar`) |
| Producer negative controls | 18/18 typed mechanisms matched: 16 negatives fail as asserted, 2 positives pass, order invariance holds (`producer-negative-controls.json`) |
| Native schema interpreter | 26/26 (`native-schema-qualification.json`) |
| Falsifiers, pack tests | pass |
| `l9.compose/stage-context@1` regression | all 4 `required_provenance` criteria `pass` (were `unresolved`) |
| `l9-projection-admission` gate (Quantum-L9/.github#221) | `RELEASED_CANDIDATE`: registration, validator and release coverage pass; not admitted, as expected |

Residual (not provenance): `l9.compose/stage-context@1` over the GAR projection still composes to `unknown` because of 8 `payload_schema` criteria. Neither the GAR components nor the stage-context output has a registered payload schema. This predates SV and is outside D2.

## Closeout checklist

| # | Item | State |
| --- | --- | --- |
| 1 | Composition provenance native criterion resolved | **DONE** (R2: catalog declaration + compiler criteria + RC-033) |
| 2 | Real composition receipt reports PASS | **DONE** at `daca00e` |
| 3 | SV-001 final wording approved and frozen | **DONE** (D1 Option B) |
| 4 | Eight dispositions authorized at exact digest | **APPROVED** (owner-decision.yaml; ADR-029 binds the final tree) |
| 5 | PR #215 merged into its staging branch | PENDING review (#220 stacks on it) |
| 6 | Overlay applied to freshly resolved main | **DONE** (`9488d8f`, then refreshed by merge to `b085dba`; applier re-pinned output and admission branch byte-identical) |
| 7 | Registry overlaps reconciled | **DONE** through #218 (merge refresh at `5ec8d2d`); #219 reconciles at its refresh (D5) |
| 8 | Successor release manifest and hash inventory | **DONE**, provisional identity v3.32.0 / ADR-029 |
| 9 | Native validation, five projections and composition PASS | **DONE** |
| 10 | Determinism and negative controls at final revision | **DONE** |
| 11 | Canonical admission PR approved and merged | OPEN — waits on D5 queue and owner merge |
| 12 | Admitted main read back and consumer replay | NOT RUN — after 11 |

## Shortest remaining path to merge

1. Merge the compiler PR (`required-provenance-criteria`) and, ideally, cut a compiler version. The final receipts pin the revision `33e4c58`.
2. Admit or withdraw v3.29.0 and v3.30.0 (#218 is merged as a candidate), then land #219.
3. Refresh the admission branch from `main` and re-run `apply_to_pinned_checkout.py` (re-pin through its guard). Then run `tools/prepare_successor_release.py` with no remaining `--queued` claims. It re-selects the release and ADR identity from the new merged state.
4. Re-run `tools/run_producer_qualification.py` twice, the verifier and the negative controls at the refreshed revision. Every coordinate changes, so this evidence must be regenerated.
5. Owner admits: ADR status `Accepted`, the release status line flips to ADMITTED, and the hashes are regenerated (the ADR-025 precedent). Then merge to `main`.
6. Post-merge: run `l9-projection-admission` `--require downstream` on a clean `main` checkout, then consumer trusted replay.
