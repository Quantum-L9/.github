# Quantum-L9/.github Semantic Foundation v3.2.0

Status: **ACTIVE / CANONICAL / RELEASE-READY**

This package extends the v3.1.0 L9 semantic foundation with the formal node-birth layer required to compile new nodes from minimal declarative intent.

## Node-birth architecture

```text
NodeSpec
  -> Requirement Closure
  -> Semantic Resolution
  -> Contracts / Laws / Conformance
  -> Architecture / Ports
  -> Technology Binding
  -> NodeManifest
  -> Implementation / Target Artifacts
```

## New canonical semantic ledgers

- `node_spec.schema.yaml`
- `requirement_model.yaml`
- `resolution_model.yaml`
- `capability_resolution.yaml`
- `architecture_rules.yaml`
- `port_catalog.yaml`
- `technology_profiles.yaml`
- `conformance_model.yaml`
- `node_manifest.schema.yaml`

Six new global contract families are integrated into the existing single `contracts.yaml` catalog. The architecture is wired through canonical sources, projections, compilation profiles, IRs, solvers, artifact/lifecycle semantics, and the semantic dependency model.

See `docs/adr/` for the accepted architecture decisions.
