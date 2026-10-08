# Semantic Foundation Manifest v3.15.0

Release status: **ADDITIVE SUCCESSOR CANDIDATE**

## Install surface

The release contains **50** canonical semantic YAML files:
- `semantics/actor_registry.yaml`
- `semantics/architecture_patterns.yaml`
- `semantics/architecture_rules.yaml`
- `semantics/artifact_model.yaml`
- `semantics/authority_model.yaml`
- `semantics/binding_catalog.yaml`
- `semantics/canonical_sources.yaml`
- `semantics/capabilities.yaml`
- `semantics/capability_resolution.yaml`
- `semantics/compilation_profiles.yaml`
- `semantics/compiler_contract.yaml`
- `semantics/compiler_passes.yaml`
- `semantics/compiler_receipt.schema.yaml`
- `semantics/composed_projection.schema.yaml`
- `semantics/composition_engine_contract.yaml`
- `semantics/composition_profiles.yaml`
- `semantics/conformance_model.yaml`
- `semantics/contracts.yaml`
- `semantics/dependency_archetypes.yaml`
- `semantics/derivation_profiles.yaml`
- `semantics/error_taxonomy.yaml`
- `semantics/generic_compiler_manifest.yaml`
- `semantics/identity_assertion.schema.yaml`
- `semantics/identity_model.yaml`
- `semantics/invariants.yaml`
- `semantics/ir_catalog.yaml`
- `semantics/lifecycle.yaml`
- `semantics/node_archetypes.yaml`
- `semantics/packet_catalog.yaml`
- `semantics/port_catalog.yaml`
- `semantics/product_kinds.yaml`
- `semantics/product_manifest.schema.yaml`
- `semantics/product_topology.schema.yaml`
- `semantics/projection_artifact.schema.yaml`
- `semantics/projection_engine_contract.yaml`
- `semantics/projection_profiles.yaml`
- `semantics/receipt_catalog.yaml`
- `semantics/repository_classes.yaml`
- `semantics/repository_registry.yaml`
- `semantics/requirement_model.yaml`
- `semantics/resolution_model.yaml`
- `semantics/selector_model.yaml`
- `semantics/semantic_dependency_model.yaml`
- `semantics/solver_catalog.yaml`
- `semantics/strategic_cognition_model.yaml`
- `semantics/strategic_plan_model.yaml`
- `semantics/surface_registry.yaml`
- `semantics/technology_capabilities.yaml`
- `semantics/technology_profiles.yaml`
- `semantics/vocabulary.yaml`

The inventory is unchanged from v3.14.0: no ledger is added or removed. Two previously registered placeholder ledgers now carry admitted content.

## Architecture decision records

The release contains **15** accepted ADRs plus the ADR index under `docs/adr/`.

v3.15.0 adds no ADR. The canonical ledgers `semantics/repository_classes.yaml` and `semantics/repository_registry.yaml` were registered in v3.6.0 as the owners of repository class and repository identity; this release records the admission decision inside the ledgers that own the question (ADR-001, ADR-010).

## Repository class admission and registry population

v3.15.0 makes a semantic change to two canonical ledgers and no mechanical digest refresh:

- `semantics/repository_classes.yaml`: admits exactly one RepositoryClass, `l9.repository-class/l9@1` (`status: current`, `organization_membership: l9`), with exactly three obligations (`canonical_authority_consumption`, `projection`, `memory`) and nine prohibitions. Its projection obligation requires derived authority, no manual edit of a generated projection, source coordinate, source digest, provenance, no silent stale consumption and no authority expansion; it names no projection profile and no compiler receipt, because `l9.contract/projection@1` owns whether a derived view uses a profile or a selector contract. Its memory obligation is `namespace: l9`, `membership: required`, `membership_source: resolved_repository_class`, `content_selection_owned_by_memory_plane: true`, `content_authority_remains_with_source_repository: true`, `memory_representation_authority_class: derived`, `consumer_may_not_independently_add_or_remove_members: true`. One derived view, `l9.repository-view/memory-namespace-l9@1`, selects `class_ref: l9.repository-class/l9@1` over `lifecycle_in: [current, superseded, retired]` and outputs `namespace: l9`, `authority_class: derived`, preserving `id`, `coordinate`, `lifecycle`, `class_ref`, with no consumer membership expansion or removal. `catalog_status.admitted_classes` is exactly `[l9.repository-class/l9@1]`.
- `semantics/repository_registry.yaml`: admits exactly 32 repositories, every one `provider: github`, `organization: Quantum-L9`, `lifecycle: current`, `class_ref: l9.repository-class/l9@1`, in registry order: `dot-github` (`.github`), `cursor-governance` (`Cursor-Governance`), `igorbot` (`igorbot`), `seo-bot` (`SEO-Bot`), `website-bot` (`Website-Bot`), `l9-original-repo` (`L9_Original_Repo`), `l9-assurance`, `l9-ci-core`, `l9-ci-debt-intelligence`, `l9-ci-debt-lsp`, `l9-ci-debt-resolver`, `l9-ci-sdk`, `l9-codegen`, `l9-cognitive-runtime`, `l9-constellation-ingest`, `l9-constellation-topology`, `l9-dependency-template`, `l9-deploy`, `l9-devpack-compiler`, `l9-goose`, `l9-graphiti-memory`, `l9-harness`, `l9-meta-injector`, `l9-node-chain-of-search`, `l9-node-template`, `l9-observability-core`, `l9-ops-mcp` (`L9-Ops-MCP`), `l9-pr-repair`, `l9-prompt-generator` (`L9-Prompt-Generator`), `l9-repo-template`, `l9-semantic-compiler-engine`, `l9-wip`. Where no coordinate is shown the GitHub repository name equals the registry id. `aliases` is empty.

Neither ledger is a derivation source of any other ledger, so `capabilities.yaml`, `lifecycle.yaml`, `receipt_catalog.yaml` and `contracts.yaml` are unchanged. `semantics/canonical_sources.yaml`, `semantics/generic_compiler_manifest.yaml` and `semantics/projection_profiles.yaml` already registered and classified both ledgers and are unchanged.

The release also adds RC-023 to `scripts/validate-semantics.py`, together with its negative-case batch, which fails closed.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.14.0/`, which is unchanged.
