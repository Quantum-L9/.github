# ADR-035 — Bounded Decision Autonomy and Material Decision Escalation

**Status:** Accepted for semantic-foundation v3.38.0. The repository owner admitted v3.38.0 on 2026-11-12 by an explicit instruction in a governed Claude Code session (`session_017xwbxw3RduoWFP29VkobHR`): "push Stages B and C as stacked branches, Stage b admits all 6". Stage B is the autonomy subject of the CTO semantics admission pack v2; "all 6" selects its four recommended records and the two it marked conditional. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when the pull request carrying this record merges into `main`, after the v3.37.0 pull request it is stacked on.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.38.0**, additive successor to v3.37.0 |
| Pull request | The Quantum-L9/.github pull request from `claude-mobile/adoring-goodall-8u0rlb-autonomy` that carries this record and the candidate commit below, stacked on the v3.37.0 pull request from `claude-mobile/adoring-goodall-8u0rlb`. |
| Approved semantic tree | `semantics/` tree `7d238c39c7493f73df12d196e50747aa2086665d`, at the release-cut candidate commit `7418bd5849b986de6ad42ad7d9c88b77b573a038`. No later commit changes `semantics/`: they add this ADR, its index entry and the v3.38.0 status lines. |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges this record. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Invariants in `semantics/invariants.yaml`: `L9-AUTONOMY-001`, `L9-AUTONOMY-002` and `L9-AUTONOMY-003`.
- Vocabulary terms in `semantics/vocabulary.yaml`: `decision_resolution_class`, `material_decision_escalation` and `bounded_replanning` (all `semantic_concept`).

Admission is scoped to the v3.38.0 delta. The derivation coordinates rebound in `contracts.yaml`, `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml` are derived, not admitted meaning.

## Context

Agents with sufficient authority still escalated decisions that evidence or admitted policy already settled, and escalated vaguely ("what architecture do you want?") instead of naming the one governing decision that blocked progress. Existing law bounds authority (`L9-AUTH-001`, `L9-AUTH-002`, `L9-MONOTONIC-001`), Unknowns (`L9-UNKNOWN-001`) and hard constraints (`L9-HARD-001`), and `bounded_autonomy` names the bounded space, but none states the positive duty to resolve within it or the shape of a material escalation.

## Decision

1. Admit the six definitions above exactly as they stand in the approved semantic tree.
2. `L9-AUTONOMY-001`: decisions determined by authoritative evidence or governing policy are resolved without a new discretionary approval; a reversible realization choice within the accepted objective, architecture, contracts, scope and authorization ceiling is the agent's. It grants no capability, fact, semantics change or risk acceptance.
3. `L9-AUTONOMY-002`: a governing-decision request names the smallest material blocker, blocks only its dependency closure, and is not triggered by novelty, model confidence or preference alone. Mandatory incident, safety, security and operational notifications are never suppressed.
4. `L9-AUTONOMY-003` and `bounded_replanning`: future execution work may be revised within its accepted objective, architecture, contracts, permission ceiling, risk acceptance and convergence gates, on an evidence-backed trigger, without rewriting historical outcomes or receipts. The owner admitted these knowing the pack marked them conditional.
5. Provider-specific permissions, confidence thresholds, runtime leases, publication and merge semantics stay local to their consumers and are not imported.

## Consequences

- An agent within authority resolves evidence-determined and policy-determined decisions itself, and a request to a human names one exact decision, its owner and the blocked work.
- Profiles that select whole invariant or vocabulary sections carry the new records on their next projection: `l9.projection/stage-laws@1`, `l9.projection/stage-requirement-resolution@1` and `l9.projection/architecture-intelligence@1` (`$.invariants`), and `l9.projection/semantic-compiler-core@1` and `l9.projection/machine-vocabulary-json@1` (whole vocabulary). The profiles themselves do not change.

## Evidence relied on

- Subject discovery measured from the v3.37.0 candidate: exactly these six identities; no revision, no unclassified change, no missing dependency.
- `check_admission_closure.py --require released --main-ref claude-mobile/adoring-goodall-8u0rlb` on the candidate commit: verdict `RELEASED_CANDIDATE`, with registration, validator, `make validate`, `make check`, `make test`, release inventory and scope closure all passing.
- `scripts/validate-semantics.py` exits 0 with 61 PASS lines and no FAIL.
- Donor evidence, read-only: `Quantum-L9/Cursor-Governance@1d79d50e028935961dd631990a030ba1f22f7afc` (Program Execution safe-autonomy policy, ADR-0009, ADR-0011, ADR-0012, coding-agent authority boundaries). The pack's harvest is PARTIAL and is not admission evidence.

## Accepted limitations

- Irreducibility of `L9-AUTONOMY-003` and `bounded_replanning` against the Program Execution Program Lock and `bounded_autonomy` was not independently established; the owner admitted them regardless.
- No independent cross-domain witnesses back the autonomy candidates.

## What admission does not establish

- The role projection `l9.projection/technical-coordination@1`, its composition and payload schemas. They are a separate subject.
- Any consumer behavior, CTO mode activation or host enforcement.
- Downstream usability at `main`, which needs the producer run on the merged revision.
- Merge, publication, deployment or execution authority.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
