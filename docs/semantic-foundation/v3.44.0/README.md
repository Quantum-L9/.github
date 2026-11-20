# Semantic Foundation v3.44.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.44.0 corrects canonical SurfaceIdentity drift for the `claude-code` actor. By owner decision (operator, 2026-11-20, in a governed Claude Code session) Claude Code has exactly two surfaces: `claude-code-cli`, the local command line including the command line run inside an IDE, and `claude-code-web`, the hosted cloud session whichever client starts it. `claude-code-desktop` and `claude-code-ide` were registered in error and are retired. Mobile is not a separate surface: `claude-code-mobile` is superseded by `claude-code-web`. History is kept; no identity is removed or rewritten. No ADR is added and this candidate does not admit itself.

Successor to the v3.43.0 candidate.

## Bounded delta

- `semantics/surface_registry.yaml`: `claude-code-desktop` and `claude-code-ide` → `retired`; `claude-code-mobile` → `superseded` with `successor_refs: [l9.surface-registry/global@1#claude-code-web]`; alias `claude-mobile` → `claude-code-web`; `historical_surface_alias` wording covers aliases of superseded and retired surfaces; `claude-code-cli` and `claude-code-web` descriptions state their bounds.
- `semantics/actor_registry.yaml`: the `claude-code` actor description names its two surfaces. Historical actor aliases are unchanged.
- `semantics/domain_consumer_bindings.yaml`: `l9.domain-consumer-binding/claude-code@2` (`successor_of` the admitted, unedited `claude-code@1`) binds only `claude-code-cli` and `claude-code-web`; two global rules state binding succession and current-surface use.
- `scripts/validate-semantics.py`:
  - RC-014: a superseded identity must name current successor(s) of its own registry as `<artifact_id>#<id>`, no other entry may name a successor, and no alias may canonicalize to a superseded identity.
  - RC-034: the pinned binding census gains `claude-code@2`; an `@N>1` binding must name its `@N-1` of the same consumer kind and identity, and `@1` names none; a host binding without a successor must name only `current` surfaces; the two new global rules must be `true`. RC-034-NEG grows from 28 to 33 cases.

## Evidence

See `RELEASE_VALIDATION.md`. `make validate check test` passes on this tree, and the admission gate reports `RELEASED_CANDIDATE` for the subject below.

## Admission subject

Discovered with `.claude/skills/l9-projection-admission/scripts/discover_admission_subject.py --admitted-base v3.39.0`. v3.39.0 is admitted on main (ADR-036); the current verifier rejects its decision record (ADR-036 names candidate `3f9b90a6a980`, which does not carry the approved `semantics/` tree), so the default base would fall back to v3.38.0 and pull v3.39.0's own admitted identities into this subject. That verification gap is reported, not waived.

Because v3.40.0 to v3.43.0 are open candidates, the subject is everything changed since v3.39.0, not only this release's delta:

- canonical sources: `l9.source/actor-registry@1`, `l9.source/surface-registry@1`, `l9.source/domain-consumer-bindings@1` (this release), and `l9.source/binding-catalog@1`, `l9.source/compilation-profiles@1`, `l9.source/ir-catalog@1`, `l9.source/product-manifest-schema@1`, `l9.source/product-topology-schema@1`, `l9.source/repository-registry@1`, `l9.source/technology-capabilities@1`, `l9.source/vocabulary@1` (open candidates v3.40.0 to v3.43.0);
- schemas: `conformance_ir.schema.yaml`, `fixture_ir.schema.yaml`, `harness_surface.schema.yaml` (open candidate v3.40.0);
- revisions: none. No registry entry of a canonical source, and no invariant, term, contract, source class or schema of this release, is redefined.

Admitting v3.44.0 admits its whole approved `semantics/` tree, so it also admits the open candidates' content. The owner may instead admit v3.40.0 to v3.43.0 first.

## Downstream

Consumers re-project. Profiles selecting `surface_registry.yaml` (`l9.projection/identity-attribution@1`, `l9.projection/identity-assurance@1`, `l9.projection/identity-assurance@2`, `l9.projection/cursor-governance-identity@1`) and `actor_registry.yaml` (`identity-assurance@1/@2`, `cursor-governance-identity@1`, `identity-attribution@1`) produce new bytes. `Quantum-L9/Cursor-Governance` (`generated/governance/canonical_identity.yaml`, the `domain_identity_attribution` bundle) refreshes its projections and moves its Claude Code host binding to `claude-code@2`; this foundation does not mutate that repository. A downstream resolver keeps reading a retired or superseded surface value for historical resolution but must not emit one for new authorship.

## Outstanding Unknowns

- `semantics/identity_assurance_projection.schema.yaml` and `semantics/identity_assurance_composition.schema.yaml` (`l9.schema-definition/v1`, governing the superseded `l9.projection/identity-assurance@1` and `l9.compose/identity-assurance@1`) pin every surface to `status: const current`. They are admitted and are not edited here. A payload of `identity-assurance@1` compiled at this revision therefore fails those schemas for the three retired or superseded surfaces. The admitted successor pair `identity-assurance@2` (ADR-032, `successor_of` @1) declares `status` as a string with open entries and accepts the new registry. Whether @1 stays a historical, non-producible version or receives a declared schema revision is an owner decision.
- The real compiler was not run for this candidate: no compiler checkout is reachable from this session, and no profile is in the subject (downstream is `not_applicable`).

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants mutation, publication, merge, admission, deployment or execution authority. Admission of v3.44.0 requires the repository owner's explicit decision for this exact subject.
