# Release Validation v3.35.0

Release status: **additive successor candidate**.

## Closure

- **SC-001** parses 94 canonical sources as YAML mappings.
- **PROJECTION-013**, **PROJECTION-014** and **PROJECTION-017**: each @2 profile is a new version `successor_of` its @1, removes no @1 selection, and resolves its output schema from the verified profile and the verified source class.
- **SC-008** proves this release record: **94** canonical sources, **31** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with 59 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

Not admitted. Admission requires the owner's explicit decision recorded in an accepted ADR.
