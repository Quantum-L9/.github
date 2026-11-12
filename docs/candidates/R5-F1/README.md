# R5-F1 candidate pack — Fixture-IR and Conformance-IR structural schemas

Contract `L9-GH-R5-F1-001`, campaign R5 conformance-first. Status: **candidate, not registered, not admitted.**
Baseline `Quantum-L9/.github@f8e44d1536cb218de41dde4685c606a4d6460915` (v3.39.0, ADR-036). First drafted on
`dcd9d00` (v3.36.0, ADR-033) as v3.37.0 / ADR-034; renumbered to v3.40.0 / ADR-037 when v3.37.0 to v3.39.0 were
admitted on `main` first (audited predecessor tip `15faa586ae2c` on `agent/r5/F1`).

This pack is evidence for an owner decision. Nothing here is canonical until it is registered under `semantics/`,
released and admitted by the owner (`.claude/skills/l9-projection-admission`).

## Contents

| Path | What |
| --- | --- |
| `semantics/fixture_ir.schema.yaml` (registered at repo root in M2) | `l9.schema/fixture-ir@1`, structural contract of `l9.fixture-ir/v1` (Stage 8 output) |
| `semantics/conformance_ir.schema.yaml` (registered at repo root in M2) | `l9.schema/conformance-ir@1`, structural contract of `l9.conformance-ir/v1` (Stage 12 output) |
| `scripts/fixture_conformance_ir.py` (repo root; RC-035) | Shape interpreter (the `l9.schema-definition/v1` descriptor grammar) plus a validator for every document-decidable semantic rule |
| `semantics/harness_surface.schema.yaml` (registered in the 2026-11-12 amendment) | `l9.schema/harness-surface@1`, structural contract of the product-authored `l9.harness-surface/v1` (Stage 8 input) |
| `ops/fixtures/fixture-conformance-ir/positive/` | Synthetic, product-neutral positive witnesses: fixture IR, conformance IR consuming it, harness surface, a synthetic manifest for the closure digest, product files with a RepositorySpec slice, and reference evaluations |
| `ops/fixtures/fixture-conformance-ir/negative/` | 110 falsifying fixtures: one or more per checked, evaluated or cross-document rule, plus structural controls |
| `language-test/state_fixture_ir.candidate.yaml` | The State language test (5 cases), evidence only |
| `semantics/binding_catalog.yaml#pytest/v2` | Registered in v3.40.0 by operator decision F1-D2 (the earlier proposal file is removed) |

Run: `python3 scripts/fixture_conformance_ir.py --fixtures ops/fixtures/fixture-conformance-ir --schemas semantics`

## Design (precedent: ADR-027, `implementation_ir.schema.yaml`)

Both schemas are `l9.schema-definition/v1` documents whose `properties.schema.const` names the IR from
`ir_catalog.yaml` (`l9.fixture-ir/v1`, `l9.conformance-ir/v1`). Cross-field obligations the v1 interpreter cannot
express are named `semantic_rules`, assigned by `enforcement` to the registered solvers
`fixture-derivation-validator/v1` (stage `fixtures`) and `reference-conformance/v1` (stage `conformance`).

Law input (`law_index`, **interim substitution — part of the admission subject, not canonical until admitted**):
stage 8 of `l9.compilation/product-build@1` consumes `semantic_law_ir` and `law_provenance`, but `l9.law-ir/v1` has
no structural schema at `f8e44d1` and stage 7 is not realized (compiler M0, D-LAW). Until the owner admits an
`l9.law-ir/v1` schema, the fixture IR carries `law_index`: each entry is a governed, digest-bound semantic already in
the product's resolved closure (`product_invariant`, `admitted_contract`, `admitted_invariant`) with
`source {artifact, revision, digest}`. Every `source_law_refs` entry must resolve to exactly one index entry, and
`provenance.law_index_digest` binds the index. The schema's `interim_law_input` block states the substitution and
names the **`l9.law-ir/v1` schema as an owner-owned follow-up Unknown**; this pack does not author one. Resolution
against the consumed manifest's closure is the solver's obligation (external rule).

Fixture case (`fixture_cases[]`):

- `id`, `disposition` (`executable` | `unresolved`), `blocked_by` (unresolved only).
- `source_law_refs` — non-empty (`conformance_model.yaml#fixture_or_test_must_not_invent_law`); every assertion's
  `law_ref` must be one of them.
- `given.steps[]` — declared contract-typed setup: `interface_action` (a manifest interface action) or
  `port_fixture` (a contract of a declared setup port). Optional `precondition` makes a failed setup an `error`, never
  a pass or fail.
- `when` — `mode: single` with exactly one `operation` + `request` (the `pytest/v1` `when.operation` field), or a
  declared `sequence` (≥1) / `parallel` (≥2) group of `steps`.
- `expect.observations[]` — follow-up `read_observation` interface actions; `expect.assertions[]` — predicates over
  when-step results, the when group, or observations only, never over given steps.
- Value references: `$from` (request value from an earlier step result; never inside one's own parallel group) and
  `$observed` (relational operand only; never its own target). Any other `$`-operand is rejected: expected values are
  literals traced to law, never values produced by the system under test.

Conformance obligation (`obligations[]`): exactly the `conformance_requirement_shape` of `conformance_model.yaml`
(`id`, `subject_class`, `governing_refs`, `observable_semantics`, `verification_class`; optional `profile_hint`,
`binding_constraints`, `evidence_requirements`) plus `witnessed_by` (fixture case ids), `disposition`, and a
target-neutral `execution_plan` (`fixture_replay`, `fresh_subject_per_case`, a fixed verdict rule). Verdict domain:
`pass | fail | error | unresolved`; an unresolved obligation aggregates to `unresolved`, never `pass`.

Fixture profile (`fixture_profile`, `unknowns`): when the product declares no applicable fixture profile, the
conformance IR records `status: absent` and exactly one typed `fixture_profile_absent` Unknown, and no obligation
carries a `profile_hint` — absence is never a satisfied requirement. Product-declared cases still compile: an
obligation whose witnesses are all executable is executable whether or not a profile is declared. (State's own
`STATE_CONFORMANCE_PROFILE` Unknown at ce0c4973 is exactly this case.)

## Required semantic rules → validator → falsifying fixture

| Contract requirement | Rule (schema) | Falsifying fixture |
| --- | --- | --- |
| Expectation never derives from the SUT | `no_expected_value_derives_from_the_system_under_test`; `an_observed_operand_appears_only_in_a_relational_predicate_and_never_names_its_own_target_value`; conformance `no_expected_result_is_defined_by_the_system_under_test_or_by_conformance_evidence` | `f10`, `f11`, `f12`, `c10` |
| Unresolved compiles to unresolved, never pass | `an_unresolved_case_is_listed_…`, `an_executable_case_has_no_blocked_by_…`, `an_obligation_with_an_unresolved_witness_or_no_executable_witness_is_unresolved`, `an_unresolved_obligation_is_listed_…`, `an_unresolved_obligation_never_yields_a_pass_verdict` | `f15`, `f16`, `c03`, `c04`, `c12` |
| Every requirement traces to governing semantics | `every_fixture_case_cites_at_least_one_source_law_…`, `every_obligation_traces_to_governing_semantics_…`, `every_obligation_witness_names_a_fixture_case_…` | `f01`, `f18` (structural), `c01`, `c02` |
| `pytest/v1` field alignment | Field names `fixture_cases`, `given`, `when.operation`, `expect` | see below |

| `source_law_refs` resolve to governed, digest-bound semantics (interim law input) | `every_source_law_ref_resolves_to_exactly_one_law_index_entry_with_source_provenance`, `law_index_refs_are_unique`, `provenance_law_index_digest_is_the_semantic_digest_of_law_index` | `f21` (unresolvable ref refused), `f22`, `f23`, `f24` (structural) |
| Absent fixture profile is a typed Unknown | `an_absent_fixture_profile_is_recorded_as_…`, `a_declared_fixture_profile_names_…`, `an_obligation_whose_witnesses_are_all_executable_is_executable_…` | `c13`, `c14`, `c15`, `c16` |

Amendment of 2026-11-12 (ADR-037 decisions 12–20) adds:

| Contract requirement | Rule (schema) | Falsifying fixture |
| --- | --- | --- |
| Pre-manifest closure binding | fixture `subject_and_provenance_closure_digest_are_equal`, `subject_closure_digest_is_the_closure_digest_of_the_consumed_product_manifest`; manifest `manifest_closure_digest_is_…`, `a_manifest_that_records_conformance_compilation_…`; conformance `subject_and_provenance_closure_digest_equal_…` | `f17`, `x04`–`x08`, `c09` |
| Raw-bytes product files, RepositorySpec resolution, typed refusals | topology `a_conformance_product_file_digest_is_…`, `a_conformance_product_file_ref_resolves_to_exactly_one_…`, `an_unresolved_ambiguous_escaping_or_digest_mismatched_…` | `p01`–`p07` |
| Harness surface | harness `control_refs_and_observation_refs_are_unique_…`, `a_fault_injection_control_declares_…`, `every_implementation_ref_is_…`; fixture `harness_controls_and_harness_observations_equal_…`, `no_harness_control_or_harness_observation_ref_is_an_interface_surface_action` | `h01`–`h07`, `x01`–`x03`, `f40` |
| Presence and relational evaluation | `is_present_holds_iff_…`, `a_relational_assertion_whose_target_or_observed_path_is_absent_…` | `e03`–`e05`, `e01`, `e02` |
| Exact `count_where` | `a_count_where_operand_is_…`, `count_where_holds_iff_exactly_count_…` | `f41`–`f46`, `e06`, `e07` |
| Flat precondition | `a_given_step_precondition_is_a_flat_map_…`, `a_precondition_holds_iff_…` | `f47`, `f48`, `q01`, `q02` |
| Observation context | `invocation_context_appears_only_on_gate_action_steps_and_interface_action_observations_…` | `f30`–`f32`, `f49`, `f50` |
| Obligations derived from law, closed verification class | `there_is_exactly_one_obligation_per_law_index_entry_…`, `an_obligation_is_witnessed_by_exactly_…`, `an_obligation_subject_class_observable_semantics_and_verification_class_…`, `an_obligation_whose_verification_class_is_not_fixture_replay_…`, `a_fixture_replay_obligation_with_witnesses_has_an_execution_plan_…` | `c17`–`c26`, `c05` |

Every checked (fixture 29, conformance 18, harness 3, topology 3, manifest 2), evaluated (4) and cross-document (2)
rule has at least one falsifying fixture; the runner fails if a rule lacks one or if a rule list drifts from its
schema. Result at this revision: **127 passed, 0 failed** (17 positive checks across 6 witness files, 110 negative).
Rules that need a resolved manifest closure, the product repository's code, or state a non-authority property are
the solvers' obligations and are listed as external in the validator.

## `pytest/v1` alignment

`binding_catalog.yaml#pytest/v1.maps`: `fixture_case → pytest_test_function`, `given → setup_phase`,
`when.operation → system_under_test_call`, `expect → pytest_assertions`.

- `mode: single` cases are aligned exactly: one `fixture_cases[]` item, `given`, `when.operation`, `expect`.
- `mode: sequence | parallel` cases have no `when.operation`; their calls are `when.steps[].operation`.
  `expect.observations[].operation` and `given.steps[].kind: port_fixture` are also unmapped. `pytest/v1` is admitted
  (unchanged since ADR-025) and is not edited. A **`pytest/v2` successor is proposed** in
  `semantics/binding_catalog.yaml#pytest/v2` (registered in v3.40.0, operator decision F1-D2; `pytest/v1` unchanged).

## State language test (`Quantum-L9/l9-wip@ce0c4973`, `fixtures/SEMANTIC_CASES.yaml`)

Encoded (validator: 0 violations): `create_revision_zero`, `duplicate_exact_operation`, `concurrent_revision_writers`
(parallel group, `count_where`), `terminal_conflict_is_sticky` (4 given steps, `$from`, relational `$observed`),
`expired_event_cursor` (State's settled C5 page form, now executable through a declared `journal_retention` control). No State-specific schema field was needed.

All 15 cases, classified (inference from contracts and `src/` at ce0c4973; not executed):

| Case | Expressible? | Note |
| --- | --- | --- |
| create_revision_zero | yes (encoded) | event `prior_revision` via `state.events` observation |
| duplicate_exact_operation | yes (encoded) | relational `equals $observed original` |
| operation_collision | yes | StateProblem `IDEMPOTENCY_COLLISION` + unchanged `state.get` |
| concurrent_revision_writers | yes (encoded) | rendering must really race; see U5 |
| active_claim_requires_fence | yes | claim, then transition without fence |
| lease_reassignment | yes | via release + re-claim, or via a declared `clock` control |
| list_then_events_cold_resume | no (out of scope) | "no second directory store" is an architecture property, not an observable result |
| expired_event_cursor | yes (encoded) | C5 page form; precondition via declared `trim_journal_before` control |
| tombstone_restore | yes | tombstone, restore, assert new revision > tombstoned revision |
| erased_object_recreate | yes | `erased` reached by a declared `internal_setup` control (retention executor); `state.hard_erase` stays forbidden |
| terminal_conflict_is_sticky | yes (encoded) | |
| terminal_refusal_is_sticky | yes | port fixture admits the schema between the refusal and the retry |
| changed_world_retry | yes | new `operation_id` after a terminal receipt |
| precommit_deadline | yes | `context.budget_ms` + declared fault/clock control |
| ambiguous_commit | yes | declared `fault_injection` with `after_effect: after` + harness receipt-count observation |

State C5/C9/C10 are settled (relayed operator decisions): C5 page form is encoded above; C9 (INVALID_REQUEST dual-registered) and
C10 (negative terminal outcome commits the operation receipt only) affect no encoded case; both are expressible with existing predicates.

## Step 0 admission verdicts (M0)

`check_admission_closure.py --require admitted` on the host sources `l9.source/{binding-catalog,compilation-profiles,
solver-catalog,conformance-model,ir-catalog}@1`: exit 0, `ADMITTED` via v3.36.0 / ADR-033 at `dcd9d00`, and re-measured
at `f8e44d1`: exit 0, `ADMITTED` via v3.38.0 / ADR-035, no host changed on `main` since that admission. Entry level (the
gate admits host ledgers, not entries): canonical-JSON comparison at `c6ee11d` (v3.28.0 admission, ADR-025) and at
`dcd9d00` and `f8e44d1` (host bytes unchanged between them) is identical for `pytest/v1`, `l9.binding/repository-operations-pyproject@1`,
`l9.binding/repository-operations-makefile@1`, `fixture-derivation-validator/v1`, `reference-conformance/v1`,
product-build@1 stages 8 and 12, `conformance_model.yaml` and `ir_catalog.yaml`, so ADR-025's approved tree covers them and none joins this subject.

Caveat recorded: python-gate-node@1 lives in the same admitted binding_catalog.yaml host and the gate cannot distinguish
it at entry level; per campaign direction it is NOT treated as admitted (ADR-026 still says candidate). F1 does not
depend on it.

## F1 Unknowns (recorded, fail closed)

Amendment (operator decisions relayed 2026-11-11): U1, U2, U3 and U5 are closed as language by the harness surface, the Gate invocation `context` and `pytest/v2`. Amendment of 2026-11-12: U4 is closed by the closed `verification_class` domain (ADR-037 decision 20). U0 remains. New: RepositorySpec authoritative source entries do not yet carry the `coordinate` that product-file resolution reads (that schema is owned outside this repository). The original entries are kept below for the record.

- **U0 `l9.law-ir/v1` schema.** No structural schema exists; `law_index` is an explicit interim substitution for
  stage 8's `semantic_law_ir` / `law_provenance` inputs. The law-ir schema is an owner-owned follow-up.

- **U1 Invocation context.** A `when` operation is a Gate action over TransportPacket; tenant, principal,
  authorization and request budget come from the packet, not the request contract. The IR has no field for it, so
  cases that depend on it (authorization-gated retry, `STATE-TENANT-001`, deadlines) are not expressible. Adding a
  packet-context block is a language decision, not taken here.
- **U2 Controllable preconditions.** No declared interface or setup-port operation advances time or the journal
  retention horizon. Expiry and deadline cases are `unresolved`.
- **U3 Port fixture semantics.** `port_fixture` requests are free objects addressed to a port contract; no ledger
  defines a fixture-setup vocabulary for ports, and seeding the SUT's own provider port (to reach `erased` or inject
  an ambiguous commit) would bypass the system under test. Not admitted here.
- **U4 `verification_class` domain.** `conformance_model.yaml` requires the field; no ledger defines its domain, so
  the schema types it as `semantic_ref`.
- **U5 Parallel-group realization.** The schema states the group has no ordering guarantee; whether a rendering must
  prove real concurrency is a binding obligation (`pytest/v2`) left open.
- **U6 Registration rung (resolved by OPERATOR DECISION F1-D1 = A).** The gate previously required each
  `l9.schema-definition/v1` in `artifact_schemas` to be the output of exactly one profile, so a profile-less IR schema
  was `INCOMPLETE`. Commit `c85ca1b` adds a narrow IR-schema rule to `Registration.schema` with 8 tests (positive;
  IR id not in `ir_catalog.yaml#irs`; missing catalog; IR id also a profile output; missing / empty / undefined
  `governed_by.contracts`; governing profile named). Purely additive; the 193 pre-existing skill tests stay green.
  **The grading instrument changed in this release.**
