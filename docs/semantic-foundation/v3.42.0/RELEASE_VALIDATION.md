# Release Validation v3.42.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed. The predecessor v3.41.0 is itself a candidate.

## Closure

- **RC-023** keeps its pinned census of 33 repositories. An entry carrying `birth_provenance` is counted apart and must pass `rc023_factory_entry_problems`: exact entry and provenance keys, `factory: Quantum-L9/l9-repo-template`, `receipt_schema: l9.birth-receipt/v1`, a `sha256:<64 hex>` digest, 40-hex `root_commit`, `template_sha` and `org_policy_sha`, a birth-profile name, non-empty `template_version` and `born_at`, and an id equal to `rc023_factory_repository_id(coordinate.repository)`. The registry-wide coordinate, lifecycle, class and uniqueness rules apply to it unchanged. **RC-023-NEG**: 70 mutations fail closed at their intended field. The 13 new ones cover another factory, a malformed digest, a wrong receipt schema, a malformed root commit, a missing or unknown provenance key, provenance that is not a mapping, a free-form id, an unknown entry key, a pinned entry claiming provenance, a non-current or wrongly classed factory entry, and a factory entry re-registering a pinned repository.
- **SC-008** proves this release record: **117** canonical sources, **39** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- `ops/test-register-birth.py` (run by `ops/validate-starters.sh`) renders an entry from a fixture birth, applies it to a copy of this tree (the registry entry plus a generated v3.42.1 registry-only release record, which then passes the full semantic validator), re-applies it idempotently, and refuses a duplicate, a tampered receipt, disagreeing trailers, a receipt modified after birth, a foreign factory, a shallow clone, an ambiguous class, a factory verifier that does not PASS, and a template commit that is not on the factory's default branch.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle or receipt ledger is touched.

## Projection effects

`l9.projection/architecture-intelligence@1` selects `repository_registry.yaml` at `$.purpose`, `$.global_rules`, `$.does_not_own`, `$.repository_lifecycle`, `$.repositories`, `$.aliases` and `$.downstream_obligations`. None of these changes in this release, so its projected bytes are unchanged. A later factory registration adds an item under `$.repositories` with an extra `birth_provenance` key. Both payload schemas declare repository items as open objects that require only `id`, `coordinate`, `lifecycle` and `class_ref`, so they accept it. No profile, selector or payload schema changes.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories, including the v3.41.0 candidate, are byte-identical.

## Admission state

Not admitted. The owner decision covers the factory-born entry shape, the id and class rules, the RC-023 change, and the registration automation. No repository is registered by this release. `Quantum-L9/l9-state` will be proposed by the automation once this release is merged.
