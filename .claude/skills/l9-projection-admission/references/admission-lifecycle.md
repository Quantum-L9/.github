<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: authority-and-lifecycle
version: 2.0.0
status: active
-->

# Admission lifecycle and authority

## Authority (read these, do not paraphrase from memory)

| Source | Decides |
| --- | --- |
| `semantics/authority_model.yaml#admission_rules` | Admission needs exact subject identity, an exact revision or digest, the target class, target-class authority and an explicit decision record. `candidate_generation_is_not_admission`. Self-admission without target-class authority is forbidden. |
| `semantics/lifecycle.yaml` | Profile lifecycle `candidate → admitted → published → resolvable → superseded`. A membership change requires a new version. |
| `docs/adr/` + `docs/adr/README.md` | The decision record. The index is a flat `- ADR-NNN: Title` list plus a count sentence. |
| Highest `docs/semantic-foundation/vX.Y.Z/` | The release record. `make validate` checks the ledgers against the highest version directory, **whether or not it is admitted**. |
| `docs/PROJECTION_PUBLICATION.md`, ADR-021 | Consumer bundle, verification and trusted replay. |

## Rungs (the order is fixed)

| Rung | Who moves it | What changes |
| --- | --- | --- |
| Candidate | agent | Overlays and evidence on a candidate branch. Nothing under `semantics/` on `main`. |
| REGISTERED | agent, on an admission branch from freshly fetched `main` | Every surface in `registration-surfaces.md`, with the digest cascade rebound. |
| RELEASED_CANDIDATE | agent | Successor release directory with status `ADDITIVE SUCCESSOR CANDIDATE`. `make validate check test` passes. The subject is closed (`subject-closure.md`). |
| ADMITTED | **owner only** | The owner gives an explicit decision for the exact subject. The agent then writes the ADR that records it, flips the release status lines, bumps the ADR count and index, regenerates `HASHES.sha256`, and the PR merges to `main`. |
| DOWNSTREAM_USABLE | agent, post-merge | Real projection and composition PASS at the `main` revision, independently verified. Consumers then bundle, verify and replay. |

## The precedent to copy: ADR-025 / commit `c6ee11d`

v3.28.0 was admitted by one ADR and one commit that touched no `semantics/` file. That commit:

- added `docs/adr/ADR-025-…md`. Its `**Status:** Accepted for semantic-foundation v3.28.0 …` line names the owner's instruction, its session and the PR. Its subject table pins the release, the approved `semantics/` tree hash, the qualified candidate commit and the target class. It records the admitted definitions, accepted limitations, evidence relied on, and what admission does not establish;
- appended `- ADR-025: …` to `docs/adr/README.md` and bumped its count;
- flipped `MANIFEST.md`, `README.md` and `RELEASE_VALIDATION.md` from `ADDITIVE SUCCESSOR CANDIDATE` to `**ADMITTED ADDITIVE SUCCESSOR** (ADR-025, <date>)`;
- updated the "accepted ADRs" count and regenerated `HASHES.sha256`.

ADR-026 shows the opposite case: a candidate release whose ADR says it "does not admit itself".

## Admission evidence (`l9.projection-admission-evidence/v1`)

`scripts/verify_admission_evidence.py` produces this record, and the checker requires it for ADMITTED. The status line and an `Accepted` ADR only *nominate* a release. Each field below must bind:

| Field | How it is established |
| --- | --- |
| `admission_release` | A release on main with the ADMITTED status line and an ADR that accepts exactly that version, not a candidate of it |
| `admission_commit` | The oldest commit on main's first-parent mainline whose release README carries the ADMITTED status line. For a pull request, squashed or merged, that is the commit that lands it: the PR's own commits were never on `main`, and the ADR takes effect when the PR merges. The release directory and the ADR must be unedited on the mainline after it, and the full SC-008 inventory must verify at that commit. |
| `adr` | Existed and accepted the version **at the admission commit**: its status line accepts exactly that version and does not call itself a candidate, pending, withdrawn or self-denying. It is listed in the ADR index there, hashed by the release at its bytes, and unedited or not removed on main since. |
| `admitted_semantics_tree` | The first 40-hex value in the ADR's `Approved semantic tree` row. It must equal `git rev-parse <admission_commit>:semantics`. |
| `candidate_revision` | Further 40-hex commits in that row. Each one that resolves must carry the approved tree. |
| `target_authority_class` | The `Target class (and authority)` row **starts with** "Canonical global semantics". A row that only mentions it, such as "NOT canonical global semantics", is rejected. |
| `authorized_decision_ref` | A governed session id, a `Quantum-L9/<repo>#<n>` reference, or a GitHub pull-request or issue URL, in the status paragraph or target row. An arbitrary URL is not one. |
| `decision_scope` | Every subject identity the release *introduced* is named inside the ADR's **Admitted definitions** block. A mention elsewhere (evidence, limitations, an exclusion) does not count. "Introduced" means absent or different at the predecessor state: the admission commit of the highest *admitted* lower release, so an unadmitted candidate in between cannot absorb introductions. The predecessor directory's last commit is used only when no lower release was ever admitted. Ledger content changes count. Dependency records do not count; closure covers those. A composition is covered by the projection profile it composes only when both are introduced together. A schema is covered by its artifact id, its output id, or its profile's covering names. |
| `subject_digest` | The canonical-JSON digest of the subject's records at the admission commit |

Once admitted, a subject stays ADMITTED only while its records **and its dependencies** are unchanged on main and at HEAD. The dependencies are a projection's source files, its schema and forbidden-criterion definitions; a composition's projection profile and that profile's dependencies; a contract's source invariants; and a term's parent and detailed model. Drift in any of them is reported under `changed_*_since_admission` as a `dep:` key.

### What evidence cannot prove

Parsing a record cannot show that its author held authority. Evidence binds a decision record to an exact subject, tree, release and commit, and rejects every detached, late, edited or forged variant the tests construct. Whether a real owner decided is still a human fact. Quote it, never infer it.

Releases before v3.28.0 predate this record shape. Identities unchanged since v3.28.0 are admitted through ADR-025's approved tree, which covers them. ADR-025 does not need to name them, because v3.28.0 did not introduce them.

## What an agent must never do

- Write `Accepted`, flip a status line to ADMITTED, or fill a decider reference without the owner's explicit decision in the conversation or on GitHub. A gate passing is evidence. It is not a decision.
- Add or edit the ADR after the status flip, or edit it later. Either breaks the historical proof by design.
- Edit a historical release directory. Each release is immutable once cut, so changes go in a successor directory.
- Edit an admitted profile in place. RC-028, RC-030 and RC-032 pin some profiles and schemas by canonical-JSON digest, and `membership_change_requires_new_version`. A changed meaning is `@N+1`.
- Delete a declared constraint to turn `unknown` into `pass`. Prove equivalence or implement the criterion, and let the owner choose.
- Treat a verified consumer bundle as admission. `PROJECTION_PUBLICATION.md` says it is "verified, not admitted".
