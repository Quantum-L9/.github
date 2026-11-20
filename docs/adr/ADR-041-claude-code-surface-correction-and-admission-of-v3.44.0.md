# ADR-041 — Claude Code Surface Correction and Admission of v3.44.0

**Status:** Accepted for semantic-foundation v3.44.0. The repository owner admitted v3.44.0 on 2026-11-20 in the governed Claude Code session (`session_017xwbxw5DHxx5UrgJwAxGPS`) that produced Quantum-L9/.github#275: first "Admit v3.44.0", then, binding the exact subject, "Admit v3.44.0, subject digest sha256:f5e953d0…, semantics tree c971aac", which names the subject digest and approved `semantics/` tree recorded in full below. This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when Quantum-L9/.github#275 merges into `main`.

Before that decision the owner was told, in plain terms, that admitting v3.44.0 also admits the open releases v3.40.0, v3.41.0, v3.42.0, v3.42.1 and v3.43.0, because an admission covers the whole approved `semantics/` tree. The decision was given with that scope. The earlier decision in the same session, also on 2026-11-20, fixed the semantic change itself: the `claude-code` actor has exactly two surfaces, `claude-code-web` (the hosted cloud session) and `claude-code-cli` (the local command line, including the command line run inside an IDE); `claude-code-desktop` and `claude-code-ide` never existed as surfaces; a cloud session started from a phone is Claude Code Web.

## Subject

| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.44.0**, additive successor to v3.43.0. The admitted tree also carries the content of v3.40.0, v3.41.0, v3.42.0, v3.42.1 and v3.43.0, measured from the last admitted release v3.39.0. |
| Pull request | Quantum-L9/.github#275, branch `claude-mobile/peaceful-knuth-vx6c9d`, based on `main` at `c788b991f2ed5f670a2d5660a7faa4e1d52f64e3`. |
| Approved semantic tree | `semantics/` tree `c971aaca00a5efa3ff4d5860d73329f1b8530d86`. It is identical at the qualified candidate commits `8fb255603be8a66b94a776ad7f50fd61a27b3ff2` (#275 head when the decision was given) and `867d376804af80657a29cc7c691bdff742640d12` (the release cut). No later commit changes `semantics/`: they add this ADR, its index entry and the v3.44.0 status lines. |
| Subject digest | `sha256:f5e953d03df1da40b1a6d4bf0bc7067926ee43f957a2b68837630cb87a109143`, the canonical-JSON digest of the subject records below at that tree (`check_admission_closure.py` `digest(registration(...).records)`). |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them, and its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges #275. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |

Admitted definitions:

- Canonical source content changed by this release (the Claude Code surface correction):
  - `l9.source/surface-registry@1` (`semantics/surface_registry.yaml`): `claude-code-desktop` and `claude-code-ide` retired with no successor; `claude-code-mobile` superseded with `successor_refs: [l9.surface-registry/global@1#claude-code-web]`; alias `claude-mobile` canonicalizes to `claude-code-web`; aliases `claude-desktop` and `claude-ide` keep their retired coordinates; the `historical_surface_alias` definition covers aliases of superseded and retired surfaces; the `claude-code-cli` and `claude-code-web` descriptions state their bounds. All eleven surface ids stay registered.
  - `l9.source/actor-registry@1` (`semantics/actor_registry.yaml`): the `claude-code` actor description names its two surfaces. The historical actor aliases `claude-code-desktop` and `claude-code-mobile` are kept.
  - `l9.source/domain-consumer-bindings@1` (`semantics/domain_consumer_bindings.yaml`): binding `l9.domain-consumer-binding/claude-code@2`, `successor_of` the unedited `l9.domain-consumer-binding/claude-code@1`, naming only `claude-code-cli` and `claude-code-web`; global rules `a_successor_binding_names_its_predecessor_version_of_the_same_consumer` and `a_host_binding_without_a_successor_names_only_current_surfaces`, both `true`.
- Canonical source content carried from the open releases v3.40.0 to v3.43.0, admitted as it stands in the approved tree:
  - `l9.source/binding-catalog@1` (`semantics/binding_catalog.yaml`)
  - `l9.source/compilation-profiles@1` (`semantics/compilation_profiles.yaml`)
  - `l9.source/ir-catalog@1` (`semantics/ir_catalog.yaml`)
  - `l9.source/product-manifest-schema@1` (`semantics/product_manifest.schema.yaml`)
  - `l9.source/product-topology-schema@1` (`semantics/product_topology.schema.yaml`)
  - `l9.source/repository-registry@1` (`semantics/repository_registry.yaml`)
  - `l9.source/technology-capabilities@1` (`semantics/technology_capabilities.yaml`)
  - `l9.source/vocabulary@1` (`semantics/vocabulary.yaml`)
- IR schemas carried from v3.40.0, registered under `semantics/generic_compiler_manifest.yaml#requires.artifact_schemas`:
  - `fixture_ir.schema.yaml` (`l9.schema/fixture-ir@1`, `l9.fixture-ir/v1`)
  - `conformance_ir.schema.yaml` (`l9.schema/conformance-ir@1`, `l9.conformance-ir/v1`)
  - `harness_surface.schema.yaml` (`l9.schema/harness-surface@1`, `l9.harness-surface/v1`)

No invariant, contract, vocabulary term identity, source class, projection profile or composition profile is redefined, and the subject declares no revision. The `scripts/validate-semantics.py` changes (RC-014 lifecycle succession, RC-034 binding succession and current-surface use, and those of v3.40.0 to v3.43.0) are validation tooling, not admitted meaning.

## Context

`surface_registry.yaml` listed five Claude Code surfaces. Two were registered in error and one duplicated another, so every consumer validating a Claude Code surface against the registry accepted coordinates that name nothing real, and the `claude-code` host binding inherited them. The registry is the one upstream authority for SurfaceIdentity (ADR-013), so the correction belongs here, with history kept: a coordinate once registered stays addressable.

## Decision

1. Admit v3.44.0 as recorded in `docs/semantic-foundation/v3.44.0/`, together with the approved tree's content from v3.40.0 to v3.43.0 listed above.
2. `claude-code-desktop` and `claude-code-ide` are `retired`: ended for future use, kept for historical resolution, with no successor. `claude-code-mobile` is `superseded` by `claude-code-web` (`lifecycle.yaml#lifecycle_relations.successor_of`).
3. A historical surface alias follows a superseded surface to its successor and keeps a retired surface's coordinate. No alias canonicalizes to a superseded surface.
4. An admitted domain consumer binding is not edited: `claude-code@2` succeeds `claude-code@1`, and the binding without a successor is the current one. A current host binding names only current surfaces.
5. The release records of v3.40.0 to v3.43.0 and ADR-037 to ADR-040 stay unedited. Their content is admitted through this record and the approved tree.

## Accepted limitations

- `semantics/identity_assurance_projection.schema.yaml` and `semantics/identity_assurance_composition.schema.yaml` govern the superseded `l9.projection/identity-assurance@1` and `l9.compose/identity-assurance@1` and pin every surface to `status: const current`. They are not edited. As ADR-025 accepted for such pinned-snapshot constraints, a later source change may fail them: an `identity-assurance@1` payload compiled at this tree fails them for the three retired or superseded surfaces. The admitted successor pair `identity-assurance@2` (ADR-032) accepts the registry. Making @1 producible again would need a declared schema revision.
- ADR-036's decision record names a commit that does not carry its approved tree, so the current verifier rejects v3.39.0's evidence. The subject is measured from v3.39.0 (`--admitted-base v3.39.0`) and that gap is reported, not waived.

## Consequences

- Consumers re-project. Profiles selecting the two registries (`l9.projection/identity-attribution@1`, `l9.projection/identity-assurance@1`, `l9.projection/identity-assurance@2`, `l9.projection/cursor-governance-identity@1`) produce new bytes. `Quantum-L9/Cursor-Governance` refreshes its identity bundles and moves its Claude Code host binding to `claude-code@2`; this record does not mutate that repository.
- A downstream resolver may still read a retired or superseded surface value for historical resolution but must not emit one for new authorship.
- Adding a further binding version is a pinned-census edit to RC-034.

## Evidence relied on

- Subject discovery at #275 head `8fb2556` with `--admitted-base v3.39.0`: exactly the eleven canonical sources and three schemas above; no revision; every dependency admitted or in the subject; no unclassified change; no derived coordinate changed.
- `check_admission_closure.py --admitted-base v3.39.0 --require released` at the release cut `867d376`: verdict `RELEASED_CANDIDATE`, registration with no gaps and no unresolvable declarations, validator, `make validate`, `make check`, `make test`, release inventory (117 semantic files, 161 hashed files), release sequence and scope closure all passing.
- `scripts/validate-semantics.py`: RC-014 closes both registries under the new succession rules, RC-034 resolves 7 bindings, and RC-034-NEG fails 33 mutations closed at their intended fields.
- Quantum-L9/.github#275 CI green at `2887873`.

## What admission does not establish

- Downstream usability at `main`: no projection or composition profile is in the subject, and no producer run is recorded here.
- Any consumer's migration to `claude-code@2` or to the corrected registry.
- Any credential, role, grant, merge, publication, deployment or execution authority.

## Relationship to CANONICAL_LAW.md

These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
