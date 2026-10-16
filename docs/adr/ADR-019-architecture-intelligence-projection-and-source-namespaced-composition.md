# ADR-019 — Architecture Intelligence Projection and Source-Namespaced Composition

**Status:** Accepted for semantic-foundation v3.22.0 candidate. The repository owner approved the decisions below for bounded implementation on 2026-10-15. Admission of v3.22.0 is the acceptance gate; this record does not admit itself.

## Context

`l9.projection/gar-architecture-observer@1` gives the L9 Global Architect (GAR) a narrow selection of seven sources. `l9.projection/architecture-intelligence@1` widens that to 24 canonical sources and keeps every observer selection.

The producer emits one projection artifact per source (`l9.schema/projection-artifact@1` carries one `source_ref`). Composing the 24 artifacts with `l9.compose/consumer-view@1` deep-merges them at the root. Same-named sections then collide and the composition fails closed: `authority_classes`, `derivation`, `global_rules`, `properties`, `purpose` and `type`. Other sections, such as `required` or `rules` from two different schemas, merge into one list that no longer records which source each part came from.

Three further gaps:

- Neither payload had a schema, so every receipt stayed `unknown`.
- A profile's `forbidden` categories had no mechanical meaning at all.
- The engine refused `successor_of` outright, including on admitted successor profiles.

## Decisions

1. **Explicit consumer migration.** `l9.projection/architecture-intelligence@1` is a new consumer profile. It declares `successor_of: l9.projection/gar-architecture-observer@1` under PROJECTION-014: same class and consumer, every predecessor selector kept. The observer stays byte-for-byte as admitted and resolvable by its exact identity. No rule resolves a consumer-class consumer to its unsuperseded profile, so a consumer moves to the successor only through its own explicit binding. There is no implicit fallback in either direction.

2. **Source-namespaced composition.** `composition_engine_contract.yaml` gains `placement_strategies`:
   - `deep_merge` describes the existing behavior and is unchanged.
   - `source_class_namespace` places each component payload whole under the source class that declares its source in the composed projection profile.

   Under the namespace strategy:
   - coverage is exact;
   - a duplicate component is a conflict even when byte-identical;
   - an identity-bearing record (a sequence member carrying a string `id`) asserted by two sources must be canonically equivalent;
   - no value is merged, concatenated, reconciled or discarded.

   `l9.compose/architecture-intelligence@1` names `composes.projection_profile` and selects this strategy. `l9.compose/consumer-view@1` and `l9.compose/stage-context@1` are unchanged. The ordered composition pipeline is unchanged.

3. **Payload schemas.**
   - `l9.projection.architecture-intelligence/v1` types every selected section of a source projection and requires each record collection's identity fields, as its canonical source declares them.
   - `l9.composed-projection.architecture-intelligence/v1` requires exactly one namespace per declared source class and, within each namespace, exactly the sections that source's selectors produce.

   The `l9.schema-definition/v1` dialect has no closed-object keyword, so rejecting extra content stays with selection equivalence and exact source coverage, both of which are mechanical. The generic projection, composition and receipt envelopes are unchanged.

4. **Forbidden-constraint criteria.** The profile catalog declares `forbidden_constraints` in criterion language `l9.forbidden-constraint` v1 (PROJECTION-016). A category is evaluated only through a criterion declared there; otherwise it stays unresolved. Criteria:
   - `payload_excludes` (canonical paths the payload must not carry);
   - `source_authority` (the source ledger is owned by the catalog's authority).

## Review finding (recorded, not resolved)

`unrelated_domain_payloads` is not independently restrictive under current law:

- The first criterion, `selection_closure`, only restated selection equivalence and is retired.
- Its replacement, `source_authority`, holds a true property, but the canonical authority loader already refuses a ledger owned by anyone else, so the criterion cannot fail on its own.

Every selectable source is `.github`-owned global law. A criterion that rejects payloads unrelated to a consumer's purpose would need a canonical domain or plane classification of sources. That would be a new semantic primitive, and it is escalated rather than invented here.

`provider_implementation_details` excludes provider-class bindings. None exist at this revision; all four bindings are `target` class. The guard is proven by compiler tests, not by live data.

## Consequences

- Each of the 24 source projections and the composed view can now reach a PASS receipt at the producer.
- GAR consumes a producer-emitted, consumer-verified bundle through its own runtime integration binding. GAR implements no selector or composition semantics.
- Changing either profile in place now fails RC-030's digest pins; any change needs a new version.
