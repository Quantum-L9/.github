# Independent evidence review: two-invariant reduction

**Reviewer:** a separate AI agent session, briefed with the subject and the questions but not with the author's conclusions, read-only on the repository. **This is not a human, owner or canonical review** and grants no admission authority.
**Subject:** commit `f4cc0d0` (reduction) and the files committed up to `ff38d1f`; the reviewer re-ran the suite, `--check`, the native schema runner, and the applier plus native validator in its own scratch clone.

## Findings and dispositions

| # | Severity | Finding | Disposition in this candidate |
|---|---|---|---|
| 1 | blocking for a "lossless" claim | Amended SV-001 narrows "cannot establish a complete Strategic Value ranking" to "...a complete **causally attributed**... ranking" | **Recorded, not changed.** The amended text is mandated by the development pack; changing it is an owner decision. The ledger and `IRREDUCIBILITY_OWNER_REVIEW.md` record it as a weakening and give a non-weakening alternative. Docs no longer call the SV-001/SV-015 change lossless. |
| 2 | blocking for a "lossless" claim | Merged SV-015 safeguard narrows scope (only claimed causal effects, only quantified claims) and replaces "quantify" with "identified and justified" | **Recorded, not changed.** Ledger `meaning_preservation: MERGE_WITH_WEAKENING_REQUIRES_OWNER_DECISION`; tested by `test_sv001_amendment_is_ledgered_with_its_weakening_points`. |
| 3 | should-fix | "Lossless" test names overstate what the SV-001 test proves | Fixed: a new test asserts the original clause is *absent* from the amended text and that the ledger records each weakening point. |
| 4 | note | No normative use of SV-015..020 remains; contract unchanged except `source_invariants`; normative support for parts of SV-016/017 rests on model and contract text | Agreed; carried as an owner-review note. |
| 5 | should-fix | Lineage `governing_invariants` enum was exempt from removed-ID checks | Fixed: closure helper, applier and native runner require each lineage enum to equal exactly the twelve IDs; a negative test adds `L9-SV-015` and is caught. |
| 6 | should-fix | Model `governed_by.invariants` schema had only `min_items: 12` | Fixed: a 12-value enum is added in both schemas and checked. The contract-record `source_invariants` field is **not** restricted, because the projected `authority-boundary`, `projection` and `hard-constraint` contracts legitimately cite other invariants. |
| 7 | should-fix | Lineage `meaning`/`model_section`/`contract_obligation`/`when` were plain strings; records not closed | `const` pins added for all four (two native negatives added). Closing records is **not possible**: the compiler dialect has no `additionalProperties`, so an unsupported keyword is not invented. |
| 8 | should-fix | Schema-equality test swapped in the donor's whole invariant descriptor | Fixed: only `enum` and `min_items` are masked, so dropping a required field is detected. |
| 9 | should-fix | Checksum tamper test was vacuous | Fixed: `checksum_mismatches()` is run on a tampered copy of the package and must name exactly the tampered file. |
| 10 | should-fix | `--apply` writes were not atomic | Fixed: all files are staged first, then renamed into place. A staging failure removes the staged files; a failure during the final renames is reported. |
| 11 | note | `--disposable` is self-declared; no contract-count check; CRLF hashing fails closed | Contract count +1 check added; the self-declared flag is documented as such. |
| 12 | should-fix | Producer negative controls counted any non-zero exit as detection; two were mislabelled; the order-reversal case was not a negative | Fixed: each control asserts its expected exit code, typed failure and criterion or message. The labels now name the real mechanism (request validation; profile selector resolution). Order reversal is an invariance check on the composed digest. All 18 match. |
| 13 | should-fix | Determinism unverifiable: run-2 bytes not committed; rehearsal commit unpushed | Fixed: both runs are committed byte-exact as deterministic tar archives, and the rehearsal tree hash and per-file digests are recorded so the tree can be reproduced. The rehearsal commit stays unpushed by design. |
| 14 | should-fix | `admission-readiness.json` cited this file before it existed; "MET" for enum agreement overstated | Fixed: this file now exists, and the readiness entries are requalified. |
| 15 | should-fix | Docs, manifest and checksums stale at `f4cc0d0` | Already fixed in `dbe3c8a`/`ff38d1f`; regenerated again after these fixes. |
| 16 | note | Native log, composition `unknown`, schema-only scope and authority resolution are honestly stated | No change. |

## What remains outside this review

- Owner decisions on all eight dispositions, especially findings 1-2.
- Human or owner review of the evidence. This agent review does not substitute for it.
- Canonical-revision projection and replay after admission.
