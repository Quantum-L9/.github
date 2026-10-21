# Release Validation v3.24.0

Candidate status: **additive successor candidate**.

## PR-audit projection closure

- **RC-031** (new) pins `l9.projection/pr-audit@1`, `l9.compose/pr-audit@1`, `l9.schema/pr-audit-projection@1`, and `l9.schema/pr-audit-composition@1` whole by canonical-JSON digest; requires exact-id selectors over global records for record collections and existing sections (or one named child) for section selectors; requires the 16 selected contracts to close over their `source_invariants` within the 24 selected invariants; requires every forbidden category to have a declared criterion and no selector to overlap a `payload_excludes` entry for its own source class; requires the composed schema to name exactly one namespace per declared source class, in declaration order, with exactly the sections its selectors produce; and requires each output schema to be defined by exactly one registered artifact schema. **36 negative cases** fail closed at their intended field, including an exclusion widened onto a selected section, an excluded authority section selected, an excluded source class added, a ledger-side scope demotion, and a ledger-side closure break.
- **RC-028** and **RC-030** (unchanged) keep pinning the coding-agent execution and architecture-intelligence profiles; the shared `forbidden_constraints` block and PROJECTION-016 are unchanged.
- **SC-008** proves this release record: the manifest lists all **60** canonical sources, the ADR count is **21**, and `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.
- **Producer evidence (not CI):** `l9-semantic-compiler` at `8bbd882f6a84c55449b9706c39a62e98eec1057b` run against the candidate commit emits thirteen `l9.projection-artifact/v1` artifacts and thirteen `l9.compiler-receipt/v1` receipts for the profile, every one `result: pass` with `unresolved_criteria: []`; `payload_schema` resolves to `l9.schema/pr-audit-projection@1`, and each of the five `declared_constraint:forbidden:*` criteria passes for every source. `compose` under `l9.compose/pr-audit@1` emits one `l9.composed-projection/v1` artifact receipted `operation: composition`, `result: pass`, `unresolved_criteria: []`.

## Existing closure

SC-001 to SC-010 and RC-001 to RC-030 are unchanged and pass.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.24.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
