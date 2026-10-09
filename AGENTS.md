# Agents

`semantics/` is the Semantic Foundation. Its current release record is the
highest version directory under `docs/semantic-foundation/`; `make validate`
checks the ledgers against that record. `Quantum-L9/.github`
owns this language. A domain repository owns the meaning of its own capability. Read the
ledger below for a decision that is already global. Cite its `artifact_id`.
Do not copy this tree into a product repository.

**ProductTopology** is the product contract
(`semantics/product_topology.schema.yaml`). **ProductManifest** is the derived
realization of one topology (`semantics/product_manifest.schema.yaml`). A
manifest records what was resolved. Schemas check shape. The compiler carries
out decisions recorded in these ledgers (`semantics/compiler_contract.yaml`).

v3.5.0 admits two ProductKinds in `semantics/product_kinds.yaml`. A Node is
remote invocation with an independent runtime. A Dependency is installed and
composed inside a consumer. SDK is not an admitted kind. Kind follows
consumption and deployment. Archetypes specialize a kind:
`semantics/node_archetypes.yaml` and `semantics/dependency_archetypes.yaml`.

Identity dimensions stay distinct in `semantics/identity_model.yaml`.
Downstream work consumes an assertion that matches
`semantics/identity_assertion.schema.yaml`. GovernanceProfile selects policy.
ActorIdentity names who acted. The canonical ActorIdentity IDs and their typed
historical aliases are `semantics/actor_registry.yaml`; the canonical
SurfaceIdentity IDs and their typed historical aliases are
`semantics/surface_registry.yaml`. The registries name identity only: runtime
evidence resolution remains downstream, the registries do not bind
ActorIdentity to SurfaceIdentity, and they do not select GovernanceProfile.

`semantics/canonical_sources.yaml` is the source registry. A registered source
names its path and whether derivation is allowed. Global contracts live only
in `semantics/contracts.yaml`. The decisions are the accepted records in
`docs/adr/`, indexed by `docs/adr/README.md`. The release record is the highest
version directory under `docs/semantic-foundation/`.

Add a ledger here only when it retires a decision that would otherwise be
remade in every product (ADR-010). Register it in
`semantics/canonical_sources.yaml`. Leave a material Unknown explicit.

The same repository still runs the organization governance, control, and
distribution plane. That plane does not own product meaning. Its map is
`README.md`.

## Language and authority

| File | What it decides |
| --- | --- |
| `semantics/canonical_sources.yaml` | Which ledgers are registered, and whether each may be projected or derived |
| `semantics/vocabulary.yaml` | Global terms |
| `semantics/authority_model.yaml` | Who may admit global law, and which classes of artifact can grant authority |
| `semantics/contracts.yaml` | The single global contract catalog |
| `semantics/invariants.yaml` | Global invariants |
| `semantics/artifact_model.yaml` | What kinds of artifact exist and how they relate to authority |

## Product contract

| File | What it decides |
| --- | --- |
| `semantics/product_topology.schema.yaml` | Shape of the authoritative product contract |
| `semantics/product_kinds.yaml` | Admitted kinds and how kind is determined |
| `semantics/node_archetypes.yaml` | Architecture obligations for a Node |
| `semantics/dependency_archetypes.yaml` | Architecture obligations for a Dependency |
| `semantics/identity_model.yaml` | Identity dimensions and resolution |
| `semantics/identity_assertion.schema.yaml` | Shape of a resolved identity assertion |
| `semantics/actor_registry.yaml` | Canonical ActorIdentity IDs and typed historical aliases |
| `semantics/surface_registry.yaml` | Canonical SurfaceIdentity IDs and typed historical aliases |
| `semantics/product_manifest.schema.yaml` | Shape of a derived realization |

## Resolution

| File | What it decides |
| --- | --- |
| `semantics/requirement_model.yaml` | How requirements are stated and closed |
| `semantics/resolution_model.yaml` | How a requirement becomes a resolved decision |
| `semantics/capabilities.yaml` | Global capability coordinates |
| `semantics/capability_resolution.yaml` | How a capability resolves to architecture |
| `semantics/semantic_dependency_model.yaml` | Which semantic artifacts depend on which |
| `semantics/selector_model.yaml` | Deterministic selectors used when projecting a ledger |

## Architecture

| File | What it decides |
| --- | --- |
| `semantics/architecture_rules.yaml` | Architecture law applied after resolution |
| `semantics/architecture_patterns.yaml` | Reusable architecture patterns |
| `semantics/port_catalog.yaml` | Ports, in owner vocabulary |
| `semantics/packet_catalog.yaml` | Bounded packets that carry candidates and do not create authority |

## Compiler

| File | What it decides |
| --- | --- |
| `semantics/compiler_contract.yaml` | The generic compiler: inputs, operations, and what it may not invent |
| `semantics/compiler_passes.yaml` | Ordered compiler passes |
| `semantics/compiler_receipt.schema.yaml` | Shape of a compiler receipt |
| `semantics/generic_compiler_manifest.yaml` | Manifest of the generic compiler itself |
| `semantics/compilation_profiles.yaml` | Compilation profiles the compiler may apply |
| `semantics/composition_engine_contract.yaml` | Contract for composition |
| `semantics/composition_profiles.yaml` | Composition profiles |
| `semantics/derivation_profiles.yaml` | Derivation profiles, including law-to-fixture |
| `semantics/projection_engine_contract.yaml` | Contract for projection |
| `semantics/projection_profiles.yaml` | Projection profiles |
| `semantics/projection_artifact.schema.yaml` | Shape of a projection artifact |
| `semantics/composed_projection.schema.yaml` | Shape of a composed projection |
| `semantics/ir_catalog.yaml` | Implementation IR kinds |
| `semantics/solver_catalog.yaml` | Solvers the compiler may call |

## Technology

| File | What it decides |
| --- | --- |
| `semantics/binding_catalog.yaml` | Bindings from a resolved port to a technology |
| `semantics/technology_capabilities.yaml` | What a technology can supply |
| `semantics/technology_profiles.yaml` | Technology profiles applied after semantic resolution |

## Evidence

| File | What it decides |
| --- | --- |
| `semantics/conformance_model.yaml` | What must be proven for a realization |
| `semantics/lifecycle.yaml` | Lifecycle coordinates |
| `semantics/receipt_catalog.yaml` | Receipt kinds |
| `semantics/error_taxonomy.yaml` | Error classes |

<!-- BEGIN L9 FORMATTER OWNERSHIP (generated — do not edit) -->

## Formatter ownership

Workspace class: `biome_default` — Default for every governed workspace: Biome owns JS/TS/JSON, VS Code JSON language features owns JSONC (the Biome extension cannot format jsonc), Ruff owns Python, Prettier owns Markdown (format-on-save off so governance docs do not churn).

Exactly one formatter owns each language. Do not reformat a file with a tool other than its owner, and do not add config for a competing formatter: the result is a diff that churns on every save.

| Languages | Owner | Note |
|---|---|---|
| `javascript`, `javascriptreact`, `typescript`, `typescriptreact`, `json` | **biome** | bound by the governed IDE profile |
| `jsonc` | **vscode-json** | bound by the governed IDE profile |
| `python` | **ruff** | bound by the governed IDE profile |
| `markdown` | **prettier** | bound by the governed IDE profile |

Generated from `environment/ide/policy.json` in the governance clone by `ops/scripts/adapters/agentdocs.sh`. Edit the policy, not this block.

<!-- END L9 FORMATTER OWNERSHIP -->
