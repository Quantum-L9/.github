# Release Validation v3.43.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed. The predecessor v3.42.1 is itself a candidate.

## Closure

- **RC-023** pins a census of 60 repositories (33 earlier plus the 27 admitted here) with `golden-repo` `retired` and every other pinned entry `current`; factory-born and organization-admitted entries are counted apart and checked by shape. Every entry's id must equal `rc023_factory_repository_id(coordinate.repository)`, except the grandfathered `dot-github` (`.github`). `global_rules` must not carry `organization_hosting_does_not_imply_l9_membership` and must carry its four successors and the kept rules as `true`; `organization_completeness` is pinned. **RC-023-NEG**: 99 mutations fail closed at their intended field. The 29 new ones cover a retired entry made current, the superseded rule reintroduced, three successor rules made false, the explicit-admission rule dropped, the completeness block missing or drifting (decision record, archived scope, organization case, archived lifecycle, admission field set, admission basis), a non-folded id, and 15 organization-admitted shape violations (basis, decision record, non-integer or boolean GitHub id, missing or unknown marker key, marker not a mapping, unknown entry key, an entry claiming both markers, a free-form id, a grandfathered id, a pinned entry claiming the marker, re-registering a pinned repository, not current, wrong class).
- **SC-008** proves this release record: **117** canonical sources, **40** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- `ops/test-registry-completeness.js` proves the registry COMPLETE against the organization listing observed on 2026-11-17 (`ops/fixtures/org-listing-2026-11-17.json`, 61 repositories, `golden-repo` archived), INCOMPLETE with one synthetic unregistered repository, an archived-but-current entry or a case-only mismatch, and UNKNOWN (never complete) without a readable listing. It drives the real `registry-completeness.yml` script.
- `ops/test-register-org-repository.py` renders an organization-admitted entry, applies it to a copy of this tree (the entry plus a generated v3.43.1 registry-only release record, which then passes the full semantic validator), re-applies it idempotently, and refuses an archived repository, an invalid name, a grandfathered id, a non-positive GitHub id, an already-registered coordinate and an ambiguous class without a partial write.
- `ops/test-org-admission-workflow.js` drives the real `admit` job scripts: an ordinary repository is proposed in one PR on `org-registry/<name>`, factory-born, archived and `.github` targets are skipped, an unclear receipt probe fails, a re-run is idempotent, foreign work is never rewritten, a dry run opens nothing, and nothing is merged or force-moved.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle, class, derived view or receipt ledger is touched.

## Projection effects

`l9.projection/architecture-intelligence@1` selects `repository_registry.yaml` at `$.purpose`, `$.global_rules`, `$.does_not_own`, `$.repository_lifecycle`, `$.repositories`, `$.aliases` and `$.downstream_obligations`; `$.purpose`, `$.global_rules`, `$.repositories` and `$.downstream_obligations` change, so its projected bytes change and consumers must re-project. Its payload schemas declare those members as open objects (repository items require only `id`, `coordinate`, `lifecycle` and `class_ref`), so they accept the new content. `$.organization_completeness` is not selected. No profile, selector or payload schema changes. `l9.repository-view/memory-namespace-l9@1` is unchanged in definition; its output grows from 34 to 61 members.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown (`sha256sum` with `./` paths, `LC_ALL=C` order by path). Prior release directories are byte-identical.

## Admission state

Not admitted. The owner decision covers the superseding global rules, the 27 admissions, the RC-023 change, the completeness check and the admission automation.
