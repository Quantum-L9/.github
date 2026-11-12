# Semantic Foundation Manifest v3.40.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **117** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/affected_strategic_closure.schema.yaml`
- `semantics/architecture_break_test_composition.schema.yaml`
- `semantics/architecture_break_test_projection.schema.yaml`
- `semantics/architecture_intelligence_composition.schema.yaml`
- `semantics/architecture_intelligence_projection.schema.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_header_model.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/authority_resolution_composition.schema.yaml`
- `semantics/authority_resolution_projection.schema.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
- `semantics/coding_agent_execution_projection.schema.yaml`
- `semantics/compilation_profiles.yaml`
- `semantics/compiler_contract.yaml`
- `semantics/compiler_passes.yaml`
- `semantics/compiler_receipt.schema.yaml`
- `semantics/composed_projection.schema.yaml`
- `semantics/composition_engine_contract.yaml`
- `semantics/composition_profiles.yaml`
- `semantics/conformance_ir.schema.yaml`
- `semantics/conformance_model.yaml`
- `semantics/contracts.yaml`
- `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml`
- `semantics/dependency_archetypes.yaml`
- `semantics/derivation_profiles.yaml`
- `semantics/domain_architecture_composition.schema.yaml`
- `semantics/domain_architecture_projection.schema.yaml`
- `semantics/domain_capabilities_dependencies_composition.schema.yaml`
- `semantics/domain_capabilities_dependencies_projection.schema.yaml`
- `semantics/domain_consumer_bindings.yaml`
- `semantics/domain_contracts_conformance_composition.schema.yaml`
- `semantics/domain_contracts_conformance_projection.schema.yaml`
- `semantics/domain_evidence_provenance_composition.schema.yaml`
- `semantics/domain_evidence_provenance_projection.schema.yaml`
- `semantics/domain_governance_composition.schema.yaml`
- `semantics/domain_governance_projection.schema.yaml`
- `semantics/domain_identity_attribution_composition.schema.yaml`
- `semantics/domain_identity_attribution_projection.schema.yaml`
- `semantics/domain_projection_model.yaml`
- `semantics/domain_signals_composition.schema.yaml`
- `semantics/domain_signals_projection.schema.yaml`
- `semantics/domain_strategic_value_composition.schema.yaml`
- `semantics/domain_strategic_value_projection.schema.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/evidence_assessment_composition.schema.yaml`
- `semantics/evidence_assessment_projection.schema.yaml`
- `semantics/fixture_ir.schema.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/globalization_assessment_composition.schema.yaml`
- `semantics/globalization_assessment_projection.schema.yaml`
- `semantics/hard_constraint_context_composition.schema.yaml`
- `semantics/hard_constraint_context_projection.schema.yaml`
- `semantics/harness_surface.schema.yaml`
- `semantics/identity_assertion.schema.yaml`
- `semantics/identity_assurance_composition.schema.yaml`
- `semantics/identity_assurance_composition_v2.schema.yaml`
- `semantics/identity_assurance_projection.schema.yaml`
- `semantics/identity_assurance_projection_v2.schema.yaml`
- `semantics/identity_model.yaml`
- `semantics/implementation_ir.schema.yaml`
- `semantics/invariants.yaml`
- `semantics/ir_catalog.yaml`
- `semantics/lifecycle.yaml`
- `semantics/node_archetypes.yaml`
- `semantics/packet_catalog.yaml`
- `semantics/port_catalog.yaml`
- `semantics/pr_audit_composition.schema.yaml`
- `semantics/pr_audit_projection.schema.yaml`
- `semantics/product_kinds.yaml`
- `semantics/product_manifest.schema.yaml`
- `semantics/product_topology.schema.yaml`
- `semantics/projection_artifact.schema.yaml`
- `semantics/projection_engine_contract.yaml`
- `semantics/projection_profiles.yaml`
- `semantics/receipt_catalog.yaml`
- `semantics/repository_classes.yaml`
- `semantics/repository_registry.yaml`
- `semantics/requirement_model.yaml`
- `semantics/resolution_model.yaml`
- `semantics/selector_model.yaml`
- `semantics/semantic_change_context_composition.schema.yaml`
- `semantics/semantic_change_context_projection.schema.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/strategic_cognition_model.yaml`
- `semantics/strategic_interaction_composition.schema.yaml`
- `semantics/strategic_interaction_projection.schema.yaml`
- `semantics/strategic_metacognition_composition.schema.yaml`
- `semantics/strategic_metacognition_composition_v2.schema.yaml`
- `semantics/strategic_metacognition_projection.schema.yaml`
- `semantics/strategic_metacognition_projection_v2.schema.yaml`
- `semantics/strategic_plan_graph.schema.yaml`
- `semantics/strategic_plan_metacognitive_analysis.schema.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/strategic_plan_revision_candidate.schema.yaml`
- `semantics/strategic_planner_value_composition.schema.yaml`
- `semantics/strategic_planner_value_projection.schema.yaml`
- `semantics/strategic_planning_context_composition.schema.yaml`
- `semantics/strategic_planning_context_composition_v2.schema.yaml`
- `semantics/strategic_planning_context_projection.schema.yaml`
- `semantics/strategic_planning_context_projection_v2.schema.yaml`
- `semantics/strategic_planning_episode.schema.yaml`
- `semantics/strategic_value_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technical_coordination_composition.schema.yaml`
- `semantics/technical_coordination_projection.schema.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`
- `semantics/work_state_continuity_composition.schema.yaml`
- `semantics/work_state_continuity_projection.schema.yaml`

The v3.39.0 inventory is preserved. Three files are added; no ledger is removed or renamed.

## Architecture decision records

The release contains **37** accepted ADRs plus the ADR index under `docs/adr/`.

v3.40.0 adds ADR-037 (structural contracts for `l9.fixture-ir/v1` and `l9.conformance-ir/v1`), a candidate for this release; admission of the release is its acceptance gate.

## Semantic changes

- `semantics/fixture_ir.schema.yaml` (`l9.schema/fixture-ir@1`): `l9.schema-definition/v1` whose `properties.schema.const` is `l9.fixture-ir/v1` (Stage 8 output). Fixture cases with non-empty `source_law_refs`, contract-typed `given` setup (interface actions, port fixtures, declared harness controls, a flat `{path: literal}` precondition), a single `when.operation` or a declared sequence/parallel group, a literal Gate invocation `context` per Gate action step and per interface-action observation, and `expect` over result contracts, declared read observations and declared harness observations only. The interface surface declares forbidden actions, harness controls (`clock`, `journal_retention`, `fault_injection`, `authorization_policy`, `internal_setup`) and harness observations. Evaluation semantics are pinned: presence predicates treat an absent path as a value, relational predicates on an absent path are an error, and `count_where {where: [{path, predicate, operand?}], count}` counts exactly. `subject`/`provenance` bind the pre-manifest `closure_digest`. `law_index` entries carry the law `statement` and a closed `verification_class`. 38 `semantic_rules` enforced by `fixture-derivation-validator/v1`.
- `semantics/conformance_ir.schema.yaml` (`l9.schema/conformance-ir@1`): const `l9.conformance-ir/v1` (Stage 12 output). One obligation per `law_index` entry, derived from the law (governing ref, law kind, statement, verification class, citing cases), with disposition, a target-neutral execution plan for executable-class obligations, verdicts `pass | fail | error | unresolved`, `fixture_profile` and typed `unknowns`. Only `fixture_replay` can make an obligation executable; `static_inspection` and `external_runtime_evidence` obligations are unresolved and never pass. 19 `semantic_rules` enforced by `reference-conformance/v1`.
- `semantics/harness_surface.schema.yaml` (`l9.schema/harness-surface@1`): const `l9.harness-surface/v1`, the product-authored harness surface `{schema, product_ref, owner, revision?, harness_controls, harness_observations}`. Entries reuse the fixture-IR entry shapes and add a required, verified-never-regenerated `implementation_ref`. Stage 8 consumes it as `product_harness_surface`. 6 `semantic_rules` enforced by `fixture-derivation-validator/v1`.
- **Interim law input** (part of the admission subject, not canonical until admitted): `fixture_ir.schema.yaml#interim_law_input` and `law_index` substitute for Stage 8's `semantic_law_ir` and `law_provenance` until an owner-admitted `l9.law-ir/v1` schema exists. No law-ir schema is authored.
- `semantics/product_topology.schema.yaml#properties.conformance`: optional `fixture_case_refs: [{ref, digest}]` and `harness_surface_ref: {ref, digest}`; `product_file_resolution` (raw-bytes digests, resolution to exactly one RepositorySpec authoritative source entry by `coordinate`, confinement to the repository, four typed refusals); six `semantic_rules`. `conformance.required` is unchanged; existing topologies stay valid.
- `semantics/product_manifest.schema.yaml`: optional `closure_digest` and `conformance.compilation {fixture_ir_digest, conformance_ir_digest}`, `closure_digest_definition` (the semantic digest of the manifest without `manifest_digest`, `closure_digest` and `conformance.compilation`), two `semantic_rules`. `required` is unchanged.
- `semantics/ir_catalog.yaml`: adds `l9.harness-surface/v1` so the harness-surface schema registers through the same IR-schema route as the two IR schemas.
- `semantics/compilation_profiles.yaml` (`l9.compilation/product-build@1` stage 8) and `semantics/vocabulary.yaml#semantic_build_stages` (RC-013 parity): stage 8 consumes `product_fixture_cases` and `product_harness_surface`.
- `semantics/binding_catalog.yaml`: `pytest/v2`, `successor_of: pytest/v1`, mapping groups, observations, harness controls and observations, context (including observation context), exact `count_where`, presence checks and unresolved cases. `pytest/v1` is unchanged.
- `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas` lists the three schemas.
- `scripts/validate-semantics.py`: RC-035 and RC-035-NEG; `scripts/fixture_conformance_ir.py` and `ops/fixtures/fixture-conformance-ir/` (6 positive witness files, 108 falsifying fixtures).
- ADR-037 (candidate).

No solver, conformance-model, invariant, contract, term, projection or composition profile changes. `ir_catalog.yaml` gains one entry (`l9.harness-surface/v1`); `product_manifest.schema.yaml` gains only optional fields, its closure-digest definition and two rules. `pytest/v1` is unchanged (RC-035 pins its digest).

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.39.0/`, preserved unchanged.
