# Semantic Foundation v3.36.0

Status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-033, 2026-11-11).

v3.36.0 carries ADR-033: Domain Projection Architecture v1.

## Bounded delta

Successor to v3.35.0. A domain projection exposes canonical meaning, a domain consumer binding selects that meaning, and composition verifies compatibility; none of them creates semantic authority.

- `semantics/invariants.yaml`: `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`, `L9-SIGNAL-002`, `L9-SIGNAL-003` and `L9-SIGNAL-004`, record-equal to the Quantum-L9/.github#234 candidates.
- `semantics/vocabulary.yaml`: terms `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`, `signal_feedback_episode` and `signal_consumption` (record-equal to #234), and `domain_projection` and `domain_consumer_binding`.
- `semantics/contracts.yaml`: `l9.contract/domain-composition-compatibility@1` and `l9.contract/domain-composition-provenance@1`.
- `semantics/projection_profiles.yaml`: profile class `domain` and eight domain profiles `l9.projection/<name>@1` for `architecture`, `strategic-value`, `signals`, `governance`, `evidence-provenance`, `contracts-conformance`, `capabilities-dependencies` and `identity-attribution`, each declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`.
- `semantics/composition_profiles.yaml`: the eight `l9.compose/<name>@1` compositions, source-class namespaced, declaring the same protocol.
- New ledgers `semantics/domain_projection_model.yaml` (`DOMAIN-001`..`DOMAIN-010`) and `semantics/domain_consumer_bindings.yaml` (six bindings, `BINDING-001`..`004`, `COMPOSE-001`..`005`), registered in `semantics/canonical_sources.yaml` and `semantics/generic_compiler_manifest.yaml#requires.semantic_catalogs`.
- Sixteen registered payload schemas of type `l9.source-class-payload-schema/v1` (one projection and one composition schema per domain, each named domain_NAME_projection or domain_NAME_composition with suffix .schema.yaml under semantics/), listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`.
- Derived coordinates rebound from final bytes: `semantics/contracts.yaml#derivation` (40 invariants), and the `source_artifacts` of `semantics/capabilities.yaml` (40 invariants, 31 contracts), `semantics/lifecycle.yaml` and `semantics/receipt_catalog.yaml`.
- `scripts/validate-semantics.py`: RC-034 and RC-034-NEG.

No existing projection or composition profile changes; RC-034 pins both predecessor catalogs by canonical-JSON digest.

## Evidence

Candidate pack: `docs/candidates/domain-projection-architecture-v1/` (design departures, open blockers, reproduction). Producer rehearsal: `docs/candidates/domain-projection-architecture-v1/evidence/rehearsal.json`, compiler `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (0.10.0). Migration equivalence: `docs/candidates/domain-projection-architecture-v1/evidence/migration_equivalence.json`. Draft decision record: `docs/candidates/domain-projection-architecture-v1/ADMISSION_DECISION_DRAFT.md`.

## Outstanding Unknowns

- `l9.domain-consumer-binding/strategic-planner@1` has no resolved repository or entrypoint and is blocked for activation.
- Every binding with predecessor profiles is blocked for consumer migration until its owner records dispositions or a review.
- Compiler 0.10.0 projects and composes each domain; it does not evaluate the composition contracts over a binding's domain set.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants plan admission, strategic commitment, execution, publication, merge, admission or deployment authority, and no consumer is switched. ADR-033 admits the v3.36.0 delta.
