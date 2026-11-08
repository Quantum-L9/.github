# Release Validation v3.35.0

Release status: **admitted additive successor** (ADR-032, 2026-11-08). Admission takes effect at the `main` commit that merges the pull request carrying ADR-032.

## Closure

- **SC-001** parses 94 canonical sources as YAML mappings.
- **PROJECTION-013**, **PROJECTION-014** and **PROJECTION-017**: each @2 profile is a new version `successor_of` its @1, removes no @1 selection, and resolves its output schema from the verified profile and the verified source class.
- **SC-008** proves this release record: **94** canonical sources, **32** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with 59 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.35.0 in ADR-032. The decision relied on the validation evidence above and on the admission gate (`check_admission_closure.py --require released --admitted-base v3.34.0`), run on the candidate commit `451a87c2649a2e01f27371e3ec2ebdae5a9c2dd2`:

- **Verdict:** `RELEASED_CANDIDATE`. Registration, the validator, `make validate check test`, the release record and scope all pass.
- **Discovery:** measured from v3.34.0, it finds exactly this subject, with no unclassified change and no moved derived coordinate.
- **Producer:** `Quantum-L9/l9-semantic-compiler-engine@d5ce17d01de72c8017e4021fbe43f9eaed2b69de` is a clean checkout. It projected and composed the three @2 pairs twice, and every artifact passes. The two runs are byte-identical across 48 files. Independent verification passes, including all 112 negative controls.
- **Base gap (reported, not waived):** ADR-031 has no target-class row.

Post-merge trusted replay on `main` is a separate, later step.
