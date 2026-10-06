# Release Validation v3.10.0

Candidate status: **additive successor candidate**.

This release preserves the v3.9.0 semantic-foundation inventory and adds one canonical ledger, one ADR, and one validator closure check. No invariant, contract, artifact class, schema, projection profile, or capability is added.

## Gate 0 necessity finding

A new canonical owner was admitted only after an audit of the existing owners found that none can own Strategic Plan content without contamination. `strategic_cognition_model.yaml` disclaims Strategic Plan content and structure; `requirement_model.yaml` requires hardness and satisfaction semantics that strategic beliefs and desired futures do not have; `semantic_dependency_model.yaml` would make reality change mark strategy stale automatically; and `vocabulary.yaml`, `authority_model.yaml`, `artifact_model.yaml`, `lifecycle.yaml`, `contracts.yaml`, and `product_topology.schema.yaml` each own a different question. ADR-015 records the finding.

## Semantic changes

Added canonical ledger:

- `semantics/strategic_plan_model.yaml` (`l9.strategic-plan-model/global@1`), registered as `l9.source/strategic-plan-model@1` with `projection_allowed: true` and `derivation_allowed: false`.

Modified canonical ledgers, additively:

- `semantics/canonical_sources.yaml`: one registration entry. No existing entry changed.
- `semantics/generic_compiler_manifest.yaml`: `strategic_plan_model.yaml` added once under `requires.semantic_catalogs`. `does_not_own` is unchanged; its existing `strategic_cognition` entry covers the Strategic Plan as a concept of Strategic Cognition.
- `semantics/vocabulary.yaml`: terms `strategic_goal`, `strategic_target`, `strategic_hypothesis`, `strategic_commitment`, and `affected_strategic_closure`, each with `detailed_model: strategic_plan_model.yaml`. No existing term changed; `objective` and `strategic_plan` are untouched.

Explicitly unchanged: `semantics/strategic_cognition_model.yaml` (including `content_defined_here: false` and `structure_defined_here: false`), `semantics/authority_model.yaml`, `semantics/invariants.yaml` (31 invariants), `semantics/contracts.yaml` (26 contracts), `semantics/lifecycle.yaml`, `semantics/requirement_model.yaml`, every schema, capability, artifact class, and projection profile, and all prior release records.

## Mechanical derivation refreshes

None. No ledger whose bytes are pinned by a derivation coordinate changed: `invariants.yaml`, `contracts.yaml`, and `capabilities.yaml` are byte-identical to v3.9.0, so every coordinate in `capabilities.yaml`, `lifecycle.yaml`, and `receipt_catalog.yaml` remains current.

## Validator delta

- `scripts/validate-semantics.py`: RC-018 Strategic Plan semantic closure plus an isolated negative-case batch, each case required to fail at its intended file and field. No other check changed.

## RC-018 Strategic Plan semantic closure

RC-018 proves:

- `l9.strategic-plan-model/global@1` is declared exactly once, is canonical, is owned by `Quantum-L9/.github` with scope `l9_global_strategic_plan_semantics`, and declares exactly its admitted sections;
- the ledger is registered exactly once with the expected projection and derivation flags and classified exactly once, as a semantic catalog;
- it cites `L9-STRATEGY-001` and only existing invariants and contracts;
- it anchors to `strategic_cognition_model.yaml#concepts.strategic_plan` and `authority_model.yaml#strategic_cognition_authority`, and those targets still make the Plan Keeper the Strategic Plan owner and keep Strategic Plan content and structure undefined in Strategic Cognition;
- its global rules are exactly the admitted seven, each true;
- it admits exactly four primitives, each with exactly a definition and a characteristic question;
- it reuses exactly `objective` and Strategic Intent by reference with `owned_here: false`, `objective` remains the existing optimization criterion, and Strategic Intent remains upstream;
- it admits exactly five relations, four with a meaning only and `supersedes` reusing `lifecycle.yaml#lifecycle_relations.supersedes`, which exists;
- its relation rules are exactly that relations transfer no ownership or authority and that material causal `enables` claims remain attributable to a Strategic Hypothesis;
- Affected Strategic Closure is the single reasoning concept, declares a definition, a purpose, and exactly the prohibitions on deciding strategy, modifying or invalidating the Strategic Plan, and automatically marking dependent strategy stale;
- no representation key (fields, properties, required, schema references, identifiers, confidence, probability, horizon, duration, date, or endpoint typing) appears at any depth;
- the five vocabulary terms exist and defer to the Strategic Plan model.

Every criterion is evaluated on every run. An absent section is reported as a failure, never skipped, so RC-018 cannot report partial coverage as complete (`l9.contract/validation-and-correctness@1`).

The negative-case batch proves fail-closed behavior, each at its intended file and field, for: a fifth primitive; a `strategic_objective` primitive; the Plan absorbing Capability; `objective` redefined as Plan-owned; a sixth relation; `supersedes` redefined locally; a relation endpoint type matrix; the causal `enables` attribution removed; relations transferring ownership; reality directly modifying the Strategic Plan; Affected Strategic Closure permitted to modify the Plan; a confidence field; the ledger owned by a store; the Plan re-anchored away from Strategic Cognition; the relations section absent; the Reasoner becoming the Strategic Plan owner; and Strategic Cognition absorbing Plan content.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-017. v3.10.0 adds RC-018 without weakening or replacing predecessor checks. Strategic Cognition semantics and RC-016 are unchanged.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.10.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion.
