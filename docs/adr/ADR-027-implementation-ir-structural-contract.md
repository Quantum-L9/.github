# ADR-027 — Structural Contract for l9.implementation-ir/v1

**Status:** Candidate for semantic-foundation v3.30.0. Drafted on 2026-11-08 at the repository owner's instruction as unit R4-A (`R4-A-IMPLEMENTATION-IR-QUALIFICATION`) of campaign `L9-COMPILER-R4-EXECUTABLE-NODE-001`. Admission of v3.30.0 is the acceptance gate; this record does not admit itself.

## Context

`semantics/compilation_profiles.yaml` (`l9.compilation/product-build@1`) defines Stage 14 (`implementation`).
- It produces `implementation_ir` with `validation.required: true` under `implementation-contract-validator/v1`.
- `semantics/solver_catalog.yaml` registers that solver as `class: structural`, `mechanically_checkable: true`.
- Stage 15 consumes `implementation_ir` through `l9.binding/python-gate-node@1` (ADR-026).

At `Quantum-L9/.github@9488d8f31a5ddbde8f1d3c3aaf57d17f21f62b88`, nothing defines what an `l9.implementation-ir/v1` contains:
- `ir_catalog.yaml` gives the IR an id, a one-sentence purpose, and its transitions.
- The binding's maps name concepts the IR must carry, but no fields, dispositions or provenance.
- No `semantics/` file, ADR or schema states its structure.

A structural validation therefore had nothing to check against. A compiler that defined the shape itself would become the owner of ImplementationIR semantics, which `authority_model.yaml#compiler_authority.may_not` forbids (`redefine_canonical_vocabulary`, `self_expand_authority`).

The Foundation already has a mechanically enforced way to give an artifact structure:
- an `l9.schema-definition/v1` file whose `properties.schema.const` names the artifact;
- listed under `generic_compiler_manifest.yaml#requires.artifact_schemas`;
- resolved by the Semantic Compiler's `CanonicalAuthority.schema_defining`;
- checked by its v1 schema interpreter.

The twenty v3.28.0 payload schemas use exactly this mechanism.

## Options considered

### Option A — No canonical contract; let the compiler define the IR shape

- Pros: no Foundation change.
- Cons: the compiler becomes the semantic owner of ImplementationIR. Stage 14's required structural validation has no authority to validate against.

### Option B — Extend `ir_catalog.yaml` with an inline field grammar

- Pros: keeps the IR definition in one ledger.
- Cons: no enforcement mechanism reads an inline grammar from `ir_catalog.yaml`. It would be a second, unenforced schema dialect.

### Option C — One `l9.schema-definition/v1` artifact schema in the existing artifact-schema mechanism

- Pros: enforced today by the existing interpreter and resolver with no compiler change. It is the smallest addition, and `ir_catalog.yaml` stays unchanged.
- Cons: the v1 interpreter checks shape only. Cross-field obligations must be stated as named rules for `implementation-contract-validator/v1` to enforce.

## Decisions

Option C.

1. `semantics/implementation_ir.schema.yaml` (`l9.schema/implementation-ir@1`, `l9.schema-definition/v1`) defines the structure of `l9.implementation-ir/v1`. Its `properties.schema.const` is `l9.implementation-ir/v1`. It is listed under `generic_compiler_manifest.yaml#requires.artifact_schemas`.
2. **Required sections:**
   - `subject`: product identity, kind, archetype and consumed manifest digest.
   - `authority`: authority revision, `l9.compilation/product-build@1` and stage `implementation`.
   - `target`: the selected binding and technologies.
   - `interfaces`: actions with request and result contract, effect class, consequential flag, inbound port and behavior disposition; plus forbidden actions.
   - `ports`, `adapters`, `composition` (root and port dependencies), `conformance`, `unresolved` and `provenance` (manifest, topology, RepositorySpec and WorkflowSpec digests, and compiler version).
   - Every value is lowered from the resolved ProductManifest, including `interfaces`, `effects` and `implementation_ref` (ADR-026), and the admitted target binding. The IR adds no product meaning.
3. **Exactly three dispositions** for every realizable obligation (action behavior, port, adapter, composition root):
   - `generable`: fully determined by the IR and the target binding, so it may be emitted.
   - `bound`: realized by existing product-owned code named by an admitted `implementation_ref`, verified and never regenerated.
   - `unresolved`: recorded under `unresolved` and never realized.

   No fourth disposition exists.
4. **Sixteen `semantic_rules`** state the cross-field obligations the shape cannot express:
   - exact action, forbidden-action, port and adapter correspondence with the manifest;
   - consequential iff in `effects.consequential_operations`;
   - digest equality;
   - target applicability;
   - `bound` requires an admitted `implementation_ref`;
   - `generable` requires a determining behavior contract or binding map;
   - no invented adapter or provider.

   `enforcement` assigns them to `implementation-contract-validator/v1`.
5. No IR catalog, compilation profile, solver, binding, manifest or topology change, and no RC check, is part of this release.

## Review findings (recorded, not resolved)

- **Shape versus rules.** The v1 interpreter catches 15 of 15 shape-level negative controls. Eight cross-field controls are not shape violations (wrong product identity, non-Node binding selection, undeclared action, unknown technology, invented provider, behavior without contract or binding, manifest digest mismatch, unbound required port). Each maps to a named rule. Until the Semantic Compiler implements `implementation-contract-validator/v1` (unit R4-B), those obligations are declared but not enforced.
- **No pinned check.** No release check pins this schema or its rules. Authoring one is an owner decision this candidate does not take.
- **Behavior contracts.** `behavior_contract_ref` names a coordinate kind that no ledger yet defines. Until one is admitted, `generable` behavior can be justified only by a target binding map, such as action registration or composition, and never by product algorithms.
- **Second Node.** Qualification used the real `l9.state` ProductManifest. No independent second Node instance was constructed for this structural unit; generality is a Stage 14 and Stage 15 acceptance obligation (R4-B to R4-D).

## Consequences

- Stage 14 has a canonical structure to produce and to validate. A compiler cannot change the IR's shape without contradicting this admitted contract.
- An ImplementationIR with a missing provenance digest, a fourth disposition or a dropped forbidden-action list is structurally invalid before any target lowering.
- Admission of this candidate grants no producer, compiler or consumer any mutation, publication, merge, deployment or execution authority.
