# GMP-133

**Task:** Unblock strategic-planning-context@2 candidate: rehearse.py executes the pinned compiler; re-pin pack to compiler main d5ce17d (includes #34) and add SPC@2 registrations and evidence; candidate only, nothing admitted
**Tier:** RUNTIME

## TODOs

- T1: docs/candidates/source-class-dispatch-v2/rehearse.py REPLACE rehearse.py executes the pinned compiler: every compiler subprocess (builder phases, schema-synthesize, projection-coordinates, project, compose) runs with PYTHONPATH=<compiler-root>/src and the CLI is invoked through cli.main, and the run records which l9_semantic_compiler module path executed
- T2: docs/candidates/source-class-dispatch-v2/MANIFEST.json REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T2.2: docs/candidates/source-class-dispatch-v2/evidence REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T2.3: docs/candidates/source-class-dispatch-v2/overlays/registered_schemas REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T2.4: docs/candidates/schema-grammar-identity-assurance-v2 REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T2.5: docs/candidates/schema-grammar-strategic-planning-context-v2 REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T2.6: docs/candidates/schema-grammar-strategic-metacognition-v2 REPLACE Re-pin to merged compiler main d5ce17d and re-emit: strategic-planning-context@2 now synthesizes (453,301 bytes under #34); add its two registered schemas and producer evidence
- T3: docs/candidates/source-class-dispatch-v2/tests/test_candidate_pack.py REPLACE Update tests, README and checksums: all three pairs synthesize and pass; assert the executed compiler module path is the pinned root
- T3.2: docs/candidates/source-class-dispatch-v2/README.md REPLACE Update tests, README and checksums: all three pairs synthesize and pass; assert the executed compiler module path is the pinned root
- T3.3: docs/candidates/source-class-dispatch-v2/SHA256SUMS.txt REPLACE Update tests, README and checksums: all three pairs synthesize and pass; assert the executed compiler module path is the pinned root
