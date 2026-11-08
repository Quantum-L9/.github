# ADR-032 — Source-Class Payload Dispatch Successors for Three Projection Pairs

**Status:** Accepted for semantic-foundation v3.35.0. The repository owner admitted v3.35.0 on 2026-11-08. The decision was given as an explicit instruction in a governed Claude Code session (`session_017xwbxvywoFfCNxygSZn22m`): "explicit admission decision for this exact subject granted", with "bump it to mark the new protocol" (Semantic Compiler 0.10.0, Quantum-L9/l9-semantic-compiler-engine#36). In the same session the owner then decided to admit the subject without the composition global rule. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when the pull request carrying this record merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.35.0**, additive successor to v3.34.0 |
| Pull request | The Quantum-L9/.github pull request from `claude-mobile/relaxed-newton-tlo2ma` that carries this record. The candidate pack reached `main` through Quantum-L9/.github#227 and #231. |
| Approved semantic tree | `semantics/` tree `de268117ff9eab3d9efe8fa5ae54702ce67649fb`. It is identical at the qualified candidate commit `451a87c2649a2e01f27371e3ec2ebdae5a9c2dd2` and at the pull request's head. No later commit changes `semantics/`: they add this ADR, its index, the v3.35.0 release documents, a test-only import fix in the admission skill and the session handoff reports. |
| Producer | `Quantum-L9/l9-semantic-compiler-engine@d5ce17d01de72c8017e4021fbe43f9eaed2b69de` (`main`) |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges this record. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- `l9.projection/identity-assurance@2`, `l9.projection/strategic-planning-context@2` and `l9.projection/strategic-metacognition@2` in `semantics/projection_profiles.yaml`. Each is `successor_of` its @1. Each keeps every @1 selector, restores `$` on the source classes PATCH-03 narrowed (seven in all), outputs `…/v2` and declares `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`.
- `l9.compose/identity-assurance@2`, `l9.compose/strategic-planning-context@2` and `l9.compose/strategic-metacognition@2` in `semantics/composition_profiles.yaml`, each composing its @2 projection and declaring the same protocol.
- Validation rule `PROJECTION-017` in `semantics/projection_profiles.yaml#validation_rules`, which changes the registered source `l9.source/projection-profiles@1`.
- Vocabulary terms `payload_validation_protocol`, `source_class_payload_schema` and `strict_descriptor_dialect` in `semantics/vocabulary.yaml`.
- Six registered payload schemas of type `l9.source-class-payload-schema/v1`, listed in `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `identity_assurance_projection_v2.schema.yaml` (`l9.projection.identity-assurance/v2`)
  - `identity_assurance_composition_v2.schema.yaml` (`l9.composed-projection.identity-assurance/v2`)
  - `strategic_planning_context_projection_v2.schema.yaml` (`l9.projection.strategic-planning-context/v2`)
  - `strategic_planning_context_composition_v2.schema.yaml` (`l9.composed-projection.strategic-planning-context/v2`)
  - `strategic_metacognition_projection_v2.schema.yaml` (`l9.projection.strategic-metacognition/v2`)
  - `strategic_metacognition_composition_v2.schema.yaml` (`l9.composed-projection.strategic-metacognition/v2`)

Admission is scoped to the v3.35.0 delta.

## Context

PATCH-03 narrowed seven source selectors in the @1 profiles of these three pairs, because the legacy payload schemas chose a validator from a payload's own top-level `schema` field: a source that kept that field collided with the union grammar. The Semantic Compiler now selects a payload's validator from facts it has already verified: the profile's output schema and the source class (Quantum-L9/l9-semantic-compiler-engine#30). The @2 successors declare that procedure, restore the narrowed selections and register one strict descriptor per source class. The descriptors were compiled by the compiler's own grammar builder (#35) from the pinned sources. The candidate pack `docs/candidates/source-class-dispatch-v2/` rehearsed all three pairs end to end.

## Decision

1. Admit the definitions above exactly as `docs/candidates/source-class-dispatch-v2/overlays/` states them. The registered schemas drop only the candidate marker `admission: not_granted`.
2. **Withhold** the composition global rule `source_class_dispatch_composition_is_source_namespaced_and_declares_the_protocol_of_its_projection_profile`. It is non-identity content of a registry host, which the admission procedure cannot admit; the owner chose to admit without it. `PROJECTION-017`, together with each compose@2 record's own `payload_validation`, carries the protocol. The rule stays a candidate in the pack.
3. The strict descriptor dialect `l9.schema-dialect/candidate-v2@1` is admitted only as the vocabulary term that names it, and that term says the dialect is a candidate. The dialect document stays a candidate in each grammar pack. Admitting it, with the compiler change that would require, is a separate contract.
4. The @1 profiles stay admitted and unchanged. A consumer moves to @2 by its own release process.
5. The admission gate measured the subject from v3.34.0 (`--admitted-base v3.34.0`). The current verifier rejects ADR-031 because its subject table has no target-class row; that row became required (#223) after ADR-031 was accepted (#229). The gap is reported, not waived, and this record does not repair it.

## Consequences

- A projection or composition under an @2 profile is validated by the descriptor its verified source class selects. No payload field takes part in the choice.
- A restored source keeps its own top-level `schema` field in the projected payload.
- Semantic Compiler 0.10.0 marks the protocol; the compiler at `d5ce17d` already realizes it.

## Evidence relied on

- Candidate pack and rehearsal: `docs/candidates/source-class-dispatch-v2/` (`evidence/rehearsal.json`). Every receipt passes with `dispatch_basis: verified_profile_output_schema_and_verified_source_class`, and coverage is complete.
- Admission gate on the qualified candidate commit: discovery from v3.34.0 finds exactly this subject, with no unclassified change and no derived coordinate moving; the verdict reached RELEASED_CANDIDATE. The producer at the commit named above ran the three @2 pairs twice, and every artifact passed independent verification. See `docs/semantic-foundation/v3.35.0/RELEASE_VALIDATION.md`.
- `scripts/validate-semantics.py` exits 0.

## What admission does not establish

- The admission of the strict descriptor dialect document, or of the withheld composition global rule.
- Any consumer's migration from @1 to @2, or any consumer replay or binding.
- Merge, publication, deployment or execution authority.
