#!/usr/bin/env python3
"""Mechanically verify that the canonical semantic foundation is internally closed.

Scope: integrity checks over `semantics/*.yaml` and the single current release
record under `docs/semantic-foundation/`. This is NOT a semantic compiler: it
never projects, derives, resolves, or emits artifacts. It only proves that the
canonical files reference each other consistently, and it fails closed on any
reference it cannot resolve.

Gates:
  yaml_structure         every file parses (duplicate mapping keys rejected),
                         artifact ids and catalog entry ids are unique
  pass_closure           every stage / transition operation is an admitted
                         compiler pass; every pass is receiptable
  solver_closure         every solver_ref resolves and is registered for the
                         stage that references it
  stage_identity         one stage identity per produced artifact; stage ids
                         agree across profiles, vocabulary, projections, solvers
  stage_dataflow         every consumed input is produced by an EARLIER stage or
                         is a declared external input; no stage cycle
  ir_registration        produced IRs and IR transitions are registered
  derivation_inputs      conformance derivation inputs exist before derivation
  artifact_schema        artifact-model required fields agree with schemas
  reference_closure      contract, source, profile, schema, and id refs resolve
  dependency_closure     semantic dependency refs resolve; graph is acyclic
  release_integrity      one current release; hashes and manifest match

Usage: python3 ops/validate-semantic-foundation.py [--root PATH]
Exit status is 0 only when every gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

Doc = dict[str, Any]
Docs = dict[str, Doc]
Errors = list[str]

SEMANTICS_DIR = "semantics"
RELEASE_ROOT = "docs/semantic-foundation"
STAGE_CONSUMER_PREFIX = "semantic_build_stage."

# Inputs a stage may consume without an earlier stage producing them
# (vocabulary.yaml stage_rules.stage_input_formula: `∪ StageSpecificInputs_n`).
# Canonical source classes and a profile's declared input are accepted in
# addition to this list. Anything else fails closed.
STAGE_SPECIFIC_INPUTS: frozenset[str] = frozenset(
    {
        "global_authority",
        "global_invariants",
        "global_contracts",
        "global_capability_semantics",
        "canonical_l9_vocabulary",
        "project_spec",
        "project_requirements",
        "project_boundaries",
        "project_constraints",
        "desired_capabilities",
        "domain_contract_refs",
        "applicable_invariants",
        "applicable_contracts",
        "applicable_contract_projection",
        "applicable_architecture_patterns",
        "applicable_conformance_bindings",
        # Projected GOVERNING conformance semantics. It is deliberately not
        # bound to the conformance stage's outputs, so it never stands in for
        # the later conformance_requirement_ir.
        "applicable_conformance_projection",
        "node_archetype",
        "fixture_profiles",
        "technology_profile",
        "provider_constraints",
        "implementation_constraints",
        "target_binding",
        "rendering_profile",
        "compiler_coordinates",
    }
)

# Inputs that are admitted or projected forms of an earlier stage's validated
# output: the stage producing the named artifact must precede the consumer.
VALIDATED_STATE_INPUTS: dict[str, str] = {
    "admitted_project_contracts": "project_contract_ir",
    "admitted_contract_projection": "project_contract_ir",
    "validated_semantic_baseline_projection": "validated_global_baseline",
    "semantic_law_projection": "semantic_law_ir",
    "law_provenance": "semantic_law_ir",
    "final_conformance_projection": "conformance_ir",
}

REF_TOKEN = re.compile(r"\bl9\.[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9._-]*(?:@[0-9]+)?")
INVARIANT_TOKEN = re.compile(r"\bL9-[A-Z]+-[0-9]{3}\b")


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of overwriting."""


def _construct_mapping(
    loader: yaml.SafeLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key: Any = loader.construct_object(key_node, deep=deep)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate mapping key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_foundation(root: Path) -> tuple[Docs, Errors]:
    docs: Docs = {}
    errors: Errors = []
    for path in sorted((root / SEMANTICS_DIR).glob("*.yaml")):
        try:
            data = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
        except yaml.YAMLError as exc:
            errors.append(f"{path.name}: YAML parse failure: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path.name}: top level is not a mapping")
            continue
        docs[path.name] = cast(Doc, data)
    if not docs:
        errors.append(f"no YAML files found under {SEMANTICS_DIR}/")
    return docs, errors


# ─── accessors ───────────────────────────────────────────────────────────────


def _list(value: Any) -> list[Any]:
    return cast(list[Any], value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _strs(value: Any) -> list[str]:
    return [v for v in _list(value) if isinstance(v, str)]


def _doc(docs: Docs, name: str) -> Doc:
    return docs.get(name, {})


def profiles(docs: Docs) -> list[dict[str, Any]]:
    return [
        _dict(p) for p in _list(_doc(docs, "compilation_profiles.yaml").get("profiles"))
    ]


def stages(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [_dict(s) for s in _list(profile.get("stages"))]


def vocabulary_stages(docs: Docs) -> list[dict[str, Any]]:
    return [
        _dict(s)
        for s in _list(_doc(docs, "vocabulary.yaml").get("semantic_build_stages"))
    ]


def source_classes(docs: Docs) -> set[str]:
    return set(_dict(_doc(docs, "projection_profiles.yaml").get("source_classes")))


def pass_operations(docs: Docs) -> set[str]:
    passes = _list(_doc(docs, "compiler_passes.yaml").get("passes"))
    return {op for p in passes if isinstance(op := _dict(p).get("operation"), str)}


def solvers(docs: Docs) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for s in _list(_doc(docs, "solver_catalog.yaml").get("solvers")):
        sd = _dict(s)
        if isinstance(sid := sd.get("id"), str):
            out[sid] = sd
    return out


def all_stage_ids(docs: Docs) -> set[str]:
    return {
        s["id"]
        for p in profiles(docs)
        for s in stages(p)
        if isinstance(s.get("id"), str)
    }


def ir_classes(docs: Docs) -> tuple[set[str], set[str]]:
    """Return (IR ids, IR semantic classes incl. id-derived class names)."""
    ids: set[str] = set()
    classes: set[str] = set()
    for ir in _list(_doc(docs, "ir_catalog.yaml").get("irs")):
        ird = _dict(ir)
        irid = ird.get("id")
        if not isinstance(irid, str):
            continue
        ids.add(irid)
        if isinstance(cls := ird.get("semantic_class"), str):
            classes.add(cls)
        m = re.fullmatch(r"l9\.([a-z0-9-]+)/v[0-9]+", irid)
        if m:
            classes.add(m.group(1).replace("-", "_"))
    return ids, classes


def walk_strings(node: Any) -> Iterator[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for k, v in cast(dict[Any, Any], node).items():
            if isinstance(k, str):
                yield k
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in cast(list[Any], node):
            yield from walk_strings(v)


def walk_id_lists(node: Any, path: str) -> Iterator[tuple[str, list[dict[str, Any]]]]:
    """Yield every list whose items are mappings carrying an `id`."""
    if isinstance(node, dict):
        for k, v in cast(dict[Any, Any], node).items():
            yield from walk_id_lists(v, f"{path}.{k}")
    elif isinstance(node, list):
        items = [_dict(v) for v in cast(list[Any], node) if isinstance(v, dict)]
        if items and all("id" in i for i in items):
            yield path, items
        for i, v in enumerate(cast(list[Any], node)):
            yield from walk_id_lists(v, f"{path}[{i}]")


# ─── gates ───────────────────────────────────────────────────────────────────


def check_yaml_structure(docs: Docs) -> Errors:
    errors: Errors = []
    artifact_ids: dict[str, str] = {}
    for name, doc in docs.items():
        aid = doc.get("artifact_id")
        if not isinstance(aid, str):
            errors.append(f"{name}: missing artifact_id")
            continue
        if aid in artifact_ids:
            errors.append(f"{name}: artifact_id {aid} duplicates {artifact_ids[aid]}")
        artifact_ids[aid] = name
        for path, items in walk_id_lists(doc, name):
            ids = [str(i["id"]) for i in items]
            dups = sorted({i for i in ids if ids.count(i) > 1})
            if dups:
                errors.append(f"{path}: duplicate ids {dups}")
    return errors


def check_pass_closure(docs: Docs) -> Errors:
    errors: Errors = []
    admitted = pass_operations(docs)
    if not admitted:
        return ["compiler_passes.yaml: no admitted pass operations"]
    for p in profiles(docs):
        for s in stages(p):
            for op in _strs(s.get("operations")):
                if op not in admitted:
                    errors.append(
                        f"{p.get('id')} stage {s.get('id')}: operation '{op}' is not an admitted compiler pass"
                    )
    for s in vocabulary_stages(docs):
        for op in _strs(s.get("operations")):
            if op not in admitted:
                errors.append(
                    f"vocabulary.semantic_build_stages {s.get('id')}: operation '{op}' is not an admitted compiler pass"
                )
    for t in _list(_doc(docs, "ir_catalog.yaml").get("allowed_transitions")):
        td = _dict(t)
        for op in _strs(td.get("operations")):
            if op not in admitted:
                errors.append(
                    f"ir_catalog transition {td.get('from')} -> {td.get('to')}: operation '{op}' is not an admitted compiler pass"
                )
    receipt_ops = set(
        _strs(
            _dict(
                _dict(_doc(docs, "compiler_receipt.schema.yaml").get("properties")).get(
                    "operation"
                )
            ).get("enum")
        )
    )
    for op in sorted(admitted - receipt_ops):
        errors.append(
            f"compiler_receipt.schema operation enum cannot receipt admitted pass '{op}'"
        )
    return errors


def check_solver_closure(docs: Docs) -> Errors:
    errors: Errors = []
    catalog = solvers(docs)
    stage_ids = all_stage_ids(docs)
    for sid, s in catalog.items():
        if s.get("stage") not in stage_ids:
            errors.append(
                f"solver {sid}: registered stage '{s.get('stage')}' is not a compilation-profile stage"
            )
    for p in profiles(docs):
        for s in stages(p):
            validation = _dict(s.get("validation"))
            ref = validation.get("solver_ref")
            where = f"{p.get('id')} stage {s.get('id')}"
            if validation.get("required") is True and not isinstance(ref, str):
                errors.append(f"{where}: validation required but no solver_ref")
                continue
            if not isinstance(ref, str):
                continue
            solver = catalog.get(ref)
            if solver is None:
                errors.append(
                    f"{where}: solver_ref '{ref}' does not resolve in solver_catalog"
                )
            elif solver.get("stage") != s.get("id"):
                errors.append(
                    f"{where}: solver '{ref}' is registered for stage '{solver.get('stage')}'"
                )
    return errors


def check_stage_identity(docs: Docs) -> Errors:
    errors: Errors = []
    stage_ids = all_stage_ids(docs)
    producers: dict[str, set[str]] = {}
    for p in profiles(docs):
        for s in stages(p):
            for out in _strs(s.get("produces")):
                producers.setdefault(out, set()).add(str(s.get("id")))
    for s in vocabulary_stages(docs):
        sid = s.get("id")
        if sid not in stage_ids:
            errors.append(
                f"vocabulary.semantic_build_stages '{sid}' is not a compilation-profile stage identity"
            )
        for out in _strs(s.get("produces")):
            producers.setdefault(out, set()).add(str(sid))
    for out, ids in sorted(producers.items()):
        if len(ids) > 1:
            errors.append(
                f"artifact '{out}' is produced under more than one stage identity: {sorted(ids)}"
            )
    consumers: set[str] = set()
    for pp in _list(_doc(docs, "projection_profiles.yaml").get("projection_profiles")):
        consumer = _dict(pp).get("consumer")
        if isinstance(consumer, str) and consumer.startswith(STAGE_CONSUMER_PREFIX):
            consumers.add(consumer.removeprefix(STAGE_CONSUMER_PREFIX))
    for sid in sorted(stage_ids - consumers):
        errors.append(
            f"stage '{sid}' has no stage projection profile ({STAGE_CONSUMER_PREFIX}{sid})"
        )
    for sid in sorted(consumers - stage_ids):
        errors.append(
            f"projection consumer {STAGE_CONSUMER_PREFIX}{sid} names no compilation-profile stage"
        )
    return errors


def _declared_inputs(docs: Docs, profile: dict[str, Any]) -> set[str]:
    declared = set(STAGE_SPECIFIC_INPUTS) | source_classes(docs)
    if isinstance(profile.get("input_contract"), str):
        declared.add("node_spec")
    return declared


def check_stage_dataflow(docs: Docs) -> Errors:
    errors: Errors = []
    for p in profiles(docs):
        pid = str(p.get("id"))
        st = stages(p)
        ids = [str(s.get("id")) for s in st]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append(f"{pid}: stage '{dup}' declared more than once")
        ordinals = [s.get("ordinal") for s in st]
        if ordinals != list(range(1, len(st) + 1)):
            errors.append(
                f"{pid}: stage ordinals {ordinals} are not 1..{len(st)} in declaration order"
            )
        producer_at: dict[str, int] = {}
        for idx, s in enumerate(st):
            for out in _strs(s.get("produces")):
                if out in producer_at:
                    errors.append(f"{pid}: '{out}' produced by more than one stage")
                producer_at.setdefault(out, idx)
        declared = _declared_inputs(docs, p)
        for clash in sorted(
            (STAGE_SPECIFIC_INPUTS | set(VALIDATED_STATE_INPUTS)) & set(producer_at)
        ):
            errors.append(
                f"{pid}: '{clash}' is both a stage output and a declared external input"
            )
        edges: dict[int, set[int]] = {i: set() for i in range(len(st))}
        for idx, s in enumerate(st):
            for need in _strs(s.get("consumes")):
                where = f"{pid} stage {s.get('id')}"
                base = VALIDATED_STATE_INPUTS.get(need, need)
                if base in producer_at:
                    src = producer_at[base]
                    edges[idx].add(src)
                    if src >= idx:
                        errors.append(
                            f"{where}: consumes '{need}' produced by later-or-same stage '{ids[src]}'"
                        )
                elif need in VALIDATED_STATE_INPUTS:
                    errors.append(
                        f"{where}: '{need}' requires '{base}', which no stage produces"
                    )
                elif need not in declared:
                    errors.append(
                        f"{where}: consumes '{need}', which no earlier stage produces and is not a declared input"
                    )
        if _has_cycle(edges):
            errors.append(f"{pid}: stage dependency graph contains a cycle")
    return errors


def _has_cycle(edges: dict[int, set[int]]) -> bool:
    state: dict[int, int] = {}

    def visit(n: int) -> bool:
        state[n] = 1
        for m in edges.get(n, set()):
            if state.get(m) == 1 or (state.get(m) is None and visit(m)):
                return True
        state[n] = 2
        return False

    return any(state.get(n) is None and visit(n) for n in edges)


def check_ir_registration(docs: Docs) -> Errors:
    errors: Errors = []
    ir_ids, classes = ir_classes(docs)
    terms = set(_dict(_doc(docs, "vocabulary.yaml").get("terms")))
    handled = {h for s in solvers(docs).values() for h in _strs(s.get("handles"))}
    registered = classes | terms | handled
    for p in profiles(docs):
        for s in stages(p):
            for out in _strs(s.get("produces")):
                if out.endswith("_ir") and out not in registered:
                    errors.append(
                        f"{p.get('id')} stage {s.get('id')}: produced IR '{out}' is not registered"
                    )
    for t in _list(_doc(docs, "ir_catalog.yaml").get("allowed_transitions")):
        td = _dict(t)
        refs = [td.get("from"), td.get("to")]
        extra = td.get("requires_additional_inputs")
        refs += _strs(extra)
        for ref in refs:
            if isinstance(ref, str) and ref not in ir_ids:
                errors.append(
                    f"ir_catalog transition references unregistered IR '{ref}'"
                )
    return errors


def check_derivation_inputs(docs: Docs) -> Errors:
    """conformance_model.requirement_derivation_inputs must exist before derivation."""
    errors: Errors = []
    model = _doc(docs, "conformance_model.yaml")
    inputs = _strs(model.get("requirement_derivation_inputs"))
    output = model.get("output")
    classes = source_classes(docs)
    stage_ids = all_stage_ids(docs)
    for name in inputs:
        if name not in classes and name not in stage_ids:
            errors.append(
                f"conformance_model derivation input '{name}' resolves to no canonical source or stage identity"
            )
    for p in profiles(docs):
        st = stages(p)
        index = {str(s.get("id")): i for i, s in enumerate(st)}
        derivers = [i for i, s in enumerate(st) if output in _strs(s.get("produces"))]
        for d in derivers:
            consumed = set(_strs(st[d].get("consumes")))
            if "conformance_model" not in consumed:
                errors.append(
                    f"{p.get('id')} stage {st[d].get('id')}: derives '{output}' without consuming conformance_model"
                )
            for name in inputs:
                if name not in index:
                    continue
                src = index[name]
                where = f"{p.get('id')} stage {st[d].get('id')}"
                if src >= d:
                    errors.append(
                        f"{where}: derivation input '{name}' is produced by a later stage (ordinal {src + 1})"
                    )
                elif not consumed & set(_strs(st[src].get("produces"))):
                    errors.append(
                        f"{where}: derivation input '{name}' is available but not consumed"
                    )
    return errors


def _schemas_by_format(docs: Docs) -> dict[str, tuple[str, Doc]]:
    out: dict[str, tuple[str, Doc]] = {}
    for name, doc in docs.items():
        if doc.get("schema") != "l9.schema-definition/v1":
            continue
        const = _dict(_dict(doc.get("properties")).get("schema")).get("const")
        if isinstance(const, str):
            m = re.fullmatch(r"l9\.([a-z0-9-]+)/v[0-9]+", const)
            if m:
                out[m.group(1).replace("-", "_")] = (name, doc)
    return out


def check_artifact_schema(docs: Docs) -> Errors:
    errors: Errors = []
    schemas = _schemas_by_format(docs)
    for name, (_, schema) in schemas.items():
        props = set(_dict(schema.get("properties")))
        for req in _strs(schema.get("required")):
            if req not in props:
                errors.append(
                    f"schema {schema.get('artifact_id')}: required '{req}' is not a declared property"
                )
        del name
    models: list[tuple[str, dict[str, Any]]] = [
        ("artifact_model", _dict(_doc(docs, "artifact_model.yaml").get("artifacts"))),
        (
            "compilation_artifacts",
            _dict(_doc(docs, "compilation_artifacts.yaml").get("artifact_types")),
        ),
    ]
    for model_name, artifacts in models:
        for kind, spec in artifacts.items():
            if kind not in schemas:
                continue
            _, schema = schemas[kind]
            props = set(_dict(schema.get("properties")))
            required = set(_strs(schema.get("required")))
            for field in _strs(_dict(spec).get("required")):
                if field in props and field not in required:
                    errors.append(
                        f"{model_name}.{kind} requires '{field}' but {schema.get('artifact_id')} declares it optional"
                    )
    return errors


def _declared_ids(docs: Docs) -> set[str]:
    declared: set[str] = set()

    def collect(node: Any) -> None:
        if isinstance(node, dict):
            for k, v in cast(dict[Any, Any], node).items():
                if k in ("id", "artifact_id", "family_id") and isinstance(v, str):
                    declared.add(v)
                collect(v)
        elif isinstance(node, list):
            for v in cast(list[Any], node):
                collect(v)

    for doc in docs.values():
        collect(doc)
        if isinstance(fmt := doc.get("schema"), str):
            declared.add(fmt)
        const = _dict(_dict(doc.get("properties")).get("schema")).get("const")
        if isinstance(const, str):
            declared.add(const)
    return declared


def check_reference_closure(root: Path, docs: Docs) -> Errors:
    errors: Errors = []
    declared = _declared_ids(docs)
    invariant_ids = {
        str(_dict(i).get("id"))
        for i in _list(_doc(docs, "invariants.yaml").get("invariants"))
    }
    contract_ids = {
        str(_dict(c).get("id"))
        for c in _list(_doc(docs, "contracts.yaml").get("contracts"))
    }
    schema_ids = {
        str(d.get("artifact_id"))
        for d in docs.values()
        if d.get("schema") == "l9.schema-definition/v1"
    }
    for name, doc in sorted(docs.items()):
        for text in walk_strings(doc):
            for tok in REF_TOKEN.findall(text):
                if tok not in declared:
                    errors.append(
                        f"{name}: reference '{tok}' does not resolve to a declared id"
                    )
            for tok in INVARIANT_TOKEN.findall(text):
                if tok not in invariant_ids:
                    errors.append(
                        f"{name}: invariant reference '{tok}' does not resolve"
                    )
        for ref in _strs(_dict(doc.get("governed_by")).get("contracts")):
            if ref not in contract_ids:
                errors.append(f"{name}: governed_by contract '{ref}' does not resolve")
        art = _dict(doc.get("canonical_source")).get("artifact")
        if isinstance(art, str) and art not in docs:
            errors.append(f"{name}: canonical_source.artifact '{art}' does not exist")
        for family in _dict(doc.get("receipts")).values():
            ref = _dict(family).get("schema_ref")
            if isinstance(ref, str) and ref not in docs:
                errors.append(f"{name}: schema_ref '{ref}' does not exist")
    for p in profiles(docs):
        for key in ("input_contract", "resolved_output_contract"):
            if isinstance(ref := p.get(key), str) and ref not in contract_ids:
                errors.append(f"{p.get('id')}: {key} '{ref}' does not resolve")
        for key in ("input_schema", "resolved_output_schema"):
            if isinstance(ref := p.get(key), str) and ref not in schema_ids:
                errors.append(f"{p.get('id')}: {key} '{ref}' does not resolve")
    for src in _list(_doc(docs, "canonical_sources.yaml").get("sources")):
        sd = _dict(src)
        path = sd.get("path")
        if not isinstance(path, str) or not (root / path).is_file():
            errors.append(
                f"canonical source {sd.get('id')}: path '{path}' does not exist"
            )
    for cls, spec in _dict(
        _doc(docs, "projection_profiles.yaml").get("source_classes")
    ).items():
        art = _dict(spec).get("canonical_artifact")
        owner = _dict(spec).get("canonical_owner")
        if isinstance(art, str):
            if art not in docs:
                errors.append(
                    f"projection source class '{cls}': canonical_artifact '{art}' does not exist"
                )
        elif not isinstance(owner, str):
            errors.append(
                f"projection source class '{cls}': declares neither canonical_artifact nor canonical_owner"
            )
    classes = source_classes(docs)
    for pp in _list(_doc(docs, "projection_profiles.yaml").get("projection_profiles")):
        ppd = _dict(pp)
        for cls in _dict(ppd.get("sources")):
            if cls not in classes:
                errors.append(
                    f"projection profile {ppd.get('id')}: source '{cls}' is not a declared source class"
                )
    engine = _dict(
        _doc(docs, "projection_profiles.yaml").get("projection_engine_contract_ref")
    )
    if engine:
        art = engine.get("artifact")
        if not isinstance(art, str) or art not in docs:
            errors.append(
                f"projection_engine_contract_ref artifact '{art}' does not exist"
            )
        elif docs[art].get("artifact_id") != engine.get("artifact_id"):
            errors.append(
                f"projection_engine_contract_ref artifact_id does not match {art}"
            )
    requires = _dict(_doc(docs, "generic_compiler_manifest.yaml").get("requires"))
    for group, files in requires.items():
        for f in _strs(files):
            if f not in docs:
                errors.append(
                    f"generic_compiler_manifest.requires.{group}: '{f}' does not exist"
                )
    return errors


def check_dependency_closure(docs: Docs) -> Errors:
    """depends_on entries are either references or subject coordinates.

    A reference names another dependency node or a canonical source class and
    must resolve. An entry shaped like a resolved-semantics identity
    (`*_resolution`, `*_closure`) is always a reference, so a drifted or
    retired node name fails closed. Remaining entries are coordinates of the
    dependent subject itself (refs, digests, identities) and are not
    cross-file references.
    """
    errors: Errors = []
    rules = _dict(_doc(docs, "semantic_dependency_model.yaml").get("dependency_rules"))
    nodes = set(rules)
    classes = source_classes(docs)
    edges: dict[str, set[str]] = {n: set() for n in nodes}
    for node, spec in rules.items():
        deps = _strs(_dict(spec).get("depends_on"))
        if not deps:
            errors.append(f"dependency '{node}' declares no depends_on")
        for dep in deps:
            if dep in nodes:
                edges[node].add(dep)
            elif dep in classes:
                continue
            elif dep.endswith(("_resolution", "_closure")):
                errors.append(
                    f"dependency '{node}' depends on unknown dependency node '{dep}'"
                )
    index = {n: i for i, n in enumerate(sorted(nodes))}
    if _has_cycle({index[n]: {index[m] for m in ms} for n, ms in edges.items()}):
        errors.append("semantic dependency graph contains a cycle")
    return errors


def check_release_integrity(root: Path) -> Errors:
    errors: Errors = []
    base = root / RELEASE_ROOT
    releases = sorted(p for p in base.glob("v*") if p.is_dir()) if base.is_dir() else []
    if len(releases) != 1:
        return [
            f"expected exactly one current release under {RELEASE_ROOT}/, found {[r.name for r in releases]}"
        ]
    rel = releases[0]
    version = rel.name
    hashes = rel / "HASHES.sha256"
    if not hashes.is_file():
        return [f"{rel}: HASHES.sha256 missing"]
    listed: set[str] = set()
    for line in hashes.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            errors.append(f"HASHES.sha256: malformed line '{line}'")
            continue
        digest, rel_path = parts[0], parts[1].strip()
        listed.add(rel_path)
        target = root / rel_path
        if not target.is_file():
            errors.append(f"HASHES.sha256: '{rel_path}' does not exist")
        elif hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            errors.append(f"HASHES.sha256: digest mismatch for '{rel_path}'")
    semantic_files = {
        f"{SEMANTICS_DIR}/{p.name}" for p in (root / SEMANTICS_DIR).glob("*.yaml")
    }
    for missing in sorted(semantic_files - listed):
        errors.append(f"HASHES.sha256: canonical file '{missing}' is not hashed")
    manifest = rel / "MANIFEST.md"
    if manifest.is_file():
        named = set(
            re.findall(
                r"`(semantics/[^`]+\.yaml)`", manifest.read_text(encoding="utf-8")
            )
        )
        for f in sorted(semantic_files ^ named):
            errors.append(f"MANIFEST.md and semantics/ disagree on '{f}'")
    else:
        errors.append(f"{rel}: MANIFEST.md missing")
    for doc_name in ("README.md", "MANIFEST.md", "RELEASE_VALIDATION.md"):
        path = rel / doc_name
        if not path.is_file() or version not in path.read_text(encoding="utf-8"):
            errors.append(
                f"{rel.name}/{doc_name}: missing or does not name release {version}"
            )
    return errors


def run_checks(root: Path, docs: Docs, load_errors: Errors) -> dict[str, Errors]:
    gates: dict[str, Callable[[], Errors]] = {
        "yaml_structure": lambda: load_errors + check_yaml_structure(docs),
        "pass_closure": lambda: check_pass_closure(docs),
        "solver_closure": lambda: check_solver_closure(docs),
        "stage_identity": lambda: check_stage_identity(docs),
        "stage_dataflow": lambda: check_stage_dataflow(docs),
        "ir_registration": lambda: check_ir_registration(docs),
        "derivation_inputs": lambda: check_derivation_inputs(docs),
        "artifact_schema": lambda: check_artifact_schema(docs),
        "reference_closure": lambda: check_reference_closure(root, docs),
        "dependency_closure": lambda: check_dependency_closure(docs),
        "release_integrity": lambda: check_release_integrity(root),
    }
    return {name: gate() for name, gate in gates.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else None
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parent.parent
    )
    args = parser.parse_args(argv)
    root = cast(Path, args.root).resolve()
    docs, load_errors = load_foundation(root)
    results = run_checks(root, docs, load_errors)
    failed = 0
    for gate, errors in results.items():
        print(f"{'PASS' if not errors else 'FAIL'}  {gate}")
        for e in errors:
            print(f"      - {e}")
        failed += bool(errors)
    print(f"\n{len(results) - failed}/{len(results)} gates passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
