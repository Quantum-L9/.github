# Release Validation v3.40.0

Release status: **additive successor candidate**. Admission requires the repository owner's explicit decision for this exact subject; no admission is claimed.

## Closure

- **SC-001** parses 117 canonical sources as YAML mappings.
- **RC-035** proves the three schemas are registered profile-less schemas (const is an `ir_catalog.yaml` id, `governed_by.contracts` defined, enforcement names the registered solver of the stage that produces or consumes them), validates every positive witness (17 checks across 6 witness files: fixture IR, conformance IR, harness surface, the synthetic manifest closure, product files against a RepositorySpec slice, and reference evaluations including the outcomes that hold), rejects each of 107 falsifying fixtures under the semantic rule it names, falsifies every checked, evaluated and cross-document rule at least once, checks the rule lists against the schemas, pins `pytest/v1` by canonical-JSON digest, requires `pytest/v2` to succeed it with every fixture-IR form mapped, keeps the product-topology conformance fields optional with `harness_surface_ref` as `{ref, digest}` and exactly four typed product-file refusals, requires the manifest closure digest to be optional and to exclude exactly `manifest_digest`, `closure_digest` and `conformance.compilation`, and requires stage 8 to consume `product_fixture_cases` and `product_harness_surface`. **RC-035-NEG**: 20 registration and successor-surface mutations fail closed.
- **RC-013**: `vocabulary.yaml#semantic_build_stages` and `l9.compilation/product-build@1` agree on stage 8 consumes (now including `product_harness_surface`).
- **Existing manifests**: `product_manifest.schema.yaml#required` is unchanged; `closure_digest` and `conformance.compilation` are optional and checked only when present.
- **Existing topologies**: `conformance.required` is unchanged; neither `templates/semantic-authoring/product-topology.yaml` nor the State topology (`Quantum-L9/l9-wip@ce0c4973`) carries the new optional keys, and the v1 interpreter checks declared fields only when present, so their validation is unchanged.
- **SC-008** proves this release record: **117** canonical sources, **37** ADRs, and a hash inventory of every canonical source, every ADR plus the index, and this release's Markdown.
- No derivation coordinate changed: no invariant, contract or capability ledger is touched.
- Gates `make validate`, `make check` and `make test` are run on the amended tree (results in the candidate report).

`scripts/validate-semantics.py` exits 0 with 63 PASS lines and no FAIL (tree rebuilt on `f8e44d1`); `make validate`, `make check` and `make test` exit 0 (recorded in the candidate report to the coordinator).

## Release integrity

`HASHES.sha256` inventories the final semantic bytes, all ADRs plus the index, and this release's Markdown. It was generated with the v3.21.0 procedure: `sha256sum` with `./` paths, sorted with `LC_ALL=C sort -k2`. Prior release directories are byte-identical.

## Grading instrument changed in this release

The admission gate that grades this release changed in the same branch, before this release was cut: commit `c85ca1b` adds an IR-schema registration rule to `.claude/skills/l9-projection-admission/scripts/check_admission_closure.py` (`Registration.schema` → `_ir_schema`). Without it, every profile-less `l9.schema-definition/v1` in `artifact_schemas` is `INCOMPLETE` ("output of 0 profiles"), which made this release (and v3.30.0) unregistrable. The change was authorized by the operator (decision F1-D1 = A, relayed verbatim by the R5 coordinator). It is purely additive: the 193 pre-existing skill tests stay green (201 passed at this tip, with `L9_SEMANTIC_COMPILER_SRC` naming a clean checkout of the compiler at `eeac5d2`; the session's own compiler checkout carries untracked governance wiring, which the gate correctly refuses as not an exact revision) and 8 new tests cover the positive case and each refusal (IR id not in `ir_catalog.yaml#irs`, missing catalog, IR const also a profile output, missing / empty / undefined `governed_by.contracts`, governing profile named). The rule's result for v3.30.0's schema is evidence only and is not an admissibility claim.

## Admission state

Not admitted. Discovery (`discover_admission_subject.py`, base = the v3.39.0 commit `f8e44d1536cb218de41dde4685c606a4d6460915`; first measured from the v3.36.0 admission commit `dcd9d00` with the same result) finds exactly this subject: schemas `conformance_ir.schema.yaml`, `fixture_ir.schema.yaml` and `harness_surface.schema.yaml`, and canonical sources `l9.source/binding-catalog@1`, `l9.source/compilation-profiles@1`, `l9.source/ir-catalog@1`, `l9.source/product-manifest-schema@1`, `l9.source/product-topology-schema@1` and `l9.source/vocabulary@1` (residual content; no registry entry changes, so no revision); no unclassified change, no missing dependency, no changed derived coordinate. The admission gate (`check_admission_closure.py --require released`) is run on the committed candidate; the target rung is `RELEASED_CANDIDATE`. The owner decision covers the three schemas (including the interim law-input substitution in `fixture_ir.schema.yaml#interim_law_input`, the pinned evaluation semantics and the law-derived obligations), the product-topology conformance fields and product-file resolution, the optional manifest closure digest, the `l9.harness-surface/v1` entry in `ir_catalog.yaml`, the stage 8 inputs in `compilation_profiles.yaml` and `vocabulary.yaml`, and `pytest/v2` in `binding_catalog.yaml`.

Caveat carried from step 0: python-gate-node@1 lives in the same admitted binding_catalog.yaml host and the gate cannot distinguish it at entry level; per campaign direction it is NOT treated as admitted (ADR-026 still says candidate). F1 does not depend on it. `binding_catalog.yaml` joining this subject does not admit it: ADR-037 names only `pytest/v2` in that ledger. The compiler agent's test-only-lock rehearsal is separate evidence and is not part of this record.

## Admitted-base measurement (M1)

The admission gate is run with the admitted base named explicitly:

`check_admission_closure.py --checkout . --subject <subject> --require released --main-ref origin/main --admitted-base v3.39.0`

Result at this candidate: exit 0, `RELEASED_CANDIDATE`; registration, release, validator, make and scope closure pass. The gate reports one verification gap on the base, not on this subject: "ADR-036-technical-coordination-role-projection.md: names candidate 3f9b90a6a980, which does not carry the approved semantics/ tree" (`verified_base: v3.38.0`). ADR-036's 'Approved semantic tree' row names the approved tree, the approved release-cut candidate `80b0ffb4` and, as superseded, the earlier candidate `3f9b90a6a980`; `verify_admission_evidence.py` treats every commit named in that row as a candidate that must carry the approved tree, so the superseded one fails the check, and without `--admitted-base` the gate resolves the admitted base to v3.38.0 and attributes v3.39.0's four identities (`l9.projection/technical-coordination@1`, `l9.compose/technical-coordination@1` and their two payload schemas) to this subject's scope (exit 1, `REGISTERED`).

Out of scope for this release: the gap belongs to ADR-036 or to the gate's candidate parsing, both owned outside this subject. This release does not edit ADR-036, the gate, or any v3.39.0 artifact, and it claims nothing about v3.39.0's admission evidence.
