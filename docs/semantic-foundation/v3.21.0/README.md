# Semantic Foundation v3.21.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.21.0 adds one narrowly bounded product-kind exception. Under it, `Quantum-L9/l9-graphiti-memory`, the canonical Memory product, remains a **Dependency** while running as one centrally hosted service. Agents consume that service remotely through authenticated MCP Streamable HTTP. The release target downstream is Memory 3.0.0.

## Admitted delta

- `semantics/product_kinds.yaml` gains `kind_exception_model` and exactly one `kind_exceptions` entry, `l9.product-kind-exception/memory-hosted-service@1`.
- The exception binds only the exact subject:
  - product `l9-graphiti-memory:product/l9-graphite-memory`;
  - canonical repository `Quantum-L9/l9-graphiti-memory`, which is registry entry `l9-graphiti-memory`;
  - archetype `l9.dependency-archetype/semantic-subsystem@1`.
- The release floor is `3.0.0`. ProductTopology and ProductManifest are release-independent, so the floor binds at product release admission through `l9.contract/product-release@1` (`applicable_product_kind_requirements_are_resolved`).
- A ProductTopology claims the exception only through `product.kind_exception_ref`.
- For that subject, 20 enumerated Dependency obligations are displaced. Every other obligation remains.
- Every ledger that stated kind law unconditionally now scopes it to "unless an admitted exception binds the exact product", including the global rule that kind is determined by consumption and deployment:
  - contracts `l9.contract/product-kind@1` (including its purpose) and `l9.contract/product-topology@1`;
  - the global rules of `product_kinds.yaml`, `architecture_rules.yaml`, `architecture_patterns.yaml` and `dependency_archetypes.yaml`;
  - the vocabulary `dependency` term.
- The ProductTopology schema and the ProductManifest schema carry the claim. A manifest must carry it whenever its source topology claims an exception.
- `semantic_dependency_model.yaml` adds `repository_registry` to the dependencies of product-kind resolution, so a registry change invalidates it. The three existing projection profiles stay byte-for-byte as admitted. New `@2` successors (`stage-product-topology@2`, `stage-semantic-resolution@2`, `product-identity-topology@2`) declare `successor_of` and add only the exception selections. Each stage consumer resolves to its unique unsuperseded profile. The product-topology solver declares exact-subject binding.
- ADR-011 gains a dated amendment. Its original decision is unchanged.
- RC-029 pins the exception and its model, field by field and by canonical digest, and evaluates ProductTopology witnesses under `l9.contract/product-kind@1`. It has 87 hostile negative cases.

## Before → after canonical rules

| Rule | v3.20.0 | v3.21.0 |
| --- | --- | --- |
| Kind classification (`product_kinds.yaml` global rule) | `product_kind_is_determined_by_canonical_consumption_and_deployment_model` | `…_unless_an_admitted_product_kind_exception_binds_the_exact_product` |
| Dependency meaning (`product-kind@1`) | `dependency_means_local_composition_plus_consumer_bound_artifact` | Same meaning `…_unless_an_admitted_product_kind_exception_binds_the_exact_product` |
| Kind/model conflict (`product-kind@1` outcomes.invalid) | `declared_kind_conflicts_with_consumption_or_deployment` | `…_without_an_exactly_bound_admitted_product_kind_exception` |
| Kind constrains models (`product-topology@1`) | `product_kind_constrains_consumption_and_deployment` | `…_except_as_an_exactly_bound_admitted_product_kind_exception_enumerates` |
| Who may depart from kind law | nobody | only the product bound by an admitted `kind_exceptions` entry, by explicit claim |
| Memory consumption | `local_composition` only | `remote_invocation`, only through authenticated, namespace-authorized MCP Streamable HTTP |
| Memory deployment | `consumer_bound_artifact` | `independent_runtime` as one operational service |
| Memory process lifecycle and health | consumer-owned | product-owned |
| Memory runtime identity | `RuntimeIdentity(consumer)` | the service's own runtime identity, never Constellation identity |
| Memory persistence | unspecified | PostgreSQL as the shared canonical persistence backend; MemoryService semantic ownership unchanged |
| Memory and Gate | not Gate-routed | unchanged: ordinary agent MCP requests are actor-to-service consumption, not Gate-routed inter-product work |
| Memory Constellation identity, Gate admission, routing authority | forbidden | still forbidden, and the exception explicitly cannot grant them |
| Every other Node and Dependency | kind law | kind law, unchanged |

## Retained for Memory

The exception displaces nothing outside its 20 enumerated obligations. It explicitly retains all of the following:

- the protected requirements: the installable artifact, the public programmatic contract, no Constellation identity, actor and surface identity obligations, and product release admission;
- the protected prohibitions: no implicit Gate registration, no Constellation identity as a Dependency, and no provider identity as product identity;
- `l9.pattern/dependency-package@1`;
- canonical semantic ownership;
- agent attribution for every consequential memory operation;
- tenant isolation;
- namespace authorization;
- credential protection;
- lifecycle consistency;
- provenance;
- immutable release identity;
- deployment admission.

The hosted service's own runtime identity is required. Hosted-service admission has its own state sequence. A bound topology must declare `service_admitted`. That declaration is not resolution (release admission) and not admission of a running service (target-class authority). It does not self-admit, and it never confers Gate admission or routability.

## Contraction decisions

v3.21.0 deliberately does **not** add:

- a third ProductKind, an SDK kind, or a hosted-service archetype;
- a hosted-service architecture pattern;
- a generalized waiver, override, or exception platform. RC-029 admits exactly one exception, and a second requires a new amendment and a validator change;
- new consumption or deployment vocabulary. The existing `remote_invocation` and `independent_runtime` values are used;
- a new identity dimension or identity framework. `runtime_identity` is already defined "as defined by the applicable ProductKind and topology";
- a new service, MemoryService contract, or record semantic;
- a hosting coordinate. Hetzner C1 is the intended deployment coordinate, and it stays in deployment-owned documentation and artifacts.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.20.0/`, the `l9.projection/coding-agent-execution@1` candidate delivered by open PR #179 (head `aedf271d6a401c3515637bb70339a49e7cc92319`). That record is preserved unchanged and is the exact stacked baseline. This release must merge after #179.
