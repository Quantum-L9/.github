# ADR-021 — Producer-Emitted Projection Contract and Consumer-Committed Bundles

**Status:** Candidate for semantic-foundation v3.24.0. Drafted on 2026-10-21 at the repository owner's instruction to eliminate the divergence between the projection shape the producer emits and the shape the publisher transport expected. Admission of v3.24.0 is the acceptance gate; this record does not admit itself. It supersedes the publisher transport introduced by PR #180 (`docs/PROJECTION_PUBLICATION.md` as first written, `scripts/publish-projection.py`), which no ADR had recorded.

## Context

Two projection conventions existed side by side.

The producer (`l9-semantic-compiler`, the component `semantics/vocabulary.yaml` assigns the `projection` role) emits an `l9.projection-artifact/v1` whose `projection_digest` covers the whole envelope minus that field, receipts it with `exact_subject_ref` and `output.ref` equal to `<profile_ref>#<source_ref>`, and projects every selector of a source class whether the class declares one selector or nineteen. Both admitted consumers verify exactly that shape: the architecture-intelligence bundle in Cursor-Governance (ADR-019) and the coding-agent canonical binding (ADR-020).

The publisher transport (`projections` branch, `index.json`, `scripts/publish-projection.py`) expected a different shape: `projection_digest` over the payload alone, `exact_subject_ref` equal to the bare profile ref, `output.ref` keyed by source class, and single-selector classes only. No producer ever emitted that shape, the `projections` branch was never created, and the publisher refused every class of `l9.projection/coding-agent-execution@1` as `UNSUPPORTED_SOURCE_CLASS`. A downstream consumer built on the publisher convention rejected genuine producer output as tampered.

Canonical law did not settle the matter: `semantics/projection_artifact.schema.yaml` types `projection_digest` as a `semantic_digest` without saying what it is computed over, and v3.23.0 recorded that "the `semantic_digest` canonicalization is still not declared in a ledger". With the convention undeclared, a second convention could be written down and defended.

## Options Considered

### Option A: Declare the producer-emitted shape as law and consume committed bundles

- Pros: matches what the producer emits and what both admitted consumers verify; the bundle plus trusted replay already attests production for the architecture-intelligence profile; one convention, one transport, no index to keep current.
- Cons: a consumer repository carries projected bytes; the attestation depends on the producer revision being on its protected main.

### Option B: Rewrite the publisher to the producer-emitted shape and activate the `projections` branch

- Pros: keeps a single upstream transport; consumers fetch rather than commit.
- Cons: a second copy of the verification logic in `scripts/publish-projection.py` that must track the engine; an index whose currency is a new failure mode; the branch grants nothing the bundle does not, and activation was never approved.

### Option C: Keep both conventions and let each consumer choose

- Pros: no deletion.
- Cons: this is the divergence; a consumer bound to the publisher shape can never bind a real projection.

## Decisions

1. **The producer-emitted shape is the contract.** `semantics/projection_engine_contract.yaml` gains `binding_conventions`: canonical JSON (string-keyed mappings in sorted key order, sequences in order, bytes as `{"$bytes_hex": …}`, `sort_keys=True`, compact separators, `ensure_ascii=False`, UTF-8), `semantic_digest` as `sha256:` over that encoding, `source_digest` over raw ledger bytes, `projection_digest` over the artifact minus its own digest, `receipt_identity` and `receipt_digest` as the producer computes them, `exact_subject_ref` and `output.ref` as `<profile_ref>#<source_ref>`, and multi-selector source classes supported. `semantics/composition_engine_contract.yaml` gains the matching `binding_conventions` for `composition_digest` and the composed subject.

2. **Transport is a consumer-committed bundle.** A consumer repository commits the artifacts and receipts a pinned producer revision emitted for a profile at a pinned authority revision, together with a lock that records both pins and every file's digest, and a trusted replay regenerates the bundle from those pins and compares byte for byte. The bundle is non-authoritative projected data; its lock, replay, and consumer verifier are owned by the consumer repository under its own publication law.

3. **The publisher is retired.** `scripts/publish-projection.py` and `scripts/test-publish-projection.py` are deleted and their workflow step removed. `docs/PROJECTION_PUBLICATION.md` is rewritten to describe the bundle transport. No `projections` branch is created.

4. **Nothing admitted changes.** Every profile, schema, criterion, and the receipt schema are byte-for-byte as admitted. The conventions were already what the producer does; this record makes them law and removes the alternative.

## Consequences

- A consumer that verifies any other digest, subject, or output form is wrong by definition and must be corrected, not accommodated.
- Producer attestation remains unkeyed: receipts are reproducible, not signed. Trusted replay against a protected producer revision is the attestation; a bundle whose producer revision is not on that main is not attested.
- Admission of a projection as law still requires the explicit decision record `authority_model.admission_rules` demands, whose form is not yet defined upstream. A verified bundle is verified, not admitted.
