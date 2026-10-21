# Release Validation v3.23.0

Candidate status: **additive successor candidate**.

## Coding-agent execution projection closure

This candidate adds no validator check. The closure is proven by the existing checks plus producer evidence:

- **RC-028** (unchanged) pins `l9.projection/coding-agent-execution@1` field by field and by canonical digest: the profile is byte-for-byte as admitted at v3.20.0.
- **RC-030** (unchanged) proves the `forbidden_constraints` block still declares exactly the `l9.forbidden-constraint` v1 language and that the three architecture-intelligence criteria are intact.
- **SC-008** proves this release record: the manifest lists all **58** canonical sources, the ADR count is **20**, and `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.
- **Producer evidence (not CI):** `l9-semantic-compiler` at PR #13 (`7e516b6d`) run against this tree emits three `l9.projection-artifact/v1` artifacts and three `l9.compiler-receipt/v1` receipts for the profile, every one `result: pass` with `unresolved_criteria: []`; `payload_schema` resolves to `l9.schema/coding-agent-execution-projection@1`, and each of the five `declared_constraint:forbidden:*` criteria passes. The compiler at `main` (`37e6758b`) receipts the same tree `unknown` because it evaluates no forbidden criterion.

An RC-031 check mirroring RC-030 for the schema registration and the five criteria, with fail-closed negative cases, is the next step before admission.

## Existing closure

SC-001 to SC-010 and RC-001 to RC-030 are unchanged and pass.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.23.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
