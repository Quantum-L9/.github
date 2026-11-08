# Semantic Foundation v3.35.0

Status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-032, 2026-11-08).

v3.35.0 carries ADR-032: Source-Class Payload Dispatch Successors for Three Projection Pairs.

## Bounded delta

Successor to v3.34.0. The release number and ADR identity were selected from the merged state at 17303684538c1cd3f9bba8f64da788c7b4ceba19.

- `semantics/projection_profiles.yaml`: `l9.projection/identity-assurance@2`, `l9.projection/strategic-planning-context@2` and `l9.projection/strategic-metacognition@2`, each `successor_of` its @1 and declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`; validation rule `PROJECTION-017`.
- `semantics/composition_profiles.yaml`: `l9.compose/identity-assurance@2`, `l9.compose/strategic-planning-context@2` and `l9.compose/strategic-metacognition@2`, each composing its @2 projection and declaring the same protocol.
- `semantics/vocabulary.yaml`: terms `payload_validation_protocol`, `source_class_payload_schema` and `strict_descriptor_dialect`.
- Six registered payload schemas of type `l9.source-class-payload-schema/v1`, listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `semantics/identity_assurance_composition_v2.schema.yaml`
  - `semantics/identity_assurance_projection_v2.schema.yaml`
  - `semantics/strategic_metacognition_composition_v2.schema.yaml`
  - `semantics/strategic_metacognition_projection_v2.schema.yaml`
  - `semantics/strategic_planning_context_composition_v2.schema.yaml`
  - `semantics/strategic_planning_context_projection_v2.schema.yaml`
- No derived coordinate moves: no registered source's recorded digest or item count changes.

Withheld by the owner's decision, and still candidates in `docs/candidates/source-class-dispatch-v2/`: the composition global rule `source_class_dispatch_composition_is_source_namespaced_and_declares_the_protocol_of_its_projection_profile`, and the strict descriptor dialect document itself. The @1 profiles stay admitted and unchanged.

## Evidence

Candidate pack and rehearsal: `docs/candidates/source-class-dispatch-v2/` (Quantum-L9/.github#227, #231). Compiler: `Quantum-L9/l9-semantic-compiler-engine@d5ce17d01de72c8017e4021fbe43f9eaed2b69de`, which realizes the protocol (Quantum-L9/l9-semantic-compiler-engine#30, #34, #35); 0.10.0 marks it (#36).

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants plan admission, strategic commitment, execution, publication, merge, admission or deployment authority. ADR-032 admits the v3.35.0 delta.
