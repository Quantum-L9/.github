# Remediation ledger: #213 for joint admission with the reduced SV candidate

Reviewed GT head: `d9292f2440808fecb71539ef0de6d8474dfe384b`. The spec assumed PR #212 had already been reduced to two SV invariants; the reduction was published separately as PR #215 (`a64d05a`), and this pack binds to that exact commit.

| # | Spec item | Disposition | Evidence |
| --- | --- | --- | --- |
| 1 | P0 Rebind to the remediated SV | **Done.** `evidence/sv_alignment_binding.json` replaces the PR #212 binding; the applier reads it. Reduced set asserted. | `tests/test_sv_alignment.py`, `test_applier.TargetPinning` |
| 2 | P0 Schema discriminators | **Done.** `properties.schema.const` added to both schemas as an optional descriptor (not `required`); both output IDs resolve to exactly one registered schema. The polymorphic per-source schema is kept, with exact selection verified by the producer (selection equivalence), not by `oneOf`. | applier `SCHEMA_RESOLVED`; control `projection_schema_discriminator_removed` → `unknown` |
| 3 | P0 Governing-invariant closure | **Done.** Six selectors; `min_items: 6` plus a six-ID `enum` in both native schemas; draft JSON schemas add exact `contains` coverage. Uniqueness: the native dialect has no keyword for it, so the applier and producer selection enforce it. | producer payload = six IDs; controls `profile_drops_one_governing_invariant`, `governing_invariant_id_renamed` |
| 4 | P0 Undefined forbidden categories | **Done.** One `payload_excludes` criterion over the 11 SV terms, both SV invariants and the SV contract, registered by the applier. The other three protections remain contract obligations (`requires` / `forbidden` of the GT core contract). | receipts: 11/2/1 applicable selections, `pass`; schema-widened controls fail on the criterion itself |
| 5.1 | P0 PR-specific dependency tokens | **Done.** The first three `requires` became durable predicates and `exact_compatible_canonical_authority_coordinates` was added; the PR-named `forbidden` token became candidate-neutral. These are tokens, not proofs: the applier's stage B and `tools/verify_consumer_envelope.py` check them against evidence. | `test_candidate` |
| 5.2 | P0 `source_invariants` | **Done.** Adds `L9-SV-001`, `L9-SV-002`, `L9-ASSURANCE-001`, `L9-PROV-001`, `L9-COORD-001` to the existing set (eleven IDs). | `test_dependent_contract_cites_reduced_sv_law_only` |
| 5.3 | P0 Independent-admission release order | **Done.** Stage `core` (release A) never applies the dependent contract; stage `dependent` (release B) refuses until a reviewed commit records the admitted revision. There is no override flag. | `test_applier.DependentStage` |
| 6 | P0 Harden the applier | **Done.** Duplicate IDs inside overlays; verified contract derivation (old digest and count, exactly-once replacement, new digest and count); derived-ledger rebinding; manifest append that keeps prior registrations; forbidden registration; whole-candidate verification before any write; staged writes; `--disposable`. | 25 applier tests; reproduces 15 rehearsal digests byte for byte |
| 7 | P1 Boundary tests | **Done (synthetic plus real receipts).** No additive uplift, nonanticipativity, joint dependence, ε-Nash deviation versus convergence, method evidence, stale coordinates, no authority escape. | `tests/test_gt_sv_boundaries.py` |
| 8 | P1 Consumer envelope | **Kept as a candidate consumer contract.** No eight-source composition. A verifier now checks receipt-backed digests, coordinate equality and numerical evidence against the producer receipts it is given. It does not authenticate those receipts; the consumer must obtain them through a verified channel, for example the compiler's `verify-projection`. | `ConsumerEnvelopeAgainstRealReceipts` |
| 9 | File census | **Derived: 15 paths, not 12.** The three extra are derived-ledger digest rebinds. | `ADMISSION_HANDOFF.md`, `rehearsal.json` |
| 10 | Real producer qualification | **Done at a local rehearsal revision:** GT 3+1 pass; SV 5 pass and composition `unknown`; ten receipts; repeat run byte-identical; 19 controls matched. Not at a canonical revision. | `evidence/integration-v1/` |
| P1 | Adjudicate `L9-GT-001` | **Not done:** this is an owner decision. | `ADMISSION_HANDOFF.md` gate 1 |
| — | SonarQube (7 issues) | **Triaged.** All seven were in the replaced applier (duplicated literals, cognitive complexity, `"  "` in regexes); the equivalent patterns in the new applier were removed. | commit `46f9fab` |
| — | Codex review (2 findings) | **Fixed by items 2 and 4.** | — |

## Findings this remediation surfaced

1. Under compiler 0.9.3 the SV composition is `unknown` while `required_provenance` stays declared. A GT+SV envelope therefore cannot be verified as `evaluated` at this candidate; the verifier refuses it on the real receipt.
2. Two original GT producer controls were conflating layers: the payload schema rejects an SV invariant or contract before the forbidden criterion runs. Both layers now have their own controls.
3. Both PR #212 SV and GT core rebind the same derived ledgers, so the GT applier must verify against the SV-applied bytes rather than the bare `020a94b` bytes. The pinned SV-applied digests make that exact.
