# GMP-129

**Task:** Implement operating-plane@2 pack stage upstream: @2 profile, PROJECTION-014 amendment, payload schema, v3.26.0 release record, ADR-023
**Tier:** RUNTIME

## TODOs

- T1: semantics/projection_profiles.yaml REPLACE Add l9.projection/cursor-governance-operating-plane@2 after @1 and amend PROJECTION-014 rule text and global_rules key
- T2: semantics/cursor_governance_operating_plane_v2_projection.schema.yaml REPLACE Add the @2 payload schema and register it
- T2.2: semantics/generic_compiler_manifest.yaml REPLACE Add the @2 payload schema and register it
- T3: docs/adr/ADR-023-operating-plane-v2-major-successor-and-declared-selection-removal.md REPLACE Add ADR-023 and index it
- T3.2: docs/adr/README.md REPLACE Add ADR-023 and index it
- T4: docs/semantic-foundation/v3.26.0/README.md REPLACE Add the v3.26.0 release record with computed install surface, counts and hash inventory
- T4.2: docs/semantic-foundation/v3.26.0/MANIFEST.md REPLACE Add the v3.26.0 release record with computed install surface, counts and hash inventory
- T4.3: docs/semantic-foundation/v3.26.0/RELEASE_VALIDATION.md REPLACE Add the v3.26.0 release record with computed install surface, counts and hash inventory
- T4.4: docs/semantic-foundation/v3.26.0/HASHES.sha256 REPLACE Add the v3.26.0 release record with computed install surface, counts and hash inventory
