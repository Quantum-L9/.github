# Release Validation v3.8.0

Candidate status: **additive successor candidate**.

This release preserves the v3.7.0 semantic-foundation inventory and adds only the Strategic Cognition semantics: one canonical ledger, one constitutional invariant, the Plan Keeper / Strategic Plan Metacognitive Reasoner authority separation, and the Current Meta View expressed through existing projection and composition law.

## Semantic changes

New canonical ledger:

- `semantics/strategic_cognition_model.yaml`: Strategic Cognition, Strategic Plan, Current Meta View, Plan Keeper, Strategic Plan Metacognitive Reasoner, and their authority separation.

Modified canonical ledgers:

- `semantics/invariants.yaml`: one constitutional invariant, `L9-STRATEGY-001`.
- `semantics/vocabulary.yaml`: five terms — `strategic_cognition`, `strategic_plan`, `plan_keeper`, `strategic_plan_metacognitive_reasoner`, `current_meta_view` — each deferring to the new model.
- `semantics/authority_model.yaml`: `strategic_cognition_authority`, resolving Strategic Plan ownership, Strategic Plan reasoning-analysis ownership, and the metacognition denials.
- `semantics/canonical_sources.yaml`: registration `l9.source/strategic-cognition-model@1`.
- `semantics/generic_compiler_manifest.yaml`: the ledger listed once under `requires.semantic_catalogs`, and `strategic_cognition` listed under `does_not_own`.

## Mechanical derivation refreshes

These four ledgers changed only because existing repository law pins the exact bytes of their upstream sources. Their semantic payload is unchanged; only derivation coordinates changed, and only because `invariants.yaml` gained one invariant. They do not carry Strategic Cognition semantics.

| Ledger | Changed coordinates |
|---|---|
| `semantics/contracts.yaml` | `derivation.source_digest_sha256` (invariants), `derivation.source_invariant_count` 30 → 31 |
| `semantics/capabilities.yaml` | `derivation.source_artifacts[0].sha256` and `item_count` 30 → 31 (invariants); `[1].sha256` (contracts) |
| `semantics/lifecycle.yaml` | `derivation.source_artifacts[0..2].sha256` (invariants, contracts, capabilities) |
| `semantics/receipt_catalog.yaml` | `derivation.source_artifacts[0..2].sha256` (invariants, contracts, capabilities) |

Refresh order follows the declared derivations: invariants, then contracts, then capabilities, then lifecycle and receipt catalog. Each digest was computed from the final bytes of its upstream file. SC-004, RC-001, RC-002, and RC-011 prove the refreshed coordinates against those bytes.

Explicitly unchanged: `semantics/artifact_model.yaml`, `semantics/semantic_dependency_model.yaml`, `semantics/projection_profiles.yaml`, `semantics/composition_profiles.yaml`, `semantics/actor_registry.yaml`, `semantics/surface_registry.yaml`, `semantics/architecture_patterns.yaml`, `semantics/architecture_rules.yaml`, every schema, every capability, contract, artifact class, and projection profile, and all prior release records.

## Validator delta

- `scripts/validate-semantics.py`: RC-016 Strategic Cognition closure plus seven isolated negative cases, each required to fail at its intended field.

## RC-016 Strategic Cognition closure

RC-016 proves:

- the Strategic Cognition ledger is declared exactly once, is canonical, is owned by `Quantum-L9/.github` within `l9_global_strategic_cognition_semantics`, and declares no section outside the admitted semantics;
- the ledger is registered exactly once in `canonical_sources.yaml` and classified exactly once, as a semantic catalog, by the generic compiler manifest;
- `L9-STRATEGY-001` exists exactly once with the admitted statement, and it is the only Strategic Cognition invariant;
- the Plan Keeper owns the Strategic Plan and nothing else, owns no underlying truth source, and draws authority only from explicitly granted strategic authority;
- the Strategic Plan Metacognitive Reasoner owns only Strategic Plan reasoning analysis, is not universal metacognitive authority, is denied Strategic Plan mutation, supersession, and strategic authority, and emits advisory output to the Plan Keeper;
- both roles are semantic roles, not ActorIdentities, and neither is registered as an actor;
- the Current Meta View is derived and non-authoritative, may not reinterpret source truth or create authority, and reuses the existing `composed_projection` and `projection_artifact` classes and the composed-projection schema; no artifact class is added;
- the Semantic Compiler does not own Strategic Cognition and gains no strategic capability;
- the Reasoning Plane separation in `vocabulary.yaml` `stage_rules.reasoning_plane_rule` is intact;
- the five vocabulary terms exist and defer to the model.

The negative-case batch proves fail-closed behavior, each at its intended field, for: the Reasoner gaining Strategic Plan mutation; the Reasoner becoming strategic authority; the Current Meta View promoted to canonical authority; the Current Meta View reinterpreting source truth; the Plan Keeper owning truth sources by consuming projections; Strategic Cognition owned by the Semantic Compiler; and removal of the Plan Keeper / metacognition separation.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-015. v3.8.0 adds RC-016 without weakening or replacing predecessor checks.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.8.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion.
