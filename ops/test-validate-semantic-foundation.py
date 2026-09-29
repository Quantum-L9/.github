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


def _stage(docs: dict[str, Any], profile_id: str, stage_id: str) -> dict[str, Any]:
    for p in docs["compilation_profiles.yaml"]["profiles"]:
        if p["id"] == profile_id:
            for s in p["stages"]:
                if s["id"] == stage_id:
                    return s
    raise KeyError(f"{profile_id}/{stage_id}")


def _stages(docs: dict[str, Any], profile_id: str) -> list[dict[str, Any]]:
    for p in docs["compilation_profiles.yaml"]["profiles"]:
        if p["id"] == profile_id:
            return p["stages"]
    raise KeyError(profile_id)


def expect_failure(
    name: str, gate: str, mutate: Callable[[dict[str, Any]], None], needle: str
) -> None:
    docs = copy.deepcopy(DOCS)
    mutate(docs)
    results = V.run_checks(ROOT, docs, [])
    errors: list[str] = results[gate]
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


def unknown_solver(docs: dict[str, Any]) -> None:
    _stage(docs, "l9.compilation/node-build@2", "ports")["validation"]["solver_ref"] = (
        "l9.solver/interface-compatibility-validator@1"
    )


def unknown_operation(docs: dict[str, Any]) -> None:
    _stage(docs, "l9.compilation/node-build@2", "laws")["operations"].append(
        "formalization"
    )


def future_stage_dependency(docs: dict[str, Any]) -> None:
    # architecture consumes the conformance requirements derived after it
    _stage(docs, "l9.compilation/node-build@2", "architecture")["consumes"].append(
        "conformance_requirement_ir"
    )


def conformance_before_bindings(docs: dict[str, Any]) -> None:
    stages = _stages(docs, "l9.compilation/node-build@2")
    ids = [s["id"] for s in stages]
    i, j = ids.index("provider_bindings"), ids.index("conformance")
    stages[i], stages[j] = stages[j], stages[i]
    stages[i]["ordinal"], stages[j]["ordinal"] = i + 1, j + 1


def stage_identity_drift(docs: dict[str, Any]) -> None:
    _stage(docs, "l9.compilation/node-build@2", "provider_bindings")["id"] = (
        "technology_bindings"
    )


def drifted_derivation_input(docs: dict[str, Any]) -> None:
    inputs = docs["conformance_model.yaml"]["requirement_derivation_inputs"]
    inputs[inputs.index("provider_bindings")] = "technology_bindings"


def drifted_dependency_node(docs: dict[str, Any]) -> None:
    deps = docs["semantic_dependency_model.yaml"]["dependency_rules"]["node_manifest"][
        "depends_on"
    ]
    deps[deps.index("provider_binding_resolution")] = "technology_binding_resolution"


def dependency_cycle(docs: dict[str, Any]) -> None:
    docs["semantic_dependency_model.yaml"]["dependency_rules"]["node_spec"][
        "depends_on"
    ].append("node_manifest")


def missing_manifest_digest(docs: dict[str, Any]) -> None:
    docs["node_manifest.schema.yaml"]["required"].remove("manifest_digest")


def unresolved_contract(docs: dict[str, Any]) -> None:
    docs["compilation_profiles.yaml"]["profiles"][1]["input_contract"] = (
        "l9.contract/node-birth@9"
    )


def unregistered_ir(docs: dict[str, Any]) -> None:
    _stage(docs, "l9.compilation/node-build@2", "ports")["produces"].append(
        "port_contract_ir"
    )


def undeclared_input(docs: dict[str, Any]) -> None:
    _stage(docs, "l9.compilation/node-build@2", "ports")["consumes"].append(
        "provider_api_surface"
    )


def unreceiptable_pass(docs: dict[str, Any]) -> None:
    docs["compiler_receipt.schema.yaml"]["properties"]["operation"]["enum"].remove(
        "resolution"
    )


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
    expect_failure(
        "unknown solver",
        "solver_closure",
        unknown_solver,
        "does not resolve in solver_catalog",
    )
    expect_failure(
        "unknown operation",
        "pass_closure",
        unknown_operation,
        "'formalization' is not an admitted compiler pass",
    )
    expect_failure(
        "future-stage dependency",
        "stage_dataflow",
        future_stage_dependency,
        "produced by later-or-same stage 'conformance'",
    )
    expect_failure(
        "conformance before provider bindings",
        "derivation_inputs",
        conformance_before_bindings,
        "'provider_bindings' is produced by a later stage",
    )
    expect_failure(
        "stage identity drift",
        "stage_identity",
        stage_identity_drift,
        "more than one stage identity",
    )
    expect_failure(
        "drifted derivation input",
        "derivation_inputs",
        drifted_derivation_input,
        "'technology_bindings' resolves to no canonical source or stage identity",
    )
    expect_failure(
        "drifted dependency node",
        "dependency_closure",
        drifted_dependency_node,
        "unknown dependency node 'technology_binding_resolution'",
    )
    expect_failure(
        "dependency cycle", "dependency_closure", dependency_cycle, "contains a cycle"
    )
    expect_failure(
        "missing required manifest digest",
        "artifact_schema",
        missing_manifest_digest,
        "requires 'manifest_digest'",
    )
    expect_failure(
        "unresolved contract",
        "reference_closure",
        unresolved_contract,
        "input_contract 'l9.contract/node-birth@9' does not resolve",
    )
    expect_failure(
        "unregistered IR",
        "ir_registration",
        unregistered_ir,
        "'port_contract_ir' is not registered",
    )
    expect_failure(
        "undeclared stage input",
        "stage_dataflow",
        undeclared_input,
        "consumes 'provider_api_surface'",
    )
    expect_failure(
        "unreceiptable pass",
        "pass_closure",
        unreceiptable_pass,
        "cannot receipt admitted pass 'resolution'",
    )
    test_duplicate_yaml_key_rejected()
    test_release_tamper_detected()
    if FAILURES:
        print(f"\n{len(FAILURES)} case(s) failed: {FAILURES}")
        return 1
    print("\nall cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
