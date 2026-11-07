# Quantum-L9/.github GT candidate aligned with SV PR #212

**Status: CANDIDATE_ONLY, NO_CANONICAL_ADMISSION.**

Source: [`.github` PR #212](https://github.com/Quantum-L9/.github/pull/212) head `85531616cee2da94bbb7154418a78537549a4d76`; original canonical main `020a94bea86e7c5c5e4107da7014ec259508f397`. The 40-file SV PR adds documentation only and is not an admitted semantic authority.

This ZIP includes **only GT-owned candidate artifacts** (no SV model, schema, overlay, or skill). It carries one GT global-invariant proposal, twelve GT-only vocabulary definitions, a GT-only global contract, an independent dependent contract requiring future SV admission, one 3-source Planner GT profile, one 3-source composition profile, two typed GT-only schema candidates, strict local schema/test fixtures, PR212 cross-reference evidence, and a clean checkout script.

**Important difference from predecessor:** `strategic_commitment` duplicated current Plan-owned canonical vocabulary and is now renamed `incentive_bearing_commitment` in GT. The original `strategic_commitment` stays owned by `.github` Strategy. See `PR212_ALIGNMENT.md` for ten break-tests and the exact SV mapping.

**Separate projected semantic views:** GT selects `vocabulary+invariants+contracts`; SV selects `strategic_value_model+vocabulary+invariants+contracts+authority_model`. Each is a source-namespaced, non-authoritative view. Neither semantic composition runs numerical valuation.

**Combined assessment:** only after independently admitted SV, the Numerical Reasoning owner may evaluate one SV claim conditioned on GT joint response paths using PR212 SV's exclusive five-bucket accounting. GT alone requires no SV; no mandatory Q/V, additive uplift, duplicate value, or plan authority.

## Local checks

`python -m unittest discover -s tests -v` (requires PyYAML and jsonschema).

`python apply_to_pinned_checkout.py --checkout /path/to/Quantum-L9/.github` performs a read-only dry-run only if that checkout is clean at the PR #212 HEAD and the original canonical blobs plus PR #212 SV candidate document blobs match. `--apply` writes the GT core to that **local checkout only**; it never commits, pushes, or admits. The dependent contract is **not** part of that canonical GT-core preparation.

Check `ADMISSION_HANDOFF.md`, `PR212_ALIGNMENT.md`, and `evidence/pr212_alignment_binding.json` for outstanding native proof. No modifications to GitHub were made.
