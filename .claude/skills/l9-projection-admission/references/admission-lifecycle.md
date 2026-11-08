<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: authority-and-lifecycle
version: 1.0.0
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
| RELEASED_CANDIDATE | agent | Successor release directory with status `ADDITIVE SUCCESSOR CANDIDATE`. `make validate check test` passes. |
| ADMITTED | **owner only** | The owner gives an explicit decision. The agent then writes the ADR that records it, flips the release status lines, bumps the ADR count and index, regenerates `HASHES.sha256`, and the PR merges to `main`. |
| DOWNSTREAM_USABLE | agent, post-merge | Real projection and composition PASS at the `main` revision. Consumers then bundle, verify and replay. |

## The precedent to copy: ADR-025 / commit `c6ee11d`

v3.28.0 was admitted by one ADR and one commit that touched no `semantics/` file. That commit:

- added `docs/adr/ADR-025-…md`. Its `**Status:** Accepted for semantic-foundation v3.28.0 …` line names the owner's instruction and its session. Its subject table pins the approved `semantics/` tree hash and the PR. It records the admitted definitions, accepted limitations, evidence relied on, and what admission does not establish;
- appended `- ADR-025: …` to `docs/adr/README.md` and bumped its count;
- flipped `MANIFEST.md`, `README.md` and `RELEASE_VALIDATION.md` from `ADDITIVE SUCCESSOR CANDIDATE` to `**ADMITTED ADDITIVE SUCCESSOR** (ADR-025, <date>)`;
- updated the "accepted ADRs" count and regenerated `HASHES.sha256`.

ADR-026 shows the opposite case: a candidate release whose ADR says it "does not admit itself".

## What an agent must never do

- Write `Accepted`, flip a status line to ADMITTED, or fill a decider reference without the owner's explicit decision in the conversation or on GitHub. A gate passing is evidence. It is not a decision.
- Edit a historical release directory. Each release is immutable once cut, so changes go in a successor directory.
- Edit an admitted profile in place. RC-028, RC-030 and RC-032 pin some profiles and schemas by canonical-JSON digest, and `membership_change_requires_new_version`. A changed meaning is `@N+1`.
- Delete a declared constraint to turn `unknown` into `pass`. Prove equivalence or implement the criterion, and let the owner choose.
- Treat a verified consumer bundle as admission. `PROJECTION_PUBLICATION.md` says it is "verified, not admitted".
