# Release Validation v3.31.0

Candidate status: **corrective successor candidate**.

## Single-kind architecture pattern fields

- **SC-001** parses 83 canonical sources as YAML mappings, including the changed ledger.
- An exhaustive kind scan of the 24 sources `l9.projection/architecture-intelligence@1` selects (`tools/build_schema_grammar_candidate.py` in `Quantum-L9/l9-semantic-compiler-engine`) finds two mixed-kind fields at `9488d8f` and none at this release. This is evidence for the candidate, not a release check.
- **RC-029** still passes: `l9.pattern/dependency-package@1`, including its `lifecycle`, is unchanged.
- **RC-030** and **RC-032** still pass. They re-project `architecture-intelligence@1` and `pr-audit@1`, which select the changed patterns, against their registered payload schemas.
- **Not mechanically checked:** that a pattern field has one kind across patterns. Scratch-copy probes that restore either old form raise no failure beyond the expected SC-008 hash mismatch.
- **SC-008** proves this release record:
  - the manifest lists all **83** canonical sources;
  - the ADR count is **28**;
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 57 PASS lines and no FAIL, the same set as on `72cf686` (v3.30.0, Quantum-L9/.github#218). No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.31.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
