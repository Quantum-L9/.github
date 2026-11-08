# Source-class dispatch @2: candidate pack

**Status:** LOCAL CANDIDATE, not admitted (`CANDIDATE_NOT_ADMITTED`). Nothing under `semantics/` changes, no release directory is cut and no ADR is written. The owner directed: candidate only, do not admit anything.

**Target:** `Quantum-L9/.github@535400e8c4fb89771c9f08136b4c0309bb5f2a1d`, exact pinned revision. The three @1 records are identical at this revision and at the first pin, `c9bbfaf`. Re-basing past the v3.33.0 and v3.34.0 admissions refreshed the source digests of `invariants` and `contracts`.
**Compiler:** `Quantum-L9/l9-semantic-compiler-engine@d5ce17d01de72c8017e4021fbe43f9eaed2b69de` (merged `main`). It carries the grammar builder for any pair (#35), source-class dispatch (#30) and the B2/B3 synthesis fixes (#34).

## What this proposes

1. **Declarations** (`overlays/`). These record the source-class dispatch protocol the compiler already realizes:
   - the top-level profile field `payload_validation: {protocol: l9.payload-validation/source-class-dispatch@1}` (`PROJECTION-017`, one composition global rule, vocabulary term `payload_validation_protocol`);
   - the registration document type `l9.source-class-payload-schema/v1` (vocabulary term `source_class_payload_schema`);
   - the strict descriptor dialect `l9.schema-dialect/candidate-v2@1` (vocabulary term `strict_descriptor_dialect`). Following the #29/#219 precedent, the dialect itself stays a candidate document (`dialect.yaml`) in each grammar pack. Admitting it as a canonical document, together with the compiler change that would require, is a separate contract.
2. **Successor pairs** (`overlays/projection_profile_additions.yaml`, `overlays/composition_profile_additions.yaml`). These are `identity-assurance@2`, `strategic-planning-context@2` and `strategic-metacognition@2`, each with its `l9.compose/<name>@2`. Each record is its @1 record with only these changes:
   - the id becomes `@2`, with `successor_of` naming @1;
   - the seven sources PATCH-03 narrowed keep every @1 selector and add `$`, so their own top-level `schema` field is selected again;
   - `output.schema` becomes `…/v2`;
   - `payload_validation` is declared.

   PROJECTION-014 compares selectors as strings, so keeping every @1 selector means no selection is removed and no `breaking_changes` is needed.
3. **Grammars** (`../schema-grammar-<name>-v2/`). The compiler builder compiled one source-field grammar per source class: 6 + 9 + 6 = 21, 0 inexpressible.
   - The structural layer is `type`, `fields` and `items` only, with explicit `additional_properties: true`.
   - No `required`, `const`, `enum` or `min_items` is inferred from observed values.
   - A restored source's `schema` field is drafted as `type: string`, never `const`.
4. **Registered output schemas** (`overlays/registered_schemas/`). These were rendered by `payload_validation.registered_schema_documents()` from the pinned candidate synthesis.
   - Each schema governs exactly one profile and carries one strict descriptor per source class, with no legacy union grammar.
   - They say `canonical: true` only so the rehearsal's authority loader can read them. They also carry `admission: not_granted`, and nothing registers them in `semantics/`.

## Results (`evidence/rehearsal.json`)

| Pair | Grammars | Synthesis | Producer: project + compose |
| --- | --- | --- | --- |
| `identity-assurance@2` | 6, 0 inexpressible | candidate pair produced | 7 receipts PASS, coverage complete; `actor_registry` and `surface_registry` keep `schema` |
| `strategic-metacognition@2` | 6, 0 inexpressible | candidate pair produced | 7 receipts PASS, coverage complete; the restored source keeps `schema: l9.schema-definition/v1` |
| `strategic-planning-context@2` | 9, 0 inexpressible | candidate pair produced (453,301 bytes) | 10 receipts PASS, coverage complete; the four restored sources keep `schema: l9.schema-definition/v1` |

Every PASS receipt reports `payload_schema: pass` with `dispatch_basis: verified_profile_output_schema_and_verified_source_class`: the output schema comes from the verified profile and source class, never from a payload field.

### Formerly blocked: `strategic-planning-context@2`

The first rehearsal reported `candidate_pair_exceeds_size_limit` for this pair. That came from compiler code that predated #34; its B3 fix shares trace provenance and brings the pair to 453,301 bytes, about 23% of the 2,000,000-byte cap. No cap was raised. That first rehearsal also exposed a defect, now fixed: `rehearse.py` ran whichever compiler its interpreter had installed. It now imports only from `--compiler-root` and refuses to run otherwise, and it records the module that executed in `evidence/rehearsal.json` (`compiler.executed_module`).

## Reproduce

```bash
# from this repository's root, with the compiler checkout at the pinned revision
python3 docs/candidates/source-class-dispatch-v2/rehearse.py \
  --disposable <new directory outside this checkout> \
  --compiler-root <l9-semantic-compiler-engine checkout> --check
python3 -m unittest discover -s docs/candidates/source-class-dispatch-v2/tests
```

The compiler checkout's HEAD must equal the pinned revision. When it has moved on, clone it at that revision and pass `--compiler-root <clone> --compiler-python <an environment with the compiler's dependencies>`. The compiler code is always imported from `--compiler-root`, never from that environment.

`rehearse.py` clones this repository into the disposable directory, pins `535400e` and commits the rehearsal steps A (overlays), G1 (grammars), G2 (catalog) and R (registrations) with a fixed identity and dates. Two fresh clones produced the same four commit ids (`d5a656c`, `6a70a5c`, `40a01f6`, `916b1f3`) and the same 42 files. The grammar packs' pins name those rehearsal commits, which exist only in a rehearsal clone. `rehearse.py` never pushes, never opens a pull request and grants no admission.

## Proposed destinations, on a future admission (not done here)

| Overlay | Destination |
| --- | --- |
| `projection_profile_additions.yaml` | `semantics/projection_profiles.yaml#projection_profiles` |
| `projection_rule_additions.yaml` | `semantics/projection_profiles.yaml#validation_rules` |
| `composition_profile_additions.yaml` | `semantics/composition_profiles.yaml#profiles` |
| `composition_global_rule_additions.yaml` | `semantics/composition_profiles.yaml#global_rules` |
| `vocabulary_additions.yaml` | `semantics/vocabulary.yaml#terms` |
| `registered_schemas/*.yaml` | `semantics/` plus `generic_compiler_manifest.yaml#requires.artifact_schemas` |

Admission would follow `.claude/skills/l9-projection-admission`: register, cut a successor release, then admit on an explicit owner decision.
