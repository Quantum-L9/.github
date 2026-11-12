# Release Validation v3.37.0

Release status: **admitted additive successor** (ADR-034, 2026-11-11). Admission takes effect at the `main` commit that merges the pull request carrying ADR-034.

## Closure

- **SC-001** parses 112 canonical sources as YAML mappings.
- **SC-004**, **RC-001**, **RC-002** and **RC-011**: the derivation cascade is rebound from final bytes (41 invariants, 31 contracts).
- **SC-008** proves this release record: **112** canonical sources, **34** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.37.0 in ADR-034, by an explicit instruction in governed session `session_017xwbxw3RduoWFP29VkobHR` to admit the candidates of the CTO semantics admission pack v2; this release admits its Stage A subject only: `L9-INTEGRATION-001`, `technical_coordination_role` and `integration_responsibility`. Target class: canonical global semantics, owned by `Quantum-L9/.github`. Approved `semantics/` tree: `73a6adf716799365163926ef6b3eb66661007a13` at candidate commit `360c5d304c70883d9b1b62acaa8c51864f8ac584`, where `check_admission_closure.py --require released` reported `RELEASED_CANDIDATE`.

Post-merge trusted replay on `main` is a separate, later step.
