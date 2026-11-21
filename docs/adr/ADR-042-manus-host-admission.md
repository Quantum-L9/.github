# ADR-042 — Manus Host Admission and v3.45.0
**Status:** Accepted for semantic-foundation v3.45.0. The repository owner directed the cut on 2026-11-21 in this session: "Cut the v3.45.0 release commit to turn the CI green and finalize the ADR census." This record is the explicit decision record that `semantics/authority_model.yaml#admission_rules` requires. It takes effect when this pull request merges into `main`, and only while the merged `semantics/` tree is the approved tree `5dc33138ee3c92b372b3089a1f538271139a8ad3` named below. A merge that produces a different `semantics/` tree is not covered by this decision. The canonical subject digest was not computed: `check_admission_closure.py` is not present in this tree, so it is recorded as **Unknown** rather than substituted with a different measure.

**Date:** 2026-11-21
**Deciders:** Igor Beylin, repository owner of `Quantum-L9/.github`, who holds `target_class_authority` for canonical global semantics.
**Related:** `Quantum-L9/Cursor-Governance` PR #1127 (adapter capability derivation) and PR #1126 (`feat/manus-adapter-activation`); ADR-041 (the admission shape this record follows); ADR-033 (domain projection architecture).

## Subject
| Item | Value |
|---|---|
| Release | Semantic Foundation **v3.45.0**, additive successor to v3.44.0. Additive only: one binding and one count correction. |
| Pull request | Quantum-L9/.github#278, branch `agent/manus/host-admission`, based on `main` at `08b2d072651083011a708c1ffd07497fc0d0e6b3`. |
| Approved semantic tree | `semantics/` tree `5dc33138ee3c92b372b3089a1f538271139a8ad3`, measured at the cut commit. |
| Subject digest | **Unknown**: not computed. `check_admission_closure.py` is not present in this tree, so the canonical-JSON subject digest was not produced and is not substituted with a different measure. |
| Target class and authority | Canonical global semantics. `Quantum-L9/.github` owns them; its repository owner holds `target_class_authority`. |
| Effective revision | The `main` commit that merges the admission pull request. It is recorded on the merged pull request; it cannot be recorded inside the hashed bytes it admits. |
| Measured against | `main` at `08b2d072651083011a708c1ffd07497fc0d0e6b3`, the merge of #275 that admitted v3.44.0 (ADR-041). |

Admitted definitions:
- `l9.source/domain-consumer-bindings@1` (`semantics/domain_consumer_bindings.yaml`):
  - New binding `l9.domain-consumer-binding/manus@1`. `consumer.kind: host`; `consumer.identity: manus`; `consumer.actor_ref: l9.actor-registry/global@1#manus`; `consumer.surface_refs` exactly `[l9.surface-registry/global@1#manus-cloud]`. No `successor_of`: this is the first binding for this consumer, not a successor to a Manus predecessor.
  - `requires` the five profiles the Claude Code host default requires: `l9.projection/governance@1`, `l9.projection/identity-attribution@1`, `l9.projection/capabilities-dependencies@1`, `l9.projection/contracts-conformance@1`, `l9.projection/evidence-provenance@1`.
  - `conditional`: `l9.projection/architecture@1` under `hosted_skill_requirement`; `l9.projection/strategic-value@1` and `l9.projection/signals@1` under `explicit_task_requirement`.
  - `authority.binding_grants_permissions: false`; `authority.action_authority: externally_resolved`; `unresolved: []`; `predecessor_profiles: []`.
  - Catalog `purpose` prose: "each of six named consumers" becomes "each of seven named consumers". This is a count correction, not a rule change; the catalog's `global_rules`, `consumer_kinds`, `activation_conditions`, `unresolved_blocks`, `composition` and `validation_rules` are unchanged.
- No other canonical source changes. No invariant, contract, vocabulary term identity, source class, projection profile or composition profile is redefined. The subject declares no revision.
- `scripts/validate-semantics.py` gains `manus` in `DOMAIN_BINDING_IDS` and the RC-034 census message moves from six to seven v1 bindings. Following ADR-041's classification, that is validation tooling, not admitted meaning.

## Context
`semantics/actor_registry.yaml` declares `manus` as `kind: agent`, `status: current`. `semantics/surface_registry.yaml` declares `manus-cloud` as `status: current`, "The Manus hosted cloud surface." Both registries have carried those entries across admitted releases. `semantics/domain_consumer_bindings.yaml`, by contrast, declares bindings for gar, strategic-planner, cursor, coding-agent, simple-plan and claude-code (`@1` and its admitted successor `@2`) — seven bindings across six consumers — and none for manus.

The effect is an identity that resolves and a selection that does not exist. A Manus session validates as `l9.actor-registry/global@1#manus` on `l9.surface-registry/global@1#manus-cloud`, and no canonical record states which domain projections that host requires. `Quantum-L9/Cursor-Governance` compensates locally: `governance/host-bindings/manus.yaml` binds the admitted operating plane `l9.projection/cursor-governance-operating-plane@2` plus `l9.projection/coding-agent-execution@1` by recorded owner decision, and carries `canonical_binding_ref: null` precisely because there is nothing canonical to name. A repository-local decision is not a canonical declaration, so the parity with the Claude Code host default exists in practice and not in law.

Two constraints shape the fix. First, an admitted binding is not edited; a change is a new version with `successor_of`. Since no `manus` binding has ever been admitted, `manus@1` is a first version, not a successor. Second, the binding catalog is pinned in three places: the catalog's own consumer count prose, the validator's `DOMAIN_BINDING_IDS` census, and the admitted release's `HASHES.sha256`. All three move together or the tree fails closed.

## Decision
1. Admit v3.45.0 as recorded in `docs/semantic-foundation/v3.45.0/`, containing the `manus@1` binding and the consumer count correction, and nothing else.
2. `manus@1` names exactly one surface, `manus-cloud`. Manus exposes no separately registered command-line interaction surface; the shell a Manus session runs commands in is not a distinct surface, and no `manus-cli` coordinate is created by this record. This matches the reasoning already recorded in the Cursor-Governance host binding.
3. The binding selects the same domain set as the admitted Claude Code host default, because the owner's stated intent is parity with that default rather than a narrower Manus profile. Architecture is conditional on a hosted skill requiring it; strategic value and signals are conditional on an explicit task requirement.
4. The binding grants nothing. `binding_grants_permissions: false` and `action_authority: externally_resolved` restate BINDING-004: a binding selects domain projections only, and every permission, credential and action authority is resolved elsewhere.
5. `unresolved: []`. No coordinate this binding needs is unresolved. The relationship to `l9.projection/cursor-governance-operating-plane@2` is stated in "What admission does not establish" rather than as an unresolved coordinate, because the binding does not require that profile and must not block on it.
6. The validator census is extended in the same change. A binding that the catalog declares but the census omits fails RC-034 by design; admitting the binding without the census edit would leave the tree permanently red.

## Accepted limitations
- **No host hook.** Manus exposes no SessionStart or Stop hook. The binding is made by the adapter's bootstrap (`install.sh` → `bootstrap_agent_environment.sh --surface manus`), so `session_start.autobind` in the local host binding means "no skill gates it", not "the host fires a hook". A Manus session that cannot run the bootstrap cites no operating plane and this binding is not in force for it.
- **Capability breadth is unchanged.** This record selects domains, not endpoints. The adapter's Infisical manifest renders one capability (`github.get_repository`, a projection of one of `github.mcp`'s 21 paths) and excludes the other seven registry entries with named reasons. Admission does not widen that, and should not be read as doing so.
- **Memory is out of scope.** The memory lane is governed by the operating role and groups in `environment/agents/agent_registry.yaml`, owned elsewhere. This record asserts nothing about memory admission.
- **The release record must be cut before the tree is green.** `docs/semantic-foundation/v3.44.0/HASHES.sha256` pins the pre-edit bytes of the binding catalog, so SC-008 fails until v3.45.0 exists with its own inventory and hashes. That failure is the release gate working, not a defect in the binding.

## Consequences
- Consumers that select `l9.source/domain-consumer-bindings@1` produce new bytes. `Quantum-L9/Cursor-Governance` then moves `governance/host-bindings/manus.yaml` from `canonical_binding_ref: null` to `l9.domain-consumer-binding/manus@1`, regenerates its canonical identity projection and receipt, and tightens `validate_manus_adapter.py` to require a resolvable binding instead of tolerating null. This record does not mutate that repository.
- `scripts/validate-semantics.py` reports eight domain consumer bindings and passes RC-034 with the same one binding blocked for activation and four for migration. The negative-case suite is unchanged at 33 cases and still passes.
- Adding a further binding version for Manus is a pinned-census edit plus a `successor_of` binding, exactly as `claude-code@2` was.
- The catalog's consumer count prose moves from six to seven. Any document that repeats the old count is stale from the merge commit.
- Manus becomes the seventh named consumer and the third host-kind consumer, after cursor and claude-code. The other four consumers (gar, strategic-planner, coding-agent, simple-plan) are skill-kind and are unaffected.

## Evidence relied on
- A validator run over a byte copy of the authority tree at `08b2d072651083011a708c1ffd07497fc0d0e6b3` with the `manus@1` binding, the count correction and the census edit applied: `RC-034` PASS, reporting "8 domain consumer bindings resolve to those profiles with distinct host and skill identities and no permission grant", one binding blocked for activation and four for migration, and no pre-existing projection or composition profile changed; `RC-034-NEG` PASS with all 33 negative cases failing closed at their intended field; every other rule PASS. The single remaining failure is `SC-008` against `docs/semantic-foundation/v3.44.0/HASHES.sha256`, which the v3.45.0 cut replaces.
- Shape parity with the admitted `l9.domain-consumer-binding/claude-code@2`: host kind, the same five required profiles, the same three conditional profiles with the same activation conditions, no permission grant, empty `predecessor_profiles`.
- Existence and status of the coordinates named: `manus` (`kind: agent`, `status: current`) in `semantics/actor_registry.yaml`; `manus-cloud` (`status: current`) in `semantics/surface_registry.yaml`.
- **Unknown and not guessed:** the canonical subject digest, the merge commit and any CI run identifier. The pull request and the approved `semantics/` tree are named above; the digest was not computed because its tool is absent from this tree, and the merge commit does not exist until the merge.

## What admission does not establish
- Any credential, role, grant, merge, publication, deployment or execution authority. The binding grants no permission and leaves action authority externally resolved.
- Any capability breadth, endpoint allowlist or secret access. The adapter's one rendered capability and seven named exclusions are unaffected.
- Any replacement of `l9.projection/cursor-governance-operating-plane@2`, which the Cursor-Governance adapter continues to bind at session start. Whether a future `manus@2` absorbs that profile is undecided; this record leaves it undecided rather than implying either answer.
- Any memory admission, token, namespace or group assignment.
- Downstream usability at `main`: no producer run is recorded here, and no consumer's migration is performed by this record.
- That Manus sessions in fact run the bootstrap. The binding is in force for a session that does; a session that does not cites no operating plane.

## Relationship to CANONICAL_LAW.md
These ADRs record why global semantic law was admitted. Workspace policy for
agent conduct and symlink wiring stays in
[`CANONICAL_LAW.md`](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)
in `Quantum-L9/Cursor-Governance`. A semantic ledger is edited in `semantics/`.
A workspace rule is edited in that policy file.
