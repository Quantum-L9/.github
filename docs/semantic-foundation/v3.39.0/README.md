# Semantic Foundation v3.39.0

Status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-036, 2026-11-12).

v3.39.0 carries ADR-036: the technical coordination role projection.

## Bounded delta

Successor to v3.38.0.

- `semantics/projection_profiles.yaml`: `l9.projection/technical-coordination@1` (class `consumer`, consumer `technical_coordination_role`), declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`. It selects the v3.37.0 and v3.38.0 records (`technical_coordination_role`, `integration_responsibility`, `decision_resolution_class`, `material_decision_escalation`, `L9-INTEGRATION-001`, `L9-AUTONOMY-001`, `L9-AUTONOMY-002`) with `bounded_autonomy`, `plan_keeper`, `signal_consumption`, thirteen existing invariants, five contracts, and `authority_model` and `strategic_cognition_model` sections. `L9-AUTONOMY-003` and `bounded_replanning` are not selected.
- `semantics/composition_profiles.yaml`: `l9.compose/technical-coordination@1`, source-class namespaced, declaring the same protocol.
- Two registered payload schemas of type `l9.source-class-payload-schema/v1`, `semantics/technical_coordination_projection.schema.yaml` (`l9.projection.technical-coordination/v1`) and `semantics/technical_coordination_composition.schema.yaml` (`l9.composed-projection.technical-coordination/v1`), rendered by the compiler and listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`.
- `scripts/validate-semantics.py`: DOMAIN-010 (RC-034) names the profiles registered after its pin, so the predecessor digests stay exact.

No invariant, vocabulary term, contract or existing profile changes.

## Evidence

Producer rehearsal: `docs/candidates/technical-coordination-v1/evidence/rehearsal.json`, compiler `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (0.10.0): 5 grammars, 0 inexpressible; 5 projections and 1 composition pass with complete coverage and empty unresolved criteria; byte-identical replay (12 files). Reproduce with `docs/candidates/technical-coordination-v1/rehearse.py --check`.

## Outstanding Unknowns

- Downstream usability at `main` needs the producer run on the merged revision.
- The consumer in Quantum-L9/Cursor-Governance (CTO mode) binds this profile with candidate digests until it rebinds to the admitted ones.

## Authority

`Quantum-L9/.github` owns these ledgers. ADR-036 admits the v3.39.0 delta. Nothing here creates an actor identity, Constellation routing, Plan Keeper authority, or execution, publication, merge, admission or deployment authority.
