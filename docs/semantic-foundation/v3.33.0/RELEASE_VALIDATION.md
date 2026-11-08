# Release Validation v3.33.0

Release status: **admitted additive successor** (ADR-030, 2026-11-08). Admission takes effect at the `main` commit that merges Quantum-L9/.github#225.

## Closure

- **SC-001** parses 88 canonical sources as YAML mappings.
- **SC-004** and **RC-001**, **RC-002**, **RC-011** bind the contracts derivation and the derived ledgers to the rebound digests.
- **SC-008** proves this release record: **88** canonical sources, **30** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with 59 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.33.0 in ADR-030. The validation evidence above, and the producer qualification recorded in the GT candidate pack, are what the decision relied on; the evidence itself grants no authority. The `semantics/` tree is unchanged since the producer qualification, so that evidence applies to the admitted bytes without requalification. Post-merge trusted replay is a separate, later step.
