---
name: l9-projection-admission
description: Validate, register, admit and confirm downstream use of new Quantum-L9/.github semantics (invariants, vocabulary, contracts, sources, projection or composition profiles, payload schemas). Use when a candidate must land in semantics/, cut or admit a release, or be proven to compile for consumers. Not for generic wiring (l9-wire-into-repo) or consumer bundles.
metadata:
  skill_schema: 1
  layer: control_plane
  role: skill_entrypoint
  tags: [l9, semantics, admission, projection, release]
  owner: Quantum-L9/.github
  status: active
  version: "1.0.0"
  updated: "2026-11-08"
  license: Proprietary
  tier: strong
---

# L9 Projection Admission

Take new canonical semantics from a candidate to "admitted and usable downstream" in
`Quantum-L9/.github` without faking any rung. This repository owns the skill, because it
owns the language the skill admits.

## Activate / reject

| Activate when | Route elsewhere when |
| --- | --- |
| A candidate pack (`docs/candidates/<X>/` on a candidate branch) must land in `semantics/` | Wiring an arbitrary artifact into a repo: `l9-wire-into-repo` |
| A successor `docs/semantic-foundation/vX.Y.Z/` must be cut, validated or admitted | Building or verifying a consumer bundle: that consumer repository's own workflow |
| Someone asks "is X admitted / registered / usable by the compiler?" | Changing the compiler itself: `l9-semantic-compiler-engine` |
| An owner decision must be turned into an ADR plus status flips | Editing an admitted profile in place: refuse, propose `@N+1` |

## Authority (highest first)

1. The owner's explicit decision for an exact subject. Nothing below substitutes for it.
2. `semantics/authority_model.yaml#admission_rules` and `semantics/lifecycle.yaml`.
3. Accepted ADRs (`docs/adr/`) and the highest release record (`docs/semantic-foundation/`).
4. The repository validator (`make validate`) and the real compiler's receipts. These are evidence, not authority.
5. Candidate-pack evidence. It describes a rehearsal and never covers the admission revision.

On a conflict, the higher source wins, and you report the lower one as stale.

## Workflow

1. **Name the subject.** Write `subject.json` with schema `l9.projection-admission-subject/v1`. It takes lists `invariants`, `vocabulary_terms`, `contracts`, `canonical_sources`, `source_classes`, `projection_profiles`, `composition_profiles` and `schemas` (bare filenames under `semantics/`). Name every new item; an item left out is never checked.
2. **Branch.** Create a fresh branch from freshly fetched `origin/main`. A pack pinned to an older base is re-resolved, never forced: read the diff of the target files since the pin first.
3. **Register.** Add each item to every surface in `references/registration-surfaces.md`, then rebind the digest cascade in order. Gate: `--require registered`.
4. **Release.** Cut the successor directory as a CANDIDATE and generate `HASHES.sha256` with the exact command in that reference. Run `make validate check test`. Gate: `--require released`.
5. **Admit.** Only after the owner decides. Follow `references/admission-lifecycle.md` (the ADR-025 precedent): write the ADR, append it to the index and count, flip the three status lines, then regenerate hashes. Merge through the governed PR path. Gate, on a `main` checkout after the merge: `--require admitted`.
6. **Confirm downstream.** On a clean checkout whose HEAD is `origin/main`, run `--require downstream --compiler-src <l9-semantic-compiler-engine checkout> --output-root <scratch dir>`. Explain consumer next steps with `references/downstream-confirmation.md`.

```bash
python3 .claude/skills/l9-projection-admission/scripts/check_admission_closure.py \
  --checkout . --subject subject.json --require admitted
```

`scripts/check_admission_closure.py` prints one JSON report. The `verdict` field holds the highest rung reached:

| Verdict | Meaning |
| --- | --- |
| `INCOMPLETE` | At least one gap in `registration.gaps`. |
| `REGISTERED` | Registration passes, but `validator.fail_lines` is non-empty or `release.gaps` is non-empty. |
| `RELEASED_CANDIDATE` | Validator passes and the release covers the subject, but no admitted release covers it on main. `admission.tried` shows why. |
| `ADMITTED` | Admission found: `admission.release`, `admission.adr` and `admission.release_commit`, with `changed_since_admission` empty. |
| `DOWNSTREAM_USABLE` | Admitted, and every projection and composition is PASS at `main`. |

Exit 0 means the `--require` rung was reached, 1 means it was not, and 2 means UNRESOLVED (an unreadable input or ref). Never report exit 2 as a pass.

## Judgment rules

- **A candidate release is still checked.** SC-008 validates the highest directory whether or not it is admitted. If another candidate release is open, ask the owner whether to fold into it or follow it before cutting a directory.
- **An UNKNOWN composition means a missing criterion, not missing law.** Prove the declared facts independently, then let the owner choose: drop the declaration or implement the criterion. Deleting the declaration to get green is forbidden.
- **A gate PASS is evidence, never a decision.** Write `Accepted` only when quoting a real owner decision for the exact subject, and record that decision's reference in the ADR.
- **A changed meaning needs a new version.** The validator pins some profiles whole (RC-028, RC-030, RC-032), and any membership change needs `@N+1`.
- **Evidence goes stale when the subject changes.** Rerun the gate after any edit to a covered file, and rerun the producer after any wording, profile or base change.

## Failure handling

State the exact gap from the report: its file, its id and the rung it blocks. Fix the narrowest cause. Never weaken a validator check, edit a historical release, or hand-edit a digest you did not recompute. When owner authority is missing, stop at `RELEASED_CANDIDATE` and say who must decide what.

## Resources

- `references/admission-lifecycle.md`: authority, rungs, the ADR-025 precedent, and what an agent must never do.
- `references/registration-surfaces.md`: entry shapes, digest cascade and the successor release record.
- `references/downstream-confirmation.md`: the producer run, the consumer bundle, trusted replay, and wording.
- `scripts/check_admission_closure.py`: the deterministic gate.
- `tests/test_check_admission_closure.py`: rung tests. Run them with `python3 -m unittest discover -s .claude/skills/l9-projection-admission/tests`.
