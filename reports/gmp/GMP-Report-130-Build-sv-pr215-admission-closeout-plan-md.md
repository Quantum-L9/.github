# GMP-130

**Task:** Build sv_pr215_admission_closeout.plan.md
**Tier:** RUNTIME

## TODOs

- T1: docs/candidates/SV/tests/verify_composition_provenance.py CREATE Independent composition-provenance verifier (no compiler imports) over a composed run directory
- T2: docs/candidates/SV/tests/test_composition_provenance_equivalence.py CREATE Positive and negative-control tests for the verifier (digest corruption, ref swap, profile digest change, duplicate, missing source, payload drift, receipt drift)
- T3: docs/candidates/SV/evidence/admission/composition-provenance-equivalence.json CREATE Committed verifier result over evidence/reduction-v1/projection-run1.tar and projection-run2.tar
- T4: docs/candidates/SV/evidence/admission/owner-decision.yaml CREATE Owner-decision record scaffold, decision_status PENDING, all authority refs null, both SV-001 options and both provenance routes
- T5: docs/candidates/SV/evidence/admission/ADMISSION_CLOSEOUT.md CREATE Admission closeout record with the re-resolved target (main 9488d8f, v3.28.0 admitted, v3.29.0 candidate), 12-item checklist and blockers
- T6: docs/candidates/SV/evidence/reduction-v1/admission-readiness.json REPLACE Update the readiness ledger with the composition-equivalence evidence and the re-resolved target; status unchanged (not admission ready)
- T7: docs/candidates/SV/SHA256SUMS.txt REPLACE Regenerate pack checksums covering the new files
- T8: docs/candidates/SV/MANIFEST.json REPLACE Register new files in the pack manifest
- T9: docs/candidates/SV/README.md REPLACE Point the pack README at the admission closeout record
