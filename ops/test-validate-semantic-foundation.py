#!/usr/bin/env python3
"""Regression tests for ops/validate-semantic-foundation.py.

The current foundation must pass every gate, and each deliberately broken copy
must fail the gate that owns that defect class. Mutations are applied to
in-memory copies (or a temporary tree for file-level gates); the repository is
never modified.
"""

from __future__ import annotations

import copy
import importlib.util
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
NODE_BUILD_1 = "l9.compilation/node-build@1"
NODE_BUILD_2 = "l9.compilation/node-build@2"

Docs = dict[str, Any]
Mutation = Callable[[Docs], None]


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "validate_semantic_foundation", ROOT / "ops" / "validate-semantic-foundation.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load ops/validate-semantic-foundation.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _load_validator()
DOCS, LOAD_ERRORS = V.load_foundation(ROOT)
FAILURES: list[str] = []


def _stages(docs: Docs, profile_id: str) -> list[dict[str, Any]]:
    for p in docs["compilation_profiles.yaml"]["profiles"]:
        if p["id"] == profile_id:
            return p["stages"]
    raise KeyError(profile_id)


def _stage(docs: Docs, profile_id: str, stage_id: str) -> dict[str, Any]:
    for s in _stages(docs, profile_id):
        if s["id"] == stage_id:
            return s
    raise KeyError(f"{profile_id}/{stage_id}")


def _artifact(docs: Docs, kind: str) -> dict[str, Any]:
    return docs["artifact_model.yaml"]["artifacts"][kind]


def _schema_props(docs: Docs, name: str) -> dict[str, Any]:
    return docs[name]["properties"]


# ─── mutations ───────────────────────────────────────────────────────────────


def undeclared_receipt_operation(docs: Docs) -> None:
    docs["compiler_receipt.schema.yaml"]["properties"]["operation"]["enum"].append(
        "compilation"
    )


def composition_as_pass(docs: Docs) -> None:
    docs["compiler_passes.yaml"]["passes"].append(
        {"id": "l9.pass/compose@1", "operation": "composition"}
    )


def verb_spelling_in_catalog(docs: Docs) -> None:
    ops = docs["compiler_contract.yaml"]["operations"]
    ops[ops.index("projection")] = "project"


def unreceiptable_operation(docs: Docs) -> None:
    docs["compiler_receipt.schema.yaml"]["properties"]["operation"]["enum"].remove(
        "resolution"
    )


def unknown_operation(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "laws")["operations"].append("formalization")


def unknown_solver(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "ports")["validation"]["solver_ref"] = (
        "l9.solver/interface-compatibility-validator@1"
    )


def wrong_stage_solver(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "ports")["validation"]["solver_ref"] = (
        "graph-constraint-validator/v1"
    )


def dangling_solver_selector(docs: Docs) -> None:
    for s in docs["solver_catalog.yaml"]["solvers"]:
        if s["id"] == "logic-sat/v1":
            s["handles"] = ["law_ir"]


def no_validation_subjects(docs: Docs) -> None:
    del _stage(docs, NODE_BUILD_2, "laws")["validation"]["subjects"]


def subject_not_produced(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "ports")["validation"]["subjects"] = ["architecture_ir"]


def subject_not_handled(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_1, "global_baseline")["validation"]["subjects"] = [
        "global_baseline"
    ]
    _stage(docs, NODE_BUILD_1, "global_baseline")["produces"].append("global_baseline")


def future_stage_dependency(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "architecture")["consumes"].append(
        "conformance_requirement_ir"
    )


def conformance_before_bindings(docs: Docs) -> None:
    stages = _stages(docs, NODE_BUILD_2)
    ids = [s["id"] for s in stages]
    i, j = ids.index("provider_bindings"), ids.index("conformance")
    stages[i], stages[j] = stages[j], stages[i]
    stages[i]["ordinal"], stages[j]["ordinal"] = i + 1, j + 1


def stage_identity_drift(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "provider_bindings")["id"] = "technology_bindings"


def drifted_derivation_input(docs: Docs) -> None:
    inputs = docs["conformance_model.yaml"]["requirement_derivation_inputs"]
    inputs[inputs.index("provider_bindings")] = "technology_bindings"


def drifted_dependency_node(docs: Docs) -> None:
    deps = docs["semantic_dependency_model.yaml"]["dependency_rules"]["node_manifest"][
        "depends_on"
    ]
    deps[deps.index("provider_binding_resolution")] = "technology_binding_resolution"


def dependency_cycle(docs: Docs) -> None:
    docs["semantic_dependency_model.yaml"]["dependency_rules"]["node_spec"][
        "depends_on"
    ].append("node_manifest")


def missing_manifest_digest(docs: Docs) -> None:
    docs["node_manifest.schema.yaml"]["required"].remove("manifest_digest")


def second_artifact_model(docs: Docs) -> None:
    docs["compilation_artifacts.yaml"] = {
        "artifact_id": "l9.compilation-artifacts/global@1",
        "artifact_types": {
            "node_manifest": {"authority_class": "derived", "required": ["x"]}
        },
    }


def unbound_requirement(docs: Docs) -> None:
    _artifact(docs, "node_manifest")["required"].append("runtime_image")


def unresolvable_binding(docs: Docs) -> None:
    _artifact(docs, "node_manifest")["schema_binding"]["ports"] = ["port_list"]


def missing_node_spec_source_coordinate(docs: Docs) -> None:
    docs["node_spec.schema.yaml"]["required"].remove("source_revision")


def missing_source_spec_digest(docs: Docs) -> None:
    _schema_props(docs, "node_manifest.schema.yaml")["source_spec"]["required"].remove(
        "digest"
    )


def missing_compiler_profile_digest(docs: Docs) -> None:
    _schema_props(docs, "node_manifest.schema.yaml")["compiler"]["required"].remove(
        "profile_digest"
    )


def unschematized_binding(docs: Docs) -> None:
    del _artifact(docs, "node_spec")["schema_ref"]


def unresolved_contract(docs: Docs) -> None:
    docs["compilation_profiles.yaml"]["profiles"][1]["input_contract"] = (
        "l9.contract/node-birth@9"
    )


def unregistered_ir(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "ports")["produces"].append("port_contract_ir")


def undeclared_input(docs: Docs) -> None:
    _stage(docs, NODE_BUILD_2, "ports")["consumes"].append("provider_api_surface")


# (name, gate, mutation, expected error fragment)
CASES: list[tuple[str, str, Mutation, str]] = [
    # F146-08 compiler operation identity
    (
        "undeclared receipt operation",
        "operation_catalog",
        undeclared_receipt_operation,
        "receipt operation 'compilation' is not a declared compiler operation",
    ),
    (
        "composition registered as a pass",
        "operation_catalog",
        composition_as_pass,
        "'composition' is an engine operation",
    ),
    (
        "verb spelling in operation catalog",
        "operation_catalog",
        verb_spelling_in_catalog,
        "compiler pass 'projection' is not a declared compiler operation",
    ),
    (
        "operation not receiptable",
        "operation_catalog",
        unreceiptable_operation,
        "compiler operation 'resolution' cannot be receipted",
    ),
    (
        "unknown stage operation",
        "pass_closure",
        unknown_operation,
        "'formalization' is not an admitted compiler pass",
    ),
    # F146-09 solver validation subjects
    (
        "unknown solver",
        "solver_closure",
        unknown_solver,
        "does not resolve in solver_catalog",
    ),
    (
        "solver registered to the wrong stage",
        "solver_closure",
        wrong_stage_solver,
        "is registered for stage 'architecture'",
    ),
    (
        "projection selector names unhandled class",
        "solver_closure",
        dangling_solver_selector,
        "names solver class 'semantic_law_ir'",
    ),
    (
        "required validation without subjects",
        "validation_subjects",
        no_validation_subjects,
        "declares no subjects",
    ),
    (
        "subject not produced by its stage",
        "validation_subjects",
        subject_not_produced,
        "'architecture_ir' is not produced by this stage",
    ),
    (
        "subject not handled by its solver",
        "validation_subjects",
        subject_not_handled,
        "'global_baseline' is not handled by solver 'predicate-validator/v1'",
    ),
    # F146-10 artifact authority and schema binding
    (
        "second canonical artifact model",
        "artifact_authority",
        second_artifact_model,
        "compilation_artifacts.yaml.artifact_types declares artifact types",
    ),
    (
        "unbound artifact-model requirement",
        "schema_binding",
        unbound_requirement,
        "required 'runtime_image' has no schema binding",
    ),
    (
        "binding to a nonexistent schema path",
        "schema_binding",
        unresolvable_binding,
        "bound path 'port_list' does not exist",
    ),
    (
        "schematized type without schema_ref",
        "schema_binding",
        unschematized_binding,
        "node_spec: schematized by l9.schema/node-spec@1",
    ),
    (
        "missing NodeSpec source coordinate",
        "schema_binding",
        missing_node_spec_source_coordinate,
        "bound path 'source_revision' is not required",
    ),
    (
        "missing NodeManifest source-spec digest",
        "schema_binding",
        missing_source_spec_digest,
        "bound path 'source_spec.digest' is not required",
    ),
    (
        "missing compiler-profile digest",
        "schema_binding",
        missing_compiler_profile_digest,
        "bound path 'compiler.profile_digest' is not required",
    ),
    (
        "missing required manifest digest",
        "schema_binding",
        missing_manifest_digest,
        "bound path 'manifest_digest' is not required",
    ),
    # F146-01..07 regressions
    (
        "future-stage dependency",
        "stage_dataflow",
        future_stage_dependency,
        "produced by later-or-same stage 'conformance'",
    ),
    (
        "undeclared stage input",
        "stage_dataflow",
        undeclared_input,
        "consumes 'provider_api_surface'",
    ),
    (
        "conformance before provider bindings",
        "derivation_inputs",
        conformance_before_bindings,
        "'provider_bindings' is produced by a later stage",
    ),
    (
        "stage identity drift",
        "stage_identity",
        stage_identity_drift,
        "more than one stage identity",
    ),
    (
        "drifted derivation input",
        "derivation_inputs",
        drifted_derivation_input,
        "'technology_bindings' resolves to no canonical source or stage identity",
    ),
    (
        "drifted dependency node",
        "dependency_closure",
        drifted_dependency_node,
        "unknown dependency node 'technology_binding_resolution'",
    ),
    ("dependency cycle", "dependency_closure", dependency_cycle, "contains a cycle"),
    (
        "unresolved contract",
        "reference_closure",
        unresolved_contract,
        "input_contract 'l9.contract/node-birth@9' does not resolve",
    ),
    (
        "unregistered IR",
        "ir_registration",
        unregistered_ir,
        "'port_contract_ir' is not registered",
    ),
]


def expect_failure(name: str, gate: str, mutate: Mutation, needle: str) -> None:
    docs = copy.deepcopy(DOCS)
    mutate(docs)
    errors: list[str] = V.run_checks(ROOT, docs, [])[gate]
    if any(needle in e for e in errors):
        print(f"✅ {name}: {gate} fails closed")
    else:
        FAILURES.append(name)
        print(f"❌ {name}: expected {gate} to report '{needle}', got {errors}")


def test_current_foundation_passes() -> None:
    results = V.run_checks(ROOT, DOCS, LOAD_ERRORS)
    failed = {g: e for g, e in results.items() if e}
    if failed:
        FAILURES.append("current foundation")
        print(f"❌ current foundation: failing gates {failed}")
    else:
        print(f"✅ current foundation: all {len(results)} gates pass")


def test_duplicate_yaml_key_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        sem = Path(tmp) / "semantics"
        sem.mkdir()
        (sem / "dup.yaml").write_text(
            "artifact_id: a\nartifact_id: b\n", encoding="utf-8"
        )
        _, errors = V.load_foundation(Path(tmp))
    if any("duplicate mapping key" in e for e in errors):
        print("✅ duplicate YAML key: yaml_structure fails closed")
    else:
        FAILURES.append("duplicate YAML key")
        print(f"❌ duplicate YAML key: got {errors}")


def test_release_tamper_detected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(ROOT / "semantics", Path(tmp) / "semantics")
        shutil.copytree(ROOT / "docs", Path(tmp) / "docs")
        target = Path(tmp) / "semantics" / "solver_catalog.yaml"
        target.write_text(
            target.read_text(encoding="utf-8") + "# tampered\n", encoding="utf-8"
        )
        errors: list[str] = V.check_release_integrity(Path(tmp))
    if any("digest mismatch for 'semantics/solver_catalog.yaml'" in e for e in errors):
        print("✅ tampered canonical bytes: release_integrity fails closed")
    else:
        FAILURES.append("tampered canonical bytes")
        print(f"❌ tampered canonical bytes: got {errors}")


def main() -> int:
    print("=== semantic foundation validator regression ===")
    test_current_foundation_passes()
    for case in CASES:
        expect_failure(*case)
    test_duplicate_yaml_key_rejected()
    test_release_tamper_detected()
    total = len(CASES) + 2
    if FAILURES:
        print(f"\n{len(FAILURES)} case(s) failed: {FAILURES}")
        return 1
    print(f"\nall {total} negative cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
