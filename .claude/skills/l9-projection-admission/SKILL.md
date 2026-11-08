---
name: l9-projection-admission
description: Discover, validate, register, admit and confirm downstream use of new Quantum-L9/.github semantics (invariants, vocabulary, contracts, sources, projection or composition profiles, payload schemas). Use when a candidate must land in semantics/, a subject's dependency closure must be computed, a release must be cut or admitted, or admitted semantics must be proven to compile for consumers. Not for generic wiring (l9-wire-into-repo) or consumer bundles.
metadata:
  skill_schema: 1
  layer: control_plane
  role: skill_entrypoint
  tags: [l9, semantics, admission, projection, release, closure]
  owner: Quantum-L9/.github
  status: active
  version: "2.0.0"
  updated: "2026-11-08"
  license: Proprietary
  tier: strong
---

# L9 Projection Admission

This skill takes new canonical semantics in `Quantum-L9/.github` from a candidate to "admitted and usable downstream" without faking any rung. The repository owns the skill because it owns the language the skill admits.

The skill prepares, validates and verifies admission. It never grants canonical authority to itself. `semantics/authority_model.yaml#admission_rules` forbids the compiler or a candidate artifact from admitting its own global law. Admission needs the exact subject identity, the exact revision or digest, target-class authority and an explicit decision record.

## Activate / reject

| Activate when | Route elsewhere when |
| --- | --- |
| A candidate pack (`docs/candidates/<X>/` on a candidate branch) must land in `semantics/` | Wiring an arbitrary artifact into a repo: `l9-wire-into-repo` |
| You must know everything a change affects before an owner decides | Building or verifying a consumer bundle: that consumer repository's own workflow |
| A successor `docs/semantic-foundation/vX.Y.Z/` must be cut, validated or admitted | Changing the compiler itself: `l9-semantic-compiler-engine` |
| Someone asks "is X admitted / registered / usable by the compiler?" | Editing an admitted profile in place: refuse, propose `@N+1` |

## Authority (highest first)

1. The owner's explicit decision for an exact subject. Nothing below substitutes for it.
2. `semantics/authority_model.yaml#admission_rules` and `semantics/lifecycle.yaml`.
3. Accepted ADRs (`docs/adr/`) and the highest release record (`docs/semantic-foundation/`).
4. `make validate check test` and the real compiler's receipts. These are evidence, not authority.
5. Candidate-pack evidence. It describes a rehearsal and never covers the admission revision.

When two sources conflict, the higher one wins. Report the lower one as stale.

## Capabilities: plan and verify versus apply

| Capability | Tool | Writes canonical files? |
| --- | --- | --- |
| **Plan**: compute the complete subject and its closure | `scripts/discover_admission_subject.py` | No |
| **Verify** a rung: registration, qualification, release, admission, downstream | `scripts/check_admission_closure.py` | No |
| **Verify** admission evidence for one release | `scripts/verify_admission_evidence.py` | No |
| **Apply**: edit `semantics/`, cut the release, write the ADR, flip the status, merge | You, through the governed PR path | Yes. Admission steps need the owner's decision first. |

A passing plan or verify step never leads automatically to apply. Technical qualification is not authorization.

## Lifecycle

| # | Stage | What happens | Gate |
| --- | --- | --- | --- |
| 1 | DISCOVER | Resolve the admitted base, then compute the complete subject from the exact base→candidate diff. | `discover_admission_subject.py --write-subject subject.json` |
| 2 | RECONCILE | Review the discovery. Check ownership, irreducibility, compatibility and every listed revision. Declare each intended revision in `revisions`. Resolve every `required_dependencies` entry. | `discover_admission_subject.py --declared subject.json` exits 0 |
| 3 | PREPARE | On a fresh branch from freshly fetched `origin/main` in an isolated worktree, add each item to every surface in `references/registration-surfaces.md`, then rebind the digest cascade. | `--require registered` |
| 4 | QUALIFY | Run `make validate check test`, the native validator, the payload schemas and a rehearsal producer run with negative controls. | `--require registered` (qualification is reported) |
| 5 | RELEASE CANDIDATE | Cut exactly one successor directory as `ADDITIVE SUCCESSOR CANDIDATE` and generate the full `HASHES.sha256`. | `--require released` |
| 6 | AUTHORIZE | **Owner only.** Present the subject digest, the approved `semantics/` tree, the discovery and the evidence. Get the owner's explicit decision for that exact subject. | No tool decides this |
| 7 | ADMIT | Write the ADR in the ADR-025 shape (`references/admission-lifecycle.md`), index it, flip the status lines, regenerate hashes, and merge through `make pr`. | On `main`: `--require admitted` |
| 8 | CONFIRM | On a clean checkout whose HEAD is `origin/main`, run the real producer twice, verify every artifact independently, then hand off to consumers. | `--require downstream --compiler-src <engine> --output-root <scratch>` |

Commands for each stage:

```bash
S=.claude/skills/l9-projection-admission/scripts
python3 $S/discover_admission_subject.py --checkout . --write-subject subject.json   # 1
python3 $S/discover_admission_subject.py --checkout . --declared subject.json        # 2
python3 $S/check_admission_closure.py --checkout . --subject subject.json --require released   # 3-5
python3 $S/verify_admission_evidence.py --checkout . --subject subject.json --release vX.Y.Z    # 7
python3 $S/check_admission_closure.py --checkout . --subject subject.json --require downstream \
  --compiler-src ../l9-semantic-compiler-engine --output-root "$SCRATCH/out"                   # 8
```

## Verdicts

`check_admission_closure.py` prints one JSON report. Its `verdict` field is the highest rung every lower rung supports.

| Verdict | Meaning | Where to look |
| --- | --- | --- |
| `INCOMPLETE` | A registration gap. Causes: a missing surface, an ambiguous registry (duplicate source id or path, duplicate output-schema id), a type-specific rule, an unresolved selector, or an admitted profile edited in place. | `registration.gaps` |
| `REGISTERED` | Registered, but a qualification gate fails. Causes: the validator, `make validate`, `make check` or `make test`; release coverage, the full inventory or the sequence; or, when not yet admitted, the subject's closure (an omitted subject, an undeclared revision, an unadmitted dependency). | `validator`, `make`, `release.gaps`, `scope.gaps` |
| `RELEASED_CANDIDATE` | Every gate passes and the subject is closed, but no admitted release covers it. This is ready for an owner decision. | `admission.tried[*].reason` |
| `ADMITTED` | Admission evidence verifies, the decision covers what the release introduced, and the records are unchanged at admission, on main and at HEAD. | `admission.evidence`, `admission.decision_scope` |
| `DOWNSTREAM_USABLE` | Admitted, HEAD is main, and the real compiler at an exact clean revision produces PASS with empty unresolved criteria, twice, byte-identical. Every artifact and receipt verifies independently, and every negative control is rejected. | `downstream.verification`, `downstream.deterministic_replay` |

Exit codes: 0 means the `--require` rung was reached. 1 means it was not. 2 means UNRESOLVED: an unreadable input or ref, a missing compiler, `make`, Makefile or receipt interpreter, or malformed producer output. Never report exit 2 as a pass. A subject with no profile reports `downstream.status: not_applicable` and stays at `ADMITTED`.

## Judgment rules

- **The subject is computed, not remembered.** Admitting a release admits its whole approved tree. An identity that changed since the admitted base and is missing from the subject fails closure. Every new or changed identity must be named.
- **A redefinition is declared or it is refused.** A changed invariant, term, contract, source-registry entry, source class or schema needs a `revisions` entry. Admitted profiles never change in place: register `@N+1` (PROJECTION-013).
- **A candidate release is still checked.** SC-008 validates the highest directory whether or not it is admitted. If another candidate release is open, ask the owner whether to fold into it or follow it. The sequence gate allows only that open candidate to change.
- **UNKNOWN is not PASS.** An undefined forbidden category, a `rules` entry, an `output` key other than `schema`, or `required_provenance` cannot be evaluated by compiler 0.9.3. Registration lists these under `unresolvable_declarations`, and downstream stays non-PASS. Prove the declared facts independently, then let the owner choose to drop the declaration or implement the criterion. Deleting a declaration to get green is forbidden.
- **A gate PASS is evidence, never a decision.** Write `Accepted` only when quoting a real owner decision for the exact subject. Record that decision's reference, the approved tree and the subject in the ADR.
- **Evidence goes stale when the subject changes.** Rerun discovery and the gate after any edit to a covered file. Rerun the producer after any wording, profile or base change.

## Failure handling

State the exact gap from the report: its file, its id and the rung it blocks. Fix the narrowest cause. Never weaken a validator check, edit a historical release, or hand-edit a digest you did not recompute. When owner authority is missing, stop at `RELEASED_CANDIDATE` and say who must decide what.

## Resources

- `references/subject-closure.md`: discovery, the closure report and subject schemas, the dependency graph, and the scope rules.
- `references/registration-surfaces.md`: type-specific registration policy, entry shapes, the digest cascade and the successor release record.
- `references/admission-lifecycle.md`: authority, rungs, the ADR-025 precedent, the admission evidence schema, and what an agent must never do.
- `references/downstream-confirmation.md`: the producer run, independent verification, replay, negative controls, consumers and wording.
- `scripts/`: the three deterministic, read-only tools above.
- `tests/`: synthetic rung, closure, evidence and adversarial tests, plus real-repository integration tests. Run them with `python3 -m unittest discover -s .claude/skills/l9-projection-admission/tests`.
