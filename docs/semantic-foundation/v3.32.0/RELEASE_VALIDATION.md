# Release Validation v3.32.0

Release status: **admitted additive successor** (ADR-029, 2026-11-08). Admission takes effect at the `main` commit that merges Quantum-L9/.github#222.

## Strategic Value and composition provenance closure

- **SC-001** parses 86 canonical sources as YAML mappings, including the three added files.
- **SC-004** binds the contracts derivation to the new invariants digest and count; **RC-001**, **RC-002** and **RC-011** bind capabilities, lifecycle and receipt catalog to the rebound digests (D3).
- **RC-006** finds `strategic_value_model.yaml` in both the source registry and `semantic_catalogs`.
- **RC-033** proves every `required_provenance` token of `l9.compose/stage-context@1` and `l9.compose/strategic-planner-value@1` is defined in `provenance_constraints` with an implemented criterion; its 8 negative cases fail closed.
- **SC-008** proves this release record: **86** canonical sources, **29** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

## Existing closure

`scripts/validate-semantics.py` exits 0 with 59 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.32.0 in ADR-029. The validation evidence above is what the decision relied on; the evidence itself grants no authority or promotion. The `semantics/` tree is unchanged since the producer qualification, so that evidence applies to the admitted bytes without requalification. Post-merge trusted replay is a separate, later step.
