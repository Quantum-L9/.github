<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: registration-contract
version: 1.0.0
status: active
-->

# Registration surfaces and the release record

Copy the shape of an entry already on `main`, never one from memory. All paths are under `semantics/` unless they say otherwise.

## Per kind of new semantics

| New item | Surface | Entry shape |
| --- | --- | --- |
| Invariant | `invariants.yaml#invariants` | `{id, statement, scope: global, owner}`, unique id |
| Vocabulary term | `vocabulary.yaml#terms.<key>` | `{semantic_class, definition, question?, detailed_model}` |
| Contract | `contracts.yaml#contracts` | `{id, purpose, scope, owner, source_invariants, applies_to, requires, guarantees, forbidden, outcomes}` |
| Model ledger | new file + `canonical_sources.yaml#sources` + `generic_compiler_manifest.yaml#requires.semantic_catalogs` | `{id: l9.source/<name>@1, path, format: yaml, canonical: true, projection_allowed, derivation_allowed}`. RC-006 requires the registry to equal `semantic_catalogs`. |
| Source class | `projection_profiles.yaml#source_classes.<name>` | `{canonical_artifact: <file>}`. The file must be a registered source. |
| Projection profile | `projection_profiles.yaml#projection_profiles` | `{id, class: consumer, consumer, purpose, sources.<class>.selectors[], output.schema: l9.projection.<name>/v1, forbidden[]}` |
| Composition profile | `composition_profiles.yaml#profiles` | `{id: l9.compose/<name>@1, purpose, accepts: [projection_artifact], composes.projection_profile, merge_strategy{placement: source_class_namespace, source_coverage: exact, duplicate_source: conflict, semantic_identity_collision: require_equivalence}, conflict_result: invalid, output.schema}` |
| Payload schema | new file + `generic_compiler_manifest.yaml#requires.artifact_schemas` (bare filename) | `schema: l9.schema-definition/v1`, `artifact_id: l9.schema/<name>@1`, `governed_by`, and `properties.schema.const` equal to the profile's `output.schema` |

`required_provenance` on a composition profile has no mechanical criterion in compiler 0.9.3. Declaring it makes the composition `unknown` even when every named fact holds. Decide it before the producer run (see `l9.compose/stage-context@1` for the one precedent).

## Digest cascade (rebind in this order)

Each item below holds a digest of the item before it, so changing the first invalidates the rest:

1. `invariants.yaml` (any invariant change)
2. `contracts.yaml#derivation.source_digest_sha256` and `source_invariant_count` (SC-004)
3. `capabilities.yaml` derivation `source_artifacts` sha256 and `item_count` (RC-001)
4. `lifecycle.yaml` and `receipt_catalog.yaml` derivation `source_artifacts` sha256 (RC-002, RC-011)

Commit `2ae5dfa` is the worked precedent. Rebind digests from the final bytes, never from an intermediate state.

## The successor release record (SC-008)

New directory `docs/semantic-foundation/vX.Y.Z/`, one version above the highest. Never edit a previous one.

- `MANIFEST.md` must list every `semantics/*.yaml` as a backticked path. It must state "contains **N** canonical semantic YAML files" with N equal to the directory count, and "contains **N** accepted ADRs" with N equal to the `docs/adr/ADR-*.md` count.
- `README.md` holds the status line (`Status: **ADDITIVE SUCCESSOR CANDIDATE**` until admitted), bounded delta, evidence, outstanding Unknowns and authority.
- `RELEASE_VALIDATION.md` holds closure, release integrity and admission state.
- `HASHES.sha256` covers every `semantics/` file, every ADR, `docs/adr/README.md` and this release's Markdown. Generate it with the v3.21.0 procedure:

```bash
# from the repository root; the release's own Markdown is hashed from inside its directory
( sha256sum ./semantics/*.yaml ./docs/adr/ADR-*.md ./docs/adr/README.md
  cd docs/semantic-foundation/vX.Y.Z && sha256sum ./MANIFEST.md ./README.md ./RELEASE_VALIDATION.md
) | LC_ALL=C sort -k2 > docs/semantic-foundation/vX.Y.Z/HASHES.sha256
```

This command, run with `vX.Y.Z = v3.29.0`, reproduces that release's `HASHES.sha256` byte for byte. Regenerate it after the last edit to any covered file, including the status flip at admission.

`scripts/validate-semantics.py` selects the highest version directory when `--release` is omitted, and so does `make validate`. A candidate release therefore becomes what SC-008 checks as soon as it exists. If another candidate (for example v3.29.0) is open, decide with the owner whether to fold in or follow it before cutting a directory.
