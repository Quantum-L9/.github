# ADR-039 — Factory-Born Repository Registration

**Status:** Candidate for semantic-foundation v3.42.0. Drafted on 2026-11-13 for lane P4 of campaign L9-NODE-PIPELINE-01 ("semantic compiler → l9-repo-template birth → org CI → Meta-Injector → Topology → l9-deploy → admitted node"). Predecessor: the v3.41.0 candidate (ADR-038), unadmitted on admitted v3.39.0. Admission of v3.42.0 by the repository owner is the acceptance gate; this record does not admit itself.

Operator decisions this applies, verbatim (2026-11-13): "This must become a repeatable pipeline. That Includes activating org ci and running injector." and "I don't want to make those types of manual fixes on future nodes."

## Context

`semantics/repository_registry.yaml` is explicit membership: a repository is a member because an entry names it. Every entry so far was typed by hand, and adding one also needed a hand edit to RC-023's census pin (`RC023_REPOSITORIES`, `RC023_REPOSITORY_COUNT`) and a new release record, because SC-008 hashes the registry in the highest release record and a released record is immutable (L9-REVISION-001).

The factory (`Quantum-L9/l9-repo-template`, `make birth`) already produces an attested record of every birth: `.l9/birth-receipt.json` (`l9.birth-receipt/v1`, digest over its own content), a single root commit whose trailers carry that digest, the template commit and the birth profile, and `scripts/birth-runner/verify_birth_integrity.py`, which proves the three agree. The birth then dispatches `.github`'s `repo-birth-bootstrap.yml`. Core lane P1 needs to recognise a factory-born repository from its registry entry.

## Options considered

- **A — Keep hand entries.** Every node needs a manual registry edit, validator edit and release record. Rejected by the operator decision above.
- **B — Infer membership from the birth (no entry).** Contradicts `every_entry_is_an_explicit_admission_decision` and `birth_profile_does_not_imply_repository_class`. Rejected.
- **C — Automation also edits the RC-023 pin.** Keeps the pin, but makes the second "decision" a mechanical text edit, so it adds no review value. Rejected.
- **D — Automation proposes one entry plus its release record, derived only from the attested birth record. The entry's provenance identifies it, RC-023 checks it by shape, and the owner's merge admits it.** Adopted.

## Decisions (proposed)

1. **Entry.** A factory-born entry has exactly `id`, `coordinate {provider: github, organization: Quantum-L9, repository}`, `lifecycle`, `class_ref` and `birth_provenance`.
2. **`birth_provenance`** (the field Core keys factory birth on) has exactly `factory` (= `Quantum-L9/l9-repo-template`), `receipt_schema` (= `l9.birth-receipt/v1`), `receipt_digest` (`sha256:<64 hex>`), `root_commit`, `template_sha`, `org_policy_sha` (40-hex commits), `template_version`, `birth_profile` (a `policies/repo-classes.yml` profile name, not a RepositoryClass) and `born_at`. It is evidence (L9-EVIDENCE-001): it confers no authority, does not admit a product and does not imply a class.
3. **Id.** The repository name lowercased, with every run of `.`, `_` and `-` folded to one `-` (`rc023_factory_repository_id`). It is never typed.
4. **Lifecycle.** `current`: the entry is the current canonical coordinate. Registration is not product admission, deployment or readiness, which the registry `does_not_own`. No lifecycle value is added.
5. **Class.** The single current admitted RepositoryClass (today `l9.repository-class/l9@1`). The automation proposes it only while it is unique. If the class catalog admits a second current class, registration fails closed (`unknown_or_ambiguous_class_assignment_fails_closed`).
6. **RC-023.** The 33-entry census stays pinned. An entry carrying `birth_provenance` is counted apart and checked by shape (`rc023_factory_entry_problems`): exact keys, factory, receipt schema, digest and commit shapes, and an id that equals the id rule. The registry-wide rules (`github`/`Quantum-L9` coordinate, `current`, admitted class, unique id, unique coordinate) apply to it unchanged. A pinned entry never carries `birth_provenance`. A factory entry for a pinned id or coordinate fails. RC-023-NEG gains 13 mutations (57 to 70).
7. **Derivation.** `ops/register-birth.py` reads the newborn's committed receipt from a full clone. It re-checks schema, `repository == Quantum-L9/<name>`, factory, digest, the root-commit trailers and the receipt's immutability since the root commit. It then runs the factory's own `verify_birth_integrity.py --require-receipt` from the template commit the receipt names, and refuses unless that commit is on the factory's default branch and every check is PASS. It renders the entry and cuts the release record.
8. **Release.** Each registration is its own registry-only successor release record: the highest `vX.Y.Z` becomes `vX.Y.(Z+1)`, with a generated MANIFEST, README, RELEASE_VALIDATION and HASHES. The tool runs the semantic validator on the result and writes nothing unless it passes.
9. **Trigger.** `repo-birth-bootstrap.yml` gains a `register` job after a passing, non-dry-run attestation. It opens or updates one PR on branch `birth-registry/<repository>`. A re-run against a registry that already holds the identical entry does nothing. A different entry for the same id or coordinate is refused. A stale PR branch is advanced by a merge commit, never force-pushed. The job never merges.
10. Nothing else changes: no invariant, contract, term, capability, receipt family, lifecycle, class, projection or composition profile, and no existing registry entry.

## Consequences

- A newborn's registry entry needs no hand-made file. The only human act is the merge, which is the admission decision this ledger already required.
- Core can treat `birth_provenance.factory == Quantum-L9/l9-repo-template` as the factory-birth marker without reading the newborn.
- Registrations are serialized by the release sequence. Two births pending at once both propose the next patch version, and the second is regenerated on re-run after the first merges.
- **Outstanding Unknowns.** The org secret `GH_TOKEN` must be able to read the newborn (private) and the factory, and to write branches and PRs on `.github`. This record does not verify that grant. Births made before the receipt existed have nothing to attest and stay hand-registered.
