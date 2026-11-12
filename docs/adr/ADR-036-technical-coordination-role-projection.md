# ADR-036 — Technical Coordination Role Projection

**Status:** Accepted for semantic-foundation v3.39.0. The repository owner admitted v3.39.0 by explicit instructions in a governed Claude Code session (`session_017xwbxw3RduoWFP29VkobHR`): on 2026-11-11, "I want to formally admit these candidates to https://github.com/Quantum-L9/.github" and "Use https://github.com/Quantum-L9/l9-semantic-compiler-engine to compile the missing files", for the CTO semantics admission pack v2, whose Stage C is this profile pair; and on 2026-11-12, "push Stages B and C as stacked branches". This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when the pull request carrying this record merges into `main`, after the v3.38.0 and v3.37.0 pull requests it is stacked on.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.39.0**, additive successor to v3.38.0 |
| Pull request | The Quantum-L9/.github pull request from `claude-mobile/adoring-goodall-8u0rlb-coordination` that carries this record and the candidate commit below, stacked on the v3.38.0 pull request from `claude-mobile/adoring-goodall-8u0rlb-autonomy`. |
| Approved semantic tree | `semantics/` tree `d7f2fd0aa782a53dba3a101af2d4a551441e3f04`, at the release-cut candidate commit `80b0ffb4d0df4d1ffd69bdd388fcdf9c7873b704`. The earlier candidate commit `3f9b90a6a980e10d34e909d8df9b5ef2d0c24ca5` (tree `55fd1a232c395bbddf66d2cfa2934f92466e721f`) is superseded: review on the pull request found that the selected contracts cited six invariants the profile did not select, and the profile now closes over them. No later commit changes `semantics/`: they add this ADR, its index entry and the v3.39.0 status lines. |
| Producer | `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (Semantic Compiler 0.10.0) |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges this record. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Projection profile `l9.projection/technical-coordination@1` in `semantics/projection_profiles.yaml` (class `consumer`, consumer `technical_coordination_role`), declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`.
- Composition profile `l9.compose/technical-coordination@1` in `semantics/composition_profiles.yaml`, source-class namespaced over that profile, declaring the same protocol.
- Registered payload schemas of type `l9.source-class-payload-schema/v1`, listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `technical_coordination_projection.schema.yaml` (`l9.schema/technical-coordination-projection@1`, `l9.projection.technical-coordination/v1`)
  - `technical_coordination_composition.schema.yaml` (`l9.schema/technical-coordination-composition@1`, `l9.composed-projection.technical-coordination/v1`)

Admission is scoped to the v3.39.0 delta. The `scripts/validate-semantics.py` change is validation tooling, not admitted meaning.

## Context

A technical coordination role needs a small, source-bound semantic context: the integration and autonomy law admitted in v3.37.0 and v3.38.0, with the authority, ownership, assurance, Unknown, provenance, strategy and signal law it operates under. Without a profile, each consumer re-selects that context itself.

## Decision

1. Admit the four definitions above exactly as they stand in the approved semantic tree.
2. The profile selects `technical_coordination_role`, `integration_responsibility`, `decision_resolution_class`, `material_decision_escalation`, `bounded_autonomy`, `plan_keeper` and `signal_consumption`; `L9-INTEGRATION-001`, `L9-AUTONOMY-001`, `L9-AUTONOMY-002` and nineteen existing invariants; five global contracts; and `authority_model` and `strategic_cognition_model` sections. `L9-AUTONOMY-003` and `bounded_replanning` are not selected.
3. It is a `consumer` profile, not a ninth domain projection, and it grants no authority or runtime capability. Its forbidden categories all have declared criteria.
4. The payload schemas were rendered by the compiler, not hand-authored.
5. Every selected contract is closed over its `source_invariants`: the profile also selects `L9-SEM-001`, `L9-SCOPE-001`, `L9-CORRECTNESS-001`, `L9-EVIDENCE-001`, `L9-REVISION-001` and `L9-DERIVED-001`.
6. DOMAIN-010 keeps its predecessor digests exact and names this pair as registered after its pin.

## Consequences

- A consumer can bind the role's semantics by exact profile id and digest. `Quantum-L9/Cursor-Governance` CTO mode (`/lcto`) is that consumer and rebinds to the admitted digests after merge.
- Adding a further non-domain profile is an explicit DOMAIN-010 edit.

## Evidence relied on

- Producer rehearsal (`docs/candidates/technical-coordination-v1/evidence/rehearsal.json`), reproducible with `rehearse.py --check` from any commit carrying the approved `semantics/` tree, because its base is derived from that tree: 5 grammars, 0 inexpressible; the candidate pair synthesized; 5 projections and 1 composition pass with complete coverage and empty unresolved criteria; byte-identical replay of 12 files.
- Subject discovery measured from the v3.38.0 candidate: exactly the four identities above; every dependency admitted or in the subject; no unclassified change.
- `check_admission_closure.py --require released --main-ref claude-mobile/adoring-goodall-8u0rlb-autonomy` on the candidate commit: verdict `RELEASED_CANDIDATE`, registration with no unresolvable declarations, validator, `make validate`, `make check`, `make test`, release inventory and scope closure all passing.
- `scripts/validate-semantics.py` exits 0 with 61 PASS lines and no FAIL; a mutation of a predecessor profile still fails DOMAIN-010.

## What admission does not establish

- Downstream usability at `main`, which needs the producer run on the merged revision.
- Any consumer's activation, or a host's enforcement of the role.
- An actor identity, Constellation routing, Plan Keeper authority, or merge, publication, deployment or execution authority.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
