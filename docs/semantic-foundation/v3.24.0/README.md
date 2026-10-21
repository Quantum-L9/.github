# Semantic Foundation v3.24.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.24.0 makes the projection shape the producer emits the only projection contract and retires the `projections`-branch publisher that had defined a second one. It closes the v3.23.0 finding that the `semantic_digest` canonicalization was not declared in any ledger.

## Bounded delta

- `semantics/projection_engine_contract.yaml` gains `binding_conventions` (`l9.projection-binding-conventions/v1`): canonical JSON, `semantic_digest`, `source_digest`, `projection_digest`, `receipt_identity`, `receipt_digest`, the `<profile_ref>#<source_ref>` subject and output form, multi-selector support, and the consumer-committed bundle as the transport.
- `semantics/composition_engine_contract.yaml` gains the matching `binding_conventions` for `composition_digest`, the composed subject, and component records.
- ADR-021.
- `docs/PROJECTION_PUBLICATION.md` is rewritten to the bundle architecture; `scripts/publish-projection.py`, `scripts/test-publish-projection.py`, and their workflow step are removed. No `projections` branch exists.
- Every profile, schema, criterion, and receipt field is byte-for-byte as admitted. The pipelines of both engine contracts are unchanged; only descriptive `binding_conventions` blocks are added.

## Evidence

The conventions declared here are the ones `l9-semantic-compiler` at `main` already realizes, recomputed and verified by both admitted consumers: the architecture-intelligence bundle in Cursor-Governance reproduces byte for byte from the engine at `main`, and the coding-agent canonical binding verifies the engine's `pass` receipts for every class of `l9.projection/coding-agent-execution@1`. The retired publisher accepted none of that output.

## Outstanding Unknowns and findings

- Producer attestation remains unkeyed; trusted replay against a protected producer revision is the attestation, and a bundle cut from an unmerged producer revision is not attested.
- The explicit decision record `authority_model.admission_rules` requires for admitting a projection as law has no defined form; a verified bundle is verified, not admitted.
- The v3.23.0 findings on `source_authority` and RC-031 are unchanged.

## Authority

`Quantum-L9/.github` owns the conventions and the profiles. The compiler (`l9-semantic-compiler`) realizes them, consumers verify, and replay attests. This candidate does not admit itself.
