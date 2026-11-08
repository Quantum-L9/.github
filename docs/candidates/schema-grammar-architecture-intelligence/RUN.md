# schema-synthesize run: architecture-intelligence@1

Run on 2026-11-08. `.github` is both the authority and the governance root.

| Pin | Value |
|---|---|
| Authority | `Quantum-L9/.github` @ `f9db38b1035870c0c271249712f2324fff7e0046` (v3.31.0 candidate, ADR-028; stacked on #218) |
| Projection | `l9.projection/architecture-intelligence@1`, `sha256:f4dfd0599742efb66de16d545a2c903a32fd3318d307c419ef51e89933fafec4` |
| Composition | `l9.compose/architecture-intelligence@1`, `sha256:7b40fe358e3f1496a19389742874de622040fe124cb5139b8343680108df09c1` |
| Selector model | `l9.selector-model/global@1`, `sha256:2c2e221c3e5455f3359723d0e1b4da2cdbd02542782b7cd4bb22bfb7cd5aad56` |
| Grammar revision (G1) | `abf6fe82d3a3f18ec71657455fe6072b9099bee7` |
| Governance revision (G2) | `8bd4ed27d4309671a11ab0855c669cb408d47fe3` |
| Compiler | `Quantum-L9/l9-semantic-compiler-engine` @ `e1db49786ce9fb491ca800058aea49a9b98dd7a6` (caller-asserted) |

## Canonical run

```text
$ l9-semantic-compiler schema-synthesize request.yaml
exit=3
{"admission":"not_granted","canonical":false,
 "error":{"code":"UNKNOWN_SEMANTIC_OPERATOR",
          "diagnostics":{"path":"$","reason":"work_limit_exceeded"},
          "message":"experimental grammar projection is not provable"},
 "schemas_emitted":[],"status":"unknown"}
```

Every pin was accepted: the authority, both profiles, the selector model, 24 sources, the
operation, dialect and binding catalog, and 24 grammars. **No schema was emitted.** The run
stops at the first source, `vocabulary`, on a compiler ceiling (B2 below). No grammar is
missing, and no source is inexpressible.

## Diagnostic runs (in memory only)

The compiler's ceilings were raised in the Python process only, to find what lies behind
each stop. These are diagnostics, not a configuration proposal, and their output is not a
candidate the unmodified compiler produced.

| Ceilings raised | Result |
|---|---|
| none | `work_limit_exceeded` at `$` (`vocabulary`) — B2 |
| `PROJECTION_MAX_WORK` | `byte_limit_exceeded` at `$` (`vocabulary`) — B2 |
| work and `PROJECTION_MAX_BYTES` | `candidate_pair_exceeds_size_limit` — B3 |
| work, bytes and `_MAX_CANDIDATE_PAIR_BYTES` | **synthesized**; `verify_candidate_pair` passes |

The diagnostic pair, recorded by digest only:

| Output | Canonical JSON bytes | Digest (`output_digests`, with newline) |
|---|---|---|
| projection schema | 88,813 | `sha256:b417a4993e0aa5b5a664ae2e39aad07814d0d904c46f92c053e5c77c7134280b` |
| composition schema | 89,299 | `sha256:30b9fa05a808e2e8cb81b8f80ab803de35dc31a9a968301f1bd5d809fb28bf22` |
| provenance | 5,926,664 | `sha256:708b192427465929c300aafcc1c6320dd1b6c6d688c8aa5b1c17a09be8b364aa` |

The whole pair is 6,105,257 bytes. The provenance carries 4,550 constraint traces: 3,616
`type`, 928 `additional_properties`, 4 `const` and 2 `required`.

## Blockers, all in the compiler

| # | Ceiling | Measured | Cause |
|---|---|---|---|
| B2 | `PROJECTION_MAX_WORK` 12,000,000 and `PROJECTION_MAX_BYTES` 64,000,000 (`engine/schema_grammar_projection.py`) | `vocabulary` reserves 21,342,120 work | `project_selected_grammar` reserves `4·(nodes·(1+steps+len(selector))+bytes)` work, and 16 times that in bytes, **per selector** before evaluating. `vocabulary` has 45 selectors over 2,419 nodes and 54,867 bytes. |
| B3 | `_MAX_CANDIDATE_PAIR_BYTES` 2,000,000 (`passes/schema_candidate_synthesis.py`) | 6,105,257 bytes | Every constraint trace repeats the full grammar coordinate, about 1.3 KB each. The 3,616 `type` traces alone exceed the cap. |

Both are deliberate bounds, so changing them is a reviewed compiler change. Two options
would clear them without raising a limit: reserving selector work once per source document
rather than per selector, and referencing each grammar coordinate once from the traces
instead of repeating it.

## Resolved here

- **B1** — two mixed-kind fields in `semantics/architecture_patterns.yaml`, fixed by
  normalization in v3.31.0 (ADR-028).
- **Object openness** — the assembler requires every object descriptor to declare
  `additional_properties`. Every grammar now declares `true`.
