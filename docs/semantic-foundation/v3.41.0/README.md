# Semantic Foundation v3.41.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.41.0 defines the datastore capability tokens that technologies already assert, states how a provider binding is decided against a port's required capabilities in two tiers, and registers the first provider binding (MongoDB) with vendor-cited facts. Before this release `transactions`, `conditional_updates` and the other datastore tokens had no definition, the provider binding family had no entry, and `l9.contract/technology-binding@1` could reach only `unresolved` for a datastore port.

Successor to the v3.40.0 candidate (ADR-037, `.github#247`, head `821c477`), which is not admitted; the admitted base is v3.39.0. This is contract `L9-GH-R5-D2-003` of campaign R5 (conformance-first). ADR-038 is its candidate decision record and does not admit itself. Its decisions 1–8 apply the operator's rulings DR-D2-01..08 ("accept all", 2026-11-12).

## Bounded delta

- `semantics/technology_capabilities.yaml#capability_definitions`: 13 provider-neutral tokens with scope, guarantee, `not_implied`, failure signal and runtime probe; aliases `unique_indexes`, `unique_constraints` → `unique_key`; coverage of `mongodb` and `postgresql`; deployment profiles `standalone`, `replica_set`, `sharded_cluster`; runtime receipt `l9.receipt/conformance@1` with additional bound coordinates.
- `semantics/technology_capabilities.yaml#binding_rules.provider_compatibility_tiers`: D2-EVAL-01..10, overall rule, empty-set rule, mapping to `technology-binding@1` outcomes. Runtime qualification is not an admission precondition; an admitted definition never implies it.
- `semantics/binding_catalog.yaml`: `l9.binding/provider/mongodb@1` (facts pinned to `[9.0, 9.1)`; `snapshot_isolation` provided by labelled inference; `serializable_isolation`, `server_authoritative_time_in_query_filters` and `document_storage` unknown; every runtime obligation `not_executed`); `compatibility.unknown_capability: incompatible_until_resolved`.
- `scripts/validate-semantics.py`: RC-036 and RC-036-NEG; `scripts/datastore_capability_compatibility.py`; `ops/fixtures/datastore-capability-compatibility/` (5 positive, 20 negative).
- ADR-038 (candidate).

## Evidence

Candidate pack: `docs/candidates/R5-D2/` (rulings → canonical locations, executor choices, unknown-capability reconciliation with consumer search, downstream projection effects). Vendor facts: official MongoDB documentation, retrieved 2026-11-11; all 23 quotes re-matched on 2026-11-12 against the raw page HTML. Requirement evidence (State, `Quantum-L9/l9-wip@ce0c4973`) and gap evidence (`Quantum-L9/l9-semantic-compiler-engine@94138a2`, R5-A §3 D2, §4) are cited in ADR-038 and not carried into the ledgers.

## Outstanding Unknowns

- No runtime qualification: live MongoDB replica-set conformance is R5-C.
- `serializable_isolation`, `server_authoritative_time_in_query_filters` and `document_storage` for MongoDB; every PostgreSQL fact (no provider binding).
- Tokens of `graphiti-mcp` and `zep` remain undefined (outside coverage).
- MongoDB server lines other than 9.0 are uncited.
- `l9.projection/stage-provider-bindings@1` does not select `capability_definitions` or the tiers; a profile successor is needed for a compiler to evaluate tiers from that projection.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants mutation, publication, merge, admission, deployment or execution authority, and no provider becomes a semantic owner. Admission of v3.41.0 requires the repository owner's explicit decision for this exact subject; it presupposes the owner's decision on v3.40.0.
