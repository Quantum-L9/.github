# Release Validation v3.20.0

Candidate status: **additive successor candidate**.

This release preserves the v3.19.0 semantic-foundation inventory and adds one runtime projection profile. No invariant, contract, schema, ledger, source registration, projection framework, producer, or ADR is added.

## Semantic changes

Modified canonical ledger:

- `semantics/projection_profiles.yaml`: one profile appended after `l9.projection/repository-operations-compiler@1`:
  - `id: l9.projection/coding-agent-execution@1`, `class: runtime`, `consumer: Cursor-Governance`.
  - `sources.invariants.selectors`: 19 exact-id filters, `$.invariants[?(@.id=="<id>")]`, for `L9-AUTH-001`, `L9-AUTH-002`, `L9-OWNER-001`, `L9-MONOTONIC-001`, `L9-PROMOTION-001`, `L9-DERIVED-001`, `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-UNKNOWN-001`, `L9-DEGRADE-001`, `L9-PROV-001`, `L9-COORD-001`, `L9-COMPAT-001`, `L9-REVISION-001`, `L9-ADMISSION-001`, `L9-PROJECTION-001`, `L9-VALIDATION-001`, `L9-CORRECTNESS-001`, `L9-GLOBALIZATION-001`.
  - `sources.contracts.selectors`: 10 exact-id filters, `$.contracts[?(@.id=="<id>")]`, for `authority-boundary@1`, `monotonic-subordination@1`, `admission-and-promotion@1`, `derived-artifact@1`, `evidence-and-receipt@1`, `assurance-and-verification@1`, `unknown-and-degradation@1`, `provenance-and-coordinate@1`, `projection@1`, `validation-and-correctness@1`, each under `l9.contract/`.
  - `sources.authority_model.selectors`: `$.agent_authority`, `$.human_authority`, `$.escalation_rules`, `$.admission_rules`.
  - `output.schema: l9.projection.coding-agent-execution/v1`.
  - `forbidden`: `obligation_not_admitted_in_a_selected_source`, `skill_command_or_routing_semantics`, `adapter_host_or_surface_specific_semantics`, `repository_local_policy_as_global_law`, `execution_publication_or_merge_authority_grant`.

Every selector uses the equality-filter or plain-field grammar of `semantics/selector_model.yaml`. Exact-id selection makes the payload a fixed, enumerable set of whole admitted records, so a consumer receives each record as admitted and the profile adds no meaning. All three sources are registered in `semantics/canonical_sources.yaml` (`l9.source/invariants@1`, `l9.source/contracts@1`, `l9.source/authority-model@1`) with `projection_allowed: true`.

Explicitly unchanged: `semantics/invariants.yaml` (31), `semantics/contracts.yaml` (26), `semantics/authority_model.yaml`, `semantics/canonical_sources.yaml`, `semantics/projection_engine_contract.yaml`, `semantics/projection_artifact.schema.yaml`, `semantics/compiler_receipt.schema.yaml`, `semantics/selector_model.yaml`, every other projection profile, every schema, capability, artifact class, and ADR, and all prior release records. The profile count rises from 24 to 25.

## Mechanical derivation refreshes

None. `projection_profiles.yaml` is not a declared derivation source of any other ledger. The only pre-release failure was SC-008 against the v3.19.0 hash inventory, which this record supersedes.

## Validator delta

- `scripts/validate-semantics.py`: RC-028 coding-agent execution projection closure plus an isolated negative-case batch, each case required to fail at its intended field. Every earlier check is unchanged.

## RC-028 Coding-agent execution projection closure

RC-028 governs the exact coordinate `l9.projection/coding-agent-execution@1` and proves:

- the profile exists exactly once;
- its class is `runtime` and its consumer is exactly `Cursor-Governance`;
- its sources are exactly `invariants`, `contracts`, and `authority_model`. Each must resolve through `source_classes` to the canonical ledger declaring `l9.invariants/global@1`, `l9.contracts/global@1`, or `l9.authority-model/global@1` with `canonical: true`, and be registered exactly once in `canonical_sources.yaml` as canonical with `projection_allowed: true`;
- every invariant and contract selector is an exact-id equality filter over its own collection. Each resolves to exactly one declared record with `scope: global`, and no selector is declared twice;
- every authority-model selector names one top-level section the ledger declares;
- each source's selection equals its pinned set exactly. An admitted `@1` profile is immutable (`L9-REVISION-001`), so a different selection requires a new profile version;
- every `source_invariants` entry of every selected contract is itself selected;
- the output schema is exactly `l9.projection.coding-agent-execution/v1`;
- the profile declares the five boundaries it does not carry;
- no string in the profile references a skill (`l9-coding-agent`, `skills/`, `SKILL.md`).

The negative-case batch proves fail-closed behavior at the intended field for **27** cases. The ledger-side and closure cases must also fail for their stated reason, so the pinned-set check cannot mask them:

- profile deleted or duplicated;
- consumer not authorized; wrong profile class;
- contracts source missing; unpinned source added;
- a selector naming an undeclared id;
- arbitrary wildcard selector; arbitrary scope-filter selector; selector crossing into another source; duplicate selector; selector with a trailing newline;
- non-global record selected;
- obligation stripped; immutable `@1` selection changed; contract closure broken;
- human authority stripped; a selector naming a missing authority section;
- source class retargeted; source registration not projectable;
- skill dependency; wrong output schema; authority boundary dropped;
- with the profile unchanged: a selected invariant demoted from global; a selected invariant deleted; a selected contract citing an unselected invariant; a selected contract citing a non-string invariant entry.

Byte-level tampering of any selected ledger or of the profile catalog is caught by SC-008 against this release's `HASHES.sha256`.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-027. v3.20.0 adds RC-028 without weakening or replacing predecessor checks.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.20.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion. Producing the projection from this profile, and binding it on coding-agent surfaces, are downstream work. The producer is an outstanding Unknown recorded in `README.md`.
