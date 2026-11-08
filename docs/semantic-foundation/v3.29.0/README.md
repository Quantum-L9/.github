# Semantic Foundation v3.29.0

Status: **ADDITIVE SUCCESSOR CANDIDATE**

v3.29.0 lets a compiler lower a resolved Node manifest to a Gate-routed Python Node without reading the source topology and without inventing routing, idempotency or adapters. The ProductManifest gains the topology's declared inbound action surface and consequential-operation set. One target binding maps implementation IR to a Python Node shell that registers exactly those actions through the Gate SDK.

## Bounded delta

Stacked on the v3.28.0 candidate (Quantum-L9/.github#214); no file that v3.28.0 changes is touched here.


- `semantics/product_manifest.schema.yaml`:
  - Optional properties `interfaces` and `effects`.
  - Rules that they preserve the source topology's declarations exactly, and are required whenever the topology declares them.
  - Rules that Stage 14 implementation lowering takes action routing only from manifest `interfaces`, and idempotency only from manifest `effects`.
- `semantics/binding_catalog.yaml`: `l9.binding/python-gate-node@1`. This is the first admitted target binding whose source is `implementation_ir`.
  - It lowers a Node's implementation IR to Python with Gate SDK transport.
  - It maps interface actions to registered handlers, consequential operations to Gate runtime idempotency, and forbidden actions to absent registrations.
  - It binds existing port and adapter implementations by the manifest's `implementation_ref` and verifies them; it never regenerates them.
  - It emits behavior code only where an admitted behavior contract determines it, and fails closed on anything unresolved.
- `semantics/product_topology.schema.yaml`:
  - It admits the item shapes of the port and adapter entry lists, as the Semantic Compiler already enforces them.
  - It admits the optional `implementation_ref` source coordinate (`<path>[::<symbol>]`, relative to the RepositorySpec directory, never escaping it). The binding binds existing code through this coordinate.
  - The coordinate is a declared source location: it creates no code, carries no semantic authority, and never makes an entry resolve.
  - The manifest preserves it exactly.
- ADR-025.

## Evidence

The motivating observation is the resolved `l9.state` manifest. It was compiled by `Quantum-L9/l9-semantic-compiler-engine@3bf1a8241452332637ba0daffeee55c433f93e05` from `Quantum-L9/l9-wip@ce0c4973af31aa68741014febef1364ba58f3e3f`, as recorded on Quantum-L9/l9-wip#37:

- `manifest_digest sha256:a8303f93beb1f399fa189451c4facdc9ba41c7e061b9339c3fba34049d8d1d2c`
- 25/25 gate checks pass and `unresolved` is empty.
- It carries neither the topology's 13 `interfaces.actions` nor its 8 `effects.consequential_operations`.

The technologies the binding names, `python` and `gate-sdk`, were already registered in `technology_capabilities.yaml`. This evidence motivates the candidate; it is not law.

## Outstanding Unknowns and findings

- No release check pins the new binding or the new manifest rules; authoring one is an owner decision this candidate does not take.
- The Semantic Compiler implements neither `implementation-contract-validator/v1` nor `final-conformance/v1`. It pins `Quantum-L9/.github@020a94bea86e7c5c5e4107da7014ec259508f397` and must re-pin to the admitted revision of this release before relying on it.
- No ledger defines an executable behavior contract. Until one is admitted, the binding produces Node shells over bound implementations only.
- The explicit decision record that `authority_model.admission_rules` requires still has no defined form in a ledger (the v3.24.0 finding).

## Authority

`Quantum-L9/.github` owns both ledgers. Products keep the meaning of their actions, effects and implementations; the compiler keeps the mechanics of lowering. This candidate does not admit itself, and it grants no producer, compiler or consumer any mutation, publication, merge, admission, deployment, or runtime authority.
