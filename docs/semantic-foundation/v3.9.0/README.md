# Semantic Foundation v3.9.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

This successor makes L9 validation fail closed when required validation coverage is incomplete. It operationalizes existing constitutional law through the existing validation contract and repairs the Cursor-Governance operating-plane projection so that downstream consumers receive the operative contract semantics rather than headings alone.

## Bounded delta

- Strengthens the existing contract `l9.contract/validation-and-correctness@1` in `semantics/contracts.yaml`: adds `L9-ASSURANCE-001` to its source invariants; guarantees that validation success requires every applicable required criterion to be evaluated and satisfied, that unavailable, unreadable, unexecuted, or unresolved required criteria preclude success, and that validation coverage is explicit and evidence-bound; forbids silent skip of applicable required validation, default success on missing, unreadable, unexecuted, or unresolved required validation, and partial validation coverage reported as complete. The outcome keys `satisfied`, `rejected`, and `unresolved` are preserved; `satisfied` is now bound to complete evaluation of every applicable required criterion and incomplete coverage routes to `unresolved`.
- Repairs the existing profile `l9.projection/cursor-governance-operating-plane@1` in `semantics/projection_profiles.yaml`: the contract projection carries `id`, `purpose`, `scope`, `source_invariants`, `requires`, `guarantees`, `forbidden`, and `outcomes`, and the profile projects the canonical global invariants through the existing selector `$.invariants[?(@.scope=="global")]`, so the cited invariants are not stranded.
- Adds RC-017 to `scripts/validate-semantics.py` with a fail-closed negative-case batch proving each obligation is enforced for its intended reason.
- Refreshes only the derivation coordinates in `semantics/capabilities.yaml`, `semantics/lifecycle.yaml`, and `semantics/receipt_catalog.yaml` that the new `contracts.yaml` bytes made stale.

## Non-goals

v3.9.0 adds no constitutional invariant, no contract, no projection profile, no capability, no semantic ledger, no result taxonomy, no validator framework, and no ADR. It does not touch Strategic Cognition, Plan Graph, ProductKind, repository-class, or identity semantics. It does not change Cursor-Governance; the downstream operating-plane consumer is corrected in a separate change after this record lands. It introduces no cross-repository synchronization mechanism.

## Authority

`Quantum-L9/.github` owns canonical L9 validation semantics. The Cursor-Governance operating plane is a downstream consumer of the projection repaired here and holds no reinterpretation authority over it.

## Replacement basis

Immediate predecessor: `docs/semantic-foundation/v3.8.0/`. The predecessor release record remains immutable.
