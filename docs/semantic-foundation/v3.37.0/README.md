# Semantic Foundation v3.37.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**.

v3.37.0 proposes integration accountability and an authority-neutral technical coordination role.

## Bounded delta

Successor to v3.36.0. Three source records are added. Nothing else changes in meaning.

- `semantics/invariants.yaml`: `L9-INTEGRATION-001`. When independently produced contributions jointly determine one consequential artifact or acceptance subject, an integration responsibility must be explicitly assigned for that subject and scope before integrated acceptance is claimed. Individually green contributions do not prove the combination. The responsibility transfers no ownership and confers no governing decision authority.
- `semantics/vocabulary.yaml`: `technical_coordination_role` (`semantic_role`), which coordinates the assignment of bounded work to eligible executors within their existing authorization and owns no Strategy, architecture, implementation truth, durable work state or action authority; and `integration_responsibility` (`semantic_concept`), the explicitly assigned, subject-scoped accountability that the invariant requires.
- Derived coordinates rebound from final bytes: `semantics/contracts.yaml#derivation` (41 invariants), and the `source_artifacts` of `semantics/capabilities.yaml` (41 invariants, 31 contracts), `semantics/lifecycle.yaml` and `semantics/receipt_catalog.yaml`.

No contract, canonical source, projection profile, composition profile or payload schema changes. No existing projection profile selects the new records by id.

## Evidence

Admission subject discovery (`.claude/skills/l9-projection-admission/scripts/discover_admission_subject.py`) measured from the v3.36.0 admission finds exactly these three identities: no revision, no unclassified change, no missing dependency. The candidate wording is the settled D1 to D4 wording of the CTO semantics admission pack v2: "coordinates the assignment of bounded work" replaces "routes bounded work", because Gate keeps Constellation routing; responsibility is assigned before integrated acceptance is claimed; the three obligations stay in one statement paragraph; no model ledger is added. It supersedes the unpublished draft branch `feat/technical-coordination-semantic-admission-v3-37` at `0860192215b8f2045659ff04dfc0f1a241211380`.

## Outstanding Unknowns

- The role projection `l9.projection/technical-coordination@1`, its composition and payload schemas are a separate later subject. They are not in this release.
- The autonomy candidates `L9-AUTONOMY-001`, `L9-AUTONOMY-002`, `decision_resolution_class` and `material_decision_escalation` are a separate later subject.

## Authority

`Quantum-L9/.github` owns these ledgers. This candidate does not admit itself. Nothing here creates an actor identity, Constellation routing, Plan Keeper authority, or execution, publication, merge, admission or deployment authority.
