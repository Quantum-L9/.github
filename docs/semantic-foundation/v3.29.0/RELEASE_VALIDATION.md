# Release Validation v3.29.0

Candidate status: **additive successor candidate**.

## Manifest interface surface and Python Gate Node binding closure

- **SC-001** parses 82 canonical sources as YAML mappings, including the two changed ledgers.
- **SC-006** resolves 5 binding technology targets to registered technologies (4 before this release). `l9.binding/python-gate-node@1` resolves `target.technology: python`.
  - Negative probe: setting it to an unregistered id in a scratch copy fails SC-006 at `bindings[4].target.technology`.
- **SC-007** finds 5 unique binding identifiers.
  - Negative probe: renaming the new entry to `pytest/v1` in a scratch copy fails SC-007 at `bindings[4].id`.
- **RC-029** still passes against the changed manifest schema. Its `resolved_manifest_gate` and existing semantic rules are unchanged.
- **Not mechanically checked:**
  - `target.transport_technology`: a scratch-copy probe setting it to an unregistered id raised no failure beyond the expected SC-008 hash mismatch, because SC-006 reads only `target.technology` and `provider.technology`. `gate-sdk` is registered in `technology_capabilities.yaml`, so the shipped value is correct by inspection only.
  - The eight `maps` entries and fourteen `rules` of the new binding.
  - The six new manifest semantic rules, and the exactness of a manifest's `interfaces`, `effects` and `implementation_ref` copies against its source topology.
  - The new `entry_shapes` block and the three new topology rules, including the form, confinement and symbol rules of `implementation_ref`. The Semantic Compiler at `3bf1a82` enforces the port and adapter resolution law that the shapes record; it does not yet check the coordinate.
- **SC-008** proves this release record:
  - the manifest lists all **82** canonical sources;
  - the ADR count is **26**;
  - `HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 57 PASS lines and no FAIL, including the negative-case batches: SC-001 to SC-010, and every RC check it runs (RC-001 to RC-007, RC-009, RC-011 to RC-030 and RC-032). No RC check is added or amended.

## Release integrity

`HASHES.sha256` inventories:

- the final semantic bytes;
- all ADRs plus the index;
- this release's Markdown.

It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

v3.29.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion.
