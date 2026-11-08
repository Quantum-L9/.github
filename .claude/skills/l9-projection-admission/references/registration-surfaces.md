<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: registration-contract
version: 2.0.0
status: active
-->

# Registration surfaces and the release record

Copy the shape of an entry already on `main`, never one from memory. All paths are under `semantics/` unless they say otherwise.

## Per kind of new semantics

| New item | Surface | Entry shape |
| --- | --- | --- |
| Invariant | `invariants.yaml#invariants` | `{id, statement, scope: global, owner}`, unique id |
| Vocabulary term | `vocabulary.yaml#terms.<key>` | `{semantic_class, definition, question?, subtype_of?, detailed_model?}` |
| Contract | `contracts.yaml#contracts` | `{id, purpose, scope, owner, source_invariants, applies_to, requires, guarantees, forbidden, outcomes}` |
| Model ledger (source registration) | new file + `canonical_sources.yaml#sources` + `generic_compiler_manifest.yaml#requires.semantic_catalogs` | `{id: l9.source/<name>@1, path, format: yaml, canonical: true, projection_allowed, derivation_allowed}`. RC-006 requires the registry to equal `semantic_catalogs`. |
| Source class | `projection_profiles.yaml#source_classes.<name>` | `{canonical_artifact: <file>}`. The file must be exactly one registered, canonical, projectable source. |
| Projection profile (profile registration) | `projection_profiles.yaml#projection_profiles` | `{id, class, consumer, purpose, sources.<class>.selectors[], output.schema: l9.projection.<name>/v1, forbidden[], successor_of?}` |
| Composition profile | `composition_profiles.yaml#profiles` | `{id: l9.compose/<name>@1, purpose, accepts: [projection_artifact], composes.projection_profile, merge_strategy{placement: source_class_namespace, source_coverage: exact, duplicate_source: conflict, semantic_identity_collision: require_equivalence}, conflict_result: invalid, output.schema}` |
| Payload schema (payload-schema registration) | new file + `generic_compiler_manifest.yaml#requires.artifact_schemas` (bare filename) | `schema: l9.schema-definition/v1`, `artifact_id: l9.schema/<name>@1`, `governed_by.<projection|composition>_profile_ref`, and `properties.schema.const` equal to the profile's `output.schema` |
| Source-class payload schema (compiler 0.10.0, for a profile declaring `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}`) | new file + `generic_compiler_manifest.yaml#requires.artifact_schemas` (bare filename) | `schema: l9.source-class-payload-schema/v1`, `artifact_id`, `authority.owner`, `schema_id` equal to the profile's `output.schema`, `document_kind` (`projection_payload_schema` or `composition_payload_schema`), `payload_validation`, `descriptor_dialect`, `governed_by.<projection|composition>_profile_ref`, and `source_shapes[{source_class, source_ref, descriptor}]` in the profile's source-class order. No top-level `type`/`properties`/`fields`/`required`/`items`/`const`/`enum`. Render it with the compiler's `registered_schema_documents()`; never hand-write descriptors. |

## What the gate checks per kind (`INCOMPLETE` on any gap)

Registries are checked whole first. A duplicate source id, two ids at one path, a schema listed twice, or two registered schemas declaring one output id makes **every** subject INCOMPLETE. A repeated YAML mapping key in any ledger is UNRESOLVED. The gate never resolves an ambiguity by position.

| Kind | Policy |
| --- | --- |
| Global invariant | Defined exactly once; non-empty `statement`; `scope: global`; an `owner`; its statement is not identical (whitespace and case folded) to another invariant's. |
| Vocabulary term | Present; `definition` and `semantic_class`; `subtype_of` names a term; `detailed_model` is a registered source. A changed term needs a declared revision (`subject-closure.md`). |
| Contract | Defined once; `l9.contract/<name>@<N>`; `purpose`, `scope`, `owner`; non-empty `source_invariants`, each defined. Closure then requires each one to be admitted or in the subject. |
| Canonical source | Registered exactly once; the file exists; `canonical: true`; `projection_allowed: true`; listed in `semantic_catalogs`. |
| Source class | Declared; its `canonical_artifact` is bound to exactly one registered source that is canonical, projectable and catalogued. |
| Projection profile | Defined once; `l9.projection/<name>@<N>`; only fields compiler 0.10.0 knows (it adds `payload_validation`); a declared `class` (a `consumer` class names its consumer); a `purpose`; every source class bound as above; every selector inside the `l9.selector/v1` grammar and selecting something in its source (`missing_required_selector_result_is_invalid`); `output.schema` declared by exactly one registered schema whose `governed_by` names this profile; a `successor_of` profile with the same class and consumer (PROJECTION-014); not an admitted version edited in place (PROJECTION-013). |
| Composition profile | Defined once; `l9.compose/<name>@<N>`; known fields; `accepts: [projection_artifact]`; `conflict_result: invalid`; exactly the namespaced or the deep-merge strategy, and a namespaced one names the profile it composes, which is defined once; output schema as above; not edited in place. |
| Payload schema | Listed once in `artifact_schemas`; the file exists; `schema: l9.schema-definition/v1`; an `artifact_id`; `properties.schema.const` is the output of exactly one profile. |
| Source-class payload schema | Listed once in `artifact_schemas`; the file exists; `schema: l9.source-class-payload-schema/v1`; an `artifact_id`; `schema_id` is the output of exactly one profile, which declares `payload_validation` (and a profile declaring it resolves to this type); the right `document_kind`; one well-formed shape per source class of the profile, in order, each bound to the registered source of that class; no legacy union grammar. Downstream re-verification dispatches each payload by its verified source class to that shape's descriptor through the compiler's strict interpreter (`validate_descriptor_payload`). |

**Unresolvable declarations** do not block registration. They are listed under `registration.unresolvable_declarations`, and the compiler can only report them as `unresolved`, so downstream can never PASS while they remain. They are: a `forbidden` category without a criterion in `forbidden_constraints.definitions` (PROJECTION-016), a `rules` entry, an `output` key other than `schema`, and `required_provenance`. `l9.compose/stage-context@1` is the precedent. Decide each one with the owner before the producer run.

## Digest cascade (rebind in this order)

Each item below holds a digest of the item before it, so changing the first invalidates the rest:

1. `invariants.yaml` (any invariant change)
2. `contracts.yaml#derivation.source_digest_sha256` and `source_invariant_count` (SC-004)
3. `capabilities.yaml` derivation `source_artifacts` sha256 and `item_count` (RC-001)
4. `lifecycle.yaml` and `receipt_catalog.yaml` derivation `source_artifacts` sha256 (RC-002, RC-011)

Commit `2ae5dfa` is the worked precedent. Rebind digests from the final bytes, never from an intermediate state. Discovery reports these under `changed_derived_coordinates`, not as subjects.

## The successor release record (SC-008)

New directory `docs/semantic-foundation/vX.Y.Z/`, one version above the highest on main. Never edit a previous one. The gate's `release.sequence` allows only one change to an existing directory: the open, unadmitted candidate on main, when the owner chose to fold into it. It also refuses a second new directory and a new directory that does not follow main.

- `MANIFEST.md` must list every `semantics/*.yaml` as a backticked path. It must state "contains **N** canonical semantic YAML files" with N equal to the directory count, and "contains **N** accepted ADRs" with N equal to the `docs/adr/ADR-*.md` count.
- `README.md` holds the status line (`Status: **ADDITIVE SUCCESSOR CANDIDATE**` until admitted), bounded delta, evidence, outstanding Unknowns and authority.
- `RELEASE_VALIDATION.md` holds closure, release integrity and admission state.
- `HASHES.sha256` covers every `semantics/` file, every ADR, `docs/adr/README.md` and this release's Markdown. The gate's `release_inventory` re-verifies this complete inventory at any commit, not only the subject's files. Generate it with the v3.21.0 procedure:

```bash
# from the repository root; the release's own Markdown is hashed from inside its directory
( sha256sum ./semantics/*.yaml ./docs/adr/ADR-*.md ./docs/adr/README.md
  cd docs/semantic-foundation/vX.Y.Z && sha256sum ./MANIFEST.md ./README.md ./RELEASE_VALIDATION.md
) | LC_ALL=C sort -k2 > docs/semantic-foundation/vX.Y.Z/HASHES.sha256
```

This command, run with `vX.Y.Z = v3.29.0`, reproduces that release's `HASHES.sha256` byte for byte. Regenerate it after the last edit to any covered file, including the status flip at admission.

`scripts/validate-semantics.py` selects the highest version directory when `--release` is omitted, and so does `make validate`. A candidate release therefore becomes what SC-008 checks as soon as it exists. If another candidate (for example v3.29.0) is open, decide with the owner whether to fold in or follow it before cutting a directory.
