---
title: Authority-resolution projection qualification evidence
created: 2026-11-07
owner: Quantum-L9/.github
artifact_class: evidence
authority: non-authoritative
candidate_repository: Quantum-L9/.github
candidate_revision: 290bcd90378577392640cea9c6053c178423f0da
compiler_repository: Quantum-L9/l9-semantic-compiler-engine
compiler_revision: 943db9a462d35ba66771a700ece77c746295f591
consumer_driver_repository: Quantum-L9/Cursor-Governance
consumer_driver_revision: 8e4b352a0849ad6b04cda61ea9aa41f6fb1523a2
status: producer-qualified; semantic release blocked
---

# Authority-resolution qualification — 2026-11-07

This is local diagnostic evidence for the authority-resolution candidate in [code PR #211](https://github.com/Quantum-L9/.github/pull/211). It is not admission, independent candidate-consumer verification, consumer-committed publication, or a trusted protected-main replay attestation. The candidate commit is not on protected `main` at the time of this run.

## Results

- The supplied schema script exited 0 and reported 12 selected invariants, four contracts, and four static negative controls rejected. The ten candidate profiles were not changed by that script.
- The unchanged pinned consumer driver invoked the real compiler to project all four source classes and compose them in two fresh output roots. In both runs all four projection receipts and the composition receipt passed, including applicable payload-schema and equivalence criteria, with no unresolved criteria. The resulting 11-file bundles matched byte-for-byte. See `positive-summary.json` and `positive-qualification.log`.
- Ten targeted producer negative controls rejected the tested invalid inputs; these include a missing source **pin**, wrong profile pin, altered payloads, missing/duplicate components, changed receipt, and omitted composition namespace. See `negative-summary.json` and `negative-report.md` for the exact operations and error categories.
- A separate capability check **failed**: the pinned producer's schema interpreter accepted an empty `string_list` despite `min_items: 1`. The supplied script's static validator is stricter on that property than the real interpreter. Selection-equivalence checks are separate and do not establish a general nonempty-list schema rule.
- `scripts/validate-semantics.py` exited 1 and `make validate` exited 2. Both recorded eight SC-008 release-inventory failures: new schema files and their hashes are absent from the immutable v3.27.0 inventory, the install count is stale, and three changed canonical files have stale hashes. The historical release record was not edited. Other nine candidates' output schemas and independent consumer replay remain unqualified.

## Archive and provenance

`authority-resolution-run.zip` contains all 231 files generated during the run: the original supplied script, both validation logs, positive and negative harnesses, requests, command traces, two bundles, receipts, mutation samples, summaries, and check logs. ZIP SHA-256: `d2c30fdcd96cb8eecb046380d0ee7dc67293e4ea9238bd037954c0351cf50940`. Each archived member was checked byte-for-byte against its local source. Some copied inputs are intentionally tampered with for negative tests; they are not authentic bundles.

The first positive checker used the wrong kind of hash for full authority-file bytes and recorded an initial failure. The checker was corrected and revalidated the **existing** two producer outputs without rerunning the producer; the initial log, summary, and harness are preserved in the archive and `positive-initial-check.log`. The negative repeat exited 1 because the separate string-list capability check failed, not because the ten targeted rejection controls failed.

Raw reports, harnesses, and command logs preserve original sandbox absolute paths; those paths and links are not portable. The lock identifies the compiler revision as caller-asserted; the run separately compared the installed package and bytecode with the pinned compiler source. The earlier ten-profile `unknown` results in `../projection-qualification/` concern a different candidate revision and remain historical evidence.
