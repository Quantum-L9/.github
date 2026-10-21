# Projection publication

How a projection of this repository's canonical semantics reaches a consumer, and what a consumer may trust. Governing law: `semantics/projection_engine_contract.yaml` `binding_conventions`, `semantics/composition_engine_contract.yaml` `binding_conventions`, ADR-019, ADR-020, ADR-021.

**Status: active architecture.** The earlier `projections`-branch publisher (PR #180) is retired by ADR-021; no `projections` branch exists and none is created.

## Roles

- **`Quantum-L9/.github` `main`** owns the canonical sources, the projection and composition profiles, the artifact and receipt schemas, and the conventions below. It holds no projection.
- **`l9-semantic-compiler`** (the component `semantics/vocabulary.yaml` assigns the `projection` role, repository `Quantum-L9/l9-semantic-compiler-engine`) is the only producer. `project` emits one `l9.projection-artifact/v1` per source class of a profile and one `l9.compiler-receipt/v1` per artifact; `compose` emits one `l9.composed-projection/v1` and its receipt when a composition profile declares it.
- **A consumer repository** commits the producer's output as a bundle, verifies it without running the producer, and attests production by trusted replay. The consumer never produces, repairs, or restates a projection.

## The shape the producer emits

Every value below is defined in `semantics/projection_engine_contract.yaml#binding_conventions` and realized by the producer. A consumer recomputes it; it never defines another.

| Field | Computed over |
|---|---|
| `source_digest` | raw bytes of the canonical ledger at the pinned authority revision |
| `projection_digest` | canonical JSON of the artifact with `projection_digest` removed |
| `composition_digest` | canonical JSON of the composed projection with `composition_digest` removed |
| `receipt_identity` | canonical JSON of the receipt with `receipt_identity` set to `pending` and no `receipt_digest` |
| `receipt_digest` | canonical JSON of the receipt with `receipt_digest` removed |
| `exact_subject_ref`, `output.ref` | `<projection_profile_ref>#<canonical_source_ref>` (composition: `<composition_profile_ref>#<projection_profile_ref>`) |
| `output.digest` | the artifact's `projection_digest` (composition: `composition_digest`) |

Canonical JSON: string-keyed mappings in sorted key order, sequences in order, bytes as `{"$bytes_hex": …}`, serialized with `sort_keys=True`, separators `(",", ":")`, `ensure_ascii=False`, encoded UTF-8. Every digest is `sha256:` plus 64 lowercase hex digits.

A receipt whose `result` is not `pass`, or whose `verification_basis.unresolved_criteria` is not empty, binds nothing. Multi-selector source classes are projected like any other.

## Transport: a consumer-committed bundle

A consumer repository commits, under a path it owns:

- `projections/<source_class>.projection.json` — the artifact for each source class of the profile, bytes exactly as the producer rendered them;
- `receipts/<source_class>.receipt.json` — the receipt for each artifact;
- `composed.json` and `receipts/composed.receipt.json` — only when the profile has a composition profile;
- a lock file recording the authority repository and revision, the producer repository, revision, compiler and version, the profile pin, every component's `source_ref`, `source_digest`, `projection_digest`, file digest and receipt path, and the composed artifact's digests when present.

The lock is the consumer's inventory, not authority. The authority revision it names must be a commit on this repository's `main`; the producer revision it names must be a commit on the producer repository's protected `main`.

## What a consumer verifies

Without running the producer, against the pinned authority revision read from commit objects:

1. every committed file's bytes equal the lock;
2. every artifact's envelope schema, `projection_digest`, profile pin and provenance equal the lock and the recomputed convention;
3. every receipt: schema, `receipt_digest`, producer identity, `exact_subject_ref`, `output`, `profile`, `governing_coordinates.repository` and `revision`, `result: pass`, and the `payload_schema` criterion naming the profile's declared output schema;
4. every `source_digest` equals the ledger bytes at the pinned revision, and the profile entry's canonical digest equals the pin;
5. the committed source classes equal the profile's declared classes, in order;
6. where a selector form permits it, the payload is re-selected from the ledger and compared record for record.

Any failure is `REJECTED` (bytes or receipts contradicted), `STALE` (the authority moved materially), or `BLOCKED` (something could not be established). A verified bundle is verified, not admitted: admission as law still needs the explicit decision record `semantics/authority_model.yaml#admission_rules` requires, whose form is not yet defined.

## What attests production

Receipts are unkeyed. Production is attested by **trusted replay**: a workflow in the consumer repository, using only code from its default branch, checks out this repository at the lock's authority revision and the producer at the lock's producer revision, confirms both revisions are on their protected `main`, regenerates the bundle, and compares byte for byte. A bundle whose producer revision is not on the producer's `main` is not attested.

## Current consumers

- `l9.projection/architecture-intelligence@1` with `l9.compose/architecture-intelligence@1` — Cursor-Governance `generated/governance/architecture_intelligence/`, verified by the `l9-global-architect` skill (ADR-019).
- `l9.projection/coding-agent-execution@1` (no composition profile) — Cursor-Governance `generated/governance/coding_agent_execution/`, verified by the `l9-coding-agent` skill (ADR-020).

Both bundles are cut by one producer driver in the consumer repository and attested by one replay workflow.
