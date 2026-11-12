# Release Validation v3.38.0

Release status: **admitted additive successor** (ADR-035, 2026-11-12). Admission takes effect at the `main` commit that merges the pull request carrying ADR-035.

## Closure

- **SC-001** parses 112 canonical sources as YAML mappings.
- **SC-004**, **RC-001**, **RC-002** and **RC-011**: the derivation cascade is rebound from final bytes.
- **SC-008** proves this release record: **112** canonical sources, **35** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.38.0 in ADR-035, by an explicit instruction in governed session `session_017xwbxw3RduoWFP29VkobHR`: "push Stages B and C as stacked branches, Stage b admits all 6". Subject: `L9-AUTONOMY-001`, `L9-AUTONOMY-002`, `L9-AUTONOMY-003`, `decision_resolution_class`, `material_decision_escalation` and `bounded_replanning`. Target class: canonical global semantics, owned by `Quantum-L9/.github`. Approved `semantics/` tree: `7d238c39c7493f73df12d196e50747aa2086665d` at candidate commit `7418bd5849b986de6ad42ad7d9c88b77b573a038`, where `check_admission_closure.py --require released` reported `RELEASED_CANDIDATE`.

Post-merge trusted replay on `main` is a separate, later step.
