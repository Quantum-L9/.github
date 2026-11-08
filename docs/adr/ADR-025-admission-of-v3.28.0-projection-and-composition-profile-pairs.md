# ADR-025 — Admission of the v3.28.0 Projection and Composition Profile Pairs

**Status:** Accepted for semantic-foundation v3.28.0. The repository owner admitted v3.28.0 on 2026-11-08. The decision was given as an explicit instruction in a governed Claude Code session (`session_017xwbxuVL4dtKhYBnBJL62E`), which also directed the merge of Quantum-L9/.github#211 into `main`. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when #211 merges into `main`.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.28.0**, additive successor to v3.27.0 |
| Pull request | Quantum-L9/.github#211 (it integrates #214, merged into #211's branch at `4fce7fa7f17eaa08bb4dde84d014bc2a60231dd3`) |
| Approved semantic tree | `semantics/` tree `7c6f35ddc701e6913c78054745e1e2179775299f`. It is identical at the qualified authority commit `453701a671b3c9acc3400c47c926d1235adfeffd` and at #211 head `4fce7fa`, which differs from `453701a` only in the four v3.28.0 release documents. |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges #211. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Ten projection profiles in `semantics/projection_profiles.yaml`: `l9.projection/authority-resolution@1`, `l9.projection/evidence-assessment@1`, `l9.projection/semantic-change-context@1`, `l9.projection/architecture-break-test@1`, `l9.projection/globalization-assessment@1`, `l9.projection/work-state-continuity@1`, `l9.projection/hard-constraint-context@1`, `l9.projection/identity-assurance@1`, `l9.projection/strategic-metacognition@1` and `l9.projection/strategic-planning-context@1`.
- The ten matching composition profiles `l9.compose/<name>@1` in `semantics/composition_profiles.yaml`.
- Twenty payload schemas, a `<name>_projection.schema.yaml` and a `<name>_composition.schema.yaml` for each pair, registered under `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`. Two are hand-authored (`authority-resolution`); eighteen were derived by `schema-derive` and then patched in place by PATCH-01.

## Decision

Admit v3.28.0 as recorded in `docs/semantic-foundation/v3.28.0/`, and make the ten profile pairs available for use. The owner accepted these existing limitations as the basis of admission:

1. **Seven-field narrowing (PATCH-03).** It is accepted as the intended v1 selection contract of `identity-assurance@1`, `strategic-metacognition@1` and `strategic-planning-context@1`.
   - Each of the seven sources is selected field by field, without its own top-level `schema` field.
   - The excluded values stay recoverable from the pinned canonical sources through each artifact's and receipt's source coordinates. They are absent from the selected payloads.
   - Independent consumer compatibility has not been demonstrated.
2. **381 removed `string_list` `min_items` declarations (PATCH-01).** Their removal is accepted, including the 18 hand-authored `min_items: 1` of the `authority-resolution` pair.
   - The pinned v1 interpreter never enforced them, so removal changed no validation outcome.
   - No list-cardinality guarantee is claimed for any `string_list`.
3. **3,970 pinned-snapshot constraints (PATCH-02).** They are accepted as revision-bound restrictions that describe the selected data at the qualified coordinates.
   - They are not universal semantic law.
   - A later change to a selected source may fail `payload_schema` until the schema is updated and requalified. The 361 governing constraints follow from canonical declarations.
4. **Independent consumer replay.** It remains unestablished. Admission does not claim that any consumer has been migrated, validated or deployed.

## Evidence relied on

Producer qualification at the approved semantic tree is recorded in `docs/semantic-foundation/v3.28.0/RELEASE_VALIDATION.md` (PATCH-04). Machine evidence is in Quantum-L9/.github#210. The run used `Quantum-L9/l9-semantic-compiler-engine@943db9a462d35ba66771a700ece77c746295f591` (`l9-semantic-compiler` 0.9.3):

- 10 of 10 profile pairs pass `project` and `compose`, with 53 source projections, 10 compositions and no unresolved criterion;
- all 63 outputs pass independent re-verification with `payload_schema` and `selection_equivalence` both `pass`;
- all 63 receipts validate with `coverage: complete`;
- 461 of 461 negative cases are rejected or controlled as intended;
- an independent run reproduced all 126 artifact and receipt files byte-for-byte.

The semantic tree is unchanged since that run, so the evidence applies without requalification.

## What admission does not establish

- Independent consumer replay or compatibility for any of the ten profiles. The declared consumers (`l9-identity-assurance`, `strategic_plan_metacognitive_reasoner`, `plan_keeper`, among others) have no implementation reachable from this decision.
- Cardinality of any `string_list`, completeness of a payload through `payload_schema` alone, or exact membership. Those remain `selection_equivalence` and producer checks.
- Durability of the pinned-snapshot constraints across later source revisions.
- Any publication, deployment, runtime or consumer authority.

## Consequences

- The ten profile pairs and their twenty payload schemas are canonical at the effective revision. A producer pinned to it may project and compose them.
- A change to any selected source can invalidate a pinned-snapshot constraint. That is a requalification event for the affected schema, not a silent drift.
- The open findings recorded by v3.27.0 remain open.
