# Release Validation v3.7.0

Candidate status: **additive successor candidate**.

This release preserves the v3.6.0 semantic-foundation inventory and adds only the bounded Python repository-operations semantics required by the frozen Repository Documentation Compiler prerequisite.

## Bounded semantic delta

Modified canonical ledgers:

- `semantics/ir_catalog.yaml`: `l9.repository-operations-ir/v1` and its lowering transition.
- `semantics/technology_capabilities.yaml`: target technologies `toml` and `makefile`.
- `semantics/binding_catalog.yaml`: `l9.binding/repository-operations-pyproject@1` and `l9.binding/repository-operations-makefile@1`.
- `semantics/projection_profiles.yaml`: `l9.projection/repository-operations-compiler@1`.

Validator delta:

- `scripts/validate-semantics.py`: RC-015 repository-operations closure plus seven isolated negative cases.

Explicitly unchanged: `semantics/capabilities.yaml`, `semantics/technology_profiles.yaml`, compilation stages, repository-birth policy, Node/package.json semantics, CI semantics, Docker semantics, and all prior release records.

## RC-015 repository operations closure

RC-015 proves:

- the repository operations IR exists exactly once and lowers to Target IR through binding selection and lowering;
- the pyproject and Makefile bindings each exist exactly once and bind the intended target technologies and artifacts;
- Makefile binding v1 maps exactly `build`, `test`, and `validate`;
- the repository-operations consumer profile selects the exact IR, both bindings, and `python`/`toml`/`makefile` technology facts;
- required forbidden semantics are present;
- no repository-operation capability was globalized;
- no technology profile was added for repository build metadata.

The embedded negative-case batch proves fail-closed behavior for: unregistered pyproject target technology; missing Makefile source IR; Makefile v1 widening with `publish`; missing repository-operations IR selector; Node/package.json concern leakage; global capability leakage; and technology-profile leakage.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-014. v3.7.0 adds RC-015 without weakening or replacing predecessor checks.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.7.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion.
