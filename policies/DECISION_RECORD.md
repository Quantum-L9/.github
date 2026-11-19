# Organization-policy candidate, not an admission

Campaign `L9-ORG-AUTHORITY-CUTOVER-2026-11-18-v1`, lane A.

`semantics/authority_model.yaml` at `00500268eb24de29a5e647a447d6f992d609f6f5` requires an explicit decision record and does not define its schema. `docs/PROJECTION_PUBLICATION.md` and candidate ADR-021 say the same. This file records the candidate. It does not admit the policy.

## Owner directory

Source names `Quantum-L9/.github` as the global governance owner and does not name a subdirectory. The authorized campaign contract names the existing `policies/` concern, preferred path `policies/ORG_INVARIANTS.yaml`. The scout found no `L9-ORG` or org-invariants file on this pin, so that path is a first file rather than an extension of an existing body.

## Predecessor

`Quantum-L9/Cursor-Governance` `ORG_INVARIANTS.yaml` policy `4.0.0` at `59c0b3e0fae7418c67b7e3be76c4e3f412ad49dd`.

## Candidate digests

| Path | SHA-256 |
| --- | --- |
| `policies/ORG_INVARIANTS.yaml` | `fdb3a6d45af46f237470671b57873557301f1261679d67c352cda5a81661b59c` |
| `policies/ASSERTION_TYPES.yaml` | `c9fe11f8886ba5851e6497131f8984d4628008d780bfa2f77529ec759566aa93` |
| `policies/org-invariants.schema.json` | `ba69d5712d893dce7b43229e88a2656465949c3bbbb01ab6a45f12e0f6ca5832` |
| `policies/POLICY_RELEASE.schema.yaml` | `6256b1f82710c0b48220a18b4f1346b263576dfb51c7991dcdda6be7d8b11094` |

## Reasoned delta from 4.0.0 to 4.1.0

- Canonical repository and path are `Quantum-L9/.github` and `policies/ORG_INVARIANTS.yaml`.
- `L9-ORG-005` excludes the source repository `.github` from the consumer-mirror rule.
- Protected paths name the policy artifacts in this repository. `CANONICAL_LAW.md` stays Cursor operating law and is not an organization-policy path.
- `L9-CTRL-005` names the live required check `Analyze (central Core)`. Enforcement state stays `unenforced`.
- `L9-CTRL-006` and `L9-CTRL-007` require authenticated owner authorization. They do not require a second human. Platform branch protection is unchanged.
- Preserved intent records `historical_Cursor_Governance_was_canonical_through_4_0_0`.

## Still required of the owner

The release schema now requires a signature reference and an in-toto attestation reference, and both flags are const true. A reference is not verification. `policy-provenance.yml` can ask GitHub Sigstore to sign the policy bytes with this repository's OIDC identity. A pull-request signature is rejected, and a default-branch signature without an owner admission is rejected. Bind an admission decision to the exact pull-request head. This file does not supply that decision, and no `refs/heads/main` attestation of this candidate exists yet.
