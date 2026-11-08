# GMP-131

**Task:** Build r4 plan: admit implementation coordinate (Codex P1 on #217)
**Tier:** RUNTIME

## TODOs

- T1: semantics/product_manifest.schema.yaml INSERT Add optional `interfaces` and `effects` object properties and their preservation / implementation-input rules to the ProductManifest schema
- T2: semantics/binding_catalog.yaml INSERT Admit target binding l9.binding/python-gate-node@1 (implementation_ir -> target_ir, technology python, Gate SDK transport) with maps and fail-closed rules
- T3: docs/adr/ADR-025-manifest-interface-surface-and-python-gate-node-binding.md INSERT ADR-025 recording the decision, options and non-goals
- T4: docs/adr/README.md INSERT Index ADR-025
- T5: docs/semantic-foundation/v3.29.0/README.md INSERT v3.29.0 release record README
- T6: docs/semantic-foundation/v3.29.0/MANIFEST.md INSERT v3.29.0 release record MANIFEST
- T7: docs/semantic-foundation/v3.29.0/RELEASE_VALIDATION.md INSERT v3.29.0 release validation record
- T8: docs/semantic-foundation/v3.29.0/HASHES.sha256 INSERT v3.29.0 release hash inventory
- T9: semantics/product_topology.schema.yaml INSERT Admit port and adapter entry shapes (the compiler-enforced port/adapter law) and the optional `implementation_ref` source coordinate in the ProductTopology schema (Codex P1 on
