# Strategic Value campaign closeout — 2026-11-08

Evidence for `L9-SV-CAMPAIGN-CLOSEOUT-CONTRACT/v1`. The terminal state reached is **SV_CANONICALLY_ADMITTED_AND_VERIFIED**. Semantic Foundation v3.32.0 (ADR-029) was admitted by the repository owner and took effect at `main` `64d8b85` (Quantum-L9/.github#222). It was then replayed and gated on that revision.

This directory records evidence; it grants nothing. Admission is ADR-029 and the v3.32.0 release status on `main`.

| Record | What it shows |
|---|---|
| [`authority-resolution.md`](authority-resolution.md) | Who could admit, by what mechanism, and what the admission covers |
| [`merge-ledger.yaml`](merge-ledger.yaml) | Seven merges in order, with exact heads and merge commits |
| [`compiler-lock.yaml`](compiler-lock.yaml) | The producer of record (`33e4c58`) and the compiler-`main` cross-check |
| [`qualification.yaml`](qualification.yaml), [`pre-merge-qualification-c4c4a1d/`](pre-merge-qualification-c4c4a1d/) | Producer qualification of the exact subject the owner admitted |
| [`diff-census.yaml`](diff-census.yaml) | All 20 files #222 brought to `main`; no predecessor release touched |
| [`release-validation.yaml`](release-validation.yaml) | v3.32.0 hash inventory (119/119) and native validation at `main` |
| [`merge-verification.yaml`](merge-verification.yaml) | The merged tree equals the admitted head, and the `semantics/` tree is unchanged since qualification |
| [`post-merge-replay/`](post-merge-replay/) | Producer replay, independent verifier and the `--require downstream` gate at `64d8b85` |
| [`final-receipt.yaml`](final-receipt.yaml) | The five statuses, admitted identities, what is not established, and the remaining dependencies |

The candidate pack in `docs/candidates/SV/` keeps its own owner-decision and closeout records. This change updates them from "approved, not admitted" to "admitted".
