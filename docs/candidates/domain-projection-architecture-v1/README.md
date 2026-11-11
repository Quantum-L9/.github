# Domain Projection Architecture v1: candidate pack

**Status:** `CANDIDATE_NOT_ADMITTED`. The subject is registered in `semantics/` and cut as Semantic Foundation
**v3.36.0, ADDITIVE SUCCESSOR CANDIDATE**. Nothing here is admitted. Admission is the owner's decision for the exact
subject; `ADMISSION_DECISION_DRAFT.md` is the record an accepted ADR would copy, and it decides nothing.

Rule of the design: a domain projection exposes canonical meaning, a domain consumer binding selects that meaning,
and composition verifies compatibility. None of the three creates semantic authority.

## What is registered (v3.36.0 subject)

| Surface | Items |
| --- | --- |
| `semantics/invariants.yaml` | `L9-SVQ-001`, `L9-SVQ-002`, `L9-SIGNAL-001`..`004`, copied byte-for-meaning from `docs/candidates/strategic-value-signal-qualitative-admission/` (PR #234; verified record-equal) |
| `semantics/vocabulary.yaml` | `qualitative_strategic_value_screen`, `realized_strategic_compounding`, `signal`, `signal_propagation`, `signal_feedback_episode`, `signal_consumption` (PR #234, record-equal); new `domain_projection`, `domain_consumer_binding` |
| `semantics/contracts.yaml` | `l9.contract/domain-composition-compatibility@1`, `l9.contract/domain-composition-provenance@1` |
| `semantics/projection_profiles.yaml` | profile class `domain`; eight profiles `l9.projection/{architecture, strategic-value, signals, governance, evidence-provenance, contracts-conformance, capabilities-dependencies, identity-attribution}@1`, each declaring source-class dispatch |
| `semantics/composition_profiles.yaml` | eight `l9.compose/<domain>@1`, source-class namespaced |
| new ledger `semantics/domain_projection_model.yaml` | closed domain set, owned questions, invariant closure, boundaries, negative witnesses, `DOMAIN-001..010` |
| new ledger `semantics/domain_consumer_bindings.yaml` | six bindings, `BINDING-001..004`, `COMPOSE-001..005` |
| 16 registered payload schemas | `semantics/domain_<name>_{projection,composition}.schema.yaml`, rendered by the compiler |
| registry | both ledgers in `canonical_sources.yaml` and `generic_compiler_manifest.yaml#semantic_catalogs`; schemas in `#artifact_schemas` |
| digest cascade | `contracts.yaml#derivation`, `capabilities.yaml`, `lifecycle.yaml`, `receipt_catalog.yaml` rebound from final bytes (`tools/rebind_digest_cascade.py --check`) |
| validator | `scripts/validate-semantics.py` RC-034 and RC-034-NEG (28 adversarial cases plus a mapping-order determinism check) |

No existing profile or composition changes: RC-034 pins both predecessor catalogs by canonical-JSON digest
(DOMAIN-010), and they equal `main` at `b6db83d`.

## Where this departs from the design pack, and why

| Design pack | Registered | Reason |
| --- | --- | --- |
| `semantics/domain-projections/*.yaml` as modular files | not created | The pack forbids a second canonical catalog. Profiles live only in `projection_profiles.yaml`; `tools/render_domain_profiles.py` is the design source and `--check` proves the catalog equals its rendering. |
| `l9.consumer-binding/<x>@1`, `semantics/consumer-bindings/` | `l9.domain-consumer-binding/<x>@1` in one ledger | `consumer_binding` is an admitted term (product release bound to a consumer), and `domain_binding` is already a fixture-pattern node. Reusing either would redefine admitted meaning without a declared revision. |
| `l9.composition.compatibility@1`, `l9.composition.provenance@1` | `l9.contract/domain-composition-{compatibility,provenance}@1` | `contracts.yaml` is the single global contract catalog; contract ids are `l9.contract/<name>@N`. Provenance specializes `provenance-and-coordinate@1` and the ADR-021 binding conventions rather than restating them. |
| Behavioral `forbidden` tokens on profiles (`validation_as_admission`, …) | profile `forbidden` uses only criterion-backed categories; behavioral prohibitions are `forbidden_interpretations` in the domain model | PROJECTION-016: a category without a declared criterion stays `unresolved`, so downstream could never PASS. The prohibitions are kept, verbatim, as consumer obligations, and RC-034 pins them. |
| Design invariant lists | computed closure | DOMAIN-006: primary anchors + common closure (`AUTH-001, PROV-001, UNKNOWN-001, COMPAT-001, PROJECTION-001`) + mandatory closure + the `source_invariants` of every selected contract, exact and in ledger order. Architecture, for example, selected no invariant in the pack. |
| Strategic Value selects `strategic_value_model` metadata | the complete normative body (18 sections, the planner's set plus `governed_by`) and all 13 SV terms | The pack's own required correction. |
| `contracts-conformance` selects `$.contracts` | `$.contracts` plus every invariant those contracts cite (33) | Contracts are closed over their source invariants. |
| `D16` source order changes digest | determinism check: re-keying every mapping leaves all eight profile digests unchanged | Sequence order is semantic (selector order); mapping order is not. |
| Proposed ADR in `docs/adr/` | `ADMISSION_DECISION_DRAFT.md` here | The ADR records the owner's decision and is written at admission (ADR-025 precedent; candidate commit `451a87c` carried none). |

## Evidence

- **Producer rehearsal** (`rehearse.py`, `evidence/rehearsal.json`): compiler
  `Quantum-L9/l9-semantic-compiler-engine@eeac5d28f9f1a44e72287190b9087d06aeb4d574` (0.10.0), imported only from
  `--compiler-root`. See `evidence/rehearsal.json` for the base commit, grammar counts, synthesis and per-receipt
  results; `evidence/*.tar.gz` hold the synthesis requests, synthesized pairs and producer outputs.
- **Migration equivalence** (`tools/migration_equivalence.py`, `evidence/migration_equivalence.json`).
- **Validator**: `make validate check test`, RC-034 and RC-034-NEG.

Reproduce:

```bash
python3 docs/candidates/domain-projection-architecture-v1/tools/render_domain_profiles.py --check
python3 docs/candidates/domain-projection-architecture-v1/tools/rebind_digest_cascade.py --check
python3 docs/candidates/domain-projection-architecture-v1/tools/migration_equivalence.py --check
python3 docs/candidates/domain-projection-architecture-v1/rehearse.py \
  --disposable <new directory outside this checkout> \
  --compiler-root <l9-semantic-compiler-engine at eeac5d2> --check
```

## Open blockers (stated, not filled)

| Blocker | Blocks | Owner |
| --- | --- | --- |
| Owner admission decision for the exact v3.36.0 subject | `ADMITTED` | repository owner |
| Strategic Planner has no locatable repository or entrypoint | activation of `l9.domain-consumer-binding/strategic-planner@1` | owner of the strategic-planner consumer |
| Migration dispositions for GAR (123 missing nodes), Strategic Planner (14) and Cursor (24) predecessor selections | consumer migration of those bindings | each consumer owner |
| Authority-neutrality review of selections the coding-agent domains add (133 nodes, 0 missing) | consumer migration of `coding-agent@1` | Cursor-Governance owner |
| Whether the Cursor host binding replaces the Cursor-Governance operating-plane profile | consumer migration of `cursor@1` | Cursor-Governance owner |
| No v1 domain owns game-theory interaction semantics; the planner's GT vocabulary is among its missing nodes | planner migration | owner decision: a ninth domain is a v2 change |
| Runtime composition of a binding's domain set (compatibility and provenance contracts) is not implemented by compiler 0.10.0 | `DOWNSTREAM_USABLE` for bindings | `l9-semantic-compiler-engine` |
| Post-merge trusted replay on `main` | `DOWNSTREAM_USABLE` | agent, after admission |

No consumer is switched. Every historical profile stays resolvable.
