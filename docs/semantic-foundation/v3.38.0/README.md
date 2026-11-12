# Semantic Foundation v3.38.0

Status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-035, 2026-11-12).

v3.38.0 carries ADR-035: bounded decision autonomy and material decision escalation.

## Bounded delta

Successor to v3.37.0.

- `semantics/invariants.yaml`: `L9-AUTONOMY-001`, `L9-AUTONOMY-002` and `L9-AUTONOMY-003`.
- `semantics/vocabulary.yaml`: terms `decision_resolution_class`, `material_decision_escalation` and `bounded_replanning`.
- Derived coordinates rebound from final bytes: `semantics/contracts.yaml#derivation` (44 invariants), and the `source_artifacts` of `semantics/capabilities.yaml` (44 invariants, 31 contracts), `semantics/lifecycle.yaml` and `semantics/receipt_catalog.yaml`.

No contract, canonical source, source class, projection profile, composition profile or payload schema changes.

## Evidence

Admission subject discovery measured from the v3.37.0 candidate finds exactly these six identities: no revision, no unclassified change, no missing dependency. The wording is the Stage B candidate set of the CTO semantics admission pack v2 (`autonomy-semantic-candidates.CANDIDATE.yaml`), including the two records the pack marked conditional, `L9-AUTONOMY-003` and `bounded_replanning`. Donor evidence: `Quantum-L9/Cursor-Governance@1d79d50e028935961dd631990a030ba1f22f7afc` (Program Execution safe-autonomy policy, ADR-0009, ADR-0011, ADR-0012, the coding-agent authority boundaries).

## Outstanding Unknowns

- The pack's own harvest evidence is PARTIAL: source sampling, no producer-validated authority receipt, no independent cross-domain witnesses.
- `L9-AUTONOMY-003` and `bounded_replanning` were marked conditional by the pack: their irreducibility against the Program Execution Program Lock and the existing term `bounded_autonomy` was not independently established.
- The role projection `l9.projection/technical-coordination@1` that selects these records is a separate later subject.

## Authority

`Quantum-L9/.github` owns these ledgers. ADR-035 admits the v3.38.0 delta. Nothing here creates an actor identity, Constellation routing, Plan Keeper authority, or execution, publication, merge, admission or deployment authority.
