# ADR-025 — Manifest Interface Surface and the Python Gate Node Target Binding

**Status:** Candidate for semantic-foundation v3.28.0. Drafted on 2026-11-07 at the repository owner's instruction, as the canonical first step before the Semantic Compiler implements compilation Stage 14 (`implementation`) and Stage 15 (`target_artifacts`) for Nodes. Admission of v3.28.0 is the acceptance gate; this record does not admit itself.

## Context

`semantics/compilation_profiles.yaml` (`l9.compilation/product-build@1`) defines Stage 14, which consumes `product_manifest_ir` and produces `implementation_ir` under `implementation-contract-validator/v1`, and Stage 15, which consumes `implementation_ir` and a `target_binding` and produces final artifacts under `final-conformance/v1`. `semantics/product_manifest.schema.yaml` states that implementation lowering may consume only a manifest that satisfies the `resolved_manifest_gate`. `semantics/ir_catalog.yaml` admits the transitions `l9.product-manifest-ir/v1 -> l9.implementation-ir/v1 -> l9.target-ir/v1`.

Two facts prevent any compiler from lowering a runnable Node through those stages:

1. **The ProductManifest has no inbound action surface.** A ProductTopology declares `interfaces` (`actions`, each with id, request and result contract and effect class; `public_programmatic_surfaces`; `command_surfaces`; `event_surfaces`) and `effects` (`effect_classes`, `consequential_operations`, `idempotency_contract_refs`, `reconciliation_contract_refs`). The manifest schema has a property for neither. Evidence: the resolved `l9.state` manifest produced by `Quantum-L9/l9-semantic-compiler-engine@3bf1a82` from `Quantum-L9/l9-wip@ce0c497` (Quantum-L9/l9-wip#37) passes 25/25 gate checks. It still carries neither the 13 declared actions nor the 8 consequential operations. Both exist only in the source ProductTopology. Stage 14 therefore cannot derive Gate routing or Gate idempotency from its only admissible input.
2. **No target binding maps `implementation_ir` to a Node implementation.** `semantics/binding_catalog.yaml` admits JSON Schema, pytest, pyproject and Makefile target bindings. None has `source_ir: implementation_ir`. `semantics/technology_capabilities.yaml` already registers `python` (`implementation_language`) and `gate-sdk` (`constellation_transport_binding`, constraints `gate_is_routing_authority` and `application_does_not_require_peer_urls`).

## Options considered

### Option A — Let Stage 14 read `interfaces` and `effects` from the source topology

- Pros: no schema change.
- Cons: it breaks the stated rule that implementation lowering consumes only a resolved manifest. Action routing would also bypass the manifest's proof-carrying gate.

### Option B — Carry the surfaces as a compiler-local manifest extension, with a compiler-local binding

- Pros: one repository changes.
- Cons: a derived artifact would gain unadmitted fields, and the Node implementation binding would stay unadmitted. Each compiler would then re-decide the shape of a Node's action surface, which ADR-010 says belongs in a ledger.

### Option C — Admit the surfaces in the manifest schema and admit one Python Gate Node target binding

- Pros: Stage 14's only input carries everything routing needs, and Stage 15 has an admitted target. The binding is generic over any Node, not State-specific.
- Cons: two ledgers change, and the compiler must re-pin a new authority revision before it can rely on them.

## Decisions

Option C.

1. `semantics/product_manifest.schema.yaml` gains the optional object properties `interfaces` and `effects`, plus five semantic rules:
   - `manifest_interfaces_and_effects_preserve_the_source_topology_declarations_exactly`
   - `manifest_interfaces_and_effects_are_required_when_the_source_topology_declares_them`
   - `implementation_lowering_takes_inbound_action_routing_only_from_manifest_interfaces`
   - `implementation_lowering_takes_consequential_operation_idempotency_only_from_manifest_effects`
   - `an_interface_action_or_consequential_operation_absent_from_the_manifest_is_not_lowered`

   The properties are optional because a topology may declare neither. The second rule makes them mandatory when the topology does declare them, following the precedent of `manifest_product_kind_exception_ref_is_required_when_the_source_topology_declares_one`. The `resolved_manifest_gate` is unchanged.
2. `semantics/binding_catalog.yaml` admits `l9.binding/python-gate-node@1`:
   - `class: target`, `source_ir: implementation_ir`, `target_ir: target_ir`, `target.technology: python`, `target.transport_technology: gate-sdk`, `applies_to.product_kind: node`.
   - It maps each manifest interface action to a Gate SDK registered handler, each consequential operation to a Gate runtime idempotency requirement, and each forbidden action to an absent registration.
   - Port and adapter implementations are bound by the manifest's `implementation_ref` and verified, never regenerated. Behavior code is emitted only where an admitted behavior contract determines it.
   - Anything unresolved fails closed, and an optional port is never given an invented adapter.
   - The binding emits no HTTP route, authentication, peer URL or routing logic.
3. No RC check is added. No compiler, Gate SDK, product, IR catalog, compilation profile or solver catalog change is part of this release.

## Review findings (recorded, not resolved)

- The properties are typed only as `object`, like most manifest properties. Their field shape is the topology's. No release check pins that the manifest copy is exact; the compiler must prove it.
- `final-conformance/v1` and `implementation-contract-validator/v1` are registered solvers with no implementation in the Semantic Compiler at `3bf1a82`. Implementing them is compiler work that follows this release.
- The compiler pins canonical meaning to `Quantum-L9/.github@020a94b` and does not read `binding_catalog.yaml` today. Consuming this release requires a compiler re-pin to the admitted revision.
- No ledger yet defines an executable behavior contract. Until one is admitted, the binding emits Node shells that bind existing implementations and generates no behavior.

## Consequences

- A compiler can lower a resolved Node manifest to a Gate-routed Python Node shell without consulting the topology directly and without inventing routing, idempotency or adapters.
- Manifests compiled before this release remain valid for every use except Stage 14 lowering of a topology that declares `interfaces` or `effects`. Those must be recompiled.
- Gate remains the only routing authority. The binding grants no publication, admission, deployment or runtime authority.
