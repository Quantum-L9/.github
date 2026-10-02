
L9 Contract Authoring Templates

This directory contains reusable authoring scaffolds for L9-owned semantic artifacts.

These templates are not canonical semantic authority.

Canonical shared L9 semantics are owned upstream by:

Quantum-L9/.github/semantics

Product-, domain-, repository-, and workflow-specific meaning remains owned by the applicable scoped semantic owner.

Templates

product-topology.yaml

Blank authoring scaffold for a ProductTopology conforming to:

l9.schema/product-topology@1

The schema coordinate is canonical upstream.

A specialized ProductTopology is a candidate until admitted under its applicable authority and lifecycle.

repository-spec.yaml

Candidate authoring scaffold for repository-scoped semantics.

No admitted global RepositorySpec schema coordinate is assumed by this template.

The template MUST NOT be treated as an independent source of global L9 semantic law.

workflow-spec.yaml

Candidate authoring scaffold for workflow-scoped semantics.

No admitted global WorkflowSpec schema coordinate is assumed by this template.

The template deliberately does not prescribe compiler-specific, CI-specific, agent-specific, provider-specific, or runtime-specific workflow behavior.

Authority Boundary

The templates follow this ownership model:

Quantum-L9/.github/semantics
        shared global L9 semantics
                    │
                    ▼
           scoped semantic owner
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   ProductTopology       other scoped inputs
          │                   │
          ├──────► RepositorySpec
          │              when applicable
          │
          └──────► WorkflowSpec
                 when applicable
                         │
                         ▼
                derived projections

This diagram does not require every repository to have every artifact and does not require every workflow to depend on a RepositorySpec.

Dependencies MUST be explicit in the specialized artifact.

Authoring Rules

An agent or human specializing these templates MUST:

1. Resolve the applicable canonical semantics from Quantum-L9/.github/semantics.
2. Resolve the applicable product-, domain-, repository-, and workflow-owned semantics from their actual authoritative owners.
3. Bind exact semantic coordinates where the governing contract requires revision- or digest-bound identity.
4. Use admitted canonical terminology when canonical terminology exists.
5. Preserve Unknown, unresolved, and ambiguous states instead of guessing.
6. Never treat a blank, null, or empty template value as an implicit semantic default.
7. Never copy global semantic law into a scoped artifact merely to make that artifact appear self-contained.
8. Never let a generated or projected artifact become an independent semantic authority.
9. Re-evaluate affected derived artifacts when a material governing semantic dependency changes.
10. Keep provider, implementation, repository layout, tooling, and runtime choices separate from semantic identity unless canonical semantics explicitly bind them.

Blank-Value Semantics

In these templates:

null
[]
{}

mean:

not yet resolved or not yet declared

They do not mean:

false
disabled
none by policy
not applicable
default
approved

A specialized artifact MUST distinguish an intentionally empty value from an unresolved value whenever that distinction is material under its governing schema or contracts.

ProductTopology Rule

product-topology.yaml is schema-backed.

Its schema defines the available topology vocabulary.

The template therefore does not pre-select:

* ProductKind
* archetype
* provider policy
* deployment model
* consumption model
* lifecycle family
* conformance policy
* admission authority
* architecture patterns
* implementation technology
* repository layout
* compiler profile

Those values are resolved by the applicable authorities and product semantics.

RepositorySpec Rule

A RepositorySpec may describe repository-scoped facts such as:

* repository identity
* repository responsibility
* source and generated surfaces
* repository structure
* validation entry points
* projection inputs and outputs
* repository-scoped ownership
* provenance

It MUST NOT independently redefine product meaning already owned by an admitted ProductTopology or shared meaning already owned by canonical L9 semantics.

Until a canonical RepositorySpec model/schema is admitted upstream, this template remains candidate authoring scaffolding.

WorkflowSpec Rule

A WorkflowSpec may describe workflow-scoped facts such as:

* workflow identity and purpose
* authority roles
* inputs and preconditions
* states and transitions
* passes or steps
* failure and recovery behavior
* security requirements
* outputs
* receipts
* validation
* provenance
* material Unknowns

The template does not assume that every workflow:

* is a compiler;
* is deterministic;
* performs incremental compilation;
* has a NO_CHANGE outcome;
* produces projections;
* performs conformance;
* runs offline;
* forbids network access;
* forbids LLM use;
* has filesystem output paths;
* has budget or deadline transitions;
* emits a particular receipt type.

Those are scoped workflow requirements when applicable, not universal template defaults.

Publication Rule

Do not describe a specialized artifact as canonical merely because it was created from one of these templates.

Canonicality, admission, publication, authority, and currentness are governed by their applicable semantic and lifecycle contracts.

Conflict Rule

If any template structure conflicts with current admitted canonical semantics, the admitted semantics win.

Do not make canonical semantics fit the template.

Correct or supersede the template instead.
