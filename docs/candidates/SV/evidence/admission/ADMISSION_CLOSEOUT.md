# Strategic Value admission closeout

**Status:** candidate-side closeout prepared, **not admitted**. No owner decision exists, so nothing below is
approved. The remaining steps need the owner's authority or a canonical base, and an agent can't supply either.

## What this change establishes

| Item | Result | Evidence |
| --- | --- | --- |
| Why the composition result is UNKNOWN | Compiler 0.9.3 has no evaluator for `required_provenance`. `passes/projection.py::_declared_constraints` marks every declared value `unresolved` without reading it, and any unresolved criterion makes the result `unknown`. | `composition-provenance-equivalence.json` (`finding`) |
| The four declared facts hold | PASS on both rehearsal runs, with identical reports. Profile ref and digest, five component refs and digests, composition digest, exact five-class coverage with whole-payload placement, and receipt binding (5 PASS projection receipts, 1 composition receipt, one revision, sealed digests) all re-derive without compiler code. | `tests/verify_composition_provenance.py` |
| Fails closed | 17 negative controls fail on the intended check: corrupted component or source digest, swapped or foreign ref, relabelled source classes, changed profile digest or ref, edited profile record, duplicated or missing source, payload drift, unsealed artifact, tampered projection, wrong revision, receipt input mismatch, UNKNOWN forged to PASS, missing projection receipt. Unreadable input returns `UNRESOLVED` (exit 2), never PASS. | `tests/test_composition_provenance_equivalence.py` |
| Canonical precedent | Mixed. On `main`, `l9.compose/stage-context@1` declares the same four tokens, and the other 13 composition profiles declare none. `global_rules.source_projection_provenance_required: true` is not read by the compiler. | `semantics/composition_profiles.yaml` at `9488d8f` |
| Owner-decision scaffold | Five decisions (D1–D5) carry exact option texts. Every authority reference is `null`. | `owner-decision.yaml` |

The verifier result is **evidence for decision D2**. It is not a compiler PASS receipt, and the composition result
stays `unknown` until D2 is decided and the producer is rerun.

## Admission target, re-resolved 2026-11-08

The pack was built against `020a94b`. `origin/main` has since moved to `9488d8f`:

- **v3.28.0 is admitted** (ADR-025, PR #211). The successor version the brief proposed is taken.
- **v3.29.0 is an open candidate** (ADR-026, PR #217). `scripts/validate-semantics.py` SC-008 validates the
  highest numeric release directory whether or not it is admitted. SV therefore lands in v3.30.0 or is folded into
  v3.29.0 before that release is admitted (decision D4).
- Unchanged since the pin: `invariants`, `contracts`, `vocabulary`, `canonical_sources`, `capabilities`,
  `lifecycle`, `receipt_catalog`.
- Changed since the pin, all additive: `projection_profiles.yaml` (+532), `composition_profiles.yaml` (+140) and
  `generic_compiler_manifest.yaml` (+20). The new entries sit at exactly the anchors the SV applier writes to. Each
  anchor is still unique, so the merge logic should hold. That is inferred, not run.
- `apply_to_pinned_checkout.py` refuses because HEAD is not `020a94b`. Re-pinning means updating `BASE_SHA` and
  the authority resolution, then rehearsing on `9488d8f` or later. Do not override the SHA guard.

## Closeout checklist (0 / 12 admitted)

| # | Item | State | Blocker |
| --- | --- | --- | --- |
| 1 | Composition provenance equivalence or native criterion resolved | Equivalence **proved**; route not chosen | Owner decision D2 |
| 2 | Real composition receipt reports PASS | UNMET | D2, then producer rerun |
| 3 | SV-001 final wording approved and frozen | UNMET (options A/B recorded verbatim) | Owner decision D1 |
| 4 | Eight dispositions authorized at exact digest | UNMET | Owner decision record (ADR) |
| 5 | PR #215 merged into `docs/candidates-strategic-value-sv1` | PENDING | Review |
| 6 | Thirteen-path overlay applied to freshly resolved `main` | UNMET | Re-pin from `020a94b` to current `main` |
| 7 | PR #211 and v3.28.0/v3.29.0 registry overlaps reconciled | PARTIAL: #211 is merged, and the anchors survive by inspection | Rehearsal on the new base, plus D5 |
| 8 | Successor release manifest and hash inventory | UNMET | D4 |
| 9 | Native validation, five projections and composition PASS | UNMET | Items 2, 6 and 8 |
| 10 | Determinism and negative controls at the final revision | Reusable assets exist (82 + 32 tests, 18 producer controls, this verifier) | Final subject |
| 11 | Canonical admission PR approved and merged | UNMET | Items 1–10 |
| 12 | Admitted `main` read back and consumer replay verified | UNMET | Item 11 |

## Next actions, in order

1. **Owner:** decide D1 (SV-001 wording) and D2 (provenance route). Either choice changes the subject, so freeze
   both before any final producer run.
2. **Owner:** decide D4 and D5 (release vehicle and order relative to v3.29.0).
3. **Agent:** apply D1 and D2 in the pack. Regenerate the schemas, tests, ledgers and checksums. Re-pin the applier
   to current `main` and rehearse. Rerun the five projections and the composition at the rehearsal revision, plus
   this verifier.
4. **Owner:** record one scoped decision (an ADR, following ADR-025) that binds the eight dispositions to the
   exact final subject digest.
5. **Agent:** open the admission branch from freshly fetched `main`. Apply the 13 paths, add the successor release
   (MANIFEST, README, RELEASE_VALIDATION, HASHES) without touching earlier releases, and run
   `make validate check test`. Rerun the producer at the admission revision, then open the PR to `main`.
6. **Owner:** approve and merge. Then read back `main` and replay the consumer bundle as post-admission trusted
   replay.
