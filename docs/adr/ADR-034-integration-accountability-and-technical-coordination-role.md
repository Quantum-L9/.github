# ADR-034 — Integration Accountability and the Technical Coordination Role

**Status:** Accepted for semantic-foundation v3.37.0. The repository owner admitted v3.37.0 on 2026-11-11 by an explicit instruction in a governed Claude Code session (`session_017xwbxw3RduoWFP29VkobHR`): "I want to formally admit these candidates to https://github.com/Quantum-L9/.github". The candidates are the CTO semantics admission pack v2, whose Stage A subject is exactly the three records below, in the wording the owner settled in that pack (decisions D1 to D4). This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It admits Stage A only. It takes effect when the pull request carrying this record merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.37.0**, additive successor to v3.36.0 |
| Pull request | The Quantum-L9/.github pull request from `claude-mobile/adoring-goodall-8u0rlb` that carries this record and the candidate commit below. |
| Approved semantic tree | `semantics/` tree `73a6adf716799365163926ef6b3eb66661007a13`, at the release-cut candidate commit `360c5d304c70883d9b1b62acaa8c51864f8ac584`. No later commit changes `semantics/`: they add this ADR, its index entry and the v3.37.0 status lines. |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges this record. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Invariant in `semantics/invariants.yaml`: `L9-INTEGRATION-001`.
- Vocabulary terms in `semantics/vocabulary.yaml`: `technical_coordination_role` (`semantic_role`) and `integration_responsibility` (`semantic_concept`).

Admission is scoped to the v3.37.0 delta. The derivation coordinates rebound in `contracts.yaml`, `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml` are derived, not admitted meaning.

## Context

Independently verified technical contributions can fail when they are combined into one consequential artifact. Global law already governs authority (`L9-AUTH-001`, `L9-AUTH-002`), canonical ownership (`L9-OWNER-001`), coordination (`L9-COORD-001`), correctness (`L9-CORRECTNESS-001`), assurance (`L9-ASSURANCE-001`) and Strategy (`L9-STRATEGY-001`). None of them requires that one accountable integration responsibility be explicitly assigned for an exact shared acceptance subject before integrated acceptance is claimed, or states that individually green receipts do not prove the combination. That is the irreducible law added here. The existing law stays in force unchanged.

## Decision

1. Admit the three definitions above exactly as they stand in the approved semantic tree.
2. `technical_coordination_role` "coordinates the assignment of bounded work to eligible executors within their existing authorization". It does not route: Gate keeps Constellation admission and routing, and task assignment confers no capability or action authority (D1).
3. `L9-INTEGRATION-001` requires the responsibility to be assigned before integrated acceptance is claimed. A label attached after a release does not satisfy it (D2).
4. The invariant keeps accountability, combined-subject verification and the no-authority-transfer guard in one statement paragraph (D3).
5. Both concepts are vocabulary terms. No model ledger, contract, actor identity or projection profile is added (D4).

## Consequences

- A claim of integrated correctness or completion must name its exact combined subject and the responsibility assigned to it, and must carry evidence about that combination.
- A role, agent or session can coordinate technical work without inheriting Strategy, canonical architecture, durable work state, or execution, admission, publication or merge authority.
- Profiles that select whole invariant or vocabulary sections carry the new records on their next projection: `l9.projection/stage-laws@1`, `l9.projection/stage-requirement-resolution@1` and `l9.projection/architecture-intelligence@1` (`$.invariants`), and `l9.projection/semantic-compiler-core@1` and `l9.projection/machine-vocabulary-json@1` (whole vocabulary). The profiles themselves do not change.

## Evidence relied on

- Subject discovery measured from the v3.36.0 admission: exactly `L9-INTEGRATION-001`, `technical_coordination_role` and `integration_responsibility`; no revision, no unclassified change, no missing dependency; declared scope closure passes.
- `check_admission_closure.py --require released` on the candidate commit: verdict `RELEASED_CANDIDATE`, with registration, validator, `make validate`, `make check`, `make test`, release inventory and scope closure all passing.
- `scripts/validate-semantics.py` exits 0 with 61 PASS lines and no FAIL.
- Adversarial witnesses from the pack, checked against the wording: two individually green contributions that conflict when combined (W1) and two components that bind different revisions at a shared boundary (W2) are not integrated acceptance; a responsibility named only after a release (W3) does not meet the assignment requirement; a coordination role attempting a Constellation routing decision or a merge grant (W4) is denied by the term's definition and rules.

## What admission does not establish

- The role projection `l9.projection/technical-coordination@1`, its composition and payload schemas. They are a separate later subject.
- The autonomy candidates `L9-AUTONOMY-001`, `L9-AUTONOMY-002`, `decision_resolution_class` and `material_decision_escalation`, and the conditional `L9-AUTONOMY-003` and `bounded_replanning`. They are a separate later subject.
- Any consumer contract, CTO mode or host behavior in `Quantum-L9/Cursor-Governance`.
- Downstream usability at `main`, which needs the producer run on the merged revision.
- An actor identity, Constellation routing, Plan Keeper authority, or merge, publication, deployment or execution authority.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
