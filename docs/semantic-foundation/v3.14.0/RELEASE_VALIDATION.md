# Release Validation v3.14.0

Candidate status: **additive successor candidate**.

This release keeps the v3.13.0 semantic-foundation inventory. It corrects the base `requires` of one existing contract so that it equals the authority-model admission requirements it consumes, relocates the one conditional obligation that list wrongly carried into the same contract's `guarantees` verbatim, refreshes the derivation digests that change made stale, and adds one validator check. It adds no ledger, schema, invariant, contract, receipt family, vocabulary term, authority coordinate, ProductKind, or ADR.

v3.13.0 remains unchanged. v3.14.0 repairs a pre-existing canonical inconsistency discovered after v3.13.0; it does not create the product admission authority, which v3.13.0 declared.

## The contradiction

`semantics/authority_model.yaml#admission_rules.global_requirements` declares six universal admission prerequisites, and `product_admission_authority.inherits_global_requirements` inherits exactly that list by anchor. `semantics/contracts.yaml#l9.contract/admission-and-promotion@1.requires` operationalizes the same base set, but at v3.13.0 it read:

```
exact_subject_identity
exact_subject_revision_or_digest_when_revisioned
target_semantic_or_authority_class
target_class_authority
explicit_decision_record
explicit_compatibility_contract_when_reusing_a_prior_decision_after_material_change
independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence
```

Two defects:

- **Spelling drift.** The authority model names `explicit_compatibility_contract_when_reusing_prior_decision_after_material_change`. The contract carried `…reusing_a_prior_decision…`, which resolves to no authority-model requirement.
- **Conditional evidence promoted to an unconditional prerequisite.** `independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence` is not in `admission_rules.global_requirements`. Listed under the unconditional `requires`, it would make cross-domain witnesses mandatory for every admission, including one that asserts no recurrence. `L9-GLOBALIZATION-001` makes recurrence evidence for a globalization candidate, never a base condition of admission. The witness obligation was conditional by its own semantics but was stored in the unconditional base `requires` list. Removing it from that list is correct, but its independent-witness requirement must remain canonical: the existing guarantee `cross_domain_recurrence_claims_are_evidence_bound_when_used_to_support_higher_scope_admission` binds recurrence claims to evidence and does not by itself require that evidence to come from independent domain witnesses. v3.14.0 therefore relocates the exact existing token to `guarantees`.

## Semantic changes

Modified canonical ledger:

- `semantics/contracts.yaml`, `l9.contract/admission-and-promotion@1` only:
  - `requires` is now exactly, in order:
    ```
    exact_subject_identity
    exact_subject_revision_or_digest_when_revisioned
    target_semantic_or_authority_class
    target_class_authority
    explicit_decision_record
    explicit_compatibility_contract_when_reusing_prior_decision_after_material_change
    ```
  - `guarantees` gains exactly one entry by relocation from `requires`: `independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence`, placed after `cross_domain_recurrence_claims_are_evidence_bound_when_used_to_support_higher_scope_admission`. No pre-existing guarantee is removed or rewritten.
  - `id`, `purpose`, `scope`, `owner`, `source_invariants` (`L9-PROMOTION-001`, `L9-ADMISSION-001`, `L9-GLOBALIZATION-001`, `L9-DERIVED-001`), `applies_to`, `forbidden` and `outcomes` are byte-identical to v3.13.0. No field is added, the contract is not split, and no `@2` is created.

Preserved recurrence and globalization law, unchanged in meaning:

- guarantee `recurrence_or_validation_creates_no_implicit_promotion`
- guarantee `cross_domain_recurrence_claims_are_evidence_bound_when_used_to_support_higher_scope_admission`
- guarantee `independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence` (relocated verbatim from `requires`)
- prohibition `treating_recurrence_as_global_admission`
- prohibition `treating_hypothetical_reuse_repeated_assertion_or_single_domain_repetition_as_cross_domain_recurrence`
- invariant `L9-GLOBALIZATION-001`, cited by the contract and unchanged in `semantics/invariants.yaml`

The repair separates universal admission prerequisites (the authority model's six requirements, binding every admission) from the conditional evidence obligations that apply only when cross-domain recurrence is actually asserted (the evidence must be bound, and the domain witnesses must be independent). When no recurrence is asserted, independent domain witnesses are not a prerequisite. The law moved semantic slot; none was deleted, so globalization law is not weakened.

Explicitly unchanged:

- `semantics/authority_model.yaml`, in full. The authority model is the side the canonical product-admission declaration consumes and RC-021 pins; the stale consumer was the contract.
- `semantics/product_topology.schema.yaml`, `semantics/product_kinds.yaml`, `semantics/node_archetypes.yaml`, `semantics/lifecycle.yaml` (payload), `semantics/identity_model.yaml`, `semantics/vocabulary.yaml`, `semantics/invariants.yaml`, `semantics/receipt_catalog.yaml` (payload), `semantics/canonical_sources.yaml`, `semantics/projection_profiles.yaml`, `semantics/semantic_dependency_model.yaml`, `semantics/product_manifest.schema.yaml`.
- Every other contract in `contracts.yaml`. The contract count remains 26.
- All prior release records, including `docs/semantic-foundation/v3.13.0/`.

## Mechanical derivation refreshes

These three ledgers changed only because existing repository law pins the exact bytes of their upstream sources. Their semantic payload is unchanged.

| Ledger | Changed coordinates |
|---|---|
| `semantics/capabilities.yaml` | `derivation.source_artifacts[1].sha256` (contracts) |
| `semantics/lifecycle.yaml` | `derivation.source_artifacts[1].sha256` (contracts), `[2].sha256` (capabilities) |
| `semantics/receipt_catalog.yaml` | `derivation.source_artifacts[1].sha256` (contracts), `[2].sha256` (capabilities) |

`invariants.yaml` did not change, so `contracts.yaml` `derivation.source_digest_sha256` and `source_invariant_count` (31) are unchanged. The `item_count` of contracts (26) is unchanged. Refresh order follows the declared derivations: contracts, then capabilities, then lifecycle and receipt catalog. The refresh was required by evidence, not assumption: after the contract repair and before the refresh, the validator failed exactly at RC-001 `semantics/capabilities.yaml derivation.source_artifacts[1].sha256`, RC-002 `semantics/lifecycle.yaml derivation.source_artifacts[1].sha256`, and RC-011 `semantics/receipt_catalog.yaml derivation.source_artifacts[1].sha256`, each naming the new `contracts.yaml` digest. SC-004, RC-001, RC-002, and RC-011 prove the refreshed coordinates against the final bytes.

## Validator delta

- `scripts/validate-semantics.py` gains RC-022, the admission contract / authority-model requirement closure, plus an isolated negative-case batch. Each case must fail at its intended file and field, and a case that raises instead of failing is itself a failure.
- RC-021 and every earlier check are unchanged. RC-021 keeps ownership of the product-admission authority identity, the exact subjects, the inherited admission and escalation law, the ProductTopology projection, the receipt owner and the non-implication semantics. RC-022 does not re-pin the authority list: it reads it live and proves the contract consumes it exactly. No doctrine is duplicated between the two checks.

## RC-022 Admission contract / authority-model requirement closure

RC-022 governs the exact contract `l9.contract/admission-and-promotion@1` and proves the following:

- **Authority list is well-formed.** `authority_model.yaml#admission_rules.global_requirements` is a non-empty list of unique strings. A missing, non-list, non-string or duplicated entry is a located failure at that field.
- **Contract exists exactly once.** `contracts.yaml` holds exactly one contract with that id. A missing catalog, a missing contract, a duplicated contract, or a catalog that is not a list fails at `contracts[l9.contract/admission-and-promotion@1]`.
- **Base `requires` is well-formed.** A missing, empty, non-list or non-string `requires` fails at `.requires`.
- **Exact sequence equality.** Every authority-model requirement appears in the contract's `requires`; every contract requirement appears in the authority list; and the two sequences are identical, so a reordering or a duplicate also fails. Each missing or extra requirement is its own located failure. The stale `…reusing_a_prior_decision…` spelling and the cross-domain witness each fail with a reason naming why they are not base requirements.
- **Conditional recurrence law stays declared.** The three recurrence guarantees and the two recurrence prohibitions listed above remain in `guarantees` and `forbidden`, and `L9-GLOBALIZATION-001` remains in `source_invariants`. The witness token is pinned on both sides: present in `requires` it fails as an unconditional base requirement, absent from `guarantees` it fails as a missing recurrence guarantee. It can neither drift back into universal admission nor silently disappear.
- **No crash on malformed shapes.** Comparisons are by value only; a malformed shape produces a located failure, never an uncaught exception.

RC-022 applies no rule to any other contract and does not audit every contract against every authority-model section (`L9-VALIDATION-001`).

The negative-case batch has 27 cases. Each must fail at its intended file and field. The cases cover:

- **Contract resolution:** contracts ledger missing; contract missing; contract duplicated; contract catalog not a list.
- **Malformed `requires`:** a string; empty; holding a mapping; removed.
- **Malformed authority list:** `global_requirements` missing; `admission_rules` not a mapping; a non-string requirement; a duplicated requirement.
- **Drift:** a requirement missing; an extra requirement; a requirement renamed; the stale `reusing_a_prior_decision` spelling reintroduced; the cross-domain witness reintroduced as unconditional; the order changed; a requirement duplicated; an authority-model requirement renamed underneath the contract.
- **Globalization law:** each of the three recurrence guarantees removed (the relocated witness among them); `guarantees` not a list; each of the two recurrence prohibitions removed; `L9-GLOBALIZATION-001` no longer cited.

Test-first evidence. The final RC-022 logic was run against the unmodified tree of base `07b0df96fc3008d55a96f804923e2177ff312295` (v3.13.0 as merged, `contracts.yaml` sha256 `1f6fbe45…`, extracted with `git archive` and validated with `--root`). The validator failed at exactly four RC-022 lines and nothing else; all 35 prior PASS lines held:

```
FAIL RC-022 semantics/contracts.yaml contracts[l9.contract/admission-and-promotion@1].requires='explicit_compatibility_contract_when_reusing_prior_decision_after_material_change': authority-model global admission requirement is absent from the contract's base requires (the contract carries the stale spelling 'explicit_compatibility_contract_when_reusing_a_prior_decision_after_material_change')
FAIL RC-022 semantics/contracts.yaml contracts[l9.contract/admission-and-promotion@1].requires='explicit_compatibility_contract_when_reusing_a_prior_decision_after_material_change': stale spelling; the canonical requirement identifier is the one in semantics/authority_model.yaml#admission_rules.global_requirements
FAIL RC-022 semantics/contracts.yaml contracts[l9.contract/admission-and-promotion@1].requires='independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence': cross-domain witness evidence is a conditional obligation when recurrence is actually asserted (L9-GLOBALIZATION-001), not an unconditional base admission requirement
FAIL RC-022 semantics/contracts.yaml contracts[l9.contract/admission-and-promotion@1].guarantees='independent_domain_witnesses_when_cross_domain_recurrence_is_asserted_as_admission_evidence': recurrence guarantee must stay declared; it is where the conditional cross-domain evidence obligation lives
```

The four lines are: the canonical compatibility requirement missing, the stale compatibility spelling present, the conditional witness incorrectly present in universal `requires`, and the conditional witness absent from `guarantees`. An earlier form of RC-022, before the relocation was required, failed at the first three lines only. After the repair, RC-022 and RC-022-NEG pass.

## Existing closure

The existing semantic-foundation validator still owns SC-001 through SC-010 and RC-001 through RC-021. v3.14.0 adds RC-022 without weakening, reinterpreting or replacing any predecessor check. No failure was suppressed or downgraded; unresolved state does not become success.

## Explicit boundaries

- This release does not interpret any downstream `admission.subject` value as valid. A consumer whose ProductTopology names a subject the authority model does not declare aligns to `exact_product_topology` or `exact_product_release` in separate downstream work. The subject set is not widened here.
- This release modifies no downstream repository and no Semantic Compiler artifact.
- This release creates no runtime admission authority and changes no admission decision authority or receipt ownership.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record, under the same convention as v3.13.0. Prior release directories remain byte-identical; `docs/semantic-foundation/v3.13.0/` is unchanged under `L9-REVISION-001`.

## Admission state

v3.14.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion. Aligning the admission contract admits no product.
