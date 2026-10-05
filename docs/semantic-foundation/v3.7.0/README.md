# Semantic Foundation v3.7.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor admits the minimum organization semantics required for deterministic Python repository-operations compilation without introducing a new semantic ledger or widening into Node/package.json, CI, Docker, repository birth, or product-build redesign.

## Bounded delta

- Adds `l9.repository-operations-ir/v1` as a derived, non-authoritative IR with a registered lowering path to `l9.target-ir/v1`.
- Registers `toml` and `makefile` as target technologies.
- Adds `l9.binding/repository-operations-pyproject@1` for `pyproject.toml`.
- Adds `l9.binding/repository-operations-makefile@1` with exactly `build`, `test`, and `validate`.
- Adds `l9.projection/repository-operations-compiler@1`.
- Adds RC-015 repository-operations closure and seven fail-closed negative cases to `scripts/validate-semantics.py`.

No new canonical semantic file, global capability identity, technology profile, ProductTopology stage, repository-birth policy, Node/package.json semantic, or ADR is introduced.

## Authority

`Quantum-L9/.github` remains the canonical owner of the affected global catalogs. Repository-specific intent remains downstream repository authority. Realization evidence may establish alignment or drift but does not override upstream authority.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.6.0/`. The predecessor release record remains immutable.
