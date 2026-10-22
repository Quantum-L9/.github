# Release Validation v3.26.0

Candidate status: **successor candidate with one declared major break**.

## Operating-plane @2 closure

- **PROJECTION-014** (amended) admits a successor that preserves every predecessor selection, as before, or one that removes selections only as a higher decimal version of the same profile family, same class and consumer, with `breaking_changes` naming every removed `{source_class, selector}` exactly once and nothing else, a non-empty rationale, and `consumer_migration: explicit`. The compiler realizes the same criterion; its test suite proves the exact declaration passes and that a missing declaration, a missing or extra selector, an empty rationale, or a non-explicit migration fails closed.
- **PROJECTION-013** holds: `l9.projection/cursor-governance-operating-plane@1` is byte-for-byte unchanged and resolves at its exact identity.
- **RC-003** and **RC-004** account for the added profile (31 profiles, 215 source references); **RC-006** classifies the added schema ledger exactly once. Every other RC check is unchanged and passes.
- **SC-008** proves this release record: the manifest lists all **61** canonical sources, the ADR count is **23**, and `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.
- **Producer evidence (not CI):** `l9-semantic-compiler` at `8bbd882f6a84c55449b9706c39a62e98eec1057b` with the amended PROJECTION-014 criterion applied, run against the candidate's semantic bytes, emits eight `l9.projection-artifact/v1` artifacts and eight `l9.compiler-receipt/v1` receipts for the profile, every one `result: pass` with `unresolved_criteria: []`; `payload_schema` resolves to `l9.schema/cursor-governance-operating-plane-v2-projection@1` and `successor_of` records `breaking_major: true` with the three removed selections. The unamended compiler refuses the profile (`UNKNOWN_SEMANTIC_OPERATOR`, field `breaking_changes`). No RC pins this profile; see ADR-023 review findings.

## Existing closure

SC-001 to SC-010 and RC-001 to RC-032 pass; RC-003, RC-004 and RC-006 report the counts above.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.26.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
