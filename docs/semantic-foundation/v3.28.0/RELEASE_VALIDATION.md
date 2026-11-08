# Release Validation v3.28.0

Release status: **admitted additive successor** (ADR-025, 2026-11-08). Admission takes effect at the `main` commit that merges Quantum-L9/.github#211.

## Profile and payload-schema closure

- **SC-001** parses 82 canonical sources as YAML mappings, including the 20 payload schemas.
- **SC-003** finds 82 unique `artifact_id` values.
- **SC-008** checks this release record:
  - the manifest lists all **82** canonical sources;
  - the ADR count is **25** (ADR-025 records the admission);
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown, at the patched bytes.

## Producer qualification at the patched coordinates

The run used authority commit `453701a671b3c9acc3400c47c926d1235adfeffd`, whose `semantics/` tree `7c6f35ddc701e6913c78054745e1e2179775299f` is this release's. The compiler was `l9-semantic-compiler` 0.9.3 at Quantum-L9/l9-semantic-compiler-engine `943db9a462d35ba66771a700ece77c746295f591`, the producer pinned in the #210/#211 qualification.

The earlier #214 run used `dd1a2373`. Its `passes/validate.py`, `engine/` and `passes/projection.py` are byte-identical to `943db9a`. No schema generation or derivation was run.

- **Positive:**
  - `project` and `compose` return `pass` for all ten profile pairs: 53 source projections and 10 compositions, with no unresolved criteria;
  - each output passes independent re-verification (`verify-projection`, `verify_composed_projection`) with `payload_schema` and `selection_equivalence` both `pass`;
  - all 63 receipts validate, report `pass` with `coverage: complete`, and bind the artifact digest, the profile coordinates and the exact source ref, digest and revision;
  - composition namespaces equal the declared source classes, in declared order.
- **Negative:** 461 of 461 targeted cases are rejected or controlled as intended:
  - 288 payload-schema violations (missing required field, wrong type, wrong `const`, value outside an `enum`, array below a retained `min_items`) plus 63 intact controls;
  - 110 producer cases (missing source pin, wrong profile, source or composition digest, missing or duplicate component, altered payload with and without redigest, tampered receipt, dropped composed namespace, an authority revision without the profile).
- **PATCH-01 equivalence:** all 381 removed `string_list` minimums were ignored by the interpreter before removal. The original and the patched descriptor give identical results for `[]` and for a non-list.
- **Reproducibility:** an independent run from a separate clone, process and output root reproduced all 126 artifact and receipt files byte-for-byte.
- **History:** before the derived schemas were registered, all nine derived-schema profiles were `unknown` on `payload_schema`. The original independent `schema-derive` runs produced byte-identical schema files. The registered schemas now intentionally differ from that output by the PATCH-01 removals only.

Details and the per-schema ledger are in "Schema patch ledger" below. Machine evidence is in `docs/evidence/11-07-26/schema-patch-closeout/` (#210).

## Not established

- **Independent consumer replay:** none of the ten profiles has a consumer verifier reachable from this release.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 57 PASS lines and no FAIL, including:

- the negative-case batches;
- SC-001 to SC-010;
- every RC check it runs: RC-001 to RC-007, RC-009, RC-011 to RC-030 and RC-032.

No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It is generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.28.0 in ADR-025. The validation evidence above is what the decision relied on; the evidence itself grants no authority or promotion. The `semantics/` tree is unchanged since the producer qualification, so that evidence applies to the admitted bytes without requalification.

## Schema patch ledger

Contract: `L9-PROJECTION-SCHEMA-PATCH-CLOSEOUT-01`.

This ledger records how the 20 registered payload schemas were patched in place after registration. None was regenerated, replaced or compared against a regenerated alternative, and `schema-derive` / `schema-synthesize` were not run.

### Coordinates

| Item | Value |
|---|---|
| Authority commit qualified | `Quantum-L9/.github@453701a671b3c9acc3400c47c926d1235adfeffd` |
| `semantics/` tree at that commit | `7c6f35ddc701e6913c78054745e1e2179775299f` (later commits on this branch change documentation only) |
| Pre-patch `semantics/` tree (PR #214 head `1e9cb8b`) | `d955349ec6d9359687aa0323e3a9b26836c466ac` |
| Producer (pinned compiler) | `Quantum-L9/l9-semantic-compiler-engine@943db9a462d35ba66771a700ece77c746295f591`, `l9-semantic-compiler` 0.9.3 |
| Machine evidence | `docs/evidence/11-07-26/schema-patch-closeout/` (evidence PR #210) |

Compiler choice: `943db9a` is the producer pinned in the #210/#211 qualification. The earlier #214 run used `dd1a237` (compiler PR #26, unmerged). That revision adds the schema-synthesis modules and CLI subcommands on top of `943db9a`. `passes/validate.py`, `engine/` and `passes/projection.py` are byte-identical between the two revisions, so the interpreter and producer path are the same.

### PATCH-01: `min_items` under `type: string_list`

`schema_violations` in `passes/validate.py` at `943db9a` reads `min_items` only when `type == "array"`. Under `type: string_list`, the key is never read, so a schema declaring `{type: string_list, min_items: N}` claims a minimum that the v1 interpreter does not enforce. #210 recorded this failure as `authority-resolution/negative-report.md` "String-list min_items capability: FAIL".

| Basis | Descriptors | Disposition |
|---|---:|---|
| Observed minimum written by `schema-derive` (18 derived schemas: smallest observed length) | 363 | Removed. The minimum was inferred only from the selected data. |
| Hand-authored `min_items: 1` (2 authority-resolution schemas) | 18 | Removed. No canonical source governs the non-emptiness of these lists. `scripts/validate-semantics.py` RC-017 requires listed entries only for `l9.contract/validation-and-correctness@1`, and authority-resolution does not select that contract. The owner accepted their removal (ADR-025). It is not re-expressed as an enforced array constraint. |
| **Total** | **381** | Removed. `type: string_list` and all other keys are unchanged. |

Equivalence proof: each patched file parses to its original document minus exactly those keys. The pinned interpreter accepts `[]` and rejects a non-list under the original descriptor and under the patched descriptor alike, for all 381 locations. The patch therefore changes no validation outcome. It only stops claiming enforcement the interpreter does not perform. The 49 retained `min_items` all sit on `type: array` descriptors, where they are enforced; their negative cases are below.

No other unsupported descriptor exists. A walk of every descriptor the interpreter visits found no key outside `const`, `enum` and `type`, plus `required`/`properties` (objects) and `min_items`/`items` (arrays).

### PATCH-02: basis of retained constraints

Counting unit: one `const`, one `enum`, one array `min_items`, or one key named in a `required` list.

- **Governing:** the constraint follows from a canonical declaration:
  - the profile's `output.schema` (dispatch `const`);
  - the composition profile's source classes (namespace `required`);
  - an explicit profile selector (a selected field must be present);
  - the exact set of id-filter selectors (`enum` on `id` and array `min_items`).
- **Pinned snapshot:** the constraint describes the selected data at the recorded source revision. It holds at the coordinates above. It is **not** semantic law, and a later change to a selected source can break it until the schema is edited.
- **Unsupported:** neither of the above. None remain after PATCH-01.

| Schema | Origin | `string_list` `min_items` removed | Governing | Pinned snapshot | Unsupported |
|---|---|---:|---:|---:|---:|
| `semantics/architecture_break_test_composition.schema.yaml` | derived | 14 | 22 | 119 | 0 |
| `semantics/architecture_break_test_projection.schema.yaml` | derived | 14 | 5 | 100 | 0 |
| `semantics/authority_resolution_composition.schema.yaml` | hand-authored | 9 | 18 | 80 | 0 |
| `semantics/authority_resolution_projection.schema.yaml` | hand-authored | 9 | 5 | 49 | 0 |
| `semantics/evidence_assessment_composition.schema.yaml` | derived | 28 | 17 | 166 | 0 |
| `semantics/evidence_assessment_projection.schema.yaml` | derived | 28 | 5 | 145 | 0 |
| `semantics/globalization_assessment_composition.schema.yaml` | derived | 16 | 21 | 68 | 0 |
| `semantics/globalization_assessment_projection.schema.yaml` | derived | 16 | 9 | 68 | 0 |
| `semantics/hard_constraint_context_composition.schema.yaml` | derived | 10 | 18 | 97 | 0 |
| `semantics/hard_constraint_context_projection.schema.yaml` | derived | 10 | 5 | 84 | 0 |
| `semantics/identity_assurance_composition.schema.yaml` | derived | 21 | 52 | 261 | 0 |
| `semantics/identity_assurance_projection.schema.yaml` | derived | 19 | 5 | 178 | 0 |
| `semantics/semantic_change_context_composition.schema.yaml` | derived | 21 | 16 | 171 | 0 |
| `semantics/semantic_change_context_projection.schema.yaml` | derived | 21 | 5 | 171 | 0 |
| `semantics/strategic_metacognition_composition.schema.yaml` | derived | 21 | 35 | 296 | 0 |
| `semantics/strategic_metacognition_projection.schema.yaml` | derived | 21 | 7 | 278 | 0 |
| `semantics/strategic_planning_context_composition.schema.yaml` | derived | 46 | 80 | 761 | 0 |
| `semantics/strategic_planning_context_projection.schema.yaml` | derived | 41 | 8 | 571 | 0 |
| `semantics/work_state_continuity_composition.schema.yaml` | derived | 8 | 22 | 169 | 0 |
| `semantics/work_state_continuity_projection.schema.yaml` | derived | 8 | 6 | 138 | 0 |
| **Total (20)** | 2 hand-authored, 18 derived | **381** | **361** | **3970** | **0** |

| Constraint | Governing | Pinned snapshot |
|---|---:|---:|
| `const` | 20 (dispatch `schema`) | 1,521 (observed `owner`, `scope`, booleans, single-token strings) |
| `enum` | 40 (equal to the profile's id-filter selector set) | 6 (`id` of wholly selected `rules`, `actors`, `surfaces`) |
| array `min_items` | 40 (equal to the id-filter selector count) | 9 (length of wholly selected arrays) |
| `required` | 261 (53 composition namespaces, 208 selected keys) | 2,434 (observed key presence inside selected entries) |

Every derived schema's `derivation` block records profile, composition and source digests. These digests equal the producer's pins at `453701a` for all 18 schemas, so each snapshot still describes the exact selected data at the qualified coordinates.

Revision-bound restrictions that consumers are most likely to hit:

- `identity_assurance_*`: `actors[].id` and `surfaces[].id` enumerate today's registry entries. Adding an actor or surface fails `payload_schema` until the schema is edited.
- `architecture_break_test_*`: `rules[].id` enumerates today's architecture rules.
- Every derived schema: `const` on observed values (for example `scope: global`, `owner: Quantum-L9/.github`) and observed `required` keys inside selected entries.

Selector equivalence, provenance, digest validation and composition coverage stay separate producer checks. A payload schema adds no authority and does not prove exact membership.

### PATCH-03: seven-field exclusion ledger

To satisfy v1 dispatch (`properties.schema.const`), seven whole-document (`$`) selections were replaced by one `$.<field>` selector per top-level field, in source order. That change landed in `2349a90`, earlier in #214. It is preserved here unchanged. Original selections are read from `290bcd9` (#211).

| # | Profile | Source class (source ref) | Original selection | Current selection | Excluded field and value | Other fields selected |
|---:|---|---|---|---|---|---|
| 1 | `l9.projection/identity-assurance@1` | `actor_registry` (`l9.source/actor-registry@1`) | `$` | 16 field selectors, `$.<field>` in source order | `schema: l9.actor-registry/v1` | 16 of 16 (all) |
| 2 | `l9.projection/identity-assurance@1` | `surface_registry` (`l9.source/surface-registry@1`) | `$` | 15 field selectors, `$.<field>` in source order | `schema: l9.surface-registry/v1` | 15 of 15 (all) |
| 3 | `l9.projection/strategic-metacognition@1` | `strategic_plan_metacognitive_analysis_schema` (`l9.source/strategic-plan-metacognitive-analysis-schema@1`) | `$` | 12 field selectors, `$.<field>` in source order | `schema: l9.schema-definition/v1` | 12 of 12 (all) |
| 4 | `l9.projection/strategic-planning-context@1` | `strategic_plan_graph_schema` (`l9.source/strategic-plan-graph-schema@1`) | `$` | 13 field selectors, `$.<field>` in source order | `schema: l9.schema-definition/v1` | 13 of 13 (all) |
| 5 | `l9.projection/strategic-planning-context@1` | `affected_strategic_closure_schema` (`l9.source/affected-strategic-closure-schema@1`) | `$` | 12 field selectors, `$.<field>` in source order | `schema: l9.schema-definition/v1` | 12 of 12 (all) |
| 6 | `l9.projection/strategic-planning-context@1` | `strategic_planning_episode_schema` (`l9.source/strategic-planning-episode-schema@1`) | `$` | 12 field selectors, `$.<field>` in source order | `schema: l9.schema-definition/v1` | 12 of 12 (all) |
| 7 | `l9.projection/strategic-planning-context@1` | `strategic_plan_revision_candidate_schema` (`l9.source/strategic-plan-revision-candidate-schema@1`) | `$` | 12 field selectors, `$.<field>` in source order | `schema: l9.schema-definition/v1` | 12 of 12 (all) |

The full ledger is in `exclusion-ledger.json` in the evidence directory. The machine check reads each source at `453701a` and confirms:

- the selector list equals the source's top-level fields minus `schema`, in order;
- no projected payload carries the source's `schema` value.

**What stays recoverable.** Each per-source artifact keeps:

- `source_ref`;
- `source_digest`, the semantic digest of the whole source;
- its `projection_profile_ref` and `projection_profile_digest`.

Each receipt's single `inputs` entry binds `ref`, `path`, `revision` and `digest`. The source's own `artifact_id` (for example `l9.actor-registry/global@1` or `l9.schema/strategic-plan-graph@1`) is still selected. The excluded `schema` value can be read exactly from `path` at `revision`.

**What consumers lose.** The payload no longer carries the source document's kind and version marker:

- `l9.actor-registry/v1` and `l9.surface-registry/v1` for the two registries;
- `l9.schema-definition/v1` for the five schema-definition sources.

For the five schema-definition sources, a consumer that hands the selected payload to a schema interpreter must restore the dialect marker from the source coordinates.

**Consumer impact.** The declared consumers are `l9-identity-assurance`, `strategic_plan_metacognitive_reasoner` and `plan_keeper`. None has an implementation in the five repositories reachable from this session, and an organization code search found none. Whether any consumer materially requires the field is **Unknown**. It is not asserted to be lossless.

**Owner disposition: ACCEPTED** (ADR-025, 2026-11-08), as the intended v1 selection contract of the three profiles. Independent consumer compatibility remains undemonstrated.

### PATCH-04: qualification at the patched coordinates

| Check | Result |
|---|---|
| `project`, `compose` | PASS for all 10 pairs: 53 source projections and 10 compositions, every artifact `pass`, no unresolved criteria |
| Independent re-verification (`verify-projection` per source, `verify_composed_projection` per composition) | PASS for all 63. `payload_schema` and `selection_equivalence` both `pass` |
| Receipts | All 63 pass `validate_receipt_document`, with `result: pass` and `coverage: complete`. Each binds the artifact digest, the profile ref/digest and the exact source ref/digest/revision |
| Composition coverage | Namespaces equal the declared source classes and components follow declared order, for all 10 |
| Negative cases | 461 of 461 as expected (below) |
| Reproducibility | A second run from a separate clone, in a separate process and output root, produced all 126 artifact and receipt files byte-identical |

Negative cases, all against the real interpreter or real producer:

| Case | Count | Observed |
|---|---:|---|
| Missing required field | 63 | violation `required field missing` |
| Wrong type (array replaced by string) | 33 | violation `expected array` |
| Wrong top-level `schema` const | 63 | violation `expected const` |
| Wrong nested const | 63 | violation `expected const` |
| Value outside an `enum` | 33 | violation `value not in declared enum` |
| Array below retained `min_items` | 33 | violation `fewer than N items` |
| Intact payload (control) | 63 | no violation |
| Missing source pin | 10 | `INVALID_REQUEST` |
| Wrong profile digest / source digest / composition pin | 30 | `REVISION_MISMATCH` (`profile_digest`, `source_digest`, `composition_profile_digest`) |
| Missing component | 10 | `INVALID_REQUEST` (`source_coverage`) |
| Duplicate component | 10 | `AMBIGUOUS_SEMANTICS` (`duplicate_source`) |
| Altered payload, no redigest | 10 | `REVISION_MISMATCH` (`projection_digest`) |
| Altered payload, producer redigest | 10 | `SEMANTIC_DIVERGENCE` (`selection_equivalence`) |
| Receipt subject tampered | 10 | `InvalidRequest` (receipt digest mismatch) |
| Composed namespace dropped, redigested | 10 | `SemanticDivergence` (`composition_equivalence`) |
| Authority revision that does not declare the profile (`020a94b`) | 10 | `UNRESOLVED_REFERENCE` |

Observation, not a negative case: verifying an artifact against the parent commit `929edd9` passes. Its profile and source digests are identical, and freshness is bound to digests, not to commit identity. This is the declared behavior.

### Known v1 interpreter limitations

| Limitation | Effect here | Remediation |
|---|---|---|
| `min_items` read only for `type: array` | Non-emptiness of `string_list` values is not asserted by any of the 20 schemas | Upstream: enforce list cardinality for every list type, or reject the key. Owner: removal accepted (ADR-025); no minimum is claimed |
| Object `properties` checked only when the key is present; projection schemas declare no top-level `required` | A missing selected field is caught by `selection_equivalence`, not by `payload_schema` | None needed; recorded so `payload_schema` is not read as a completeness proof |
| No closed-object or exact-membership rule | Extra keys are not rejected by the schema | Covered by `selection_equivalence` |
| Dispatch by `properties.schema.const` collides with a selected source's own `schema` field | Seven whole-document selections replaced (PATCH-03) | Narrowing accepted by the owner (ADR-025); an upstream dispatch change is out of scope here |

### Owner decisions (ADR-025) and remaining Unknowns

1. **Seven-field narrowing:** accepted as the intended v1 selection contract (PATCH-03).
2. **Hand-authored authority-resolution minimums:** removal of the 18 `min_items: 1` accepted with the other 363. No cardinality guarantee is claimed.
3. **Pinned-snapshot restrictions:** accepted as revision-bound, not semantic law. A change to a selected source may require a schema update and requalification.
4. **Consumer replay (Unknown):** no independent consumer replay exists for any of the ten profiles. Consumer compatibility, migration and deployment are not claimed.
