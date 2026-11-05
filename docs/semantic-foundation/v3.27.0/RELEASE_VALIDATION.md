# Release Validation v3.27.0

Candidate status: **additive successor candidate**.

## Artifact header closure

- **SC-001** parses 62 canonical sources as YAML mappings, `semantics/artifact_header_model.yaml` among them.
- **SC-002** resolves 44 registered canonical sources (43 before this release) to existing files, with unique ids and paths.
- **SC-003** finds 62 unique `artifact_id` values, including `l9.artifact-header-model/global@1`.
- **RC-006**: the registry equals the 44 semantic catalogs of the generic compiler manifest, which now includes `artifact_header_model.yaml`.
- **RC-027** checks the ledger's `governed_by` against the canonical catalogs:
  - invariants L9-AUTH-001, L9-OWNER-001, L9-SEM-001, L9-PROMOTION-001, L9-EVIDENCE-001, L9-UNKNOWN-001, L9-IDENTITY-001 and L9-PROJECTION-001;
  - contracts `authority-boundary@1`, `semantic-ownership@1`, `evidence-and-receipt@1` and `unknown-and-degradation@1`.

  A negative probe proves the check is live for this ledger: replacing L9-EVIDENCE-001 with an undeclared id in a scratch copy fails RC-027.
- **Not mechanically checked:** the `detailed_model: artifact_header_model.yaml` references on the two new vocabulary terms. A scratch-copy probe pointing one at a nonexistent model raised no failure beyond the expected SC-008 hash mismatch. The references are correct by inspection only.
- **SC-008** proves this release record:
  - the manifest lists all **62** canonical sources;
  - the ADR count is **24**;
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.

## Existing closure

SC-001 to SC-010 and RC-001 to RC-032 pass. No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.27.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
