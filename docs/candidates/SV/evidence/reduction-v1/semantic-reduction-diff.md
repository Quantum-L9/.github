# Semantic reduction diff: PR #212 (`85531616`) → two-invariant candidate

Generated deterministically by `tools/reduce_to_two_invariants.py` from `donor/` + `owner-disposition-ledger.yaml`. `--check` proves the committed files equal that output; `tests/test_reduction_closure.py::LosslessAgainstDonor` proves each file differs from its donor **only** in the places listed below.

| File | Change | Unchanged (tested) |
|---|---|---|
| `overlays/invariants_additions.yaml` | 8 → 2 entries. `L9-SV-001` statement replaced by the ledger's amended text; `L9-SV-015..020` removed | `L9-SV-002` statement, scope and owner |
| `overlays/contracts_additions.yaml` | `source_invariants`: 8 candidate IDs → the 12 governing IDs | every `requires`, `guarantees`, `forbidden`, `outcomes`, `applies_to` and `applicability` entry, and `id`, `purpose`, `scope`, `owner` |
| `semantics/strategic_value_model.yaml` | `governed_by.invariants`: 15 → 12 (adds EVIDENCE-001, ASSURANCE-001, COORD-001; removes SV-015..020); new top-level `relocated_additional_candidate_semantics` (6 records) | all other sections, including the six `evaluation_integrity` subsections and `retained_former_candidate_semantics` |
| `overlays/projection_profile_additions.yaml` | invariant selectors 15 → 12; model selector `$.relocated_additional_candidate_semantics` added after `$.retained_former_candidate_semantics` | profile id, consumer, purpose, output schema, vocabulary/contract/authority selectors, forbidden list |
| `semantics/strategic_planner_value_projection.schema.yaml` | invariant `min_items` 15 → 12 and enum → 12 IDs; `governed_by.invariants.min_items` 15 → 12; lineage descriptor added | everything else, including the 21 boolean `const` pins |
| `semantics/strategic_planner_value_composition.schema.yaml` | same three changes inside the composed namespaces; lineage added to `strategic_value_model.required` and `properties` | everything else |
| `tests/falsification_cases.json` | `invariant_ref` → `origin_candidate_id`, `disposition`, `governing_invariants`, `contract_obligation`; description reworded | every negative/positive witness and expected failure code |

## Lineage record shape (one per relocated candidate)

```yaml
L9-SV-0NN:
  source_candidate_id: L9-SV-0NN
  meaning: <original PR #212 statement, verbatim>
  disposition: MERGE | CONTRACT | REUSE
  governing_invariants: [<subset of the 12 selected IDs>]
  model_section: evaluation_integrity.<subsection>
  contract_obligation: <unchanged contract requires entry>
  when: <applicability condition>
  authority_status: not_admitted_as_independent_invariant
```

## Applier changes (`apply_to_pinned_checkout.py`)

- Duplicate IDs inside incoming overlays and inside current canonical lists, plus their intersection, fail closed.
- Before the contracts derivation is rebound, the current `invariants.yaml` raw bytes must hash to the recorded digest, and the recorded count must match. Each substitution must happen exactly once and is read back.
- New: every `derivation.source_artifacts` entry naming a changed file is verified against the current canonical digest and item_count before it is rebound, iterated to a fixpoint (`capabilities.yaml` → `lifecycle.yaml`, `receipt_catalog.yaml`). A stale record fails closed.
- Assembled-candidate checks before any write: artifact IDs, exactly two new invariants, twelve unique resolvable governing IDs in model/contract/profile/schema enums, five source classes, model selectors resolve once, single source/schema registrations, schema ↔ profile/composition output identities, removed IDs only in lineage paths.
- `--apply` requires `--disposable` and refuses the checkout carrying the pack. `BASE_SHA` is unchanged.

## Deviations from the development pack (each recorded, none silent)

1. **Destination paths: 10 → 13.** Native validation of the pack-as-written failed RC-001/RC-002/RC-011 (`native-semantic-validation-before-derivation-rebind.log`). The three extra paths are digest-only rebinds, following the v3.8.0 precedent `2ae5dfa`.
2. **Synthetic fixture count: 3 → 12.** The section 10.4 single-invariant fixture cannot satisfy the section 10.1 requirement that every selected invariant resolve. The positive fixture carries the ten existing IDs. The single-invariant fixture is kept as a negative test (`test_unresolvable_governing_invariant_fails_closed`).
3. **Disposable target: linked worktree → throwaway clone accepted.** Governance denies a raw `git worktree add` on this surface. The applier guard is therefore "explicit `--disposable` and not the pack's own checkout".
4. **`projection-run2/`** holds a SHA-256 inventory, not duplicate bytes; every hash equals the committed run-1 file.
