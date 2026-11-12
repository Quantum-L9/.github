# Release Validation v3.41.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed. The predecessor v3.40.0 is itself a candidate.

## Closure

- **SC-001** parses 117 canonical sources as YAML mappings.
- **SC-006** resolves every binding technology, including `provider.technology: mongodb` of the new provider binding.
- **RC-036** proves: 13 capability definitions, each with scope, guarantee, `not_implied`, failure signal and a runtime probe whose id is unique under `l9.probe/datastore/` and whose text carries no connection or credential material; aliases name defined tokens; every token `mongodb` and `postgresql` assert resolves directly or by alias; the runtime receipt family exists in `receipt_catalog.yaml` and its additional bound coordinates include the binding id and digest, token, probe, deployment profile, provider server version, verdict, execution time and executor; the tier order, the exact rule set D2-EVAL-01..10, the rule order, the empty-set rule, the three non-authority flags and the mapping onto `l9.contract/technology-binding@1` outcomes; `binding_catalog.yaml#compatibility.unknown_capability` equals `technology_capabilities.yaml#binding_rules.unknown_capability.result`; every class provider binding names a registered datastore, a documentation source and an ordered server version range, records a fact for every token its technology asserts, and every fact names a defined token (not an alias), stays within the closed status and basis domains, cites vendor documentation (https URL and verbatim quote) when decided, states its inference when inferred, uses declared deployment profiles, names its token's probe in an obligation that stays `not_executed`, and carries no receipt. It then runs 6 positive and 26 negative compatibility fixtures (synthetic and ledger-sourced; a receipt qualifies only when it is of family `l9.receipt/conformance@1`, names its executor, records a timezone-aware `executed_at`, and carries a `provider_server_version` that is present, parseable, inside the binding's range and equal to the deployed version; receipts are ordered by parsed execution instant; a ledger receipt binds the digest of the canonical binding entry, fixture p06) and requires every D2-EVAL rule to be falsified at least once. **RC-036-NEG**: 26 ledger mutations fail closed, each at its intended check, and the version-blind evaluator mutant is rejected by fixtures n21 and n22.
- **SC-008** proves this release record: **117** canonical sources, **38** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle or receipt ledger is touched (RC-001, RC-002, RC-011 unchanged).
- Every pre-existing check passes unchanged, including RC-034 and RC-035 (the `pytest/v1` digest pin and `pytest/v2` in the same `binding_catalog.yaml`).

`scripts/validate-semantics.py` exits 0 with 65 PASS lines and no FAIL; `make validate`, `make check` and `make test` are run on this tree (results in the candidate report).

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories, including the v3.40.0 candidate, are byte-identical.

## Collision check (v3.37.0 to v3.40.0)

Files changed by v3.37.0–v3.39.0: `invariants`, `contracts`, `capabilities`, `lifecycle`, `receipt_catalog`, `vocabulary`, `projection_profiles`, `composition_profiles`, `generic_compiler_manifest` and two technical-coordination schemas; none is touched here. v3.40.0 changed `binding_catalog.yaml` (`pytest/v2`), which this release also changes, in disjoint regions (a binding appended after `l9.binding/python-gate-node@1`, and the `compatibility` value). No token, section, binding id, probe id, check id (RC-036), ADR number (038) or release directory (v3.41.0) introduced here exists in any of those releases.

## Admission state

Not admitted. The owner decision covers the 13 capability definitions, aliases, coverage, deployment profiles and runtime-receipt binding (ADR-038 decision 9), the two-tier rule, the unknown-capability term, and the MongoDB provider binding. Runtime qualification of any provider is not part of this subject.

**Subject.** `discover_admission_subject.py --checkout . --base 44e02a0 --candidate HEAD --main-ref origin/main` exits 0 with status `pass`: canonical sources `l9.source/binding-catalog@1` and `l9.source/technology-capabilities@1`; no gap, no unclassified change, no required dependency, no revision, no changed derived coordinate.

**Gate as specified (fails structurally).**

`check_admission_closure.py --checkout . --subject <D2 subject> --require released --main-ref origin/main --admitted-base v3.39.0`

Exit 1, verdict `REGISTERED`. Registration, validator and make pass. Two gates fail for one reason: this release is stacked on v3.40.0, an unadmitted candidate that is not on `main`, and the release-sequence and scope rules measure from admitted `main`. `release.sequence` reports "HEAD cuts 2 new releases ['v3.40.0', 'v3.41.0']; cut exactly one successor"; `scope` reports F1's eight identities (`l9.source/compilation-profiles@1`, `l9.source/ir-catalog@1`, `l9.source/product-manifest-schema@1`, `l9.source/product-topology-schema@1`, `l9.source/vocabulary@1`, `conformance_ir.schema.yaml`, `fixture_ir.schema.yaml`, `harness_surface.schema.yaml`) as new or changed since admitted v3.39.0 but omitted from the subject.

**Evidence of record while v3.40.0 is unmerged** (coordinator ruling D2-GATE-01 = A).

`discover_admission_subject.py --checkout . --admitted-base v3.39.0 --candidate HEAD --main-ref origin/main --write-subject <union subject>` (D2's two sources plus F1's five sources and three schemas), then

`check_admission_closure.py --checkout . --subject <union subject> --require released --main-ref refs/pull/247/head --admitted-base v3.39.0`

Exit 0, verdict `RELEASED_CANDIDATE`; scope and release pass (`new_releases: ['v3.41.0']`, `open_candidate_on_main: 'v3.40.0'`). The specified gate is to be re-run unchanged once `.github#247` merges. Folding into v3.40.0 and changing the gate were refused.

## Projection effects

- `l9.projection/stage-provider-bindings@1` now projects `l9.binding/provider/mongodb@1` (`$.bindings[?(@.class=="provider")]`) but not `capability_definitions` or the tiers; a successor profile `@2` is a required follow-up (ADR-038, Consequences).
- Projected bytes change, within payload schemas that declare the affected sections as open objects, for: `l9.projection/semantic-compiler-core@1` (`$.bindings`, `$.compatibility`), `l9.projection/architecture-intelligence@1` (`$.binding_rules`, `$.compatibility`; `architecture_intelligence_projection.schema.yaml` declares both `type: object`) and `l9.projection/repository-operations-compiler@1` (`$.binding_rules`, `$.compatibility`). No profile, selector or payload schema changes.
