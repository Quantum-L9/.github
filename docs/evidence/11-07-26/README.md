# Projection campaign evidence — 2026-11-07

This directory records local diagnostic evidence only. It does not change canonical semantic files, admit any profile, or establish trusted production attestation.

## Requested qualification files

`projection-qualification/` contains the qualification ZIP and the four previously delivered result files. The ZIP includes the baseline bundle, verifier and replay records, candidate producer artifacts and receipts from both runs, and the completed negative-control evidence. Its internal README explains the exact pins and limits.

The baseline consumer verifier returned `BUNDLE_VERIFIED` at the named revision; the actual local `--check` exited 0. All ten candidate projections and compositions returned `unknown` because output schema criteria were unresolved. Their raw outputs were deterministic across two runs, but the candidates were not qualified and no consumer bundle replay was established for them.

## Earlier campaign evidence

`campaign-logs/` preserves the earlier generator, validation, discovery, and replay logs, plus the candidate invariant observations. These logs record different points in the investigation; for example, the candidate validation logs record the two SC-008 release-inventory failures, while the untouched baseline validation passed. The existing release record was not rewritten.

`campaign-logs/candidate-profile-changes.patch` is an earlier local output and does **not** exactly match the later local-only candidate fixture. It is historical evidence, not an instruction to apply or admit a profile. `additional-test-output.zip` preserves the earlier negative-control pilot and baseline test copies omitted from the qualification ZIP. Some copies were intentionally tampered with for negative tests and must not be treated as authentic bundles.

Absolute paths in logs and harnesses describe the original sandbox and are not portable. A local-only candidate commit is not a protected-main revision, a published release, or an admission decision.
