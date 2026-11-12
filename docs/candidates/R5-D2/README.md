# R5-D2 candidate pack — datastore capability semantics and provider bindings

Contract `L9-GH-R5-D2-003` (rev 3), campaign R5 conformance-first. Status: **registered in the v3.41.0 candidate
release (ADR-038); not admitted.** Base: F1's candidate head `Quantum-L9/.github@44e02a0` (v3.40.0 / ADR-037,
`.github#247`, itself unadmitted on admitted v3.39.0 `f8e44d1`). Drafted first on `dcd9d00` (v3.36.0) at
`agent/r5/D2@aa1cbf2`; this branch ports the pack without that history.

This pack is evidence for an owner decision. Nothing here is canonical until v3.41.0 is admitted.

## Where the drafts went

| Draft (at `aa1cbf2`) | Canonical location in v3.41.0 |
| --- | --- |
| `token_definitions.candidate.yaml` | `semantics/technology_capabilities.yaml#capability_definitions` |
| `compatibility_evaluation.candidate.yaml` | `semantics/technology_capabilities.yaml#binding_rules.provider_compatibility_tiers` |
| `provider_bindings/mongodb.candidate.yaml` | `semantics/binding_catalog.yaml#bindings[l9.binding/provider/mongodb@1]` |
| `tools/evaluate_compatibility.py` | `scripts/datastore_capability_compatibility.py` (RC-036) |
| `fixtures/` (16) | `ops/fixtures/datastore-capability-compatibility/` (6 positive, 26 negative) |
| `tests/test_d2_candidate.py` | `scripts/validate-semantics.py` RC-036 and RC-036-NEG (26 ledger mutations and a version-blind evaluator mutant) |
| `vocabulary_reconciliation.candidate.yaml` | kept here as evidence; applied to `binding_catalog.yaml#compatibility.unknown_capability` |

The State requirement evidence the provider draft listed (`l9-wip@ce0c4973`, `mongodb.py` L79–81, L411–421,
L490–498, L309/L331/L1204/L1280; `docs/MONGODB_RUNTIME.md` "External validation still required", L87–104) is
requirement evidence only and is not carried into the canonical binding.

## Operator rulings applied (OPERATOR DECISION "accept all", 2026-11-12, relayed by the coordinator)

| Ruling | Applied as |
| --- | --- |
| DR-D2-01 admit all 13 definitions | 13 tokens in `capability_definitions.tokens` |
| DR-D2-02 `replicated_durable_commit` | the durability token's name; probe `l9.probe/datastore/replicated-durable-commit@1` |
| DR-D2-03 new section, no new ledger | `capability_definitions` in `technology_capabilities.yaml`; no `canonical_sources.yaml` change |
| DR-D2-04 one unknown-capability term + validator | `binding_catalog.yaml#compatibility.unknown_capability: incompatible_until_resolved`; RC-036 equality check |
| DR-D2-05 pin vendor facts to a server range | `server_version_range {min_inclusive: '9.0', max_exclusive: '9.1'}` (the manual's current line was labelled "Version 9.0 (current)" on retrieval); D2-EVAL-10 makes an unknown or out-of-range server `incompatible_until_resolved` |
| DR-D2-06 snapshot inference; serializable unknown | `snapshot_isolation.fact_basis: inference_from_vendor_statements` with its `inference` text; `serializable_isolation.status: unknown` |
| DR-D2-07 split server time | `server_authoritative_time_in_update_expressions` (provided) and `server_authoritative_time_in_query_filters` (unknown) |
| DR-D2-08 `unique_key` with aliases | `unique_key`; `aliases: {unique_indexes: unique_key, unique_constraints: unique_key}`; `technologies[*].provides` unchanged |

## Executor choices (reported, not owner rulings)

- **Runtime receipt.** The draft proposed a new receipt kind. The canonical text instead names the existing family
  `l9.receipt/conformance@1` plus `additional_bound_coordinates`, so `receipt_catalog.yaml` and its derivation
  cascade are untouched. An owner who wants a separate family needs a successor that registers it.
- **D2-EVAL-10** (server version outside the pinned range) is a consequence of DR-D2-05 that the draft did not have.
- **Coverage scope.** `capability_definitions.coverage.technologies` is `[mongodb, postgresql]`. The tokens of
  `graphiti-mcp` and `zep` (`graph_episode_storage`, `graph_search`, `episode_deletion_by_locator`) stay undefined
  and therefore `incompatible_until_resolved`.
- **PostgreSQL.** No provider binding; every PostgreSQL fact is Unknown pending vendor citation.

## Citations

All 23 MongoDB quotes were re-matched on 2026-11-12 by exact substring against the raw page HTML (tags stripped,
entities unescaped, whitespace folded). One quote was shortened to its exact page text ("you set the write concern
at the transaction level, not at the individual operation level"). No quote remains summarizer-reported.

## Downstream effects (not changed here)

- `l9.projection/stage-provider-bindings@1` selects `$.bindings[?(@.class=="provider")]` and so now includes the
  MongoDB binding, but selects only `$.technologies` from `technology_capabilities.yaml`: it does not carry
  `capability_definitions` or `provider_compatibility_tiers`. A profile successor (`@2`) would be needed for a
  compiler to evaluate tiers from that projection alone. Admitted profiles are not edited in place.
- `semantic-compiler-core@1`, `architecture-intelligence@1` and `repository-operations-compiler@1` select
  `$.compatibility` and/or `$.binding_rules`; their projected bytes change. Their payload schemas declare those
  sections as open objects.
