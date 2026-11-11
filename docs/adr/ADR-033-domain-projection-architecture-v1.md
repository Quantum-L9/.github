# ADR-033 — Domain Projection Architecture v1: Eight Domain Projections, Six Domain Consumer Bindings, and Qualitative Strategic Value and Signal Law

**Status:** Accepted for semantic-foundation v3.36.0. The repository owner admitted v3.36.0 on 2026-11-11 by an explicit instruction in a governed Claude Code session (`session_017xwbxxt7rGKHw3NhwSXSP4`): "Once grammar and all is compiled the projection profiles are ready for admission. There’s another skill that does that. There’s a formal process. It’s probably in https://github.com/Quantum-L9/.github find it run it open stacked pr with full admission". "Full admission" selects option 1 of the decision record prepared for this subject (`docs/candidates/domain-projection-architecture-v1/ADMISSION_DECISION_DRAFT.md`): admit the whole subject. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when the pull request carrying this record merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.36.0**, additive successor to v3.35.0 |
| Pull request | The Quantum-L9/.github pull request from `claude-mobile/kind-babbage-tr5ekt-admission` that carries this record, stacked on Quantum-L9/.github#238 (downstream rehearsal), which is stacked on Quantum-L9/.github#237 (the registered subject and the v3.36.0 release record). |
| Approved semantic tree | `semantics/` tree `16ca4cd9cd08ed4602a178a3c57032c9cd5186ac`. It is identical at the release-cut commit `f540b5ed68947064f41a76d36a7fe591fbce700f`, at the head of #237 `68b29279a32a4f3080fa4f563c5725337920a24f` and at the head of #238 `3eb08619f06f5ea44d4fd425baa6852591d5f4d1`. No later commit changes `semantics/`: they add the candidate evidence, a formatting pass over the validator and candidate tools, a `.gitignore` fix, this ADR, its index and the v3.36.0 status lines. |
| Producer | `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (`main`, Semantic Compiler 0.10.0) |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges this record. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Invariants in `semantics/invariants.yaml`, record-equal to the Quantum-L9/.github#234 candidates: `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`, `L9-SIGNAL-002`, `L9-SIGNAL-003` and `L9-SIGNAL-004`.
- Vocabulary terms in `semantics/vocabulary.yaml`: `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`, `signal_feedback_episode` and `signal_consumption` (record-equal to #234), and `domain_projection` and `domain_consumer_binding`.
- Contracts in `semantics/contracts.yaml`: `l9.contract/domain-composition-compatibility@1` and `l9.contract/domain-composition-provenance@1`.
- The profile class `domain` in `semantics/projection_profiles.yaml#profile_classes`, a content change of the registered source `l9.source/projection-profiles@1`.
- Projection profiles of class `domain` in `semantics/projection_profiles.yaml`, each declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`:
  - `l9.projection/architecture@1`
  - `l9.projection/strategic-value@1`
  - `l9.projection/signals@1`
  - `l9.projection/governance@1`
  - `l9.projection/evidence-provenance@1`
  - `l9.projection/contracts-conformance@1`
  - `l9.projection/capabilities-dependencies@1`
  - `l9.projection/identity-attribution@1`
- Composition profiles in `semantics/composition_profiles.yaml`, each source-class namespaced over its domain profile and declaring the same protocol:
  - `l9.compose/architecture@1`
  - `l9.compose/strategic-value@1`
  - `l9.compose/signals@1`
  - `l9.compose/governance@1`
  - `l9.compose/evidence-provenance@1`
  - `l9.compose/contracts-conformance@1`
  - `l9.compose/capabilities-dependencies@1`
  - `l9.compose/identity-attribution@1`
- New registered canonical sources: `l9.source/domain-projection-model@1` (`semantics/domain_projection_model.yaml`, artifact `l9.domain-projection-model/global@1`, rules `DOMAIN-001` to `DOMAIN-010`) and `l9.source/domain-consumer-bindings@1` (`semantics/domain_consumer_bindings.yaml`, artifact `l9.domain-consumer-binding-catalog/global@1`, rules `BINDING-001` to `BINDING-004` and `COMPOSE-001` to `COMPOSE-005`), with the six bindings `l9.domain-consumer-binding/gar@1`, `l9.domain-consumer-binding/strategic-planner@1`, `l9.domain-consumer-binding/cursor@1`, `l9.domain-consumer-binding/coding-agent@1`, `l9.domain-consumer-binding/simple-plan@1` and `l9.domain-consumer-binding/claude-code@1`.
- Sixteen registered payload schemas of type `l9.source-class-payload-schema/v1`, listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `domain_architecture_projection.schema.yaml` (`l9.projection.domain.architecture/v1`)
  - `domain_architecture_composition.schema.yaml` (`l9.composed-projection.domain.architecture/v1`)
  - `domain_strategic_value_projection.schema.yaml` (`l9.projection.domain.strategic-value/v1`)
  - `domain_strategic_value_composition.schema.yaml` (`l9.composed-projection.domain.strategic-value/v1`)
  - `domain_signals_projection.schema.yaml` (`l9.projection.domain.signals/v1`)
  - `domain_signals_composition.schema.yaml` (`l9.composed-projection.domain.signals/v1`)
  - `domain_governance_projection.schema.yaml` (`l9.projection.domain.governance/v1`)
  - `domain_governance_composition.schema.yaml` (`l9.composed-projection.domain.governance/v1`)
  - `domain_evidence_provenance_projection.schema.yaml` (`l9.projection.domain.evidence-provenance/v1`)
  - `domain_evidence_provenance_composition.schema.yaml` (`l9.composed-projection.domain.evidence-provenance/v1`)
  - `domain_contracts_conformance_projection.schema.yaml` (`l9.projection.domain.contracts-conformance/v1`)
  - `domain_contracts_conformance_composition.schema.yaml` (`l9.composed-projection.domain.contracts-conformance/v1`)
  - `domain_capabilities_dependencies_projection.schema.yaml` (`l9.projection.domain.capabilities-dependencies/v1`)
  - `domain_capabilities_dependencies_composition.schema.yaml` (`l9.composed-projection.domain.capabilities-dependencies/v1`)
  - `domain_identity_attribution_projection.schema.yaml` (`l9.projection.domain.identity-attribution/v1`)
  - `domain_identity_attribution_composition.schema.yaml` (`l9.composed-projection.domain.identity-attribution/v1`)

Admission is scoped to the v3.36.0 delta. The derivation coordinates rebound in `contracts.yaml`, `capabilities.yaml`, `lifecycle.yaml` and `receipt_catalog.yaml` are derived, not admitted meaning.

## Context

Each long-lived consumer (GAR, Strategic Planner, Cursor-Governance, the coding agent) re-decided which canonical semantics to select, and the qualitative Strategic Value and Signal law proposed in #234 could not be projected until it was canonical. v3.36.0 introduces reusable projections organized by semantic concern: a domain projection exposes canonical meaning, a domain consumer binding selects that meaning, and composition verifies compatibility. None of them creates semantic authority, and the canonical sources keep their owners.

## Decision

1. Admit the definitions above exactly as they stand in the approved semantic tree. This admits the whole subject, option 1 of the prepared decision record.
2. The design pack's identities `l9.consumer-binding/*` and `l9.composition.{compatibility,provenance}@1` are admitted under the names above: `consumer_binding` and `domain_binding` already carry admitted meaning, and global contracts live only in `semantics/contracts.yaml`. The mapping is recorded in `docs/candidates/domain-projection-architecture-v1/README.md`.
3. Behavioral prohibitions of each domain are admitted as `forbidden_interpretations` in the domain projection model, not as profile `forbidden` categories, because a category without a declared criterion stays unresolved (`PROJECTION-016`).
4. Every existing projection and composition profile stays admitted and unchanged; `RC-034` pins both predecessor catalogs by canonical-JSON digest.
5. No consumer is switched. Each binding carries its declared unresolved coordinates, and admission does not resolve them.

## Consequences

- A consumer can bind domain projections by exact profile id and digest instead of selecting overlapping semantics itself.
- `L9-SVQ-*` and `L9-SIGNAL-*` are global law, selectable through `l9.projection/strategic-value@1` and `l9.projection/signals@1`.
- `scripts/validate-semantics.py` `RC-034` enforces the domain, binding and composition rules on every change.

## Evidence relied on

- Producer rehearsal (`docs/candidates/domain-projection-architecture-v1/evidence/rehearsal.json`): 39 grammars, 0 inexpressible; 8 of 8 pairs synthesized; 47 of 47 projection and composition receipts pass with complete coverage and empty unresolved criteria; byte-identical replay; an independent clone reproduced all 91 emitted files.
- Admission skill CONFIRM stage on the qualified tree (`evidence/downstream/report.json`, authority commit `0b46944911bda80ba375f448a7513630216b5d89`): both producer runs pass for 8 projection profiles and 8 compositions; 39 projections and 8 compositions independently verified with 0 gaps; 225 of 225 negative controls rejected; 94 files byte-identical across runs.
- Subject discovery measured from the v3.35.0 admission (`--admitted-base v3.35.0`): exactly this subject, no revision, no unclassified change, no missing dependency; declared scope closure passes (`evidence/subject.json`).
- `scripts/validate-semantics.py`, `make validate` and `make check` pass; the pull requests' CI passes `validate-semantics.py` and `validate-starters.sh` (the `make test` suite). The checker's combined `evaluate()` was not run in the authoring session because it invokes `make test`, which that session's execution gate reserves for CI.
- Migration equivalence for the four bindings with predecessor profiles (`evidence/migration_equivalence.json`).

## What admission does not establish

- Activation of `l9.domain-consumer-binding/strategic-planner@1`, whose repository and entrypoint are unresolved.
- Any consumer's migration from its predecessor profiles: dispositions for GAR (123 uncovered nodes), Strategic Planner (14) and Cursor (24), and the authority-neutrality review of the coding agent's 133 added nodes, are still owed.
- Evaluation of the two composition contracts over a binding's domain set by the compiler, which 0.10.0 does not implement.
- Downstream usability at `main`, which needs the producer run on the merged revision.
- Merge, publication, deployment or execution authority.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
