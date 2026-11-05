# Semantic Foundation v3.27.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.27.0 gives the native `L9_META` artifact header a global meaning. Each header field is defined as a source declaration that the file makes about itself, together with an explicit statement of what the declaration does not establish. Producers and consumers can then cite one governing meaning for header claims instead of holding them as unsupported predicates, and nothing about a header can be read as authority, identity, ownership, canonical status, dependency or topology.

## Bounded delta

- `semantics/artifact_header_model.yaml` (`l9.artifact-header-model/global@1`), registered as `l9.source/artifact-header-model@1` and listed under `requires.semantic_catalogs`. It defines:
  - declaration semantics;
  - the recognized declared schemas (`l9_schema` `1` and `2`);
  - four field categories and seven value kinds;
  - 30 fields;
  - one declared value set, for `status`;
  - a projection boundary with no canonical relations;
  - a `does_not_own` list.
- `semantics/vocabulary.yaml` gains `artifact_header` and `header_declaration`.
- ADR-024.

## Evidence

The field set follows the `l9-meta-injector` `native-metadata/v1` 1.1.0 vocabulary. It was checked against the headers that producer reads at the pinned acceptance revisions:

- `L9-Ops-MCP@fecdd927f35b50ce3a32cc64f5b57371bffd04a0`
- `cognitive.engine.graphs@7ba7bf3707c8f5828798256981fcc81ba6d2e698`
- `enrichment.inference.engine@12d8b351b3c804094d3fe539ea578ea946da494b`

At those revisions:

- 713 headers were read.
- `status` takes exactly four values across 711 headers.
- `owner` takes five team labels across 516 headers, none of which is an `actor_registry.yaml` identity.
- `engine` declares both `enrich` and `enrichment`.

These observations motivate the non-establishment rules. They are evidence for this candidate, not law.

## Outstanding Unknowns and findings

- No release check pins the field list. Authoring one is an owner decision this candidate does not take.
- No check validates a vocabulary term's `detailed_model` reference, so a dangling one passes (RELEASE_VALIDATION, negative probe). The two references this release adds are correct by inspection.
- The explicit decision record that `authority_model.admission_rules` requires still has no defined form in a ledger (the v3.24.0 finding).
- Fields observed only outside a recognized schema, or outside the native vocabulary, are deliberately left undefined (ADR-024 review findings).

## Authority

`Quantum-L9/.github` owns the ledger. Producers keep carrier syntax and parsing. Consumers keep their predicate names and reconciliation policy. This candidate does not admit itself, and it grants no producer or consumer any mutation, publication, merge, admission, projection, or execution authority.
