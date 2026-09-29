# Release Validation v3.2.1

Candidate status: **unreleased candidate** (no `v3.2.x` tag exists in `Quantum-L9/.github`).

- Semantic YAML files: **40**
- Artifact IDs: **40 unique**
- Canonical artifact models: **1** (`artifact_model.yaml`)
- Global contracts: **21**
- Compiler operations: **9** (8 passes + `composition`)
- Registered solvers: **14**
- Compilation profiles: **node-build@1 (10 stages), node-build@2 (14 stages)**
- ADR pack: **10 accepted ADRs + index**

## Gates

Executed by `python3 ops/validate-semantic-foundation.py` from the repository
root. Each gate fails closed on any reference it cannot resolve.

| Gate | Verifies | Result |
| --- | --- | --- |
| `yaml_structure` | every file parses with duplicate mapping keys rejected; artifact IDs and catalog entry IDs unique | **PASS** |
| `operation_catalog` | `compiler_contract.yaml` `operations` is the compiler-operation catalog; every pass and every receipt operation is in it; the receipt operation domain equals it; every operation has a definition; engine-only operations (`composition`) are declared by an engine contract and are not passes | **PASS** |
| `pass_closure` | every stage operation (both profiles, `vocabulary.semantic_build_stages`) and IR-transition operation is an admitted pass | **PASS** |
| `solver_closure` | every `solver_ref` resolves and is registered for the stage that references it; projection solver selectors name handled classes | **PASS** |
| `validation_subjects` | every required validation declares subjects; each subject is produced by its stage and handled by its solver | **PASS** |
| `stage_identity` | each produced artifact has one stage identity; every stage has a stage projection profile and vice versa | **PASS** |
| `stage_dataflow` | every consumed input is produced by an earlier stage or is a declared external input; ordinals contiguous; no stage cycle | **PASS** |
| `ir_registration` | produced IRs and IR-transition endpoints are registered | **PASS** |
| `derivation_inputs` | `conformance_model` derivation inputs resolve and are produced and consumed before conformance-requirement derivation | **PASS** |
| `artifact_authority` | `artifact_model.yaml` is the only file declaring artifact types, and it is registered and required | **PASS** |
| `schema_binding` | every schematized artifact type declares `schema_ref`; every required semantic field is bound; every bound path exists and is required by the schema | **PASS** |
| `reference_closure` | `l9.*` ID references, invariant references, `governed_by` contracts, profile contracts and schemas, canonical-source paths, projection source classes, compiler-manifest file references | **PASS** |
| `dependency_closure` | semantic-dependency node references resolve; dependency graph acyclic | **PASS** |
| `release_integrity` | exactly one current release directory; every `HASHES.sha256` entry matches; every canonical file hashed; `MANIFEST.md` lists exactly `semantics/*.yaml` | **PASS** |

## Regression cases

`python3 ops/test-validate-semantic-foundation.py` confirms that the current
foundation passes every gate. It also confirms that each of these deliberately broken copies
fails the gate that owns it:

| Case | Failing gate |
| --- | --- |
| undeclared receipt operation (`compilation`) | `operation_catalog` |
| `composition` registered as a compiler pass | `operation_catalog` |
| verb spelling (`project`) in the operation catalog | `operation_catalog` |
| declared operation absent from the receipt domain | `operation_catalog` |
| unknown stage operation (`formalization`) | `pass_closure` |
| unknown solver (legacy `l9.solver/...` ref) | `solver_closure` |
| solver registered to the wrong stage | `solver_closure` |
| projection selector naming an unhandled solver class | `solver_closure` |
| required validation without subjects | `validation_subjects` |
| validation subject not produced by its stage | `validation_subjects` |
| validation subject not handled by its solver | `validation_subjects` |
| second canonical artifact model | `artifact_authority` |
| unbound artifact-model requirement | `schema_binding` |
| binding to a nonexistent schema path | `schema_binding` |
| schematized artifact type without `schema_ref` | `schema_binding` |
| NodeSpec `source_revision` not required | `schema_binding` |
| NodeManifest `source_spec.digest` not required | `schema_binding` |
| NodeManifest `compiler.profile_digest` not required | `schema_binding` |
| NodeManifest `manifest_digest` not required | `schema_binding` |
| future-stage dependency (architecture consumes `conformance_requirement_ir`) | `stage_dataflow` |
| undeclared stage input | `stage_dataflow` |
| conformance ordered before provider bindings | `derivation_inputs` |
| stage identity drift (`technology_bindings`) | `stage_identity` |
| drifted derivation input (`technology_bindings`) | `derivation_inputs` |
| drifted dependency node (`technology_binding_resolution`) | `dependency_closure` |
| dependency cycle | `dependency_closure` |
| unresolved contract reference | `reference_closure` |
| unregistered produced IR | `ir_registration` |
| duplicate YAML mapping key | `yaml_structure` |
| tampered canonical bytes | `release_integrity` |

The same validator was also run against the earlier candidate bytes:

- v3.2.0 candidate (`12ddcfd0b155a8956ff9130e835ad610de416699`): fails `operation_catalog`, `pass_closure`, `solver_closure`, `validation_subjects`, `stage_identity`, `derivation_inputs`, `artifact_authority`, `schema_binding`, `reference_closure` and `release_integrity`.
- Pre-closure v3.2.1 head (`e6dbfef446b0af1f313f5b52bdbd94f061baae64`): fails `operation_catalog`, `validation_subjects`, `artifact_authority` and `schema_binding`.

## Digest chain

- Predecessor: v3.2.0 candidate (unmerged), `HASHES.sha256` sha256 `d6fe8933451f7e7692b817505999f57a1c78ae958efef307395c5aa88ebd6e11`
- This release: `HASHES.sha256` in this directory. Verify it from the repository root with `sha256sum -c docs/semantic-foundation/v3.2.1/HASHES.sha256`.

**Overall: PASS**
