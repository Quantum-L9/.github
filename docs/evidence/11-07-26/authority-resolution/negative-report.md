# Authority-resolution producer negative qualification

## Outcome and scope

Authority checkout `/home/ubuntu/l9-projection-campaign/code-pr` was at **290bcd90378577392640cea9c6053c178423f0da**. The actual producer source was imported from `/tmp/l9-projection-qa.nBKv8FWo/compiler/src` at compiler commit **943db9a462d35ba66771a700ece77c746295f591**, using `/tmp/l9-projection-qa.nBKv8FWo/venv/bin/python`. This is a producer/API qualification, not candidate-consumer qualification.

| Distinct checks | PASS | FAIL | BLOCKED |
|---|---:|---:|---:|
| Positive controls: four source projections and one composition | 5 | 0 | 0 |
| Requested negative controls, including direct missing-namespace schema check | 10 | 0 | 0 |
| Separate nonempty `string_list` capability check | 0 | 1 | 0 |
| **Total** | **15** | **1** | **0** |

The five producer controls really returned receipt and reverification result `pass`, not merely successful execution, with zero unresolved criteria. Each receipt passed the pinned producer receipt validator and canonical receipt schema; its source/profile/output/governing coordinates were cross-checked against the actual emitted artifacts and exact input pins. Composition also bound all four component references and digests. [Detailed receipt binding checks](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/receipt-bindings.json).

The separate failed capability check is a known limitation, **not a passed negative control**. A repeat in an independent scratch subdirectory reproduced all counts and exited **1**, reflecting that failure. The first run's shell pipeline did not capture its exit status; no first-run exit code is asserted. See [run log](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/run.log), [repeat log](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/replay.log), and [repeat exit code](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/replay-exit-code.txt).

## Genuine source and profile coordinates

The producer resolved four real source pins at the requested authority revision. These semantic digests are not file-byte SHA-256s. Complete source refs, classes, paths, and pins are in [coordinates.json](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/inputs/coordinates.json).

| Source ref and actual file | Semantic digest |
|---|---|
| `l9.source/invariants@1`, `semantics/invariants.yaml` | `sha256:771e3509703ea7d177a4bbac965e126f77f390ec359d1544854d95ec4374082a` |
| `l9.source/contracts@1`, `semantics/contracts.yaml` | `sha256:f1fcc979534d0aa34783710657ae36d765f7078e6ab20dc3b11a31d576539d79` |
| `l9.source/authority-model@1`, `semantics/authority_model.yaml` | `sha256:9303ee5910f3db2b10abe71bdcb5e360128ee77e7e4bd3ebe9e05dba77018620` |
| `l9.source/artifact-model@1`, `semantics/artifact_model.yaml` | `sha256:21f8bb783d7611ae1b3c60474c6ca31f6096f29d7ef0e94ef81f12e6d2defe09` |

Projection profile `l9.projection/authority-resolution@1` was pinned to `sha256:7cfc37826814a450ceb9cd50fb75d55ed09520c72015eba01e9a7ca9f53d32ea`; composition profile `l9.compose/authority-resolution@1` to `sha256:d7d5a565b94588c8acf70c737d1a24e61967f183a96f3af2e89e1a2b4f78f34b`. Original producer outputs and receipts are under `/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/outputs/`; copied source inputs and exact requests are under `/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/inputs/`.

## Negative results

All cases below have actual `PASS` positive controls beforehand. `—` means that the producer exception has **no** `criterion` field. Each result links to the full typed exception, diagnostics, exact input details, and assertions. The direct schema result is a returned list, **not** a typed exception; `SCHEMA_VIOLATION` in the machine file is a harness expectation label, not a producer error code.

| Case | Observed producer result | Status |
|---|---|---|
| [Missing source pin, not source file](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/01_missing_source_pin.json) | `InvalidRequest` / `INVALID_REQUEST` / criterion `—`; exactly `l9.source/invariants@1` absent from pins while its real file exists | PASS |
| [Wrong projection profile digest](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/02_wrong_profile_digest.json) | `RevisionMismatch` / `REVISION_MISMATCH` / `profile_digest` | PASS |
| [Changed projection payload without redigest](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/03_payload_without_redigest.json) | `RevisionMismatch` / `REVISION_MISMATCH` / `projection_digest` | PASS |
| [Changed projection payload with real producer envelope redigest](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/04_payload_with_producer_redigest.json) | `SemanticDivergence` / `SEMANTIC_DIVERGENCE` / `selection_equivalence` | PASS |
| [Missing source component](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/05_missing_source_component.json) | `InvalidRequest` / `INVALID_REQUEST` / `source_coverage`; missing class `invariants` | PASS |
| [Duplicate real component](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/06_duplicate_component.json) | `AmbiguousSemantics` / `AMBIGUOUS_SEMANTICS` / `duplicate_source` | PASS |
| [Wrong composition profile pin](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/07_wrong_composition_pin.json) | `RevisionMismatch` / `REVISION_MISMATCH` / `composition_profile_digest` | PASS |
| [Receipt claim tamper, no redigest](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/08_receipt_tamper_without_redigest.json) | Producer `validate_receipt_document`: `InvalidRequest` / `INVALID_REQUEST` / criterion `—`; message `prior compilation receipt digest mismatch` | PASS |
| [Omit composed `artifact_model`, producer-redigest, real composed verifier](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/09_omitted_namespace_redigested_verify.json) | `SemanticDivergence` / `SEMANTIC_DIVERGENCE` / `composition_equivalence` | PASS |
| [Direct `schema_violations` on composed payload without namespace](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/10_missing_namespace_direct_schema.json) | `['$.artifact_model: required field missing']`; intact payload gave `[]` | PASS |

For the redigested composition case, `verify_composed_projection` rejected on recomposition equivalence before its payload-schema stage; its first divergence was the recomposed `$.composition_digest`. The direct schema check independently demonstrates the missing-namespace violation. Receipt tamper was checked using the producer's receipt helper; the producer composition call was not claimed to ingest that receipt.

## Known limitation: `string_list` minimum not enforced

The pinned compiler's actual schema descriptor at `semantics/authority_resolution_projection.schema.yaml:properties.contracts.items.properties.source_invariants` is `{type: string_list, min_items: 1}`. Direct `schema_violations([], descriptor)` returned **`[]`**, accepting the empty list. The same empty value in a copied actual contracts projection payload also produced **`[]`**; intact payload and a nonempty list likewise returned no violations. This **fails the requested nonempty-list capability check**. In the pinned implementation `min_items` is checked for type `array`, not type `string_list` (`passes/validate.py:171–174,225–228`). This is a direct schema-validator observation, not a claim that a changed projection would survive the separate producer selection-equivalence verification. [Full check](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/cases/11_string_list_min_items_capability.json).

## Integrity and boundaries

Final checks show both checkouts' HEAD, porcelain status, and all tracked file byte hashes unchanged relative to the start; both originally generated output/receipt sets also retain their original SHA-256 hashes. [Final integrity evidence](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/final-integrity.json), [first original hashes](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/outputs/original-sha256-before.json), and [repeat-original integrity](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/logs/replay-launcher-result.json). There is no candidate-consumer verifier binding, so no independent candidate-consumer rejection is claimed; no historical revision change was introduced or tested, so no real historical staleness is claimed. No code, profiles, schemas, compiler, consumer, release, repository, PR, or remote was modified or remediated.

The [machine-readable summary](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/summary.json), [qualification harness](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/qualify.py), [receipt-binding harness](/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/receipt_bindings.py), and all case inputs, copies, receipts, results, and logs reside under `/home/ubuntu/l9-projection-campaign/authority-schema-run/negative/`.
