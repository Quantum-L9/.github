# Semantic Foundation v3.20.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor closes one upstream semantic dependency: a canonical, agent-agnostic projection profile that selects the admitted global law governing repository work by a coding agent. Every coding-agent surface that the Cursor-Governance operating plane binds can then consume the same derived, digest-addressable selection from `.github`, rather than reading a coding skill or a repository-local copy of global law.

## Bounded delta

- Adds exactly one runtime projection profile to `semantics/projection_profiles.yaml`: `l9.projection/coding-agent-execution@1`, consumer `Cursor-Governance`, sources `invariants`, `contracts`, and `authority_model` only, output schema `l9.projection.coding-agent-execution/v1`.
- The profile selects whole admitted records by exact id: 19 global invariants, 10 global contracts, and the `agent_authority`, `human_authority`, `escalation_rules`, and `admission_rules` sections of the authority model. The selected contracts close over their `source_invariants`.
- Adds RC-028 to `scripts/validate-semantics.py`, a closure check for this exact profile coordinate, with a fail-closed negative-case batch.

## Obligation mapping (reuse, not new law)

| Coding-execution obligation | Admitted records selected |
| --- | --- |
| Authority and scope boundary | `L9-AUTH-001`, `L9-AUTH-002`, `L9-MONOTONIC-001`, `l9.contract/authority-boundary@1`, `l9.contract/monotonic-subordination@1`, `agent_authority`, `escalation_rules` |
| Upstream source fidelity | `L9-OWNER-001`, `L9-DERIVED-001`, `L9-PROV-001`, `L9-COORD-001`, `L9-REVISION-001`, `L9-PROJECTION-001`, `l9.contract/derived-artifact@1`, `l9.contract/provenance-and-coordinate@1`, `l9.contract/projection@1` |
| Bounded implementation, no authority expansion | `L9-AUTH-001`, `L9-MONOTONIC-001`, `L9-ASSURANCE-001`, `l9.contract/authority-boundary@1`, `l9.contract/assurance-and-verification@1` |
| Verification independent of the candidate | `L9-VALIDATION-001`, `L9-CORRECTNESS-001`, `L9-EVIDENCE-001`, `l9.contract/validation-and-correctness@1`, `l9.contract/evidence-and-receipt@1`, `l9.contract/assurance-and-verification@1` |
| Explicit Unknown and truthful failure | `L9-UNKNOWN-001`, `L9-DEGRADE-001`, `L9-COMPAT-001`, `l9.contract/unknown-and-degradation@1`, `l9.contract/validation-and-correctness@1` |
| No self-authorized admission or publication | `L9-PROMOTION-001`, `L9-ADMISSION-001`, `L9-GLOBALIZATION-001`, `l9.contract/admission-and-promotion@1`, `human_authority`, `admission_rules` |

`L9-DEGRADE-001`, `L9-COMPAT-001`, and `L9-GLOBALIZATION-001` are carried because selected contracts cite them; a projection that omitted them would leave contract citations unresolvable.

## Non-goals

v3.20.0 adds no invariant, contract, schema, semantic ledger, source registration, vocabulary term, authority class, projection framework, producer, or ADR. Global law already covers every obligation above. The profile does not carry coding-specific refinements that no admitted global record states, including the changed-file boundary, minimal-diff and no-stub rules, a verifier distinct from the producing actor, and the assignment of merge authority to a human. Those are subordinate policy for their owner under `l9.contract/monotonic-subordination@1`. Putting them in a projection would be invention (`L9-PROJECTION-001`).

The profile names no skill, command, adapter, host, or surface, and it grants no execution, publication, or merge authority. It does not modify `l9.projection/cursor-governance-operating-plane@1` or `l9.projection/cursor-governance-identity@1`, and it does not modify Cursor-Governance.

## Authority

`Quantum-L9/.github` owns the selected law and this profile. The profile catalog's existing engine contract (`l9.compiler/projection-engine@1`), artifact schema (`l9.schema/projection-artifact@1`), and receipt schema (`l9.schema/compiler-receipt@1`) govern any projection produced from it. A produced projection is derived, non-canonical, provenance-bearing, and non-current when a selected source or the profile changes.

## Outstanding Unknowns

- No admitted deterministic projection producer currently emits `l9.projection-artifact/v1` with an `l9.compiler-receipt/v1` for any profile. This release does not add one and does not mock a receipt.
- The `semantic_digest` canonicalization named by the artifact and receipt schemas is not declared in a ledger.
- `l9.schema/projection-artifact@1` carries a single `source_ref` / `source_digest`, while this profile, like most catalog profiles, selects from three sources. Whether a produced artifact is one per source or a composed projection under `composed_projection_rules` is not declared for this profile.

Producing and binding the projection remain downstream work and are not claimed here.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.19.0/`. The predecessor release record remains immutable.
