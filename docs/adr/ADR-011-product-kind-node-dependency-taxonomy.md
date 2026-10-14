# ADR-011: ProductKind is defined by canonical consumption and deployment

Status: Accepted

## Decision
`ProductKind` is the primary architectural participation form of an L9 product. It is determined by the product's canonical consumption and deployment model, not by repository shape, package format, provider identity, semantic complexity, or the mere presence of a process.

Two ProductKinds are admitted in this foundation:

- `node`: canonical consumption is `remote_invocation`; canonical deployment is `independent_runtime`.
- `dependency`: canonical consumption is `local_composition`; canonical deployment is `consumer_bound_artifact`.

SDK is intentionally unresolved and is not admitted by this decision.

## Archetypes
Archetypes specialize a ProductKind without redefining it or acquiring domain semantic ownership. Node archetypes live in `node_archetypes.yaml`. Dependency archetypes live in the sibling `dependency_archetypes.yaml`.

## Consequences
A Node and Dependency may both own rich semantics, ports, adapters, policies, receipts, provider integrations, and complex internal architecture. Those properties do not classify the product. The canonical consumption/deployment boundary does.

## Amendment 2026-10-14: Memory hosted-service exception

Status: Accepted. Decided by GAR on explicit operator direction. Admitted by the ProductKind owner, `Quantum-L9/.github`, as canonical law. Effective with Semantic Foundation v3.21.0. The decision text above is preserved as written. This amendment qualifies one rule in it, "determined by the product's canonical consumption and deployment model": an exactly bound admitted product-kind exception is the only departure from that rule.

### Context
The canonical Memory product, `l9-graphiti-memory:product/l9-graphite-memory` in `Quantum-L9/l9-graphiti-memory`, is a Dependency (`l9.dependency-archetype/semantic-subsystem@1`). From Memory 3.0.0 it is also intended to run as one centrally hosted Memory service. Agents consume that service remotely through authenticated MCP Streamable HTTP.

That realization conflicts with the Dependency meaning in this decision: local composition, a consumer-bound artifact, and a consumer-owned lifecycle. It does not match Node either. Memory holds no Constellation identity, takes no Gate admission, and its ordinary agent requests are not Gate-routed inter-product work.

Reclassifying Memory as a Node, adding a third ProductKind, or relaxing Dependency for every product would each change global law to fit one product. This amendment does none of them.

### Decision
`semantics/product_kinds.yaml` gains `kind_exception_model` and exactly one entry in `kind_exceptions`: `l9.product-kind-exception/memory-hosted-service@1`. A product-kind exception is product-scoped canonical law. It is not a ProductKind, an archetype, or a waiver class, and it is not a delegation of authority to the product.

**Binding.** The exception binds only when all of the following hold:
- a ProductTopology declares `product.kind_exception_ref` equal to the exception id;
- the topology's kind is `dependency`;
- its product id, canonical repository, and archetype equal the exception subject;
- the subject repository is a current entry in `repository_registry.yaml`;
- the exception catalog holds exactly the admitted set, and the exception model is unchanged.

ProductTopology and ProductManifest are both release-independent, so the release floor (`subject.applies_from_release: 3.0.0`) is a product-kind release obligation. It is enforced at product release admission through `l9.contract/product-release@1`, which requires `applicable_product_kind_requirements_are_resolved` and derives kind-specific release obligations from product-kind law. A ProductManifest must carry `product.kind_exception_ref` whenever its source topology claims an exception.

Copying Memory's configuration does not bind the exception. A malformed, unadmitted, unauthorized, or unbound claim is invalid. It is never ignored and never coerced to the nearest kind.

**Permitted departures.** For that exact subject only, the exception permits:
- consumption as `remote_invocation`, only through authenticated, namespace-authorized MCP Streamable HTTP;
- deployment as `independent_runtime`: one independent operational service that owns its server process lifecycle and operational health;
- a service runtime identity of its own that is never a Constellation identity;
- PostgreSQL (`technology_capabilities.yaml#technologies[postgresql]`) as the shared canonical persistence backend, with semantic ownership unchanged.

Ordinary agent Memory MCP requests are actor-to-service consumption. They are not Gate-routed inter-product work.

The exception enumerates exactly 20 displaced obligations across `product_kinds.yaml`, `architecture_rules.yaml`, `architecture_patterns.yaml` (`l9.pattern/dependency-package@1`), and `dependency_archetypes.yaml`. Every other obligation stays in force, including the `l9.pattern/dependency-package@1` requirement.

**Never displaced.** The following stay in force regardless of the exception:
- `kind_exception_model.protected_requirements`: installable artifact, public programmatic contract, no Constellation identity, actor and surface identity, and product release admission;
- `kind_exception_model.protected_prohibitions`: no implicit Gate registration, no Constellation identity as a Dependency, and no provider identity as product identity;
- canonical semantic ownership;
- agent attribution for every consequential memory operation;
- tenant isolation;
- namespace authorization;
- credential protection;
- lifecycle consistency;
- provenance;
- immutable release identity;
- deployment admission.

Hosted-service admission does not self-admit, and it never confers Gate admission or routability.

**Forbidden.** The exception may not be used to acquire Constellation identity, Gate admission, Gate routing authority, a Node archetype, or the runnable-node pattern. It forbids unauthenticated remote consumption, credential material, inheritance by another product, and treating a hosting coordinate as a semantic category.

**Hosting.** Hetzner C1 is the intended deployment coordinate. It is deployment-owned configuration and is not recorded in global semantics.

### Reconciliation
The ledgers that state Dependency law unconditionally now carry an exact-product qualifier:
- `l9.contract/product-kind@1`: purpose, guarantee, `requires`, `forbidden`, and the `resolved` and `invalid` outcomes;
- `l9.contract/product-topology@1`;
- the global rules of `product_kinds.yaml` (including the classification rule, renamed to its qualified form), `architecture_rules.yaml`, `architecture_patterns.yaml`, and `dependency_archetypes.yaml`;
- the vocabulary `dependency` term.

The following also change:
- `architecture_rules.yaml` gains `l9.arch-rule/product-kind-exception@1`;
- `product_topology.schema.yaml` gains the claim field `product.kind_exception_ref` and `kind_resolution.exception_rule`;
- `product_manifest.schema.yaml` preserves the applied exception, gates on its binding, and requires the coordinate whenever the source topology claims one;
- `semantic_dependency_model.yaml` makes product-kind resolution depend on `repository_registry`, so a change to the subject's registry entry invalidates it;
- the compiler stage projections and the identity projection select the exception catalog and the claim;
- the product-topology validator in `solver_catalog.yaml` declares exact-subject binding.

RC-028 in `scripts/validate-semantics.py` pins this single exception and its model, field by field and by canonical digest. It pins every reconciliation listed above. It evaluates ordinary Node, ordinary Dependency, and exact Memory ProductTopology witnesses under `l9.contract/product-kind@1` kind coherence.

### Consequences
- Every other Node and Dependency keeps its requirements unchanged. A second exception, or a broader one, requires a new dated amendment and a change to RC-028.
- The Memory repository must declare the claim in its own ProductTopology, and its own topology validator must consume `kind_exceptions` instead of comparing models directly with the kind. That downstream change belongs to `Quantum-L9/l9-graphiti-memory`.
