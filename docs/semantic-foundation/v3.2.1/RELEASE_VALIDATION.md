# Release Validation v3.2.1

- Semantic YAML files: **41**
- Artifact IDs: **41 unique**
- Global contracts: **21**
- Admitted compiler passes: **8**
- Registered solvers: **14**
- Compilation profiles: **node-build@1 (10 stages), node-build@2 (14 stages)**
- ADR pack: **10 accepted ADRs + index**

## Gates

Executed by `python3 ops/validate-semantic-foundation.py` from the repository
root. Each gate fails closed on any reference it cannot resolve.

| Gate | Verifies | Result |
| --- | --- | --- |
| `yaml_structure` | every file parses with duplicate mapping keys rejected; artifact IDs and catalog entry IDs unique | **PASS** |
| `pass_closure` | every stage operation (both profiles, `vocabulary.semantic_build_stages`) and IR-transition operation is an admitted pass in `compiler_passes.yaml`; every admitted pass is receiptable | **PASS** |
| `solver_closure` | every `solver_ref` resolves in `solver_catalog.yaml` and is registered for the stage that references it | **PASS** |
| `stage_identity` | each produced artifact has one stage identity across profiles and vocabulary; every stage has a stage projection profile and vice versa | **PASS** |
| `stage_dataflow` | every consumed input is produced by an earlier stage or is a declared external input; ordinals contiguous; no stage cycle | **PASS** |
| `ir_registration` | produced IRs and IR-transition endpoints are registered | **PASS** |
| `derivation_inputs` | `conformance_model` derivation inputs resolve and are produced and consumed before conformance-requirement derivation | **PASS** |
| `artifact_schema` | artifact-model required fields that a schema declares are required by that schema; schema `required` ⊆ `properties` | **PASS** |
| `reference_closure` | `l9.*` ID references, invariant references, `governed_by` contracts, profile input/output contracts and schemas, canonical-source paths, projection source classes, compiler-manifest file references | **PASS** |
| `dependency_closure` | semantic-dependency node references resolve; dependency graph acyclic | **PASS** |
| `release_integrity` | exactly one current release directory; every `HASHES.sha256` entry matches; every canonical file hashed; `MANIFEST.md` lists exactly `semantics/*.yaml` | **PASS** |

## Regression cases

`python3 ops/test-validate-semantic-foundation.py` confirms the current
foundation passes every gate and that each of these deliberately broken copies
fails the gate that owns it:

| Case | Failing gate |
| --- | --- |
| unknown solver (legacy `l9.solver/...` ref) | `solver_closure` |
| unknown operation (`formalization`) | `pass_closure` |
| future-stage dependency (architecture consumes `conformance_requirement_ir`) | `stage_dataflow` |
| conformance ordered before provider bindings | `derivation_inputs` |
| stage identity drift (`technology_bindings`) | `stage_identity` |
| drifted derivation input (`technology_bindings`) | `derivation_inputs` |
| drifted dependency node (`technology_binding_resolution`) | `dependency_closure` |
| dependency cycle | `dependency_closure` |
| missing required `manifest_digest` | `artifact_schema` |
| unresolved contract reference | `reference_closure` |
| unregistered produced IR | `ir_registration` |
| undeclared stage input | `stage_dataflow` |
| admitted pass absent from the compiler-receipt enum | `pass_closure` |
| duplicate YAML mapping key | `yaml_structure` |
| tampered canonical bytes | `release_integrity` |

The same validator run against the v3.2.0 candidate
(`12ddcfd0b155a8956ff9130e835ad610de416699`) fails `pass_closure`,
`solver_closure`, `stage_identity`, `derivation_inputs`, `artifact_schema`, and
`reference_closure` on the defects this release repairs.

## Digest chain

- Predecessor: v3.2.0 candidate (unmerged), `HASHES.sha256` sha256 `d6fe8933451f7e7692b817505999f57a1c78ae958efef307395c5aa88ebd6e11`
- This release: `HASHES.sha256` in this directory; verify with `sha256sum -c docs/semantic-foundation/v3.2.1/HASHES.sha256` from the repository root

**Overall: PASS**
