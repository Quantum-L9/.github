# Release Validation v3.12.0

Candidate status: **additive successor candidate**.

This release keeps the v3.11.0 semantic-foundation inventory and adds two technology registrations. It adds no technology class, target role, schema, ledger, invariant, contract, projection profile, or ADR.

## Semantic changes

Modified canonical ledger:

- `semantics/technology_capabilities.yaml`, two registrations appended after `makefile`:
  - `id: graphiti-mcp`, `class: datastore`, `provides: [graph_episode_storage, graph_search, episode_deletion_by_locator]`, `target_roles: [persistence_provider]`, `semantic_ownership: {implied: false}`.
  - `id: zep`, `class: datastore`, `provides: [graph_episode_storage, graph_search, episode_deletion_by_locator]`, `target_roles: [persistence_provider]`, `semantic_ownership: {implied: false}`.

Explicitly unchanged: the capability-class set, all nine prior technology registrations, `global_rules`, `binding_rules`, `registration_requirements`, `semantics/binding_catalog.yaml`, `semantics/technology_profiles.yaml`, `semantics/capabilities.yaml`, `semantics/conformance_model.yaml`, `semantics/projection_profiles.yaml`, `semantics/product_kinds.yaml`, `semantics/dependency_archetypes.yaml`, every schema, contract, invariant, and ADR, and all prior release records.

## Classification evidence

The classification uses only the provider realization that `Quantum-L9/l9-graphiti-memory` actually consumes, read at PR #80 head `dd03303e5d78534a2cbdab5b0e999f34f802a160`:

- Graphiti MCP: `src/l9_graphite_memory/transport.py` calls the Graphiti server's episode-ingest tools (`add_memory`, or the legacy `add_episode`), and its search tools (`search_memory_facts` / `search_facts`, `search_nodes`). `adapters/graphiti_projection.py` stores the returned episode locator and withdraws a projection by calling `delete_episode` with that locator through the transport.
- Zep: `src/l9_graphite_memory/zep_transport.py` calls the `zep-cloud>=3.0,<4` SDK graph API (`graph.add`, `graph.search`, `graph.episode.delete`) and keeps the episode uuid as the locator.
- `release-work/repository-review/provider-capability-matrix.md` records the same facts for both providers: graph write, search, a persisted stable locator, and verified erasure by locator.

Both technologies persist, index, and query graph episodes, so `datastore` is the faithful existing class: it covers "persistence, transaction, indexing, consistency, and query capabilities exposed by a storage technology". Neither is classed as `transport`. MCP and HTTP are only how the product reaches the store, not the capability it consumes. `datastore` is a technology class, not a claim of canonical status. In the product both stores hold derived projections that can be rebuilt, and canonical memory truth stays in the product's own record store.

`persistence_provider` is the only existing target role for a storage provider. It represents the realized fact: the technology persists and serves the projected graph. The product's own role name, `projection_provider`, stays product-local in its ProductTopology and is not globalized here.

The `provides` terms follow the catalog's existing rule. `technology_capabilities.yaml` is the declared `provider_capability_fact_source` (`capabilities.yaml#provider_realization_model`), and every prior registration states its technology facts in this catalog, the same way `mongodb` states `document_storage` and `postgresql` states `relational_storage`. The claims describe only what the technologies realize. They claim no memory admission, canonical persistence, lifecycle, curation, retrieval, receipt, or MemoryService semantics, all of which remain product-owned. Capabilities the consumer does not depend on, such as transactions or change notifications, are not claimed; `missing_capability_is_not_assumed` applies.

## Mechanical derivation refreshes

None. `technology_capabilities.yaml` is not a hashed derivation source of any other ledger. After the change, the validator reported no stale coordinate. The only failure before this release record existed was SC-008 against the v3.11.0 hash inventory, which this record supersedes.

## Validator delta

- `scripts/validate-semantics.py` gains RC-020, the Graphiti/Zep technology admission closure, plus an isolated negative-case batch. Each case must fail at its intended field and for its intended reason. RC-019 and every earlier check are unchanged.

## RC-020 Graphiti/Zep technology admission closure

RC-020 governs the exact coordinates `graphiti-mcp` and `zep` and proves that:

- each is registered exactly once;
- each carries the pinned required fields `id`, `class`, `provides`, and `target_roles`, and the catalog's `registration_requirements` is well formed and still requires them, so relaxing the grammar cannot excuse a missing field;
- every field each entry carries is a declared registration field, so a claim outside the registration grammar fails closed;
- each class is a string, is a `capability_classes` entry, and belongs to the class set admitted before this registration (`language`, `framework`, `datastore`, `transport`, `target`), so the admission cannot introduce a class, even beside a decoy registration that uses it;
- `provides` is a non-empty list of distinct explicit terms;
- `target_roles` is a non-empty list of distinct explicit roles drawn from the role set admitted before this registration, so the admission cannot introduce a parallel role system;
- any optional `constraints`, `compatible_with`, or `incompatible_with` is a non-empty list of distinct terms, and each referenced technology is registered;
- `semantic_ownership` is exactly `{implied: false}`. A falsy non-boolean such as `0` is rejected;
- a malformed catalog shape (technologies, capability classes, or registration grammar) produces a structured FAIL and never an uncaught exception.

The pinned class and role sets apply only to these two coordinates. They bound what this admission may reuse and place no limit on future admissions by canonical authority. RC-020 defines no graph-provider or memory-provider family by name, applies no rule to any other technology, and sets no cardinality on the catalog (`L9-VALIDATION-001`).

The negative-case batch has 16 cases. Each must fail at its intended field with its intended reason. The cases are:

- Graphiti registration missing;
- Zep registration missing;
- duplicate exact technology id;
- class missing;
- a non-admitted class, also held by another registration;
- a class introduced together with the admission behind a decoy;
- a class that is not a scalar;
- empty `provides`;
- `target_roles` missing;
- a target role introduced behind a decoy;
- semantic ownership implied;
- semantic ownership falsy but not `false`;
- semantic ownership undeclared;
- an ownership claim outside the registration grammar;
- the registration grammar relaxed to excuse a missing field;
- capability classes that are not a mapping.

Test-first evidence: before the registration, at commit `2ddb616` (the semantic bytes of base `14a93a94a3adaa15b506ee88c12e8b82a121c140` plus RC-020), RC-020 failed, and the only failures were the two intended absences (`technologies='graphiti-mcp'` and `technologies='zep'`, each found 0). After the registration, RC-020 and RC-020-NEG pass. The independent Validate & Repair audit found bypasses and uncaught exceptions in the first form of RC-020: a decoy registration, a falsy non-boolean ownership value, a non-scalar class, a malformed grammar, and a self-relaxed required list. These were repaired before publication. Each audit reproduction now fails closed, and the pre-registration RED is unchanged.

## Existing closure

The existing semantic-foundation validator still owns SC-001 through SC-010 and RC-001 through RC-019. v3.12.0 adds RC-020 without weakening or replacing any predecessor check.

## Explicit boundaries

- MU-001 (the missing conformance profile for `dependency` / `semantic-subsystem`) remains unresolved. Conformance profiles are owned by `l9-conformance` (`projection_profiles.yaml#conformance_profiles`), and this release creates none.
- MU-002 is closed only for its upstream authority prerequisite. The downstream ProductTopology still records `technology_ref: unknown` until a separate consumer change binds it to these coordinates.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.12.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion. Registering a technology does not authorize any product to use it (`technology_registration_does_not_authorize_use`).
