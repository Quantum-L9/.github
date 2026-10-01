# Quantum-L9/.github Semantic Foundation v3.5.0

Status: **REPLACEMENT CANDIDATE / RELEASE-READY**

## What this package is

This package is the candidate upstream semantic foundation for the Quantum-L9 organization. It is intended to replace the unmerged PR #146 foundation rather than layer another remediation PR on top of it.

Its job is to give L9 one canonical language for describing what a product is, what it owns, how it participates, what it may depend on, how it is realized, how identity works, what evidence is required, and when an exact realization is admissible.

The central primitive is **ProductTopology**.

> **ProductTopology is the authoritative product contract from which L9 product architecture and implementation are compiled.**

It replaces the older NodeSpec-centered birth model. Product-specific meaning remains with the product's semantic owner; organization-wide vocabulary, topology law, contracts, invariants, archetypes, patterns, lifecycle, conformance, and compilation semantics live upstream here.

## Why it exists

L9 has many products with different purposes: State, Memory, Evidence, Ingest, Communication, reasoning capabilities, governance systems, CI systems, SDKs, and future products not yet designed.

Without a common topology, each repository can independently invent answers to the same architectural questions:

- What kind of product is this?
- Who owns its semantics?
- What capability does it provide?
- What is inside and outside its boundary?
- Is it invoked remotely or composed locally?
- Is it independently deployed or installed into a consumer?
- Which contracts, ports, adapters, providers, and other L9 products may it use?
- Which identity is the product, runtime, actor, or execution surface?
- Which governance profile applies?
- What must be proven before the product or release is admitted?
- Which decisions are authoritative and which are compiler-derived?

Independent answers create semantic drift. Drift then propagates into templates, bootstrap, runtime behavior, memory, receipts, observability, CI, and downstream agents.

This foundation moves those recurring architectural decisions upstream and makes them mechanically resolvable.

## Objective

The objective is to make L9 product architecture **declarative, composable, deterministic, auditable, and compilable**.

A downstream architect should be able to define a product through authoritative topology and have L9 machinery derive the architecture obligations that follow from it instead of repeatedly redesigning common infrastructure and semantics by hand.

The intended end state is:

```text
Product intent and owned semantics
        ↓
Authoritative ProductTopology
        ↓
ProductKind + Archetype law
        ↓
Requirement / capability / contract closure
        ↓
Architecture patterns
        ↓
Ports / adapters / relationships
        ↓
Technology and provider bindings
        ↓
Conformance closure
        ↓
ProductManifest
        ↓
Implementation IR
        ↓
Target artifacts
        ↓
Admission evidence
```

The compiler implements decisions. It does not invent product meaning.

## The universal ProductTopology concept

Every L9 product is described through the same topology vocabulary. Product kind changes the obligations and admissible relationships, not the language used to describe the product.

The topology covers these major dimensions:

```text
ProductTopology
├── product
│   ├── id
│   ├── kind
│   └── archetype
├── identity
├── purpose
├── boundary
├── requirements
├── capabilities
├── consumption
├── deployment
├── architecture
├── contracts
├── interfaces
├── ports
├── adapters
├── relationships
├── bindings
├── providers
├── technology
├── state
├── runtime
├── communication
├── security
├── configuration
├── effects
├── receipts
├── failure
├── recovery
├── observability
├── governance
├── admission
├── lifecycle
├── conformance
├── compatibility
├── distribution
├── build
├── operations
├── provenance
└── unknowns
```

Not every coordinate is applicable to every product. Applicability is resolved by ProductKind, archetype, canonical contracts, and architecture law. A missing concept is not silently guessed; material unresolved semantics remain explicit Unknowns and can block compilation or admission.

## ProductKind

`ProductKind` answers a foundational question:

> **How is this product consumed and deployed?**

Two kinds are admitted in v3.5.0.

### Node

A Node is consumed through **remote invocation** and has an **independent runtime**.

```text
Consumer
   ↓
canonical L9 communication
   ↓
Node
   ↓
ports / adapters
   ↓
providers and tools
```

A Node is independently deployed, independently addressable through the admitted Constellation path, and owns a governed capability boundary. Consumers invoke the Node rather than installing its implementation.

### Dependency

A Dependency is consumed through **local composition** and is a **consumer-bound artifact**.

```text
Consumer runtime
┌──────────────────────────────┐
│ Consumer                     │
│    ↓                         │
│ Installed L9 Dependency      │
│    ↓                         │
│ ports / adapters / providers │
└──────────────────────────────┘
```

A Dependency may own substantial semantics, ports, adapters, receipts, persistence, policy, and provider integrations. Complexity does not make it a Node. Its defining characteristic is that the consumer installs and composes it rather than remotely addressing it as an independent Constellation participant.

### SDK

SDK is intentionally **not admitted as a ProductKind in this release**. Gate_SDK and l9-ci-sdk demonstrate that SDKs require their own architecture analysis before a canonical kind definition is safe. v3.5.0 preserves that Unknown rather than forcing SDKs into Node or Dependency semantics.

## Archetypes

ProductKind establishes the participation model. An archetype specializes architecture inside that kind.

The catalogs are deliberately separate:

```text
semantics/node_archetypes.yaml
semantics/dependency_archetypes.yaml
```

This prevents the older category collision where Dependency shapes and cross-cutting patterns appeared inside a Node archetype catalog.

Archetypes do not own domain semantics. They contribute reusable architectural obligations to a product whose semantic owner remains authoritative for the capability itself.

## Identity is topology

v3.5.0 makes identity a first-class topology primitive because identity affects bootstrap, authorization context, memory authorship, receipts, governance, observability, and provenance.

The foundation distinguishes:

```text
ProductIdentity
ReleaseIdentity
RuntimeIdentity
ConstellationIdentity
ActorIdentity
SurfaceIdentity
```

It also defines:

```text
IdentityBinding
IdentityResolution
IdentityAssertion
GovernanceProfile
```

These concepts are intentionally not aliases.

For example, a governance profile may select policy for a Claude execution surface while the ActorIdentity identifies the actual admitted writer. Equal or similar strings do not collapse identity dimensions.

The runtime model is:

```text
raw runtime evidence
        ↓
IdentityResolution
        ↓
IdentityAssertion
   ├── product
   ├── release/runtime
   ├── actor
   ├── surface
   └── provenance
        ↓
bootstrap / governance / memory / receipts / observability
```

Identity is resolved once through the canonical contract. Downstream consumers must consume a valid assertion rather than independently re-deriving identity from environment markers.

Consequential unknown or ambiguous actor identity fails closed.

`GovernanceProfile` remains separate. Governance answers which policy applies; ActorIdentity answers who performed the operation.

## Contracts, not Specs

The old `NodeSpec` concept is removed from the product birth path.

L9 now uses authoritative contracts and topology:

```text
canonical semantics + ProductTopology
        ↓
resolution / compilation
        ↓
ProductManifest
```

There is no parallel NodeSpec ledger that restates product intent.

Schemas validate structural shape. They do not become a second semantic authority.

## ProductManifest

`ProductTopology` and `ProductManifest` have deliberately different authority roles.

### ProductTopology

Authoritative product contract.

It contains declared product decisions and references canonical upstream law.

### ProductManifest

Derived, proof-carrying realization closure.

It records the exact resolved requirements, architecture, ports, bindings, providers, conformance coordinates, compiler coordinates, provenance, and unresolved material Unknowns for a particular realization.

```text
ProductTopology = what the product is required to be
ProductManifest = what exact realization was resolved and proven
```

A ProductManifest cannot rewrite its ProductTopology source.

## How downstream repositories consume this foundation

A downstream product should not copy these semantics into its own repository and mutate them locally.

It should:

1. **Identify its semantic owner and purpose.** Define the capability and the boundary it actually owns.
2. **Declare ProductTopology.** Bind `product.id`, admitted `kind`, archetype, identity architecture, purpose, boundaries, capabilities, hard contracts/invariants, consumption/deployment requirements, relationships, and genuine technology constraints.
3. **Reference upstream coordinates.** Reuse canonical capabilities, contracts, invariants, patterns, ports, lifecycle, conformance, identity, receipt, and admission semantics from this foundation instead of redefining them.
4. **Compile and resolve.** Allow the semantic compiler to derive applicable requirements, architecture patterns, ports, adapter obligations, bindings, provider constraints, conformance closure, and other permitted derived decisions.
5. **Produce ProductManifest.** Bind the exact source topology, compiler/profile coordinates, resolved architecture, provenance, and evidence requirements.
6. **Build against the resolved contract.** Implementation machinery lowers the admitted architecture rather than rediscovering it.
7. **Conform and admit.** Tests and evidence prove that the exact realization satisfies the topology and resolved manifest before it is treated as an admitted L9 product/release/runtime.

The direction is always:

```text
.github semantic authority
        ↓
product-owned topology
        ↓
derived realization
        ↓
implementation
```

Never the reverse.

## What this enables downstream

This foundation is intended to enable several compounding capabilities.

### Deterministic product birth

A new product can start from purpose and consumption/deployment requirements, resolve a ProductKind and archetype, and inherit the correct architectural obligations without copying another repository and hoping its assumptions apply.

### Consistent Node construction

Nodes share one meaning of remote invocation, independent runtime, canonical communication, runtime identity, health/readiness, admission, and product relationships while retaining their own domain semantics.

### Consistent Dependency construction

Dependencies share one meaning of installability, local composition, consumer-bound lifecycle, public contract, provider isolation, identity/binding, and conformance without being forced into Node mechanics.

### Provider substitution without semantic drift

Ports describe owner-required behavior. Adapters realize ports. Providers supply mechanisms. Provider replacement cannot silently redefine the product capability.

### Upstream drift prevention

Recurring concepts such as identity, admission, lifecycle, receipts, failure semantics, and product relationships have one canonical vocabulary instead of being independently reinvented by bootstrap, memory, CI, templates, and runtime repositories.

### Compiler-driven architecture

The semantic compiler can reason over explicit topology rather than prose and repository folklore. It can detect incompatible kinds, missing contracts, invalid relationships, unresolved ports, forbidden provider leakage, and material Unknowns before implementation.

### Evidence-backed admission

Admission can bind an exact product/release/runtime realization to its topology, manifest, provenance, conformance, and evidence instead of treating repository existence or successful deployment as proof of correctness.

### Portable identity

Bootstrap, governance, memory, receipts, evidence, and observability can consume the same typed IdentityAssertion rather than each deriving a different answer to "who is this?"

### Safer evolution

Because authoritative topology and derived realization are separate, L9 can distinguish semantic changes from implementation changes, invalidate only affected derivations, and preserve provenance across supersession.

## Architectural laws to preserve

Downstream consumers should preserve these principles:

- Product purpose determines the needed capability.
- Consumption and deployment requirements determine ProductKind.
- ProductKind and archetype determine reusable architecture obligations.
- ProductKind is not inferred from repository shape, package format, provider, complexity, or the existence of a process.
- Semantic ownership remains with the declared product owner.
- Ports use owner vocabulary rather than provider vocabulary.
- Adapters translate boundaries; they do not acquire semantic ownership.
- Providers supply mechanisms; they do not define product meaning.
- Identity dimensions remain semantically distinct.
- Runtime identity is resolved once and propagated through IdentityAssertion.
- Governance profile is policy selection, not authorship identity.
- Material Unknowns remain explicit and may block compilation/admission.
- Derived manifests and generated artifacts never become semantic authority.
- The compiler implements authoritative decisions; it does not decide what the product should mean.

## North-star example: State

State demonstrates the intended leverage.

```yaml
product:
  id: l9.state
  kind: node
  archetype: authoritative_state

purpose:
  capability_refs:
    - l9.capability/state

consumption:
  model: remote_invocation

deployment:
  model: independent_runtime
```

Those declarations lead to Node obligations such as an independent runtime boundary and canonical Constellation interaction. State-owned contracts then define revision, idempotency, fencing, receipts, journal semantics, and other domain requirements. Ports express required persistence behavior. A Mongo adapter may satisfy those ports, but Mongo never becomes the owner of State semantics.

```text
Constellation
    ↓
l9-state
    ↓
State domain/service
    ↓
StateStorePort
    ↓
Mongo adapter
    ↓
MongoDB
```

The same ProductTopology vocabulary can describe a Dependency such as governed Memory while changing the consumption and deployment coordinates rather than inventing a second architecture language.

## Scope of v3.5.0

This release intentionally establishes:

- ProductTopology as the universal authoritative product contract;
- ProductManifest as the derived proof-carrying realization;
- admitted Node and Dependency ProductKinds;
- separate Node and Dependency archetype catalogs;
- product-general compilation semantics;
- identity as a first-class topology primitive;
- typed identity resolution/assertion semantics;
- separation of governance profile from actor identity;
- explicit Unknown handling;
- removal of the unmerged NodeSpec/NodeManifest candidate path.

It intentionally does **not** canonize SDK ProductKind semantics. That work remains pending the Gate_SDK versus l9-ci-sdk architecture convergence.

## Intended organizational role

This package belongs upstream in `Quantum-L9/.github` because its semantics apply across repositories.

Individual products should own their product-specific meaning. `.github` should own the common language and laws that let those products compose coherently.

The goal is **one semantic brain, many products**.

A downstream repository should become thinner as this foundation becomes stronger: less duplicated architecture law, fewer local identity tables, fewer hand-maintained conventions, and more explicit references to canonical upstream coordinates.

## Release contents and validation

See:

- `MANIFEST.md` for package inventory and provenance;
- `RELEASE_VALIDATION.md` for validation results;
- `semantics/` for canonical semantic artifacts;
- `docs/adr/` for the architecture decisions that produced this foundation;
- `HASHES.sha256` for package integrity.
