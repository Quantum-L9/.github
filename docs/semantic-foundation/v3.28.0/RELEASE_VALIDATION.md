# Release Validation v3.28.0

Candidate status: **additive successor candidate**.

## Profile and payload-schema closure

- **SC-001** parses 79 canonical sources as YAML mappings, the 17 new payload schemas among them.
- **SC-003** finds 79 unique `artifact_id` values.
- **SC-008** proves this release record:
  - the manifest lists all **79** canonical sources;
  - the ADR count is **24**;
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.
- **Compiler evidence.** It was run at a revision whose semantics tree is byte-identical to this release's (`semantics/` tree object `6c4a971d098bf308eb77bf8079e775da4dcf9387`), using `l9-semantic-compiler` at Quantum-L9/l9-semantic-compiler-engine `dd1a2373e9cf89116bc7255250ff9c318a7b2115`:
  - **project, compose and per-source receipt verification PASS** for `evidence-assessment`, `semantic-change-context`, `architecture-break-test`, `globalization-assessment`, `work-state-continuity`, `hard-constraint-context`;
  - all 28 of their source projections verify;
  - before the schemas were registered, all nine derived-schema profiles were `unknown` on `payload_schema`;
  - `identity-assurance`, `strategic-metacognition`, `strategic-planning-context` remain `unknown`, as recorded in the README.
- **Reproducibility.** Three independent `schema-derive` runs produced byte-identical schema files.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 57 PASS lines and no FAIL, including the negative-case batches: SC-001 to SC-010, and every RC check it runs (RC-001 to RC-007, RC-009, RC-011 to RC-030 and RC-032). No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.28.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
