# ADR-024 — Artifact Header Field Semantics as Source Declarations

**Status:** Candidate for semantic-foundation v3.27.0. Drafted on 2026-11-05 at the repository owner's instruction to admit the meanings of native `L9_META` header fields before any consumer maps them. Admission of v3.27.0 is the acceptance gate; this record does not admit itself.

## Context

Constellation repositories carry a native file header, `L9_META`, in hash-comment, HTML-comment, docstring and frontmatter forms. Each header declares a schema version (`l9_schema`) and fields grouped as identity, classification, governance and retrieval. At the pinned acceptance revisions (`L9-Ops-MCP@fecdd92`, `cognitive.engine.graphs@7ba7bf3`, `enrichment.inference.engine@12d8b35`), the producer `l9-meta-injector` reads 713 headers. Of those, 516 declare `owner`, 711 declare `status`, 521 declare `layer`, and 706 declare `tags`.

The Foundation defines none of these fields: there is no match for `L9_META`, `l9_schema` or any field name as an artifact-declared field. The consumer, `l9-constellation-topology`, therefore holds every header claim as an unsupported predicate. That raises 6,431 unknowns and holds publication. The producer cannot map the fields to Foundation meaning, because `authority_model.escalation_rules.authority_missing` is `block` and nothing governs them.

Without a global definition, every consumer re-decides what `owner`, `ssot_for`, `canonical`, `references` and `status` mean. That is the decision ADR-010 says belongs in a ledger. The observed values also show what such a definition may not claim:
- `owner` takes five team labels (`engine-team`, `platform`, `platform-team`, `domain-team`, `Quantum-L9`), and none is an `actor_registry.yaml` identity.
- `engine` declares both `enrich` and `enrichment`.
- `status` declares `candidate`, which collides with `lifecycle.yaml` `state_semantics.candidate`.

## Options considered

### Option A — Leave header fields undefined

- Pros: no new ledger.
- Cons: every consumer keeps re-deciding the meanings, or holds the claims as unknowns indefinitely. The question is never answered; it is only deferred.

### Option B — Define header fields as authority-bearing facts

Under this option, `owner` resolves to an ActorIdentity, `ssot_for` and `canonical` establish canonical sources, and `references` and `requires` are dependencies.

- Pros: consumers could project ownership and dependency edges directly.
- Cons: a file would grant itself authority, which L9-AUTH-001 and `l9.contract/authority-boundary@1` forbid. It would create competing canonical sources (L9-OWNER-001, `l9.contract/semantic-ownership@1`) and would bypass `canonical_sources_must_be_registered`. There is also no observed basis for it: no header `owner` names an identity.

### Option C — Define header fields as source declarations with explicit non-establishment

- Pros: gives every field a governed meaning while keeping each a claim about the declaring file. It retires the per-consumer decision and conflicts with no invariant.
- Cons: consumers gain meaning but no new canonical edges. Any future projection into a relation needs its own admitted decision.

## Decisions

1. **Ledger.** We add `semantics/artifact_header_model.yaml` (`l9.artifact-header-model/global@1`), registered as `l9.source/artifact-header-model@1` and listed under `semantic_catalogs`. It defines semantics only. It does not define carrier syntax, parsing, predicate names, projection or reconciliation policy, identity or ownership resolution, or relation types, and its `does_not_own` list names each of these.
2. **Declaration semantics.** Every header field is a source declaration, held with evidence class `declared` and authority `source`. A parse, repetition, or agreement between headers does not make it true. Conflicts between declarations, and between a declaration and observed evidence, are preserved, not resolved.
3. **Declared schemas.** Field meanings apply only under a recognized `l9_schema` (`1` or `2`, both using the native vocabulary). Under an absent or unrecognized schema a key may be preserved but carries no meaning, and a field outside the vocabulary carries no meaning either.
4. **Fields.** Thirty fields are defined (11 identity, 6 classification, 5 governance, 8 retrieval), each with a category, a value kind, a definition and an explicit `does_not_establish`.
   - `status` is the one field with declared values: `active`, `deprecated`, `candidate`, `stub`. These are the four values observed across 711 headers. A declared `candidate` is not a lifecycle candidate, and any other value is preserved as declared.
   - Every other value set stays open and owned by the declaring domain.
5. **Non-establishment.**
   - `owner` resolves to no ActorIdentity or SurfaceIdentity and is no OWNED_BY relation.
   - `ssot_for` and `canonical` establish no canonical source.
   - `references`, `requires` and `amplifies` establish no dependency and no DEPENDS_ON relation.
   - `id`, `engine` and `component` establish no identity dimension.
   - `status` establishes no lifecycle, admission or capability state.
6. **Projection boundary.** No header field projects a canonical relation, identity binding, capability or ownership fact (`projection_boundary.canonical_relations: none`). A future projection of a header field into a canonical relation requires a separate admitted decision that names that relation's owner.
7. **Vocabulary.** `artifact_header` and `header_declaration` become global terms whose `detailed_model` is the new ledger.

## Review findings (recorded, not resolved)

- No release check pins the field list the way RC-028 to RC-032 pin their subjects. Whether admission requires an RC check is the owner's decision.
- The explicit decision record that `authority_model.admission_rules` requires still has no defined form in a ledger (the v3.24.0 finding).
- The field set was taken from the `l9-meta-injector` `native-metadata/v1` 1.1.0 vocabulary and the observed headers at the pinned revisions. Fields seen only outside a recognized schema (`author`, `domain`, `use_case`, `trigger`, and the unsupported `changes_from_v3.3.0`, `last_tested`, `eval_status`, `overload_weight`) are deliberately left undefined.

## Consequences

- A consumer can cite `l9.artifact-header-model/global@1` as the governing meaning of every header predicate, and record header claims as declared source claims instead of unknown, unsupported predicates. How the consumer classifies them in its reconciliation policy remains the consumer's decision under its own ADRs.
- No consumer may derive ownership, dependency, identity, canonical status or topology from a header. Requests to do so stay blocked until a separate admitted decision exists.
- Producers keep owning carrier syntax and parsing, so this ledger does not change the `l9-meta-injector` parser.
