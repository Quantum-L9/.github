# Semantic Foundation v3.26.0

Status: **SUCCESSOR CANDIDATE WITH ONE DECLARED MAJOR BREAK**

v3.26.0 repairs the Cursor-Governance operating-plane profile lineage in place: `l9.projection/cursor-governance-operating-plane@2` succeeds `@1`, keeps every `.github`-owned selection, adds the decision-complete selections the later consumer profiles carry, and declares the removal of the three `conformance_profiles` selectors that `.github` never owned. PROJECTION-014 is amended so that exactly this kind of break can be declared and nothing else can.

## Bounded delta

- `semantics/projection_profiles.yaml` gains `l9.projection/cursor-governance-operating-plane@2` (`class: consumer`, `consumer: Cursor-Governance`, `successor_of: l9.projection/cursor-governance-operating-plane@1`): 32 predecessor selectors kept and 23 added across the same eight source classes, 55 in total, `output.schema: l9.projection.cursor-governance-operating-plane/v2`, and `breaking_changes` naming exactly the three removed `conformance_profiles` selectors with a rationale and `consumer_migration: explicit`. `@1` is byte-for-byte unchanged.
- PROJECTION-014 reads `successor_profile_keeps_class_and_consumer_and_either_preserves_all_selections_or_declares_exact_major_version_removals_with_explicit_consumer_migration`; the catalog `global_rules` key `profile_successor_declares_successor_of_and_preserves_every_predecessor_selection` becomes `profile_successor_preserves_selections_or_declares_exact_major_break`. Every other rule, profile, criterion, and contract is unchanged.
- `semantics/cursor_governance_operating_plane_v2_projection.schema.yaml` (`l9.schema/cursor-governance-operating-plane-v2-projection@1`) defines `l9.projection.cursor-governance-operating-plane/v2` and is registered under `requires.artifact_schemas`.
- ADR-023.
- `l9-semantic-compiler-engine` realizes the amended criterion in `passes/projection.py` (`_succession_criterion`, `breaking_changes` as a mechanical profile field) with positive and negative tests; the compiler change is a predecessor of any producer run of this profile and lives in its own owner repository.

## Evidence

With the semantic bytes of this candidate and `l9-semantic-compiler` at `8bbd882f6a84c55449b9706c39a62e98eec1057b` carrying the amended PROJECTION-014 criterion (not yet merged there), `projection-coordinates` resolves the profile at digest `sha256:eeb6ccea032035aaf48436abf8e76b6adeeac2f4c281dba9fbf549ab4aa387c8` with eight source pins; `project` emits eight `l9.projection-artifact/v1` artifacts, each receipted `operation: projection`, `result: pass`, `unresolved_criteria: []`, `payload_schema` resolving to `l9.schema/cursor-governance-operating-plane-v2-projection@1`, and `successor_of` `pass` with `breaking_major: true` and the three removed selections listed. The same compiler without the amendment refuses the profile with `UNKNOWN_SEMANTIC_OPERATOR` on `breaking_changes`, which is the intended fail-closed behavior of an unamended producer. The projected `contracts` payload carries all 26 global contract records whole, `capabilities` carries the empty admitted catalog with its `catalog_status`, and `invariants` carries the 30 global invariants.

## Outstanding Unknowns and findings

- No release check pins this profile the way RC-028, RC-030 and RC-032 pin the other consumer profiles; authoring RC-033 is an owner decision this candidate does not take.
- The explicit decision record that `authority_model.admission_rules` requires for admitting a projection as law still has no defined form in a ledger (the v3.24.0 finding).
- Producer evidence above was produced against the candidate bytes at a local, unpublished revision; it is not a replay attestation and is not CI.

## Authority

`Quantum-L9/.github` owns the profile, the rule, and the schema. The compiler (`l9-semantic-compiler`) realizes them, consumers verify, and replay attests. This candidate does not admit itself and grants the consumer no mutation, publication, merge, admission, or execution authority.
