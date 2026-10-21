# ADR-020 — Coding-Agent Execution Projection Payload Schema and Forbidden-Constraint Criteria

**Status:** Candidate for semantic-foundation v3.23.0. Drafted on 2026-10-21 at the repository owner's instruction to give the coding-agent execution projection the same mechanical closure the architecture-intelligence projection received in v3.22.0 (ADR-019). Admission of v3.23.0 is the acceptance gate; this record does not admit itself.

## Context

`l9.projection/coding-agent-execution@1` (v3.20.0, RC-028) selects nineteen global invariants, ten global contracts, and four `authority_model` sections by exact id for the Cursor-Governance operating plane. Its consumer, the coding agent, binds those invariants before any repository mutation and requires a producer receipt whose `result` is `pass`.

At v3.22.0 the producer (`l9-semantic-compiler`, the component `semantics/vocabulary.yaml` assigns the `projection` role) projects the profile completely but can only receipt it as `unknown`, for the two reasons ADR-019 named for the observer:

- no registered artifact schema defines the declared output schema `l9.projection.coding-agent-execution/v1`, so the `payload_schema` criterion stays unresolved;
- the profile's five `forbidden` categories have no criterion in `forbidden_constraints`, so under PROJECTION-016 each stays unresolved.

An `unknown` receipt is honest, and the consumer must not relax its gate to accept it (L9-UNKNOWN-001, L9-VALIDATION-001). The closure therefore belongs here, with the owner of the profile, the schema catalog, and the criteria.

## Decisions

1. **Payload schema.** `semantics/coding_agent_execution_projection.schema.yaml` (`l9.schema/coding-agent-execution-projection@1`) defines `l9.projection.coding-agent-execution/v1`. It types the only sections the profile's selectors can produce (`invariants`, `contracts`, `agent_authority`, `human_authority`, `escalation_rules`, `admission_rules`) and requires the identity fields each canonical source declares for its records. It is registered under `requires.artifact_schemas` in `semantics/generic_compiler_manifest.yaml`. It constrains shape only; selection equivalence, not this schema, proves the payload is the declared selection.

2. **Forbidden-constraint criteria** in `l9.forbidden-constraint` v1 (PROJECTION-016), one per category the profile declares:
   - `obligation_not_admitted_in_a_selected_source`: `source_authority`. Every projected ledger must be owned by the catalog's authority, so the profile cannot carry a ledger a domain owner holds.
   - `skill_command_or_routing_semantics`: `payload_excludes` the packet catalog (`$.packets`), the port catalog (`$.ports[*]`), and the capability invocability contract (`$.invocability_contract`), the canonical paths where invocation and routing semantics are declared.
   - `adapter_host_or_surface_specific_semantics`: `payload_excludes` surface records (`$.surfaces[*]`), the `adapter` and `surface_identity` terms, target-class bindings, and technology profiles.
   - `repository_local_policy_as_global_law`: `payload_excludes` invariants whose scope is `semantic_foundation_release`, repository classes (`$.classes`), and repository registry records (`$.repositories[*]`).
   - `execution_publication_or_merge_authority_grant`: `payload_excludes` the `authority_model` sections that grant distribution, rollout, profile publication, and compiler authority. These are siblings of the four sections the profile selects, so the criterion is decided against the same ledger the profile reads.

3. **Profile unchanged.** `l9.projection/coding-agent-execution@1` is byte-for-byte as admitted at v3.20.0; RC-028 continues to pin it. Only the catalog-level `forbidden_constraints.definitions` and the schema registry grow.

## Review findings (recorded, not resolved)

- `obligation_not_admitted_in_a_selected_source` through `source_authority` carries the limitation ADR-019 recorded for `unrelated_domain_payloads`: the canonical loader already refuses a ledger owned by anyone else, so the criterion restates a property that cannot fail on its own. A criterion that proves no obligation beyond the selected records entered the payload would need selection-closure semantics the engine already proves through selection equivalence; it is not re-invented here.
- The packet and port catalogs hold no records at this revision, so `skill_command_or_routing_semantics` is proven by the producer's tests and the live `invocability_contract` exclusion, not by live catalog data.
- No validator check (an RC-031 mirroring RC-030) is added in this candidate. SC-008 covers the release record; RC-028 covers the profile. A dedicated closure check for the schema registration and the five criteria is the next step before admission.

## Consequences

The producer can receipt every source of the profile as `pass` when the payload schema and all five criteria hold, which lets the coding agent bind the projection without weakening its gate. A later change to any excluded canonical path, or to a selected section, is a material change under PROJECTION-007 and PROJECTION-008 and re-opens the receipt.
