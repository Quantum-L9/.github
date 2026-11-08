<!-- L9_META
schema: 1
parent: l9-projection-admission
layer: reference
role: subject-closure-contract
version: 1.0.0
status: active
-->

# Subject discovery and closure

A release admits its whole approved `semantics/` tree, so its subject must name everything that changed. `scripts/discover_admission_subject.py` computes that change instead of trusting a hand-written list. It is deterministic and read-only.

## The admitted base

`--base admitted` is the default. It resolves to the commit that admitted the highest release on main whose admission evidence verifies (`references/admission-lifecycle.md`). A status line alone does not select the base.

If no release verifies, the base is empty and every identity is new. Any exact ref may be given with `--base <ref>`. The candidate is the working tree, or `--candidate <ref>`. The report names both resolved commits.

## Identity census (per tree)

| Kind | Identity | Record compared |
| --- | --- | --- |
| `invariants` | `invariants.yaml#invariants[].id` | the entry |
| `vocabulary_terms` | `vocabulary.yaml#terms.<key>` | the entry |
| `contracts` | `contracts.yaml#contracts[].id` | the entry |
| `canonical_sources` | `canonical_sources.yaml#sources[].id` | the registry entry, plus the file's *residual* content |
| `source_classes` | `projection_profiles.yaml#source_classes.<name>` | the declaration |
| `projection_profiles` | `projection_profiles.yaml#projection_profiles[].id` | the profile |
| `composition_profiles` | `composition_profiles.yaml#profiles[].id` | the profile |
| `schemas` | each file in `generic_compiler_manifest.yaml#requires.artifact_schemas` | its bytes |

A source's **residual content** is its YAML with two parts removed: every `derivation` subtree, and the collections it hosts as identities of their own kind. Those collections are `invariants`, `terms`, `contracts`, and `source_classes` plus `projection_profiles`. As a result, adding an invariant makes the invariant a subject, not `invariants.yaml` as well. A digest-cascade update is a derived coordinate, not a change of meaning.

## Discovery report (`l9.projection-admission-subject-closure/v1`)

| Field | Meaning |
| --- | --- |
| `base`, `candidate` | Exact commits, or `null` / `WORKTREE` |
| `identities.<kind>` | `new`, `changed` and `removed` lists, and an `unchanged` count |
| `admission_subjects.<kind>` | `new` + `changed`: what the owner decision must cover |
| `revisions` | Changed identities whose meaning is redefined, as `<kind>:<id>` (see below) |
| `superseded` | New profiles declaring `successor_of` |
| `required_dependencies[]` | `{subject, dependency, state}`. `state` is `admitted` (present at the base and not a subject), `subject` or `missing`. |
| `changed_derived_coordinates[]` | `{file, path}` of each `derivation` subtree whose value changed |
| `unclassified_changes[]` | Changed `semantics/` files that no kind accounts for, such as a compiler contract file or the non-identity part of a registry host. This skill cannot admit them. |
| `status`, `gaps` | `fail` on a census ambiguity, a removed identity, an admitted profile edited in place, a missing dependency or an unclassified change |

### Dependency graph

| Subject kind | Depends on |
| --- | --- |
| contract | every `source_invariants` entry |
| vocabulary term | `subtype_of` term; the source registered at `detailed_model` |
| source class | the source registered at `canonical_artifact` |
| projection profile | each selected source class; the schema declaring its `output.schema`; its `successor_of` profile |
| composition profile | the projection profile it composes; its output schema |
| payload schema | the profile(s) in its `governed_by` |

### Revisions

A changed identity of these kinds redefines admitted meaning: invariant, vocabulary term, contract, source class, payload schema, and canonical source when its *registry entry* changes. The subject must declare each one in `revisions`, or the change is a silent reinterpretation.

A change to a model ledger's residual content is a subject but needs no revision entry. Its items are reviewed as subjects, and the approved tree binds its bytes. Profiles are never revisions: an admitted profile version is immutable (PROJECTION-013), so a change needs `@N+1`.

## Subject schema (`l9.projection-admission-subject/v1`)

```json
{
  "schema": "l9.projection-admission-subject/v1",
  "description": "optional",
  "invariants": [], "vocabulary_terms": [], "contracts": [], "canonical_sources": [],
  "source_classes": [], "projection_profiles": [], "composition_profiles": [],
  "schemas": ["<bare filename under semantics/>"],
  "revisions": ["<kind>:<id>, also listed under that kind"]
}
```

Unknown keys, repeated items and an empty subject are UNRESOLVED. `--write-subject` emits exactly the discovered subjects and revisions.

## Scope rules (`--declared`, and the checker's `scope` stage)

A declared subject passes closure only when all of these hold:

1. Every discovered admission subject is declared. Otherwise the result is `scope closure: <kind>:<id> … omitted`.
2. Every discovered revision is declared, and every declared revision is a real change. Otherwise the result is `semantic ownership: …`.
3. Every dependency of a declared item is admitted at the base and unchanged, or is itself declared. Otherwise the result is `semantic closure: … neither admitted at the base nor in the subject`.
4. The discovery itself passes.

Declaring an already-admitted dependency is allowed. It is reported under `declared_already_admitted`. `check_admission_closure.py` applies these rules only while the subject is not yet admitted. Once a subject is ADMITTED, later unrelated changes on main do not demote it.
