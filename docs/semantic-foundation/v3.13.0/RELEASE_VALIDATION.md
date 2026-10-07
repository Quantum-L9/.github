# Release Validation v3.13.0

Candidate status: **additive successor candidate**.

This release keeps the v3.12.0 semantic-foundation inventory. It adds one authority declaration, three projection selectors, and one dependency edge. It adds no ledger, schema, invariant, contract, receipt family, vocabulary term, authority class, or ADR.

## Semantic changes

Modified canonical ledgers:

- `semantics/authority_model.yaml` gains one block, `product_admission_authority`:
  - `id: l9.authority/product-admission`
  - `global_semantics_owner: Quantum-L9/.github`
  - `decision_authority: applicable_target_class_authority`
  - `operation: product_admission`
  - `subjects: [exact_product_topology, exact_product_release]`
  - `inherits_global_requirements: *id001`, which is the existing `admission_rules.global_requirements`
  - `inherits_rules: [admission_rules, escalation_rules]`
  - `candidate_generation_is_not_admission: true`
  - `self_admission_without_target_class_authority_forbidden: true`
  - `implies` set to `false` for each of: `publication`, `runtime_admission`, `runtime_availability`, `capability_invocation_authorization`, `implementation_conformance`, `consumer_compatibility`
  - five `rules`
- `semantics/projection_profiles.yaml`: the `authority_model` source of `l9.projection/stage-product-topology@1` gains `$.product_admission_authority`, `$.admission_rules`, and `$.escalation_rules`.
- `semantics/semantic_dependency_model.yaml`: `dependency_rules.product_topology.depends_on` gains `authority_model`, so a change to the declaration marks ProductTopology results stale.

Explicitly unchanged:

- Every other section of `semantics/authority_model.yaml`, including `admission_rules`, `global_admission_rules`, `escalation_rules`, `product_topology_authority`, `product_manifest_authority`, and `compiler_authority`.
- Every other projection profile, and every other dependency rule.
- These ledgers: `semantics/product_topology.schema.yaml`, `semantics/product_kinds.yaml`, `semantics/identity_model.yaml`, `semantics/lifecycle.yaml`, `semantics/node_archetypes.yaml`, `semantics/vocabulary.yaml`, `semantics/contracts.yaml`, `semantics/receipt_catalog.yaml`, `semantics/canonical_sources.yaml`, and `semantics/invariants.yaml`.
- All prior release records.

## Alignment evidence

The declaration reuses existing law and introduces no new law:

- Its decision authority equals the semantic owner of `l9.receipt/admission@1` (`receipt_catalog.yaml#receipts.admission.semantic_owner`).
- Its operation is the existing vocabulary term `product_admission`, a subtype of `admission`. That term's rules already state that admission binds the exact subject, does not imply runtime availability, and does not authorize capability invocation.
- Its subjects are the two subjects in that term's definition.
- It does not inherit `global_admission_rules`, so product admission does not require global authority.
- `implies.runtime_admission: false` restates the existing separation in `product_kinds.yaml`: product release admission and runtime participation admission are distinct.
- `implementation_conformance` and `consumer_compatibility` restate `lifecycle.yaml` (`topology_admission_does_not_imply_implementation_conformance`) and `vocabulary.yaml` (`product_admission_does_not_imply_consumer_compatibility`).

## Mechanical derivation refreshes

None. No modified ledger is a hashed derivation source of any other ledger. After the change, the validator reported no stale coordinate. Before this release record existed, the only failures were SC-008 against the v3.12.0 hash inventory, which this record supersedes.

## Validator delta

- `scripts/validate-semantics.py` gains RC-021, the product admission authority identity closure, plus an isolated negative-case batch. Each case must fail at its intended field.
- RC-020 and every earlier check are unchanged.

## RC-021 Product admission authority identity closure

RC-021 governs the exact coordinate `l9.authority/product-admission` and proves the following:

- **Declared exactly once.** The coordinate is declared at `authority_model.yaml#product_admission_authority.id`. Any other occurrence in any ledger fails closed unless it is an exact reference under a `*_ref` or `*_refs` field. That includes a key containing the coordinate, a version-suffixed or whitespace-padded value, or a value under a non-reference field.
- **Declaration pinned whole.** The declaration equals its pinned bytes key by key. An extra key, an extra `implies` consequence, a removed rule, a changed meaning, or a second decision authority each fails closed.
- **Inherited law pinned.** `admission_rules` (the six global requirements and three flags) and `escalation_rules` (four entries) equal their pinned values, so the inherited law cannot be weakened underneath the declaration.
- **Vocabulary term pinned.** The vocabulary term `product_admission` keeps its semantic class, its subtype `admission`, and its three rules: one exact-subject binding rule and two non-implication rules.
- **Receipt owner pinned.** The admission receipt owner stays `applicable_target_class_authority`.
- **Reaches ProductTopology intake.** `l9.projection/stage-product-topology@1` exists exactly once and projects `$.product_admission_authority`, `$.admission_rules`, and `$.escalation_rules` from the authority model.
- **No crash on malformed shapes.** Comparisons are by value only and selectors are filtered to strings, so a malformed shape produces a located failure, never an uncaught exception.

RC-021 applies no rule to any other authority, defines no authority family, and sets no cardinality on authority declarations (`L9-VALIDATION-001`).

The negative-case batch has 49 cases. Each must fail at its intended field, and a case that raises instead of failing is itself a failure. The cases cover:

- **The coordinate itself:** missing; declared twice; shadowed under another id key, with a version suffix, or as a mapping key; an inexact reference.
- **Decision authority:** moved to the global owner, to the compiler, or to a non-scalar.
- **Operation and subjects:** a different operation or a non-scalar operation; subjects widened, holding a mapping element, or duplicated.
- **Inheritance and flags:** a dropped requirement; emptied or substituted `inherits_rules`; the self-admission ban lifted; a non-boolean candidate-generation flag.
- **Rewrites and additions:** a replaced owner, meaning, or rules; an added alternate admitter or self-admission flag; `implies` not a mapping.
- **Removed fields:** `rules`, `inherits_rules`, or `global_semantics_owner` removed.
- **Implied consequences:** each of the six set `true`; the publication consequence omitted; an extra consequence set `true`.
- **Inherited law:** the inherited self-admission ban lifted; an inherited requirement dropped; `unknown` defaulting to pass; missing authority allowed; the escalation law removed.
- **Vocabulary term:** its rules rewritten; its subtype moved.
- **ProductTopology projection:** each of the three selectors dropped; a non-string selector; the stage profile removed.
- **Admission receipt:** its owner moved.

Test-first evidence:

- **Coordinate, base `c1d87abe00e31a2b06bda607afe54ea16bfadd77`.** RC-021 failed only because the coordinate was absent (`found []`).
- **Projection, after the declaration and before the selectors.** RC-021 failed only on the three missing selectors.

Both now pass.

Audit history:

- **Validate & Repair** found these defects in the first form of RC-021, all repaired before publication:
  - a partial pin that let unchecked fields redefine admission;
  - an unpinned inherited law;
  - shadow declarations under other keys;
  - duplicate subjects;
  - `TypeError` crashes on a list operation or a mapping subject.
- **Codex review (PR #166)** found that ProductTopology intake did not receive the declaration. The projection selectors and their RC-021 coverage close that.
- **Independent review of the successor commit** found a `TypeError` crash on a non-string stage selector, and that `semantic_dependency_model.yaml` did not make ProductTopology depend on the authority model. Both are repaired, and the crash has its own negative case.
- **Review under `L9-REVISION-001`** found that the authority change had been hashed into the published v3.12.0 record in place. That record is restored byte-identical, and this successor carries the change instead.

## Existing closure

The existing semantic-foundation validator still owns SC-001 through SC-010 and RC-001 through RC-020. v3.13.0 adds RC-021 without weakening or replacing any predecessor check.

## Explicit boundaries

- Downstream ProductTopologies that already name `l9.authority/product-admission` resolve against this declaration after they rebind to this release. This release modifies no consumer.
- A consumer whose `admission.subject` names a subject other than an exact ProductTopology or an exact product release must align its subject in separate downstream work. This release does not widen the subject set.
- This release creates no runtime admission authority.

## Release integrity

`HASHES.sha256` inventories the exact final canonical semantic bytes, all accepted ADRs plus the ADR index, and this release's Markdown record. Prior release directories remain byte-identical.

## Admission state

v3.13.0 is a candidate and does not admit itself. Validation evidence grants no authority or promotion. Declaring the product admission authority role admits no product.
