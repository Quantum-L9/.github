# Release Validation v3.42.1

Release status: **registry-only successor candidate**. Admission requires the repository owner's explicit decision (the merge) for this exact subject; no admission is claimed.

## Closure

- The factory's `verify_birth_integrity.py --require-receipt`, run from the template commit the receipt names (an ancestor of the factory's default branch), passed every check against a full clone of the newborn.
- The receipt digest, root-commit trailers and immutability were re-checked by `ops/register-birth.py`.
- RC-023 checks the entry as factory-born (ADR-039); SC-008 proves this record.

## Release integrity

`HASHES.sha256` inventories every canonical source, every ADR plus the index, and this release's Markdown (`sha256sum` with `./` paths, `LC_ALL=C` order by path).
