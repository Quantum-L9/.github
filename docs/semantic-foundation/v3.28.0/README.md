# Semantic Foundation v3.28.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.28.0 admits ten paired projection and composition profiles, and the payload schemas that let every one of them reach a PASS receipt. Each profile pair selects existing canonical sources for one consumer view. Each payload schema states what a conforming selected payload looks like, so the compiler's `payload_schema` criterion resolves instead of staying `unresolved`.

## Bounded delta

- `semantics/projection_profiles.yaml` and `semantics/composition_profiles.yaml` gain ten profile pairs: `authority-resolution`, `evidence-assessment`, `semantic-change-context`, `architecture-break-test`, `globalization-assessment`, `work-state-continuity`, `hard-constraint-context`, `identity-assurance`, `strategic-metacognition`, `strategic-planning-context`. Each composition places every source under its source-class namespace (`placement: source_class_namespace`).
- `identity-assurance`, `strategic-metacognition`, `strategic-planning-context` select each top-level field of seven sources explicitly instead of the whole document (`$`). The only field left out is the source's own `schema` field; see "Explicit field selection" below.
- 20 payload schemas are registered under `requires.artifact_schemas`, a projection and a composition schema for each of the ten profiles. The `authority-resolution` pair is hand-authored; the other 18 are derived.
- No ledger, rule, contract or invariant changes. No ADR is added.

## Derived schemas

The 18 derived schemas were written by `l9-semantic-compiler schema-derive` (Quantum-L9/l9-semantic-compiler-engine PR #26) from the payloads each profile selects. They follow the shape of the hand-authored schemas:

- keys present in every observation are `required`;
- single-token strings and booleans that never vary are `const`;
- array-item `id` values form an exact `enum`;
- arrays carry the smallest observed length as `min_items`.

Each file records its derivation in a `derivation` block:

- method `l9.schema-derivation/selected-payload@1`;
- the authority revision it was derived at;
- the profile, selector-model and source digests.

Twelve schemas were derived at `290bcd90378577392640cea9c6053c178423f0da` and six at `2349a90b86b2d90ad5b1aa5a026fee58dbec75f3`, after the selection change below.

As a control, the same method was run for the three hand-authored pairs registered at `290bcd90` (authority-resolution, pr-audit, architecture-intelligence). It carried 924 of their 936 constraints. The remaining 12 are item shapes of arrays that are empty at that revision, so nothing could be derived for them.

## Explicit field selection

The compiler finds a payload schema by `properties.schema.const`, and that same constraint is checked against the payload's own `schema` field. A profile that selects a whole source document carries that source's own `schema` field (for example `l9.actor-registry/v1` or `l9.schema-definition/v1`), so no v1 projection schema could be satisfied.

Seven `$` selectors in `identity-assurance`, `strategic-metacognition`, `strategic-planning-context` are therefore replaced by one selector per top-level field, in source order. The sources are:

- `actor_registry` and `surface_registry`;
- `strategic_plan_metacognitive_analysis_schema`;
- `strategic_plan_graph_schema`, `affected_strategic_closure_schema`, `strategic_planning_episode_schema` and `strategic_plan_revision_candidate_schema`.

Every field except the source's own `schema` declaration is still selected.

## Outstanding Unknowns and findings

- **Constraints pin the selected data.** The derived constraints describe the data selected at the recorded revision. A later change to a selected source that breaks them fails `payload_schema` until the schema is re-derived or edited. This is the same behavior as the hand-authored `authority-resolution` schemas.
- **Consumers lose one field.** Consumers of the three re-selected profiles no longer receive the seven sources' `schema` declaration fields. The source class and source ref still identify each source.
- The open findings recorded by v3.27.0 remain open.

## Authority

`Quantum-L9/.github` owns the ledgers and these schemas. A derived schema is evidence for this candidate; registering it here is what gives it standing, and only through admission of this release. This candidate does not admit itself, and it grants no producer or consumer any mutation, publication, merge, admission, projection or execution authority.
