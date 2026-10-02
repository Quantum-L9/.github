# Quantum-L9/.github Semantic Foundation v3.6.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

## What this release is

v3.6.0 is the additive successor of the v3.5.0 corrected successor candidate (`docs/semantic-foundation/v3.5.0/`). It preserves every v3.5.0 ledger, contract, invariant, and mechanically enforced closure property unchanged, and adds the canonical identity-name layer that v3.5.0 already referenced but did not yet carry:

- `semantics/actor_registry.yaml` (`l9.actor-registry/global@1`): the canonical organization ActorIdentity IDs, their kind and status, and typed historical ActorIdentity aliases;
- `semantics/surface_registry.yaml` (`l9.surface-registry/global@1`): the canonical organization SurfaceIdentity IDs, their status, and typed historical SurfaceIdentity aliases;
- typed identity-alias rules for those registries: an alias belongs to exactly one dimension, resolves to exactly one canonical coordinate, never targets another alias, and never shadows a canonical coordinate;
- mechanical identity-registry validation (`scripts/validate-semantics.py` RC-014);
- ADR-013, the authority boundary for the registries.

`identity_model.yaml` names `actor_registry_and_identity_resolution_contract` and `surface_registry_and_runtime_evidence` as the authority sources of the two dynamic identity dimensions. Until v3.6.0 those registries did not exist, so every downstream operating plane had to invent its own actor and surface vocabulary. That is the decision ADR-010 says belongs upstream: one made once here instead of remade in every product.

## Identity after v3.6.0

- `claude-code` is one ActorIdentity. Desktop, CLI, IDE, web, and mobile are SurfaceIdentity distinctions (`claude-code-desktop`, `claude-code-cli`, `claude-code-ide`, `claude-code-web`, `claude-code-mobile`), not separate actors.
- The historical actor values `claude-code-desktop` and `claude-code-mobile` are typed ActorIdentity aliases that canonicalize to `claude-code` when interpreted as actor values. The identical strings are canonical SurfaceIdentity IDs. Equal strings do not imply equal identity kinds (L9-IDENTITY-002); the two meanings coexist because they live in two separately owned ledgers.
- One actor may operate through many surfaces. No surface record owns an actor; no actor record owns a surface; neither registry owns GovernanceProfile, provider, adapter, credential, signing key, role, grant, or execution authority.
- A downstream resolver still satisfies `l9.contract/identity-resolution@1` from its own bounded runtime evidence and emits a complete `l9.identity-assertion/v1`, validating the asserted actor and surface against these registries.

## What v3.6.0 does not add

- runtime environment resolution policy;
- Cursor-specific marker precedence;
- Claude-specific marker precedence;
- credential provisioning;
- memory implementation;
- downstream resolver implementation;
- new identity dimensions;
- new governance-profile semantics.

Concrete environment markers remain runtime evidence interpreted by the applicable downstream operating plane. The upstream foundation defines what ActorIdentity and SurfaceIdentity mean, which IDs are canonical, what IdentityResolution must guarantee, and what IdentityAssertion must contain.

## How downstream repositories consume this release

After human merge, a downstream contract pins `l9.actor-registry/global@1` and `l9.surface-registry/global@1` to the exact merged `main` coordinate and file digests, migrates its actor and surface vocabulary and memory authorship to these coordinates, and implements its resolver against `l9.contract/identity-resolution@1`. None of that is part of this release.

## Admission state

v3.6.0 is a candidate. No admission decision record exists for v3.5.0 or v3.6.0 in this repository, and this release does not admit itself. `authority_model.yaml` names the admitted actor registry as the actor identity source; admission of `l9.actor-registry/global@1` is that separate, digest-bound decision.

## Release contents and validation

See:

- `MANIFEST.md` for the package inventory;
- `RELEASE_VALIDATION.md` for validation results, including every predecessor closure property carried forward;
- `semantics/` for canonical semantic artifacts;
- `docs/adr/` for the architecture decisions, now ADR-001 through ADR-013;
- `HASHES.sha256` for package integrity;
- `../v3.5.0/` for the preserved predecessor record and the full architecture description.
