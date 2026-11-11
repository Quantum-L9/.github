# Release Validation v3.36.0

Release status: **admitted additive successor** (ADR-033, 2026-11-11). Admission takes effect at the `main` commit that merges the pull request carrying ADR-033.

## Closure

- **SC-001** parses 112 canonical sources as YAML mappings.
- **SC-004**, **RC-001**, **RC-002** and **RC-011**: the derivation cascade is rebound from final bytes.
- **RC-027**: every contract `source_invariants` entry and every `governed_by` reference of the two new ledgers resolves.
- **RC-034** proves DOMAIN-001..010, BINDING-001..004 and COMPOSE-001..005, and **RC-034-NEG** that 28 adversarial mutations fail closed at their intended field and mapping order leaves every domain profile digest unchanged.
- **SC-008** proves this release record: **112** canonical sources, **33** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.

`scripts/validate-semantics.py` exits 0 with 61 PASS lines and no FAIL.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Admission state

The repository owner admitted v3.36.0 in ADR-033, by an explicit instruction in governed session `session_017xwbxxt7rGKHw3NhwSXSP4` to admit the whole subject. The decision relied on the validation evidence above and on the admission skill's stages, run on the qualified tree `16ca4cd9cd08ed4602a178a3c57032c9cd5186ac`:

- **Discovery:** measured from the v3.35.0 admission (`--admitted-base v3.35.0`), it finds exactly this subject: no revision, no unclassified change, no missing dependency; declared scope closure passes.
- **Gates:** `scripts/validate-semantics.py`, `make validate` and `make check` pass; CI passes `validate-semantics.py` and `validate-starters.sh` (the `make test` suite). The checker's combined `evaluate()` was not run in the authoring session because it invokes `make test`, which that session reserves for CI.
- **Producer:** `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574`, a clean checkout, projected and composed all eight domain pairs twice at `0b46944911bda80ba375f448a7513630216b5d89`: 39 projections and 8 compositions verified independently with 0 gaps, 225 of 225 negative controls rejected, 94 files byte-identical across runs.

Post-merge trusted replay on `main` is a separate, later step.
