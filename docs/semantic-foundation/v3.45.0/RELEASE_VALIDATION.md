# Release Validation v3.45.0
Release status: **admitted additive successor** (ADR-042, 2026-11-21). Admission takes effect at the `main` commit that merges the pull request carrying ADR-042.
## Closure
- **RC-034** resolves 8 domain consumer bindings: the six v1 bindings, `claude-code@2`, and `manus@1`. `manus@1` is a first version for a host consumer; it names only the `current` surface `manus-cloud`, grants no permission and declares no unresolved coordinate. The pinned census `DOMAIN_BINDING_IDS` carries `manus`; removing it fails the census as well as RC-034. One binding remains blocked for activation and four for migration by declared unresolved coordinates, unchanged from v3.44.0 because `manus@1` declares none. **RC-034-NEG**: all 33 mutations fail closed at their intended field.
- **RC-014** is unchanged. No actor or surface entry is edited: `manus` and `manus-cloud` were already registered as `current`.
- **SC-008** proves this release record: **117** canonical sources, **42** ADRs (ADR-001 to ADR-042), and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle or receipt ledger is touched, so the digest cascade is not rebound.
## Projection effects
`semantics/domain_consumer_bindings.yaml` is selected by no projection profile, so no projected bytes change. The eight domain profiles named by `manus@1` are selected, not modified; a consumer that cites the binding composes them under `l9.contract/domain-composition-compatibility@1` and `l9.contract/domain-composition-provenance@1`. This record performs no such composition.
## Release integrity
`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.
## Admission state
The repository owner directed the v3.45.0 cut on 2026-11-21 in this session: "Cut the v3.45.0 release commit to turn the CI green and finalize the ADR census." Approved `semantics/` tree `5dc33138ee3c92b372b3089a1f538271139a8ad3`, measured at the cut commit. The canonical subject digest was not computed; `check_admission_closure.py` is not present in this tree, so it is recorded as Unknown rather than substituted. Post-merge trusted replay on `main` is a separate, later step.
