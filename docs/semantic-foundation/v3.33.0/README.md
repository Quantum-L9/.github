# Semantic Foundation v3.33.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.33.0 carries ADR-030: Game Theory Core: Conditional Strategic Interaction.

## Bounded delta

Successor to v3.32.0. The release number and ADR identity were selected from the merged state at f03f85981a7bd8249bc5998ee04535f53608fd73.

- `semantics/invariants.yaml`: `L9-GT-001`.
- `semantics/contracts.yaml`: `l9.contract/strategic-interaction-assessment@1`; derivation digest and count rebound.
- `semantics/vocabulary.yaml`: 12 terms (`strategic_interaction`, `strategic_game_model`, `actor_response_model`, `strategy_profile`, `conditional_best_response`, `equilibrium_assessment`, `deviation_gain`, `incentive_bearing_commitment`, `information_disclosure_decision`, `policy_exploitability`, `incentive_compatibility`, `strategic_interaction_assessment`).
- `semantics/projection_profiles.yaml`: `l9.projection/strategic-planner-interaction@1` and the forbidden criterion `sv_semantic_records_excluded_from_gt_projection`.
- `semantics/composition_profiles.yaml`: `l9.compose/strategic-planner-interaction@1`.
- `semantics/strategic_interaction_projection.schema.yaml`, `semantics/strategic_interaction_composition.schema.yaml`, registered in `generic_compiler_manifest.yaml#requires.artifact_schemas`.
- `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, `semantics/receipt_catalog.yaml`: derivation sha256 and item counts only.

## Evidence

Owner decisions: `docs/candidates/GT/evidence/admission/gt-owner-decision.yaml`. Producer: `Quantum-L9/l9-semantic-compiler-engine@39a51b76057f6d950877ffe1c2c87c4cb6d4a891`.

## Authority

`Quantum-L9/.github` owns these ledgers. Nothing here grants plan admission, strategic commitment, execution, publication, merge, admission or deployment authority. This candidate does not admit itself.
