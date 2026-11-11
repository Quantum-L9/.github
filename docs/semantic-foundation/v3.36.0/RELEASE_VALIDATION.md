# Release Validation v3.36.0

Release status: **additive successor candidate**.

## Closure

- **SC-001** parses 112 canonical sources as YAML mappings.
- **SC-004**, **RC-001**, **RC-002** and **RC-011**: the derivation cascade is rebound from final bytes.
- **RC-027**: every contract `source_invariants` entry and every `governed_by` reference of the two new ledgers resolves.
- **RC-034** proves DOMAIN-001..010, BINDING-001..004 and COMPOSE-001..005, and **RC-034-NEG** that 28 adversarial mutations fail closed at their intended field and mapping order leaves every domain profile digest unchanged.
- **SC-008** proves this release record: **112** canonical sources, **32** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with 61 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

Not admitted. Admission requires the owner's explicit decision recorded in an accepted ADR.
