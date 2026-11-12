# Release Validation v3.41.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed. The predecessor v3.40.0 is itself a candidate.

## Closure

- **SC-001** parses 117 canonical sources as YAML mappings.
- **SC-006** resolves every binding technology, including `provider.technology: mongodb` of the new provider binding.
- **RC-036** proves: 13 capability definitions, each with scope, guarantee, `not_implied`, failure signal and a runtime probe whose id is unique under `l9.probe/datastore/` and whose text carries no connection or credential material; aliases name defined tokens; every token `mongodb` and `postgresql` assert resolves directly or by alias; the runtime receipt family exists in `receipt_catalog.yaml`; the tier order, the exact rule set D2-EVAL-01..10, the rule order, the empty-set rule, the three non-authority flags and the mapping onto `l9.contract/technology-binding@1` outcomes; `binding_catalog.yaml#compatibility.unknown_capability` equals `technology_capabilities.yaml#binding_rules.unknown_capability.result`; every class provider binding names a registered datastore, a documentation source and an ordered server version range, records a fact for every token its technology asserts, and every fact names a defined token (not an alias), stays within the closed status and basis domains, cites vendor documentation (https URL and verbatim quote) when decided, states its inference when inferred, uses declared deployment profiles, names its token's probe in an obligation that stays `not_executed`, and carries no receipt. It then runs 5 positive and 20 negative compatibility fixtures (synthetic and ledger-sourced) and requires every D2-EVAL rule to be falsified at least once. **RC-036-NEG**: 25 mutations fail closed, each at its intended check.
- **SC-008** proves this release record: **117** canonical sources, **38** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle or receipt ledger is touched (RC-001, RC-002, RC-011 unchanged).
- Every pre-existing check passes unchanged, including RC-034 and RC-035 (the `pytest/v1` digest pin and `pytest/v2` in the same `binding_catalog.yaml`).

`scripts/validate-semantics.py` exits 0 with 65 PASS lines and no FAIL; `make validate`, `make check` and `make test` are run on this tree (results in the candidate report).

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories, including the v3.40.0 candidate, are byte-identical.

## Collision check (v3.37.0 to v3.40.0)

Files changed by v3.37.0–v3.39.0: `invariants`, `contracts`, `capabilities`, `lifecycle`, `receipt_catalog`, `vocabulary`, `projection_profiles`, `composition_profiles`, `generic_compiler_manifest` and two technical-coordination schemas; none is touched here. v3.40.0 changed `binding_catalog.yaml` (`pytest/v2`), which this release also changes, in disjoint regions (a binding appended after `l9.binding/python-gate-node@1`, and the `compatibility` value). No token, section, binding id, probe id, check id (RC-036), ADR number (038) or release directory (v3.41.0) introduced here exists in any of those releases.

## Admission state

Not admitted. The admission subject is computed by `discover_admission_subject.py` against base `821c477` (the v3.40.0 candidate head) and graded by `check_admission_closure.py --require released --admitted-base v3.39.0`; the target rung is `RELEASED_CANDIDATE`. Results are in the candidate report. The owner decision covers the 13 capability definitions, aliases, coverage, deployment profiles and runtime-receipt binding, the two-tier rule, the unknown-capability term, and the MongoDB provider binding. Runtime qualification of any provider is not part of this subject.
