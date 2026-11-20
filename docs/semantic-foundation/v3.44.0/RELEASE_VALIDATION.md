# Release Validation v3.44.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed. The predecessor v3.43.0 and its predecessors back to v3.40.0 are themselves candidates.

## Closure

- **RC-014** closes both identity registries: 6 actors with 2 typed aliases and 11 surfaces with 5 typed aliases, no cross-dimension ownership field, no runtime-resolution structure, and the two strings `claude-code-desktop` and `claude-code-mobile` legally shared across dimensions. New in this release: a `superseded` entry must name its successor(s) as `<artifact_id>#<id>` coordinates of `current` entries of the same registry (`claude-code-mobile` → `l9.surface-registry/global@1#claude-code-web`), a `current` or `retired` entry names none, and no alias canonicalizes to a superseded entry. Mutations checked by hand against this tree, each failing closed at its field: the successor removed, pointed at a retired surface, given as a bare id, a successor added to a retired surface, and `claude-mobile` pointed back at `claude-code-mobile`.
- **RC-034** resolves 7 domain consumer bindings (the six v1 bindings plus `claude-code@2`). `claude-code@2` names its predecessor `claude-code@1` of the same host consumer and only `current` surfaces; `claude-code@1` names retired and superseded surfaces and is accepted only because a successor exists. Removing `claude-code@2` fails both the pinned census and the current-surface rule on `claude-code@1`. **RC-034-NEG**: 33 mutations fail closed at their intended field. The five new ones: the successor link dropped, the successor pointed at another consumer's binding, a retired surface and a superseded surface added to `claude-code@2`, and a first version claiming a predecessor.
- **SC-008** proves this release record: **117** canonical sources, **40** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- No derivation coordinate changed: no invariant, contract, capability, lifecycle or receipt ledger is touched, so the digest cascade is not rebound.

## Projection effects

`l9.projection/identity-attribution@1` selects `surface_registry.yaml` at `$.surfaces`, `$.aliases` and `$.alias_rules`, and `actor_registry.yaml`; `l9.projection/identity-assurance@1`, `@2` and `l9.projection/cursor-governance-identity@1` select both registries. Their projected bytes change and consumers must re-project. The source-class payload schemas of `identity-attribution@1` and `identity-assurance@2` declare surface entries as open objects with a string `status`, so they accept the new content. The `l9.schema-definition/v1` schemas of the superseded `identity-assurance@1` pair pin `status: const current` and do not; see `README.md`, Outstanding Unknowns. `domain_consumer_bindings.yaml` is selected by no profile. No profile, selector or payload schema changes.

## Admission gate

`check_admission_closure.py --admitted-base v3.39.0 --require released` reports `RELEASED_CANDIDATE` for the discovered subject (11 canonical sources, 3 schemas, no revisions; see `README.md`, Admission subject). The admitted base used is v3.39.0, whose decision record the current verifier rejects; that gap is carried in the report.

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown (`sha256sum` with `./` paths, `LC_ALL=C` order by path). Prior release directories are byte-identical.

## Admission state

Not admitted. The owner decision covers the surface lifecycle changes, the `claude-mobile` alias move, the `claude-code@2` binding, the RC-014 and RC-034 changes, and, because the subject is measured from v3.39.0, the content of the open candidates v3.40.0 to v3.43.0.
