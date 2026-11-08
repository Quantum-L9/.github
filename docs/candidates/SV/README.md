# Strategic Value @1: two-invariant `.github` admission candidate

**Status:** LOCAL CANDIDATE, not canonically admitted (`LOCAL_CANDIDATE_NOT_CANONICALLY_ADMITTED`). **Target:** `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397`, exact pinned revision. **Source candidate:** PR #212 at `85531616cee2da94bbb7154418a78537549a4d76`. **Reduction:** `SV-CONSTITUTIONAL-REDUCTION-DEV-PACK-v1`. **Donor:** `Quantum-L9/l9-wip#6@fb0ae95620cea0dc3f48aa009056ddb755d69640`.

## Decision realized in this package

The proposal now carries **two** new global Strategic Value invariants: `L9-SV-001` (amended to absorb the counterfactual identification safeguard formerly proposed as `L9-SV-015`) and `L9-SV-002` (unchanged). Every other candidate meaning is kept as traceable text:

- `L9-SV-003..014` (twelve meanings) stay in `strategic_value_model.yaml#retained_former_candidate_semantics`, unchanged.
- `L9-SV-015..020` (six meanings) move to `strategic_value_model.yaml#relocated_additional_candidate_semantics`. Each record keeps the original PR #212 statement verbatim, its disposition (MERGE, CONTRACT or REUSE), its model section, its unchanged assessment-contract obligation, its applicability condition and the existing global invariants that now govern it.

`L9-SV-015..020` are **historical candidate identifiers and falsifier-case lineage, not admitted or proposed invariants.** They appear in no invariant selector, `source_invariants`, `governed_by` list or schema enum; the tests and the applier enforce that mechanically. The six relocated meanings are governed by existing law: `L9-UNKNOWN-001` (SV-019), and `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-PROV-001`, `L9-COORD-001` (SV-020), plus the two new invariants. See `IRREDUCIBILITY_DISPOSITION.md` and `evidence/reduction-v1/owner-disposition-ledger.yaml`.

The amended `L9-SV-001` wording is a **material semantic change that needs explicit owner review**. Independent review classifies it as a weakening of both the original SV-001 consequence clause and the SV-015 safeguard. It narrows the clause to "causally attributed" rankings and to claimed causal effects, and replaces "quantify" with "identified and justified". The ledger records each point and a non-weakening alternative, and keeps the mandated text until the owner decides. The other five relocations keep their meaning verbatim, with normative force through unchanged contract obligations.

The contract `l9.contract/strategic-value-assessment@1` still applies **only** to an assessment making a material, applicable, objective-relative quantitative Strategic Value claim. Its `source_invariants` now name the twelve governing invariants; every `requires`, `guarantees`, `forbidden`, `outcomes` and `applicability` entry is byte-for-byte the PR #212 text (tested against the frozen donor).

The mathematical accounting identity is unchanged:

`SV = ImmediateExpectedValue + SystemicFutureValue - DirectCost - ExpectedRiskLoss - OpportunityCost`, with one exclusive, exhaustive causal accounting partition across material consequences. See `PR6_MATHEMATICAL_ALIGNMENT.md`.

## Governing selection

| Kind | IDs |
| --- | --- |
| New (proposed) | `L9-SV-001`, `L9-SV-002` |
| Existing (resolved at `020a94b`) | `L9-AUTH-001`, `L9-AUTH-002`, `L9-HARD-001`, `L9-UNKNOWN-001`, `L9-STRATEGY-001`, `L9-PROJECTION-001`, `L9-PROV-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-COORD-001` |

The model's `governed_by.invariants`, the contract's `source_invariants`, the profile's invariant selectors and both payload-schema enums are exactly this set of twelve, each once. The real compiler's invariants projection selected the same twelve.

## Canonical projection and composition definitions

**One value source model:** `l9.strategic.value@1`.

**Projection profile:** `l9.projection/strategic-planner-value@1`, selecting five independently authoritative source classes (`strategic_value_model`, `vocabulary`, `invariants`, `contracts`, `authority_model`): 18 model sections (now including `relocated_additional_candidate_semantics`), 11 vocabulary terms, 12 invariants, 4 contracts and 5 authority-model sections.

**Projection payload schema:** `semantics/strategic_planner_value_projection.schema.yaml`, payload version **`l9.projection.strategic-planner-value/v1`**. It describes the bounded shape of one selected source class. Selection equivalence is proven separately by the producer.

**Composition profile:** `l9.compose/strategic-planner-value@1`, a `source_class_namespace` exact-coverage composition of the five source projections.

**Composition payload schema:** `semantics/strategic_planner_value_composition.schema.yaml`, version **`l9.composed-projection.strategic-planner-value/v1`**.

Prerelease identities are unchanged by the reduction.

## Proposed `.github` edits

| Action | Proposed repository path |
| --- | --- |
| NEW | `semantics/strategic_value_model.yaml` |
| NEW | `semantics/strategic_planner_value_projection.schema.yaml` |
| NEW | `semantics/strategic_planner_value_composition.schema.yaml` |
| UPDATE | `semantics/invariants.yaml` (two candidate IDs only) |
| UPDATE | `semantics/contracts.yaml` (claim-scoped assessment contract and invariant derivation digest) |
| UPDATE | `semantics/vocabulary.yaml` (eleven terms) |
| UPDATE | `semantics/canonical_sources.yaml` (one value-model source) |
| UPDATE | `semantics/projection_profiles.yaml` (value source class and projection profile) |
| UPDATE | `semantics/composition_profiles.yaml` (one versioned composition profile) |
| UPDATE | `semantics/generic_compiler_manifest.yaml` (model and both schema registrations) |
| DIGEST ONLY | `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml` (derivation records rebound) |

The last row is new in this reduction. Those three ledgers record the digests of `invariants.yaml` and `contracts.yaml` (and two of them of `capabilities.yaml`). The PR #212 applier left them stale, and the native validator failed RC-001, RC-002 and RC-011. The applier now verifies each recorded digest against the current canonical bytes and only then rebinds it, as Semantic Foundation v3.8.0 did when it added `L9-STRATEGY-001` (`2ae5dfa`). The applier does not decide whether those ledgers' **content** must change; that stays with the owner.

## Runnable checks

```bash
python -m unittest discover -s tests -v                 # 112 local tests
python tests/verify_composition_provenance.py --archive evidence/reduction-v1/projection-run1.tar \
  --revision 0b50cf7a09c96986d2fcd46130032224ad7104a0  # independent composition-provenance check
python tests/run_strategic_value_falsifiers.py          # six bad/control pairs
python tests/run_strategic_value_falsifiers.py --case SV015   # ... through SV020
python tools/reduce_to_two_invariants.py --check        # committed files == declared reduction
PYTHONPATH=/path/to/l9-semantic-compiler-engine/src python tests/run_native_schema_qualification.py
sha256sum -c SHA256SUMS.txt
```

The local tests prove asserted candidate semantics, exact ID closure and finite falsification discriminability. They do not prove forecasts, empirical adequacy, Numerical Reasoning behaviour or admission. The native runner returns `BLOCKED` (exit 2) when the real compiler cannot be imported.

## Apply only in a clean, pinned, disposable checkout

```bash
git clone /path/to/Quantum-L9/.github /tmp/sv-rehearsal && git -C /tmp/sv-rehearsal checkout 020a94bea86e7c5c5e4107da7014ec259508f397
python apply_to_pinned_checkout.py --checkout /tmp/sv-rehearsal                       # dry run
python apply_to_pinned_checkout.py --checkout /tmp/sv-rehearsal --apply --disposable
```

The script requires the exact frozen `BASE_SHA` and a clean tree. It refuses `--apply` without `--disposable`, and it refuses the checkout that carries this pack. It checks the whole assembled candidate before writing anything. If main moves, re-resolve authority and review before changing the pin. Never weaken the pin to get a green run.

## Qualification status

Evidence lives in `evidence/reduction-v1/`; `admission-readiness.json` lists every criterion as met, unmet or Unknown. In summary:

- Local tests, falsifiers and the reduction `--check` pass.
- Native schema qualification passes 26 checks against compiler `3bf1a82`.
- In a disposable rehearsal of the applied candidate, the native `.github` validator passes every ordinary semantic check. It fails only SC-008/SC-010, because the v3.27.0 release inventory does not list the new or changed files. That needs a successor release record, which this pack must not invent.
- The real compiler projected all five source classes (**pass**). The composition result is **unknown**: compiler 0.9.3 has no mechanical criterion for the composition profile's four declared `required_provenance` entries. The profile has carried those entries unchanged since PR #212. Two runs were byte-identical.
- The four facts `required_provenance` declares (source projection refs and digests, composition profile ref and digest) re-derive independently on both runs, with exact five-class coverage and receipt binding. The verifier imports no compiler code, and its 16 negative controls fail closed. This is evidence for the owner's provenance decision, **not** a compiler PASS. See `evidence/admission/composition-provenance-equivalence.json`.
- 16 producer negative controls each failed with their asserted exit code, typed failure and criterion; both positive controls passed; reversing component order leaves the composed digest unchanged. Raw compiler bytes are archived in `projection-run1.tar` / `projection-run2.tar`.

`historical` evidence (`evidence/*.json`, `evidence/*.log`) is the PR #212 record and is deliberately left unchanged.

## Gates still requiring the authorized canonical owner

The admission closeout (`evidence/admission/ADMISSION_CLOSEOUT.md`) re-resolves the target against current `main` (`9488d8f`: v3.28.0 admitted, v3.29.0 an open candidate) and tracks the 12-item checklist. The decisions below are scaffolded as D1–D5 in `evidence/admission/owner-decision.yaml`. That record is PENDING, and every authority reference in it is null.

1. Record real owner decisions for all eight dispositions, including the amended `L9-SV-001` wording.
2. Decide whether `required_provenance` stays on `l9.compose/strategic-planner-value@1` (composition remains `unknown` under compiler 0.9.3) or is dropped in line with the `pr-audit` and `architecture-intelligence` composition profiles. This pack does not drop a declared constraint to obtain a PASS.
3. Confirm that `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml` need only digest rebinding for two new invariants and one new contract.
4. Prepare a successor semantic-foundation release record (version not chosen here) so SC-008/SC-010 can pass. Then validate, publish through the governed PR path, and admit.
5. After admission, reproduce the bundle from the admitted revision, replay it under trust, and let the consumer bind only through its own release process.

**No canonical admission, merge, release, deployment, canonical producer receipt or consumer binding is claimed.** Producer receipts in the evidence are bound to a local, never-pushed rehearsal commit.
