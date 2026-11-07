# Semantic Foundation v3.28.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.28.0 admits ten paired projection and composition profiles, and the payload schemas that let them reach a PASS receipt. Each profile pair selects existing canonical sources for one consumer view. Each payload schema states what a conforming selected payload looks like, so the compiler's `payload_schema` criterion resolves instead of staying `unresolved`.

## Bounded delta

- `semantics/projection_profiles.yaml` and `semantics/composition_profiles.yaml` gain ten profile pairs: `authority-resolution`, `evidence-assessment`, `semantic-change-context`, `architecture-break-test`, `globalization-assessment`, `work-state-continuity`, `strategic-planning-context`, `strategic-metacognition`, `identity-assurance`, `hard-constraint-context`. Each composition places every source under its source-class namespace (`placement: source_class_namespace`).
- Payload schemas registered under `requires.artifact_schemas`:
  - `authority-resolution`: projection and composition, hand-authored.
  - `evidence-assessment`, `semantic-change-context`, `architecture-break-test`, `globalization-assessment`, `work-state-continuity`, `hard-constraint-context`: projection and composition, derived.
  - `identity-assurance`, `strategic-metacognition`, `strategic-planning-context`: composition only, derived.
- No ledger, rule, contract or invariant changes. No ADR is added.

## Derived schemas

The 15 derived schemas were written by `l9-semantic-compiler schema-derive` (Quantum-L9/l9-semantic-compiler-engine PR #26) from the payloads each profile selects at `.github@290bcd90378577392640cea9c6053c178423f0da`. They follow the shape of the hand-authored schemas:

- keys present in every observation are `required`;
- single-token strings and booleans that never vary are `const`;
- array-item `id` values form an exact `enum`;
- arrays carry the smallest observed length as `min_items`.

Each file records its derivation in a `derivation` block:

- method `l9.schema-derivation/selected-payload@1`;
- the authority revision;
- the profile, selector-model and source digests.

As a control, the same method was run for the three hand-authored pairs registered at that revision (authority-resolution, pr-audit, architecture-intelligence). It carried 924 of their 936 constraints. The remaining 12 are item shapes of arrays that are empty at that revision, so nothing could be derived for them.

## Outstanding Unknowns and findings

- **No projection schema for three profiles.** `identity-assurance`, `strategic-metacognition` and `strategic-planning-context` select whole source documents (`$`), which carry their own top-level `schema` field. The compiler finds a payload schema by `properties.schema.const`, and that same constraint is checked against the payload's own `schema` field. No v1 projection schema can satisfy both, so none is registered and their projection and composition receipts stay `unknown`. The fix is either a profile change (select fields instead of `$`) or a compiler dispatch change; both are owner decisions this candidate does not take.
- **Constraints pin the selected data.** The derived constraints describe the data selected at the recorded revision. A later change to a selected source that breaks them fails `payload_schema` until the schema is re-derived or edited. This is the same behavior as the hand-authored `authority-resolution` schemas.
- The open findings recorded by v3.27.0 remain open.

## Authority

`Quantum-L9/.github` owns the ledgers and these schemas. A derived schema is evidence for this candidate; registering it here is what gives it standing, and only through admission of this release. This candidate does not admit itself, and it grants no producer or consumer any mutation, publication, merge, admission, projection or execution authority.
