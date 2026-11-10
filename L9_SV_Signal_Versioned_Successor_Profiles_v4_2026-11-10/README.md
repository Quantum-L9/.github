# Strategic Value + Signal: complete versioned projection successors

**Candidate ZIP, 2026-11-10.** No PR was changed, no admission occurred, no compiler projection was run, and no consumer was activated by this package.

## Correct version identities

| Consumer | Full admitted predecessor | Complete proposed successor | Source classes | Composition |
|---|---|---|---:|---|
| GAR | `l9.projection/gar-architecture-observer@1` | **`l9.projection/gar-architecture-observer@2`** | 8 (7 retained + `strategic_value_model`) | New `l9.compose/gar-architecture-observer@1` |
| Strategic Planner | `l9.projection/strategic-planner-value@1` | **`l9.projection/strategic-planner-value@2`** | 5 (all retained) | Successor `l9.compose/strategic-planner-value@2` |
| Cursor Operating Plane | `l9.projection/cursor-governance-operating-plane@2` | **`l9.projection/cursor-governance-operating-plane@3`** | 8 (all retained) | **None**: existing operating-plane on-demand retrieval remains the owner |

**This fixes v3's error:** no patch or append fragment is required to *understand* any proposed successor. Each profile file is a complete single catalog-native record, including **all predecessor selectors, added SV/Signal selectors, consumer, purpose, output version, forbidden semantics, dispatch protocol, and explicit `successor_of`**. Composition records are complete, self-contained definitions, not snippets. There is no separate qualitative-only projection operating in parallel as a competing version.

## Complete package content

- **`profiles/`**: exactly three complete successor profile records.
- **`compositions/`**: GAR's first complete composition and Planner's versioned successor composition. Cursor has no new composition service or mandatory composed payload.
- **`schemas/`**: five full source-class-dispatched projection/composition payload schemas, each with its own artifact ID, output schema ID, governed-by coordinates, selected source-class descriptor shapes, and producer validation protocol.
- **`consumer-contracts/`**: three complete, bounded *consumer-local candidate* contracts specifying activation, inputs, decision/output boundaries, failure behavior, and negative witnesses. **Not** proposed global L9 contracts or new agents.
- **`compatibility/predecessor_selection_contract.yaml`**: exact predecessor selector counts and digests so a standalone validator can prove none were removed, replaced or reordered.
- **`SOURCE_BINDING.yaml`**: immutable comparison root, PR #234 donor identities and current unadmitted status.
- **`tools/validate_successors.py`**, **`tools/test_negative_controls.py`**, **`VALIDATION.json`**, **`SHA256SUMS.txt`**: reproducible local evidence, not live semantic compiler receipts.

**Not included:** any copy or mutation of the six candidate invariants, six candidate vocabulary terms, existing `.github` semantic ledgers, patches/overlays, a mathematical solver, runtime hook, new authority owner, or actual canonical-source projection receipts.

## Semantic preservation

1. **GAR@2** retains every original `gar-architecture-observer@1` selector for vocabulary, invariants, contracts, capabilities, patterns, authority, and lifecycle. It adds qualitative SV/Signal records, source-bound quantitative demarcation, and whole-record selected rules. GAR's existing architecture observer and reasoning remain the same concern; no new reasoning kernel.
2. **Planner@2** retains all numerical model selectors from `strategic-planner-value@1` and the `l9.contract/strategic-value-assessment@1` obligations. Additional qualitative interpretation does *not* turn a prose appraisal into five-bucket quantitative SV, supply Numeric/Probabilistic/Formal owner evidence, mandate Q/V, or create Strategic Authority. Existing GT-only and numeric SV paths remain separately valid.
3. **Cursor@3** retains all eight source classes and all selectors of operating-plane@2. The six terms and rules are additionally addressable **only after canonical admission and actual verified projection**. Existing SessionStart stays status-only and existing on-demand owner handles selection. Profile admission is not a new boot hook or permission grant.
4. Signal topology, delivery, acceptance, later consumption and genuinely observed positive net effects are distinct. An unchanged echo, multiple forwards from one origin, new catalog registration, or successful projection is **not** compounding evidence.
5. No source-class descriptor or composition merges conflicting canonical meanings. Selected source records stay in distinct namespaces with exact provenance and producer checks.

## Admission and activation order

1. **First**: independent owner review and admission (or explicit rejection) of the exact PR #234 six candidate invariants and six terms into canonical `semantics/invariants.yaml` / `semantics/vocabulary.yaml`. A partial/reworded admission invalidates the dependent selectors and requires a new candidate revision; **do not silently substitute**.
2. Bind new **current immutable** `.github/main` SHA, registry and profile/source owners. Review the three new profile versions, two composition records, five schemas and consumer-local contracts for actual compatibility. Their files are **candidates intended for existing catalog owner registration**, not canonical by virtue of `canonical: true` in a proposed schema.
3. Have the applicable source owner register the complete successor records into the existing canonical `projection_profiles.yaml` and `composition_profiles.yaml`, and the five schemas under the existing compiler schema registry. Do not overwrite historical profile records, change numerical SV, or register arbitrary local file paths as new semantic owners. Schema registration and profile admission require actual owner authorization.
4. Run **real** Semantic Compiler with the admitted source revision to produce per-class payloads. Check selector equivalence, exact record membership, source-class descriptors, exact source digests, component provenance, currentness, repeatability and genuine producer PASS receipts. Local YAML tests do not establish these.
5. Independently test both consumer variants against their predecessors on actual decisions; only migrate consumers with demonstrated improvement in correctness and acceptable retrieval/runtime cost. Cursor migration to @3 is opt-in; no unverified default SessionStart change.

## Deliberate non-goals and blocker

PR #234 was **open/unmerged** when this package was built, while `.github/main` was `dc96a8ae9f31e359bb0e52a0b1d778fc8f265d99`. Therefore the six new terms/rules **do not resolve as admitted canonical selectors at that revision**. These successor profiles cannot legitimately be compiled or served as canonical there. All local checks concern proposal structure, with no simulated external receipts.

### Useful negative tests

- Drop a predecessor selector, corrupt an output schema ID or version, remove a required candidate term or invariant, swap a source-class ref, relax composition conflicts, or claim admission; local validator rejects the altered proposal.
- Feed a copied signal from three fan-out routes: a consumer must not infer independent evidence.
- Mark a later delivered artifact but no observed net improvement: a consumer must reject positive *realized* compounding.
- Ask for a numerical SV result from a qualitative story: the consumer must route to the numeric SV assessment contract and actual numerical-owner evidence.
- Attempt a Cursor SessionStart semantic payload or a merge/action permission derived from projection context: reject independently of profile compilation status.

**Devil's advocate:** A complete versioned profile record still requires entry in the canonical catalog, valid exact source selectors, independently validated profile version transition, producer evidence and actual consumer migration. It is self-contained as a *proposal*, not a deployable production projection.
