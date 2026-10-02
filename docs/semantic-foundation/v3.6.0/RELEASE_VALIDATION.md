# Release Validation v3.6.0

Candidate status: **additive successor candidate**.

This release preserves every v3.5.0 ledger and every mechanically enforced closure property of `docs/semantic-foundation/v3.5.0/RELEASE_VALIDATION.md` (INV-VALIDATION-MONOTONICITY), and adds two canonical identity registries with their own closure check.

## Bounded semantic delta

Added:

- `semantics/actor_registry.yaml` (`l9.actor-registry/global@1`): 6 canonical ActorIdentity IDs (`cursor`, `claude-code`, `codex`, `gemini`, `manus`, `human`), kinds `agent`/`human`, statuses `current`/`superseded`/`retired`, 2 typed historical actor aliases (`claude-code-desktop` → `claude-code`, `claude-code-mobile` → `claude-code`).
- `semantics/surface_registry.yaml` (`l9.surface-registry/global@1`): 11 canonical SurfaceIdentity IDs (`cursor-ide`, `claude-code-desktop`, `claude-code-cli`, `claude-code-ide`, `claude-code-web`, `claude-code-mobile`, `codex-cloud`, `codex-cli`, `gemini-cli`, `manus-cloud`, `operator-shell`), statuses `current`/`superseded`/`retired`, 5 typed historical surface aliases (`claude-desktop`, `claude-cli`, `claude-ide`, `claude-web`, `claude-mobile` → the corresponding `claude-code-*` surface).
- Registration of both in `semantics/canonical_sources.yaml` (`l9.source/actor-registry@1`, `l9.source/surface-registry@1`; `canonical: true`, `projection_allowed: true`, `derivation_allowed: false`) and classification under `generic_compiler_manifest.yaml` `requires.semantic_catalogs`.
- `ADR-013-global-actor-and-surface-identity-registries.md`.
- RC-014 in `scripts/validate-semantics.py`.

Not added: runtime environment resolution policy, Cursor- or Claude-specific marker precedence, credential provisioning, memory implementation, downstream resolver implementation, new identity dimensions, new governance-profile semantics. `identity_model.yaml`, `identity_assertion.schema.yaml`, `contracts.yaml`, `invariants.yaml`, `authority_model.yaml`, and `lifecycle.yaml` are byte-identical to v3.5.0.

## Closure gates carried forward from v3.5.0

- YAML parse and artifact-id uniqueness: PASS
- Single canonical artifact authority (`artifact_model.yaml`): PASS
- Canonical compiler-operation algebra: PASS
- Compiler pass operation closure: PASS
- Receipt operation domain equality: PASS
- Canonical `provider_bindings` stage identity: PASS
- Stage solver identity closure: PASS
- Validation subject is produced by its stage: PASS
- Validation subject is handled by its solver: PASS
- ProductTopology/ProductManifest retained: PASS
- IdentityTopology/IdentityAssertion retained: PASS
- SDK remains unresolved/unadmitted: PASS
- Successor validation monotonicity invariant: PASS
- Release hash integrity: PASS after packaging

## Semantic-foundation closure validator

`scripts/validate-semantics.py` runs inside `make validate`, read-only, fail-closed with file, field, and offending value. Result on the v3.6.0 candidate:

- SC-001 canonical sources parse as YAML mappings (46 files): PASS
- SC-002 `canonical_sources.yaml` ids and paths unique, every path exists (34 registered): PASS
- SC-003 `artifact_id` present and unique across ledgers (46): PASS
- SC-004 `contracts.yaml` derivation matches `invariants.yaml` bytes: PASS
- SC-005 capability model closed; pattern traits are not resolved as capabilities: PASS
- SC-006 every binding technology target is registered: PASS
- SC-007 binding identifiers unique; no binding-ID grammar declared, so grammar conformance is not enforced: PASS
- SC-008 release inventory lists every canonical source (46) and every accepted ADR (13); `HASHES.sha256` (63 entries) matches delivered bytes: PASS
- SC-009 validation is observational (no file written): PASS
- SC-010 unresolved references fail closed: PASS
- RC-001, RC-002, RC-011 derivation provenance (`capabilities.yaml`, `lifecycle.yaml`, `receipt_catalog.yaml`): PASS
- RC-003 every projection profile class resolves to `profile_classes`: PASS
- RC-004 every projection source resolves to `source_classes`: PASS
- RC-005 identity projection shape; stage profiles bind to declared `semantic_build_stages`: PASS
- RC-006 `canonical_sources.yaml` equals the `semantic_catalogs` class of `generic_compiler_manifest.yaml` (34 = 34); every other ledger classified exactly once: PASS
- RC-007 every registered path resolves to a ledger declaring `canonical: true`: PASS
- RC-009 ProductManifest required fields contain no duplicate: PASS
- RC-012 architecture obligations typed as `architecture_obligations`: PASS
- RC-013 `vocabulary.semantic_build_stages` equals the canonical compilation profile on ids, order, ordinals, consumes, operations, produces: PASS

## Identity registry closure (RC-014, new in v3.6.0)

- IR-001 actor registry shape: unique `artifact_id`, `canonical: true`, normalized unique actor IDs, kinds and statuses from the registry's declared vocabularies: PASS
- IR-002 actor aliases: unique keys, every target resolves to one canonical actor, no alias targets an alias, no alias shadows a canonical actor: PASS
- IR-003 surface registry shape: unique `artifact_id`, `canonical: true`, normalized unique surface IDs, statuses from the declared vocabulary: PASS
- IR-004 surface aliases: same closure as IR-002 within SurfaceIdentity: PASS
- IR-005 dimension separation: no `surface_ref`/`governance_profile_ref`/`provider_ref`/`adapter_ref` (actor entries), no `actor_ref`/`governance_profile_ref`/`provider_ref`/`adapter_ref` (surface entries), no credential, key, grant, permission, role, or token field: PASS
- IR-006 typed collision legality: `claude-code-desktop` and `claude-code-mobile` are ActorIdentity aliases and canonical SurfaceIdentity IDs at the same time; accepted, reported, never rejected: PASS
- IR-007 registration closure: both ledgers exist, are registered exactly once in `canonical_sources.yaml`, classified exactly once under `semantic_catalogs`, carry unique artifact IDs, and participate in SC-008: PASS
- IR-008 no resolver leakage: no key encoding environment-variable precedence, runtime-marker interpretation, host detection, memory write behavior, credential provisioning, or governance-profile inference (structural check over known field names): PASS

Negative cases proven on isolated copies (each exit 1 with file, field, and offending value): duplicate actor id; actor alias with nonexistent target; actor alias shadowing a canonical actor; duplicate surface id; surface alias with nonexistent target; surface alias shadowing a canonical surface; surface entry carrying `actor_ref`; surface entry carrying `governance_profile_ref`; actor entry carrying `surface_ref`; actor entry carrying `governance_profile_ref`; a registry carrying an `environment_variables` section; a registry unregistered in `canonical_sources.yaml`.

## Admission state

v3.6.0 is a candidate. No admission decision record exists in this repository for v3.5.0 or v3.6.0, and this release does not admit itself. The registries' authority is candidate-grade until a digest-bound admission binds `l9.actor-registry/global@1` and `l9.surface-registry/global@1`.

Left unchanged, recorded as successor concerns: `pytest/v1` keeps its binding coordinate until a binding-ID grammar is declared; no `stage` projection profile exists for `identity_topology_resolution` (whether canonical law requires total stage projection coverage is an open authority question); the downstream consumption path for the registries (projection source classes, operating-plane resolver) is the downstream convergence task after merge.

**Overall: PASS**; delivered-byte hashes are verified mechanically by SC-008 on every `make validate`.
