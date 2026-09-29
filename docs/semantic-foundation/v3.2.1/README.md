# Quantum-L9/.github Semantic Foundation v3.2.1

Status: **ACTIVE / CANONICAL**

This package extends the v3.1.0 L9 semantic foundation with the formal node-birth layer required to compile new nodes from minimal declarative intent.

v3.2.1 supersedes the unmerged v3.2.0 candidate. The v3.2.0 candidate was syntactically valid but not internally closed; v3.2.1 changes canonical semantic bytes to close it. See [Changes from the v3.2.0 candidate](#changes-from-the-v320-candidate).

## Node-birth architecture

```text
NodeSpec
  -> Requirement Closure
  -> Semantic Resolution
  -> Contracts / Laws / Fixtures
  -> Architecture / Ports
  -> Provider Bindings
  -> Conformance Requirements
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

## Changes from the v3.2.0 candidate

| Repair | Change |
| --- | --- |
| F146-01 | Stage and IR-transition operations reference only admitted compiler passes (`compiler_passes.yaml`). Drifted operation words are contracted per the locked mapping: `normalization` and `compilation` are stage-local mechanics / umbrella activity, `formalization` and `fixture_case_expansion` are `derivation`, `constraint_solving` and `pattern_resolution` are `resolution` (or stage validation), `pattern_composition` is `synthesis`, `compatibility_analysis` is `binding_selection` plus stage validation, `composition` is `derivation`. |
| F146-02 | `node-build@2` orders stages `node_spec → global_baseline → requirement_resolution → semantic_resolution → project_contracts → laws → fixtures → architecture → ports → provider_bindings → conformance → node_manifest → implementation → target_artifacts`. The conformance stage now consumes the resolved architecture, ports, and provider bindings its model declares; the dependency model records the conformance → provider-binding dependency. |
| F146-03 | `provider_bindings` is the sole stage identity. The drifted `technology_bindings` stage, derivation input, manifest field, gate, and dependency node use the canonical identity. The `l9.contract/technology-binding@1` contract ID is unchanged. |
| F146-04 | `node-build@1` references the registered canonical solvers instead of unresolvable legacy `l9.solver/...` IDs. |
| F146-05 | `NodeManifest` requires `manifest_digest`, as both artifact models already did. The compiler-receipt operation enum can receipt the admitted `resolution` pass. |
| F146-06 | `ops/validate-semantic-foundation.py` mechanically verifies closure; `ops/test-validate-semantic-foundation.py` proves it fails closed. |
| F146-07 | Release identity is v3.2.1; hashes, manifest, and release validation are regenerated. |

## Validation

```bash
python3 ops/validate-semantic-foundation.py
python3 ops/test-validate-semantic-foundation.py
sha256sum -c docs/semantic-foundation/v3.2.1/HASHES.sha256   # from the repository root
```

Both scripts also run inside `ops/validate-starters.sh` (`make validate`).
