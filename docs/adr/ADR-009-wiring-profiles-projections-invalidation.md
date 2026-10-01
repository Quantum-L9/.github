# ADR-009: Contracts are wired through profiles, projections, IRs, and dependency law

Status: Accepted

## Decision
Global contracts live in `contracts.yaml`. Canonical model files declare governing contract IDs. `compilation_profiles.yaml` binds contracts and solvers to build stages. `projection_profiles.yaml` supplies each stage/consumer only the required semantic surface. `ir_catalog.yaml` defines legal semantic representations and transitions. `semantic_dependency_model.yaml` defines invalidation and surgical recompilation.

## Consequences
- No consumer chooses arbitrary global law.
- A material upstream change produces a mechanically discoverable affected closure.
- ProductManifest records exact governing coordinates.
- Downstream repositories reference domain contracts in addition to inherited global contracts; global law is not copied into each repo.
