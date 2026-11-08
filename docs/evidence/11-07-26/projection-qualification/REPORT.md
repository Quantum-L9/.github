# Candidate producer negative-control diagnostics

Candidate commit: `432788798e06dfedd1f0089a7e2dd4e162d8032f`  
Pinned producer checkout: `943db9a462d35ba66771a700ece77c746295f591`; installed implementation: `/tmp/l9-projection-qa.nBKv8FWo/venv/lib/python3.12/site-packages/l9_semantic_compiler/__init__.py`  
Started: 2026-11-07T16:32:10.764759+00:00; completed: 2026-11-07T16:32:33.263683+00:00

**Scope:** diagnostic negative behavior only—not user-level candidate qualification or trusted replay.

## Counts by profile

| Projection profile suffix | Passed | Failed | Unrun |
|---|---:|---:|---:|
| authority-resolution | 10 | 0 | 0 |
| evidence-assessment | 10 | 0 | 0 |
| semantic-change-context | 10 | 0 | 0 |
| architecture-break-test | 10 | 0 | 0 |
| globalization-assessment | 10 | 0 | 0 |
| work-state-continuity | 10 | 0 | 0 |
| strategic-planning-context | 10 | 0 | 0 |
| strategic-metacognition | 10 | 0 | 0 |
| identity-assurance | 10 | 0 | 0 |
| hard-constraint-context | 10 | 0 | 0 |
| **Total** | **100** | **0** | **0** |

## Typed outcomes

`—` means the producer did not emit a `criterion` field. Observed outcomes aggregate all profiles.

| Control | Expected code / criterion | Observed code / criterion (count) |
|---|---|---|
| 01_missing_source_pin | `INVALID_REQUEST` / `—` | `INVALID_REQUEST` / `—` (10) |
| 02_wrong_source_pin | `REVISION_MISMATCH` / `source_digest` | `REVISION_MISMATCH` / `source_digest` (10) |
| 03_wrong_profile_pin | `REVISION_MISMATCH` / `profile_digest` | `REVISION_MISMATCH` / `profile_digest` (10) |
| 04_payload_tamper_no_redigest | `REVISION_MISMATCH` / `projection_digest` | `REVISION_MISMATCH` / `projection_digest` (10) |
| 05_payload_tamper_redigested | `SEMANTIC_DIVERGENCE` / `selection_equivalence` | `SEMANTIC_DIVERGENCE` / `selection_equivalence` (10) |
| 06_forged_stale_source_digest | `REVISION_MISMATCH` / `source_currentness` | `REVISION_MISMATCH` / `source_currentness` (10) |
| 07_missing_component | `INVALID_REQUEST` / `source_coverage` | `INVALID_REQUEST` / `source_coverage` (10) |
| 08_duplicate_component | `AMBIGUOUS_SEMANTICS` / `duplicate_source` | `AMBIGUOUS_SEMANTICS` / `duplicate_source` (10) |
| 09_wrong_composition_profile_pin | `REVISION_MISMATCH` / `composition_profile_digest` | `REVISION_MISMATCH` / `composition_profile_digest` (10) |
| 10_changed_receipt_no_redigest | `INVALID_REQUEST` / `—` | `INVALID_REQUEST` / `—` (10) |

## Evidence and limits

- The real producer emitted 53 projection artifacts and receipts in profile-specific fresh scratch directories; 53/53 have unchanged `unknown` artifact/receipt results. No passing bundle is claimed.
- Projection and source pins came from the real `projection_coordinates`; composition pins came from the real `CanonicalAuthority.resolve_profile`. Each omitted source pin refers to an existing resolved source, not a missing file.
- Payload and forged-source modifications were applied only to separate copies; recomputed envelopes used the installed producer's `envelope_digest`. The forged stale digest is a simulation, not an intervening source revision.
- The changed receipt kept its result and digest unchanged; validation used `engine.receipts.validate_receipt_document`, a producer helper, **not** an independent consumer.
- Candidate HEAD/status unchanged: True; generated original artifacts and receipts unchanged: True.
- One genuine emitted component and one emitted receipt per profile were targeted; these controls are not an exhaustive tamper campaign.
- Full per-case JSON, original emissions, and copies: `/home/ubuntu/l9-projection-campaign/candidate-negative-controls/run-9ifk7fy3/profiles/<profile>/`; execution log: `/home/ubuntu/l9-projection-campaign/candidate-negative-controls/full-run.log`; harness: `/home/ubuntu/l9-projection-campaign/candidate-negative-controls/negative_controls.py`.
