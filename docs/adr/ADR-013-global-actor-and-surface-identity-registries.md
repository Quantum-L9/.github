# ADR-013 — Global Actor and Surface Identity Registries

**Status:** Accepted for semantic-foundation v3.6.0

## Decision

ActorIdentity and SurfaceIdentity receive canonical organization-level registries, `semantics/actor_registry.yaml` (`l9.actor-registry/global@1`) and `semantics/surface_registry.yaml` (`l9.surface-registry/global@1`). Without them every downstream operating plane remakes the same identity-name decision locally; `identity_model.yaml` already names `actor_registry_and_identity_resolution_contract` and `surface_registry_and_runtime_evidence` as the authority sources of the two dimensions, and these ledgers are those registries.

Actor and surface identities remain different dimensions. One actor may operate through multiple surfaces. A surface does not intrinsically grant or imply ActorIdentity, and a surface does not intrinsically select GovernanceProfile. Neither registry carries an `actor_ref`, `surface_ref`, `governance_profile_ref`, `provider_ref`, or `adapter_ref`; relations among dimensions remain `identity_binding` declarations in a ProductTopology, never intrinsic registry fields.

Typed aliases belong to exactly one identity dimension. The same string may legally occur in different dimensions because equal strings do not imply equal identity kinds (L9-IDENTITY-002). `claude-code` is one ActorIdentity. The historical actor values `claude-code-desktop` and `claude-code-mobile` canonicalize to ActorIdentity `claude-code` when interpreted as actor values; desktop, web, mobile, CLI, and IDE remain SurfaceIdentity distinctions (`claude-code-desktop`, `claude-code-web`, `claude-code-mobile`, `claude-code-cli`, `claude-code-ide`).

Runtime environment-marker interpretation belongs to the applicable downstream operating plane, not to these global registries. No environment-variable, host-detection, or marker-precedence table is admitted upstream. A downstream resolver must still satisfy `l9.contract/identity-resolution@1` and emit a complete `l9.identity-assertion/v1`, validating the asserted actor and surface against these registries.

Identity registration grants no credential, signing key, role, grant, execution, admission, memory, or authorization authority. The registries are candidates until a digest-bound admission decision binds them, like every other ledger of the semantic foundation; `authority_model.yaml` names the admitted actor registry as the actor identity source, so admission of this registry is that separate decision.

## Consequence

`scripts/validate-semantics.py` RC-014 enforces registry shape, typed-alias closure, cross-dimension ownership exclusion, the legality of cross-dimension string equality, registration in `canonical_sources.yaml`, classification in `generic_compiler_manifest.yaml`, and the absence of runtime-resolution structure. Cursor-Governance and other operating planes migrate their actor and surface vocabularies, memory authorship, and resolvers to these coordinates as a consumer convergence task after this foundation merges; this foundation does not mutate those repositories.
