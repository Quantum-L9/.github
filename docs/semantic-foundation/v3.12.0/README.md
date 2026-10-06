# Semantic Foundation v3.12.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor admits Graphiti MCP and Zep as concrete L9 technology/provider realizations. It does not transfer semantic ownership to either one, and it does not authorize any product to use them.

It closes one upstream semantic prerequisite: the canonical technology catalog did not register either provider, so a product binding that names them had to stay `unregistered_technology`. That is the material Unknown MU-002 in the `Quantum-L9/l9-graphiti-memory` ProductTopology.

## Bounded delta

- Adds exactly two technology registrations to `semantics/technology_capabilities.yaml`: `graphiti-mcp` and `zep`. Both use the existing `datastore` class and the existing `persistence_provider` target role. Both state explicit technology-level capability claims (`graph_episode_storage`, `graph_search`, `episode_deletion_by_locator`) and `semantic_ownership.implied: false`.
- Adds RC-020 to `scripts/validate-semantics.py`. RC-020 is a closure check for these two exact coordinates, with a negative-case batch that fails closed. It defines no provider family by name. It applies no rule to any other technology and does not cap how many technologies the catalog may hold.

## Non-goals

v3.12.0 adds no technology class, target-role system, capability vocabulary term outside the technology catalog, schema, ledger, invariant, contract, projection profile, or ADR. It does not change provider-binding semantics, the compiler, the ProductManifest or ProductTopology schemas, or `technology_profiles.yaml`. It does not resolve MU-001 (the missing conformance profile for `dependency` / `semantic-subsystem`), which `l9-conformance` owns. It does not modify `Quantum-L9/l9-graphiti-memory`. Moving that product's provider bindings from `unknown` to these coordinates is separate downstream work.

## Authority

`Quantum-L9/.github` owns the technology catalog and these two coordinates. `Quantum-L9/l9-graphiti-memory` keeps ownership of its memory architecture, its provider-neutral projection port, and every memory semantic: admission, canonical persistence, lifecycle, curation, retrieval, receipts, and MemoryService semantics. Technology identity does not imply semantic ownership, and registration does not authorize use (`technology_capabilities.yaml#global_rules`).

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.11.0/` (Cursor-Governance identity projection profile). That release record is unchanged.
