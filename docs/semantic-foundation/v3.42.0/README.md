# Semantic Foundation v3.42.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.42.0 lets a factory birth propose its own repository-registry entry. Before this release every registry entry, its RC-023 pin and its release record were made by hand. Now `ops/register-birth.py` derives the entry only from the factory's attested birth record and opens a reviewable PR, and the owner's merge of that exact entry is the admission decision.

Successor to the v3.41.0 candidate (ADR-038), which is not admitted; the admitted base is v3.39.0. This is lane P4 of campaign L9-NODE-PIPELINE-01. ADR-039 is its candidate decision record and does not admit itself.

## Bounded delta

- `semantics/repository_registry.yaml#factory_born_entries`: the `birth_provenance` field set, the id rule, `lifecycle_at_registration: current`, the class rule, and `pinned_entries_never_carry_birth_provenance`. No repository entry is added or changed.
- `scripts/validate-semantics.py` RC-023: entries carrying `birth_provenance` are counted apart from the 33-entry pinned census and checked by shape. RC-023-NEG grows from 57 to 70 cases.
- `ops/register-birth.py`, `ops/test-register-birth.py`, and the `register` job in `.github/workflows/repo-birth-bootstrap.yml`.
- ADR-039 (candidate).

## Outstanding Unknowns

- Whether the org secret `GH_TOKEN` can read the private newborn and the factory, and push a branch and open a PR on `.github`, is unverified here.
- Pre-receipt repositories stay hand-registered: they have nothing to attest.

## Authority

`Quantum-L9/.github` owns this ledger. A birth receipt is evidence and confers no authority (L9-EVIDENCE-001). Nothing here grants mutation, publication, merge, admission, deployment or execution authority. Admission of v3.42.0 requires the repository owner's explicit decision for this exact subject, and presupposes the owner's decision on v3.41.0.
