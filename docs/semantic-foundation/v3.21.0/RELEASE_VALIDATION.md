# Release Validation v3.21.0

Candidate status: **additive successor candidate**.

## Objective

Admit one product-scoped ProductKind exception for the hosted Memory Dependency. Existing Node and Dependency law must keep its meaning and enforcement for every other product, and no departure may be granted silently.

## RC-029: product-kind exception closure

RC-029 must prove the following.

**Exception model**

1. `product_kinds.yaml#kind_exception_model` names `Quantum-L9/.github` as admission authority and `product.kind_exception_ref` as the only claim field.
2. Its `binding_requires`, `rules`, `protected_requirements` and `protected_prohibitions` equal the admitted values exactly.
3. Its canonical digest equals the admitted digest.

**Exception catalog**

4. `kind_exceptions` holds exactly `l9.product-kind-exception/memory-hosted-service@1`. Any other catalog content, or a drifted model, binds nothing.
5. The exception has exactly the admitted shape, and its status is `admitted`.
6. Its authority is the canonical `Quantum-L9/.github` authority, and its decision resolves to the dated ADR-011 amendment heading.
7. Its kind is admitted.
8. Its subject equals the admitted subject. The subject repository is a current registry entry with the same coordinate, and the archetype belongs to the kind's catalog.

**Field pins**

9. These fields equal their admitted values exactly:
   - `effective_models`: admitted vocabulary values `remote_invocation` / `independent_runtime`;
   - `remote_consumption`: authenticated, namespace-authorized MCP Streamable HTTP, and ordinary agent requests are not Gate-routed inter-product work;
   - `deployment`: one product-owned service with a deployment-owned coordinate and unchanged semantic ownership. Its PostgreSQL persistence ref resolves to a registered `persistence_provider` technology;
   - `identity`: service runtime identity only, never Constellation identity;
   - `hosted_service_admission`: no self-admission, no `gate_admitted` or `routable`.

**Departures**

10. Each of the 20 departures is checked independently, each at its own field:
    - it resolves (`.displaces`);
    - it belongs to the excepted kind's own law (`.scope`);
    - it does not touch a protected obligation, checked recursively through every key and string under its target (`.protected`);
    - its replacement equals the admitted replacement (`.replacement`).
11. The `(displaces, replacement)` set equals the admitted set.

**Retained, forbidden and credentials**

12. `retained_requirements`, `retained_prohibitions` and `forbidden` equal the admitted sets.
13. Credential-shaped keys or values do not appear in the exception or in a ProductTopology.
14. The exception's canonical digest equals the admitted digest.

**Reconciliation**

15. Every ledger that states kind law carries the exact-product qualifier, and the bare unconditional spelling is absent:
    - the `product_kinds.yaml` classification rule;
    - the `product_kinds.yaml` exception rules;
    - the global rules of `architecture_rules.yaml`, `architecture_patterns.yaml` and `dependency_archetypes.yaml`;
    - `l9.contract/product-kind@1`: purpose, source invariant, applies-to, `requires`, guarantees, `forbidden`, and the `resolved` and `invalid` outcomes;
    - `l9.contract/product-topology@1`;
    - the vocabulary `dependency` rules and the `product_kind_exception` term.
16. These also exist:
    - `l9.arch-rule/product-kind-exception@1`;
    - the ProductTopology claim field, exception rule and exception catalog;
    - the ProductManifest claim field and both gate items (binding, release floor);
    - both compiler-stage `$.kind_exceptions` selectors;
    - the product-topology solver flag.

**Witnesses**

17. Under `l9.contract/product-kind@1` coherence, the ordinary Node witness, the ordinary Dependency witness and the exact Memory hosted-service ProductTopology witness all resolve. Identity dimensions are checked against the kind's dimensions, or against a bound exception's dimensions.

## Hostile negative cases

RC-029 carries **71** isolated negative cases. Each must fail at its intended RC-029 field.

### Known-bad ProductTopology witnesses (20)

- unrelated Dependency configured for remote canonical consumption: fails at `consumption.model`.
- unrelated Dependency copies Memory configuration including the claim: fails at `product.kind_exception_ref`.
- copy keeps Memory's product id under another repository: fails at `product.kind_exception_ref`.
- copy keeps Memory's repository under another product id: fails at `product.kind_exception_ref`.
- Memory configuration without the explicit claim: fails at `consumption.model`.
- claim names an unknown exception: fails at `product.kind_exception_ref`.
- Node claims the Memory exception: fails at `product.kind_exception_ref`.
- Memory claims Constellation identity: fails at `identity.dimensions.constellation`.
- Memory requires Node runtime and Gate adapter patterns: fails at `architecture.required_pattern_refs`.
- Memory joins Gate-routed Constellation communication: fails at `communication.constellation_boundary_required`.
- Memory acquires Gate admission and routability: fails at `admission.kind_specific_requirements`.
- Memory drops authentication: fails at `security.authentication_contract_refs`.
- Memory drops namespace authorization: fails at `security.authorization_contract_refs`.
- Memory drops agent attribution: fails at `identity.dimensions.actor`.
- Memory drops release identity: fails at `identity.dimensions.release`.
- Memory omits MCP Streamable HTTP: fails at `consumption.public_entry_modes`.
- Memory drops the retained Dependency package pattern: fails at `architecture.required_pattern_refs`.
- Memory declares a deployment model the exception does not admit: fails at `deployment.model`.
- Memory carries credential material: fails at `credentials`.
- unrelated Dependency copies the displaced service runtime identity without a claim: fails at `identity.dimensions.runtime`.

### Malformed, unauthorized, or drifted exceptions and exception model (33)

- malformed exception without a subject: fails at `kind_exceptions[0].subject`.
- exception admitted by a non-owner: fails at `kind_exceptions[0].authority`.
- exception left as a candidate: fails at `kind_exceptions[0].status`.
- ADR-011 amendment removed: fails at `kind_exceptions[0].authority.decision_ref`.
- departure displaces a protected obligation: fails at `kind_exceptions[0].departures[20].protected`.
- departure displaces a parent mapping holding a protected obligation: fails at `kind_exceptions[0].departures[0].protected`.
- departure displaces an unresolvable obligation: fails at `kind_exceptions[0].departures[0].displaces`.
- departure displaces Node law: fails at `kind_exceptions[0].departures[0].scope`.
- departure replacement grants Constellation identity: fails at `kind_exceptions[0].departures[0].replacement`.
- generalized waiver: second exception for another product: fails at `kind_exceptions`.
- exception adds Constellation identity: fails at `kind_exceptions[0].identity`.
- runtime identity rule rewritten to Constellation identity: fails at `kind_exceptions[0].identity`.
- hosted admission confers Gate admission: fails at `kind_exceptions[0].hosted_service_admission`.
- hosted admission rule rewritten to self-admit: fails at `kind_exceptions[0].hosted_service_admission`.
- hosted admission states reduced: fails at `kind_exceptions[0].hosted_service_admission`.
- remote consumption made unauthenticated: fails at `kind_exceptions[0].remote_consumption`.
- agent MCP requests declared Gate-routed inter-product work: fails at `kind_exceptions[0].remote_consumption`.
- semantic ownership no longer unchanged: fails at `kind_exceptions[0].deployment`.
- process lifecycle handed to Gate: fails at `kind_exceptions[0].deployment`.
- persistence names an unregistered technology: fails at `kind_exceptions[0].deployment.canonical_persistence`.
- tenant isolation dropped from retained requirements: fails at `kind_exceptions[0].retained_requirements`.
- implicit Gate registration dropped from retained prohibitions: fails at `kind_exceptions[0].retained_prohibitions`.
- Gate routing authority no longer forbidden: fails at `kind_exceptions[0].forbidden`.
- subject repository absent from the registry: fails at `kind_exceptions[0].subject.repository_ref`.
- credential-shaped key in the exception: fails at `kind_exceptions[0].credentials`.
- credential embedded in a value: fails at `kind_exceptions[0].credentials`.
- effective model outside the vocabulary: fails at `kind_exceptions[0].effective_models`.
- unpinned purpose text drifts: fails at `kind_exceptions[0].canonical_digest`.
- protected prohibitions shrunk: fails at `kind_exception_model.protected_prohibitions`.
- protected requirements shrunk: fails at `kind_exception_model.protected_requirements`.
- binding requirements emptied: fails at `kind_exception_model.binding_requires`.
- exception rule inverted to inheritance: fails at `kind_exception_model.rules`.
- exception model definition drifts: fails at `kind_exception_model.canonical_digest`.

Each of these must also leave the Memory claim **unbound** (`product.kind_exception_ref`). The ordinary Node and Dependency witnesses must keep their outcome.

### Reconciliation regressions (18)

- Dependency guarantee reverted to unconditional: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].guarantees`.
- invalid outcome ignores bound exceptions: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].outcomes.invalid`.
- resolved outcome ignores bound exceptions: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].outcomes.resolved`.
- exception requirement removed from product-kind@1: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].requires`.
- exception prohibition removed from product-kind@1: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].forbidden`.
- classification purpose loses its only-departure qualifier: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-kind@1].purpose`.
- product-topology@1 kind constraint reverted to unconditional: fails at `semantics/contracts.yaml` `contracts[l9.contract/product-topology@1].guarantees`.
- global classification rule reverted to unconditional: fails at `semantics/product_kinds.yaml` `global_rules.product_kind_is_determined_by_canonical_consumption_and_deployment_model_unless_an_admitted_product_kind_exception_binds_the_exact_product`.
- owner-only admission rule removed: fails at `semantics/product_kinds.yaml` `global_rules.product_kind_exception_is_admitted_only_by_the_product_kind_owner`.
- archetype qualifier removed: fails at `semantics/dependency_archetypes.yaml` `global_rules.archetype_obligations_apply_unmodified_unless_an_admitted_product_kind_exception_displaces_them_for_its_exact_product`.
- exception architecture rule removed: fails at `semantics/architecture_rules.yaml` `rules[l9.arch-rule/product-kind-exception@1]`.
- ProductTopology claim field removed: fails at `semantics/product_topology.schema.yaml` `kind_resolution.exception_rule`.
- ProductManifest binding gate item removed: fails at `semantics/product_manifest.schema.yaml` `resolved_manifest_gate.all_of`.
- ProductManifest release-floor gate item removed: fails at `semantics/product_manifest.schema.yaml` `resolved_manifest_gate.all_of`.
- compiler stage stops projecting the exception catalog: fails at `semantics/projection_profiles.yaml` `projection_profiles[l9.projection/stage-product-topology@1].sources.product_kinds.selectors`.
- vocabulary loses the exception term: fails at `semantics/vocabulary.yaml` `terms.product_kind_exception`.
- vocabulary Dependency qualifier replaced: fails at `semantics/vocabulary.yaml` `terms.dependency.rules`.
- product-topology validator loses exact-subject binding: fails at `semantics/solver_catalog.yaml` `solvers[product-topology-validator/v1].properties.applies_admitted_product_kind_exceptions_only_by_exact_subject_binding`.

The ordinary Node and Dependency witnesses must also resolve when the exception catalog and model are removed entirely. This proves existing products do not depend on them.

The negative cases were mutation-tested against the validator. Each of these internal checks was stubbed out in turn: kind scope, recursive protection walk, credential scan, digest, ref resolution, and exception binding. Every stub was caught, either by a negative case or by the positive RC-029 check.

Crashes, unrelated failures, skipped cases, or default success are not passes.

## Test-first proof

The v3.21.0 validator was run against the **unmodified** stacked baseline at `aedf271d6a401c3515637bb70339a49e7cc92319` (PR #179 head; the same result holds at `main` `f9993ed19a07cc3a2cd3f6b512be7573f1fa897e`). The result was exit 1:

- 36 RC-029 failures (the model and catalog are absent, the 7 global-rule qualifiers are absent, the product-kind and product-topology contract clauses are absent, the exception rule, vocabulary, schema, projection and solver reconciliation are absent, and the Memory witness fails at `product.kind_exception_ref`, `consumption.model`, `deployment.model` and `identity.dimensions.runtime`);
- one RC-005 failure, because the identity projection did not select `$.product.kind_exception_ref`.

The ordinary Node and ordinary Dependency witnesses produced **no** failures against the baseline. Against the candidate bytes the same validator passes every check.

## Scope limit, stated explicitly

A ProductTopology is release-independent, so RC-029 cannot evaluate the release floor (`applies_from_release: 3.0.0`) on a topology witness. The floor is canonical law in `kind_exception_model.binding_requires` and `rules`, in `kind_resolution.exception_rule`, and in the ProductManifest resolved-gate item `product_kind_exception_release_floor_satisfied_when_claimed`. It is enforced where a release is admitted. Enforcing it against Memory's release binding is part of the downstream handoff.

## Preserved closure

RC-001 through RC-028 (including the v3.20.0 coding-agent-execution projection check) and SC-001 through SC-010 remain in force with no weakened assertion. RC-005 strengthens: its pinned identity-projection selection gains `$.product.kind_exception_ref`.

## Downstream consequences (not changed here)

`Quantum-L9/l9-graphiti-memory` is read-only to this release. To consume the exception at Memory 3.0.0, that repository must:

- declare `product.kind_exception_ref` and the hosted models in its ProductTopology;
- re-pin `Quantum-L9/.github` provenance to this release's merge revision;
- regenerate its release binding and ProductManifest;
- extend `tools/assurance/validate_product_topology.py::check_kind` to resolve `kind_exceptions` by exact subject and enforce the release floor;
- realize MCP Streamable HTTP. Its current HTTP surface is a plain JSON-RPC `POST /mcp`.

The PR that delivers this release carries the bounded handoff.

## Release integrity

`HASHES.sha256` binds the final canonical semantic bytes, all 18 ADRs plus the ADR index, and this release record. The v3.20.0 predecessor record is immutable and unchanged.

## Admission state

v3.21.0 is a candidate and does not self-admit. Passing validation produces evidence only. Applicable authority must admit the exact candidate bytes.
