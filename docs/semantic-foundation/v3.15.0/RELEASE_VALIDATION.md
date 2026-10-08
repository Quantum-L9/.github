# Release Validation v3.15.0

Candidate status: **additive successor candidate**.

This release keeps the v3.14.0 semantic-foundation inventory. It replaces the explicit-Unknown placeholders of two already registered canonical ledgers with admitted content: one RepositoryClass, one derived memory-namespace view, and an explicit census of 32 repositories. It adds one validator check. It adds no ledger, schema, invariant, contract, receipt family, vocabulary term, authority coordinate, ProductKind, or ADR.

v3.14.0 and v3.13.0 remain unchanged.

## The Unknown being closed

Since v3.6.0, `semantics/repository_classes.yaml` and `semantics/repository_registry.yaml` have been registered as `l9.source/repository-classes@1` and `l9.source/repository-registry@1` in `semantics/canonical_sources.yaml`, classified as semantic catalogs by `semantics/generic_compiler_manifest.yaml`, and named as projection source classes `repository_classes` and `repository_registry` in `semantics/projection_profiles.yaml`. Both ledgers stated that no class and no repository was admitted and that content remained an explicit Unknown until separately admitted.

That Unknown blocked every downstream consumer that must derive L9 corpus membership from organization law rather than from repository names. v3.15.0 is the separate explicit admission the placeholders called for.

## Semantic changes

Modified canonical ledgers:

- `semantics/repository_classes.yaml`:
  - `schema`, `artifact_id`, `canonical`, `authority` and `canonical_source` are unchanged.
  - `global_rules` declares that repository class is explicit and is not inferred from repository name, prefix, hosting organization, shape, language, ProductKind or birth profile; every registered repository has exactly one primary class resolved through the registry; unknown or unresolved class fails closed; class transfers no domain semantic ownership, execution authority or runtime state; generated projections are derived, non-authoritative, provenance-preserving and never authority-expanding; repository memory membership derives from repository class; repository content authority stays with the source repository; memory representation never becomes repository authority.
  - `classes` holds exactly one class, `l9`, id `l9.repository-class/l9@1`, status `current`, `organization_membership: l9`, with its obligations. The memory obligation is pinned by RC-023: `namespace: l9`, `membership: required`, `membership_source: resolved_repository_class`, `content_selection_owned_by_memory_plane: true`, `content_authority_remains_with_source_repository: true`, `memory_representation_authority_class: derived`, `consumer_may_not_independently_add_or_remove_members: true`.
  - `resolution` requires exactly one `class_ref`, resolved through `l9.repository-registry/global@1`; unresolved and unadmitted class both fail closed.
  - `derived_views.l9_memory_namespace` is `l9.repository-view/memory-namespace-l9@1`: selector `class_ref: l9.repository-class/l9@1`, `lifecycle_in: [current, superseded, retired]`; output `namespace: l9`, `authority_class: derived`, `preserve_fields: [id, coordinate, lifecycle, class_ref]`, exhaustive for matching registry entries, with consumer membership expansion and removal both forbidden and repository content never copied into the view.
  - `catalog_status.admitted_classes` is exactly `[l9.repository-class/l9@1]`.
- `semantics/repository_registry.yaml`:
  - `schema`, `artifact_id`, `canonical`, `authority`, `canonical_source` and `class_catalog_ref: l9.repository-classes/global@1` are unchanged.
  - `global_rules` declares explicit identity, immutable id, provider-scoped case-sensitive coordinate, exactly one `class_ref` resolving to an admitted class, no membership or class inferred from name, prefix, hosting, shape, ProductKind or birth profile, fail-closed unknown identity or class, rename and retirement preservation, and no runtime, ingestion, memory or credential state.
  - `repositories` holds exactly 32 entries, every one `provider: github`, `organization: Quantum-L9`, `lifecycle: current`, `class_ref: l9.repository-class/l9@1`. The ids and coordinates are listed in `MANIFEST.md` and pinned by RC-023.
  - `aliases: []`; `downstream_obligations` requires consumers to resolve the class against the catalog, reject unregistered repositories and unadmitted class refs, preserve id, coordinate, lifecycle and class_ref in generated views, and treat generated views as non-authoritative.

Explicitly unchanged:

- Every other canonical ledger, byte for byte. Neither modified ledger is a derivation source of `capabilities.yaml`, `lifecycle.yaml`, `receipt_catalog.yaml` or `contracts.yaml`, so no derivation digest changes and RC-001, RC-002 and RC-011 hold on the pre-existing bytes.
- `semantics/canonical_sources.yaml`, `semantics/generic_compiler_manifest.yaml`, `semantics/projection_profiles.yaml`: both ledgers were already registered, classified and named as projection sources; SC-002, RC-006 and the projection source checks hold unchanged.
- All prior release records, including `docs/semantic-foundation/v3.14.0/` and `docs/semantic-foundation/v3.13.0/`.

## Admission is explicit, never inferred

The 32-entry census was selected by the organization owner as the initial L9 corpus. The resulting authority is the explicit list, not the selection rule: `semantics/repository_registry.yaml` carries no predicate, and RC-023 pins each id and each case-sensitive coordinate individually. A repository whose name begins with `l9-` but is not listed is not a member (RC-023 negative case `l9-prefixed repository not admitted by name`). A repository that earlier design candidates listed, such as `Gate_SDK`, is not a member unless this registry lists it (negative case `extra repository admitted`). Admitting a future repository is a new explicit semantic decision that changes both the registry and the RC-023 pin.

## Validator delta

- `scripts/validate-semantics.py` gains RC-023, the repository class / repository registry closure, plus an isolated negative-case batch. Each case must fail at its intended file and field, and a case that raises instead of failing is itself a failure.
- RC-022 and every earlier check are unchanged.

## RC-023 Repository class / repository registry closure

RC-023 governs `semantics/repository_classes.yaml` and `semantics/repository_registry.yaml` only, and proves the following:

- **Class catalog identity.** `schema == l9.repository-classes/v1`, `artifact_id == l9.repository-classes/global@1`, `canonical == true`.
- **The l9 class exists exactly once, and alone.** `classes` is a mapping, exactly one entry carries id `l9.repository-class/l9@1`, it is `classes.l9`, and `l9` is the only key under `classes`: a second class defined beside it, under any id, fails as a new admission decision. Its `status` is `current` and its `organization_membership` is `l9`.
- **Memory obligation pinned.** `classes.l9.obligations.memory` carries `namespace: l9`, `membership: required`, `membership_source: resolved_repository_class`, `content_selection_owned_by_memory_plane: true`, `content_authority_remains_with_source_repository: true`, `memory_representation_authority_class: derived`, `consumer_may_not_independently_add_or_remove_members: true`. Each differing key is its own located failure.
- **Admitted classes pinned.** `catalog_status.admitted_classes` is exactly `[l9.repository-class/l9@1]`; listing any other class fails.
- **Derived memory view exists exactly once, and alone.** `derived_views` is a mapping, exactly one entry carries id `l9.repository-view/memory-namespace-l9@1`, it is `derived_views.l9_memory_namespace`, and that is the only key under `derived_views`: an unrelated extra view, under any id, fails as a new admission decision. Its selector is `class_ref: l9.repository-class/l9@1`, `lifecycle_in: [current, superseded, retired]` (exact sequence). Its output is `namespace: l9`, `authority_class: derived`, `preserve_fields: [id, coordinate, lifecycle, class_ref]` (exact sequence), `consumer_may_not_add_unregistered_members: true`, `consumer_may_not_remove_required_members: true`.
- **Registry identity.** `schema == l9.repository-registry/v1`, `artifact_id == l9.repository-registry/global@1`, `canonical == true`, `class_catalog_ref == l9.repository-classes/global@1`.
- **Exact census.** `repositories` is a list of exactly 32 mapping entries. Each `id` is a non-empty string registered once; each coordinate is a mapping with `provider: github`, `organization: Quantum-L9` and the pinned case-sensitive `repository` for that id; each (provider, organization, repository) coordinate is registered once; each `lifecycle` is one of `current`, `superseded`, `retired` and is `current` in this release; each `class_ref` is `l9.repository-class/l9@1`. Every pinned id and every pinned coordinate must be present; any id not in the pin fails as not admitted.
- **No crash on malformed shapes.** Comparisons are by value only; a malformed shape produces a located failure, never an uncaught exception.

RC-023 applies no rule to any other ledger and does not re-validate registration, classification or projection-source naming, which SC-002, RC-006 and the projection checks already own (`L9-VALIDATION-001`).

The negative-case batch has 49 cases. Each must fail at its intended file and field. The cases cover:

- **Class catalog identity:** catalog missing; wrong schema; wrong artifact_id; not canonical; `classes` not a mapping.
- **The l9 class:** missing; duplicated under a second key; an unadmitted class defined beside it; status not `current`; organization membership wrong; each of `namespace`, `membership`, `membership_source` and `consumer_may_not_independently_add_or_remove_members` in the memory obligation wrong; memory obligation not a mapping; an unadmitted class listed in `admitted_classes`.
- **Derived memory view:** `derived_views` not a mapping; view missing; view duplicated; an unrelated extra view defined beside it; selector names a different class; lifecycle selector narrowed; output namespace wrong; output claims canonical authority; preserved fields dropped; consumer membership expansion allowed; consumer membership removal allowed.
- **Registry identity:** registry missing; wrong schema; wrong artifact_id; not canonical; wrong class catalog ref; `repositories` not a list.
- **Census pins:** an extra repository admitted (`Gate_SDK`); an `l9-`-prefixed repository not in the pin; an admitted repository missing (`l9-goose`); coordinate case changed (`L9-Ops-MCP` to `l9-ops-mcp`); coordinate renamed; organization case changed; provider changed; coordinate not a mapping; repository id duplicated; provider coordinate duplicated under a second id; wrong class (`l9-goose` as external fork); `class_ref` missing; unrecognized lifecycle (`archived`); admitted repository not current (`retired`); repository entry not a mapping; repository id missing.

Test-first evidence. The final RC-023 logic was run against the unmodified tree of base `b0424175374a99f53a41716f7e079d6426967886` (v3.14.0 as merged, `repository_classes.yaml` sha256 `d772367b…`, `repository_registry.yaml` sha256 `b67855e0…`, extracted with `git archive` and validated with `--root`). The validator failed at exactly three RC-023 lines and nothing else; all 37 prior PASS lines held:

```
FAIL RC-023 semantics/repository_classes.yaml classes=None: must be a mapping of classes
FAIL RC-023 semantics/repository_registry.yaml class_catalog_ref=None: must equal 'l9.repository-classes/global@1'
FAIL RC-023 semantics/repository_registry.yaml repositories=None: must be a list of repository entries
```

The three lines are: the placeholder catalog has no `classes`, the placeholder registry has no `class_catalog_ref`, and the placeholder registry has no `repositories`. After the admission, RC-023 and RC-023-NEG pass.

## Existing closure

The existing semantic-foundation validator still owns SC-001 through SC-010 and RC-001 through RC-022. v3.15.0 adds RC-023 without weakening, reinterpreting or replacing any predecessor check. No failure was suppressed or downgraded; unresolved state does not become success.

## Explicit boundaries

- This release admits one class and 32 repositories. It admits no auxiliary or external-fork class and no repository outside the list; `Gate_SDK`, `Constellation.Gate`, `Cognitive.Engine.Graphs`, `Enrichment.Inference.Engine` and `golden-repo` are not admitted.
- This release does not touch repository birth mechanics, `policies/repo-classes.yml`, seed distribution, rulesets, or any workflow.
- This release modifies no downstream repository and no Semantic Compiler artifact. The memory plane's projection of `l9.repository-view/memory-namespace-l9@1` is downstream work; the view's `authority_class: derived` governs it.
- This release creates no memory record, ingestion eligibility, runtime namespace binding, credential, permission or execution authority.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record, under the same convention as v3.14.0. Prior release directories remain byte-identical; `docs/semantic-foundation/v3.14.0/` and `docs/semantic-foundation/v3.13.0/` are unchanged under `L9-REVISION-001`.

## Admission state

v3.15.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion. Admitting a repository class and registering repositories admits no product, grants no memory write, and creates no ingestion.
