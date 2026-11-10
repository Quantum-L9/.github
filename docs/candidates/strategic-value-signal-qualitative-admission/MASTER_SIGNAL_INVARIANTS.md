# Master Signal Invariants | Admission Candidate

**Candidate class:** minimal additive global semantics; not admitted, compiled, projected, or authorized.  
**Candidate destination:** `Quantum-L9/.github/semantics/invariants.yaml#invariants` (append only after exact-digest admission).  
**Frozen comparison:** `Quantum-L9/.github@dc96a8ae9f31e359bb0e52a0b1d778fc8f265d99`, `main` observed 2026-11-09.  
**Canonical source blobs:** `invariants.yaml` `87c6215aedd7aca0363451d3d307ea528e7d31dd`; `vocabulary.yaml` `22b04a8e6f97d661e30c1eb68a3281e086e74f88`; `contracts.yaml` `58103d4f5f76a83f4041bc7719a2419f875f9320`; `authority_model.yaml` `b0337e8912470d76ae64a7cbd0bd95752384f7b2`.  
**Direct donor:** previous `MASTER_SIGNAL_INVARIANTS.md`, SHA-256 `9a1c5cc60be90c5fbc87f92b600bb25cb2a07b5f1298a00a3183b4b36512ce33`; its 36 source-law statements remain traceable below.  
**Additional scoped source, not global authority:** `l9-global-architect/contracts/concerns/signal-propagation.contract.yaml` already has a local Signal concern (meaning preservation, eligibility, fan-out, reconvergence, write-back, loops, drag). Global candidates are narrow, reusable boundary propositions; they do not appropriate GAR's local operational contract or require its representation.

## Admission question and semantic gap

Canonical `.github` has `L9-PROV-001` for **derived semantic artifacts**, `L9-ASSURANCE-001` for claims of proof, `L9-OWNER-001` for ownership, `L9-UNKNOWN-001` for unresolved claims, and `L9-HARD-001` for hard constraints. Canonical vocabulary already defines `bidirectional_value_propagation` and `value_propagation_mesh` as **causal value topologies**, not movement of evidence. It defines no `signal`, `signal_propagation`, `signal_feedback_episode`, or `signal_consumption` term.

The proposed Signal concern is **evidence-bearing information movement between eligible consumers**, not a new transport, a fourth reasoning kernel, a second memory system, a graph database, or objective-relative value calculation. Its new global meaning, if admitted, should cover only information fidelity, independent evidence across paths, meaningful bounded feedback, and delivery/use distinctions. Existing authority, privacy, identity, contract and promotion law continues to do its own work.

**Trigger:** an agent or subsystem makes a consequential claim about signal movement, independent corroboration across multiple paths, feedback-driven learning, or downstream consumption. Ordinary one-way communication is not required to become bidirectional or quantified. `MUST` below is **proposed** and is not current law.

## Proposed additions to `semantics/invariants.yaml#invariants`

This is an additive YAML snippet using the current canonical record fields only. IDs are proposed and unreserved.

```yaml
invariants:
  - id: L9-SIGNAL-001
    statement: >-
      When evidence-bearing information crosses a semantic or participant boundary,
      a consequential signal claim must preserve or resolvably reference the
      producer, pertinent evidence and lineage, material context and uncertainty,
      and governing meaning needed by its authorized eligible consumer.
      Signal movement does not confer truth, ownership, authority, permission,
      or positive Strategic Value; an ineligible destination is not a valid route.
    scope: global
    owner: Quantum-L9/.github
  - id: L9-SIGNAL-002
    statement: >-
      A claim of stronger evidence through signal fan-out, reciprocal paths, or
      reconvergence must retain original-source dependence and distinguish
      nonredundant corroboration, interpretation, validation or resilience from
      repeated or correlated copies. Added branches and hops require a justified
      eligible consumer or distinct protective purpose; duplicate deliveries,
      message volume, and topology labels are not independent evidence.
    scope: global
    owner: Quantum-L9/.github
  - id: L9-SIGNAL-003
    statement: >-
      A signal feedback episode claimed to produce learning must identify an
      evidenced changed state consumable by a later eligible consumer; an
      unaccepted challenge remains a challenge, not completed learning. Such
      loops must use controls appropriate to their risks that prevent
      unbounded replay or unjustified convergence claims. Echoes, acknowledgments,
      finite hop limits, and cyclic routing alone do not establish learning,
      fixed-point convergence, or realized Strategic Value; no universal
      constellation-wide synchronization lap is required.
    scope: global
    owner: Quantum-L9/.github
  - id: L9-SIGNAL-004
    statement: >-
      A consequential signal outcome claim must distinguish production,
      attempted delivery, verified delivery, recipient acceptance, durable
      retention, actual later consumption, and any observed change in behavior
      or result. Evidence of an earlier stage does not establish a later one;
      a delivery or consumption observation alone is not a positive Strategic
      Value finding, and material failures or Unknown stages remain explicit.
    scope: global
    owner: Quantum-L9/.github
```

### Distinct falsifiers and owner-preserving interpretations

| Candidate | Passing case | Failing case | What is *not* owned or newly required |
|---|---|---|---|
| `L9-SIGNAL-001` | A consumer receives an authorized summary with sufficient reference to the actual source, context, caveats, and semantic owner | A message quietly drops uncertainty or is disseminated to a forbidden consumer | No universal envelope/packet, identity resolver, authorization system, or truth writer |
| `L9-SIGNAL-002` | Fan-out delivers independently different validation to two eligible consumers and recombination identifies the common original source | Three forwarding hops turn one assertion into a synthetic three-vote quorum | No mandatory mesh, fixed fan-out ceiling, numerical rank, or global source quorum |
| `L9-SIGNAL-003` | A bounded feedback episode produces an owner-accepted corrected constraint available to a later eligible recipient; its later outcome is evaluated separately | ACK ping-pong or a finite generation cap is called proven adaptive learning or mathematical convergence | No mandatory two-way loop, global lap, universal TTL, or imposed storage/transport choice |
| `L9-SIGNAL-004` | The emitter reports sent, receiver confirms receipt, separate evidence shows a later use; Strategic Value remains separately evaluated | “All agents improved” is inferred from a successful publish operation alone | No new delivery lifecycle state machine, receipt family, independent acceptance authority, or automatic promotion |

## Exact canonical deduplication and ownership boundary

The following meanings **must not become new global invariants** because current canonical law already owns them: `L9-AUTH-001/002` (permissions), `L9-OWNER-001` (truth owner), `L9-PROMOTION-001` and `L9-GLOBALIZATION-001` (admission), `L9-HARD-001` (privacy/security/hard constraints), `L9-UNKNOWN-001` (uncertainty), `L9-EVIDENCE-001` and `L9-ASSURANCE-001` (proof), `L9-PROV-001` (derived semantic lineage), `L9-COORD-001` (currentness), and `L9-CAPABILITY-001` (capability availability/invocation). Signal does **not** reimplement those owners; its additive meaning applies to transient or durable propagation claims across consumers that those generic rules do not completely describe.

A consumer may report a violation or challenge but cannot elevate an observation to canonical law or write to an authoritative owner merely by propagating it. Such promotion remains governed **by reference** to the current admitted owner law, not a new Signal privilege.

## Disposition of all 18 previous Signal candidates

`NEW` is an independent candidate for global admission. `REUSE` cites already-admitted authority. `LOCAL` denotes domain/workflow detail rather than a global addition. Some predecessor statements combined both.

| Previous rule | Disposition | Governing meaning or candidate successor |
|---|---|---|
| SI-01 Preserve source meaning | **NEW + REUSE** | `L9-SIGNAL-001`; derived artifact provenance still `L9-PROV-001` |
| SI-02 Consumer privacy, eligibility, permission | **NEW + REUSE** | Signal-specific eligible destination in `L9-SIGNAL-001`; hard permissions remain `L9-AUTH-002`, `L9-HARD-001` |
| SI-03 Useful routing over adjacency | **NEW + LOCAL** | `L9-SIGNAL-002` for claim-bearing paths; shortest-path algorithms belong to transport/router owner |
| SI-04 Independent evidence vs duplicate copies | **NEW** | `L9-SIGNAL-002` |
| SI-05 Bound fan-out | **NEW + LOCAL** | `L9-SIGNAL-002`; deployment-specific budgets and backpressure remain local |
| SI-06 Reconvergence synthesizes | **NEW** | `L9-SIGNAL-002` preserving source dependence and nonredundant contributions |
| SI-07 Justified topology | **NEW + LOCAL** | `L9-SIGNAL-002/003` conditional; no universal topology progression |
| SI-08 Reciprocal path must make a difference | **NEW** | `L9-SIGNAL-003`; distinguish useful return from ACK/control messages |
| SI-09 Feedback changed consumable state | **NEW** | `L9-SIGNAL-003` plus later-use distinction `L9-SIGNAL-004` |
| SI-10 Recursive episode safeguards | **NEW + LOCAL** | `L9-SIGNAL-003`; specific TTL/quorum/idempotency mechanisms chosen by domain owner |
| SI-11 No global synchronization lap | **NEW + LOCAL** | `L9-SIGNAL-003` excludes default global barrier; necessary domain synchronization remains allowed |
| SI-12 Evidence-proportional write-back | **REUSE** | `L9-EVIDENCE-001`, `L9-ASSURANCE-001`, `L9-OWNER-001`; applicable owner contract |
| SI-13 Truth owner and change stage | **REUSE** | `L9-AUTH-001`, `L9-OWNER-001`, `L9-PROMOTION-001`, `L9-ADMISSION-001` |
| SI-14 Sent, accepted, usable, used | **NEW** | `L9-SIGNAL-004`; SV compounding (net benefit) owned separately by `L9-SVQ-002` candidate |
| SI-15 Path evidence and drag | **NEW + REUSE** | `L9-SIGNAL-004` stage evidence; `L9-ASSURANCE-001`; operational observability and costs remain local |
| SI-16 Selective signal harvest | **REUSE/LOCAL** | `L9-GLOBALIZATION-001`, `L9-PROMOTION-001`; local harvest policy, not new global law |
| SI-17 Unknowns and corrections | **REUSE/LOCAL** | `L9-UNKNOWN-001`, `L9-EVIDENCE-001`; correction routing remains domain-owned |
| SI-18 Hard constraints outrank flow | **REUSE** | `L9-HARD-001`, `L9-AUTH-001/002` |

## Vocabulary dependency and admission checks

The only proposed new Signal terms are in **`SIGNAL_VOCABULARY_CANDIDATES.yaml`**, targeting existing `semantics/vocabulary.yaml#terms`:

- `signal` (evidence-bearing information, not an authoritative fact)
- `signal_propagation` (authorized meaning-preserving movement, not causal value propagation)
- `signal_feedback_episode` (bounded returned information and changed future-use state)
- `signal_consumption` (observed later use, distinct from delivery and positive value)

**Do NOT re-add** canonical `bidirectional_value_propagation`, `value_propagation_mesh`, `future_effect_identity`, or any `strategic_value` term. These already concern quantified causal effects, not the routing of evidence. No universal `signal_envelope`, transport schema, protocol, relay agent, or new memory node is proposed.

**Before admission:** (1) rebind the live exact `.github` revision; (2) check ID/term collision and inspect any admitted Signal owner added since the pinned baseline; (3) produce real cross-domain evidence before claiming globalization proven; (4) independently challenge duplicate-source quorum, forbidden route, false loop convergence, echo-only feedback, and sent-versus-used conflation; (5) obtain exact-digest global authority acceptance. The present pack is **ready for semantic admission review**, but neither the independent evidence threshold nor admission itself is asserted complete.

## Original donor identity trail

Original donor provenance distinguishes colliding `SL-01..05` IDs in `04_SIGNAL_LEVERAGE_KERNEL.md` (new) and `L9_LEVERAGE_LAW_AND_RANKING_INVARIANTS_v1.0.md` (old). It also tracks 16 draft Signal Harvesting Doctrine rules. Earlier `SI-*` maps retained below are historical references, not identifiers to admit; reconcile each via the table above.

### Unmodified historical source-ID mapping

Source identifiers in this table are donor labels, not proposed admitted IDs; consult the explicit rule-disposition table above for final placement. Duplicate `SL-01..05` labels are disambiguated in the Signal file.

| Source | Successor / disposition | Source | Successor / disposition |
|---|---|---|---|
| New-SL-01 | SI-01 | New-SL-02 | SI-02, SI-03 |
| New-SL-03 | SI-04 | New-SL-04 | SI-05 |
| New-SL-05 | SI-06 | New-SL-06 | SI-12 |
| New-SL-07 | SI-13 | New-SL-08 | SI-08, SI-14 |
| New-SL-09 | SI-09 | New-SL-10 | SI-10 |
| New-SL-11 | SI-11 | New-SL-12 | SI-02 |
| New-SL-13 | SI-07 | New-SL-14 | SI-15 |
| New-SL-15 | SI-18 | Old-SL-01 | SI-01 |
| Old-SL-02 | SI-04 | Old-SL-03 | SI-12 |
| Old-SL-04 | SI-14 | Old-SL-05 | SI-10 |
| Draft-SH-01 | SI-16 | Draft-SH-02 | SI-16 |
| Draft-SH-03 | SI-16 (type taxonomy **not** adopted) | Draft-SH-04 | SI-16 (route matrix **not** adopted) |
| Draft-SH-05 | SI-16 (fixed scores **not** adopted) | Draft-SH-06 | SI-09, SI-14 |
| Draft-SH-07 | SI-07, SI-08 (**universal two-way MUST narrowed**) | Draft-SH-08 | SI-07, SI-16 (weighted ranking **not** adopted) |
| Draft-SH-09 | SI-17 | Draft-SH-10 | SI-16 |
| Draft-SH-11 | SI-17 | Draft-SH-12 | SI-17 |
| Draft-SH-13 | OUT OF SCOPE: context-budget/task-contract policy, not a general signal primitive | Draft-SH-14 | SI-01, SI-15 (existing contracts; no new mandatory packet) |
| Draft-SH-15 | SI-09, SI-14 | Draft-SH-16 | SI-14 (aspiration, no monotonic guarantee) |
