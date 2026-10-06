# Release Validation v3.9.0

Candidate status: **additive successor candidate**.

This release preserves the v3.8.0 semantic-foundation inventory and changes only the validation-completeness semantics of one existing contract and the operative content of one existing projection profile. No invariant, contract, profile, capability, ledger, result taxonomy, or ADR is added.

## Semantic changes

Modified canonical ledgers:

- `semantics/contracts.yaml`, `l9.contract/validation-and-correctness@1` only:
  - `purpose`: extended to name complete, evidence-bound evaluation of every applicable required criterion as a condition of success.
  - `source_invariants`: `L9-ASSURANCE-001` added; `L9-VALIDATION-001`, `L9-CORRECTNESS-001`, `L9-EVIDENCE-001`, `L9-UNKNOWN-001` preserved.
  - `guarantees` added, all existing guarantees preserved:
    - `validation_success_requires_every_applicable_required_criterion_to_be_evaluated_and_satisfied`
    - `unavailable_unreadable_unexecuted_or_unresolved_required_criteria_preclude_success`
    - `validation_coverage_is_explicit_and_evidence_bound`
  - `forbidden` added, all existing prohibitions preserved:
    - `silent_skip_of_applicable_required_validation`
    - `default_success_on_missing_unreadable_unexecuted_or_unresolved_required_validation`
    - `partial_validation_coverage_reported_as_complete`
  - `outcomes`: keys `satisfied`, `rejected`, `unresolved` preserved and distinct. `satisfied` is `every_applicable_required_criterion_was_evaluated_and_evidence_supports_the_candidate_against_each`; `unresolved` is `validation_cannot_resolve_the_candidate_against_every_applicable_required_criterion`; `rejected` is unchanged. Incomplete applicable coverage therefore cannot resolve to `satisfied`.
- `semantics/projection_profiles.yaml`, `l9.projection/cursor-governance-operating-plane@1` only:
  - `sources.contracts.selectors` now carry `$.contracts[*].id`, `$.contracts[*].purpose`, `$.contracts[*].scope`, `$.contracts[*].source_invariants`, `$.contracts[*].requires`, `$.contracts[*].guarantees`, `$.contracts[*].forbidden`, `$.contracts[*].outcomes`. The prior projection carried only `id`, `purpose`, `scope`, and `outcomes`.
  - `sources.invariants.selectors` added with the existing canonical selector `$.invariants[?(@.scope=="global")]`, so the `source_invariants` the projected contracts cite resolve inside the operating plane rather than being stranded.

Explicitly unchanged: `semantics/invariants.yaml` (31 invariants), `semantics/strategic_cognition_model.yaml`, `semantics/authority_model.yaml`, `semantics/vocabulary.yaml`, `semantics/canonical_sources.yaml`, `semantics/generic_compiler_manifest.yaml`, every other contract in `contracts.yaml`, every other projection profile, every schema, every capability, artifact class, and ADR, and all prior release records. The contract count remains 26 and the profile count remains 23.

## Mechanical derivation refreshes

These three ledgers changed only because existing repository law pins the exact bytes of their upstream sources. Their semantic payload is unchanged.

| Ledger | Changed coordinates |
|---|---|
| `semantics/capabilities.yaml` | `derivation.source_artifacts[1].sha256` (contracts) |
| `semantics/lifecycle.yaml` | `derivation.source_artifacts[1].sha256` (contracts), `[2].sha256` (capabilities) |
| `semantics/receipt_catalog.yaml` | `derivation.source_artifacts[1].sha256` (contracts), `[2].sha256` (capabilities) |

`invariants.yaml` did not change, so `contracts.yaml` `derivation.source_digest_sha256` and `source_invariant_count` (31), and every invariants coordinate downstream, are unchanged. The `item_count` of contracts (26) is unchanged. Refresh order follows the declared derivations: contracts, then capabilities, then lifecycle and receipt catalog. SC-004, RC-001, RC-002, and RC-011 prove the refreshed coordinates against the final bytes.

## Validator delta

- `scripts/validate-semantics.py`: RC-017 validation-completeness closure plus an isolated negative-case batch, each case required to fail at its intended file and field. No other check changed.

## RC-017 validation-completeness closure

RC-017 proves:

- `l9.contract/validation-and-correctness@1` exists exactly once, is global, and is owned by `Quantum-L9/.github`;
- the contract declares only the uniform contract fields (`id`, `purpose`, `scope`, `owner`, `source_invariants`, `applies_to`, `requires`, `guarantees`, `forbidden`, `outcomes`), so no result taxonomy or sub-contract is carried inside it;
- it is the only contract in the validation family, and the catalog's `outcome_semantics` remains `contract_local` with `global_error_taxonomy_defined_here: false`;
- its `source_invariants` include `L9-VALIDATION-001`, `L9-CORRECTNESS-001`, `L9-EVIDENCE-001`, `L9-UNKNOWN-001`, and `L9-ASSURANCE-001`, each declared once, and each resolves to exactly one global invariant owned by the global authority in `invariants.yaml`;
- its guarantees include the three completeness guarantees and the existing `unresolved_validation_semantics_remain_unresolved`;
- its prohibitions include the three completeness prohibitions and the existing `unknown_to_success_coercion`;
- its `requires` list is declared and non-empty;
- its outcome keys are exactly `satisfied`, `rejected`, `unresolved`, with three distinct values, neither `rejected` nor `unresolved` equal to the success outcome, and the mapping pinned exactly so that `satisfied` requires complete evaluation of every applicable required criterion and incomplete coverage routes to `unresolved`;
- `l9.projection/cursor-governance-operating-plane@1` exists exactly once, is the only profile serving `Cursor-Governance`, and is a `consumer` profile;
- its `contracts` and `invariants` sources resolve to `source_classes`, its contract selectors include all eight operative fields, and its invariants selectors include `$.invariants[?(@.scope=="global")]`.

The negative-case batch proves fail-closed behavior, each at its intended file and field, for: removal of each of the three completeness guarantees; removal of the existing unresolved-remains-unresolved guarantee; removal of each of the three completeness prohibitions; removal of the existing unknown-to-success prohibition; removal of `L9-ASSURANCE-001` from `source_invariants`; `unresolved` altered to resolve as `satisfied`; `satisfied` relaxed to no longer require every applicable required criterion; a new outcome key added; a parallel result-taxonomy field added to the contract; a parallel validation contract introduced; the contract catalog defining a result taxonomy; the contract owned by the consumer; removal of each of `source_invariants`, `requires`, `guarantees`, and `forbidden` from the projection's contract selectors; removal of the governing invariants projection; invariants projected as identifiers without their statements; and a parallel Cursor-Governance profile introduced.

## Existing closure

The existing semantic-foundation validator continues to own SC-001 through SC-010 and RC-001 through RC-016. v3.9.0 adds RC-017 without weakening or replacing predecessor checks. Strategic Cognition semantics and RC-016 are unchanged.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.9.0 is a candidate and does not admit itself. Validation evidence does not grant authority or promotion.
