#!/usr/bin/env python3
"""Mechanically verify that the canonical semantic foundation is internally closed.

Scope: integrity checks over `semantics/*.yaml` and the single current release
record under `docs/semantic-foundation/`. This is NOT a semantic compiler: it
never projects, derives, resolves, or emits artifacts. It only proves that the
canonical files reference each other consistently, and it fails closed on any
reference it cannot resolve.

Gates:
  yaml_structure       every file parses (duplicate mapping keys rejected);
                       artifact ids and catalog entry ids are unique
  operation_catalog    compiler_contract operations are the one operation
                       catalog: passes and receipt operations resolve to it;
                       engine-only operations (composition) are not passes
  pass_closure         every stage / transition operation is an admitted pass
  solver_closure       every solver_ref resolves to a solver registered for
                       that stage; solver selectors resolve to declared handles
  validation_subjects  every required validation names subjects produced by
                       its stage and handled by its solver
  stage_identity       one stage identity per produced artifact; stage ids
                       agree across profiles, vocabulary, projections, solvers
  stage_dataflow       every consumed input is produced by an EARLIER stage or
                       is a declared external input; no stage cycle
  ir_registration      produced IRs and IR transitions are registered
  derivation_inputs    conformance derivation inputs exist before derivation
  artifact_authority   artifact_model.yaml is the only canonical artifact model
  schema_binding       every schematized artifact-model requirement is bound to
                       a schema path that the schema itself requires
  reference_closure    contract, source, profile, schema, and id refs resolve
  dependency_closure   semantic dependency refs resolve; graph is acyclic
  release_integrity    one current release; hashes and manifest match

Usage: python3 ops/validate-semantic-foundation.py [--root PATH]
Exit status is 0 only when every gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from collections.abc import Callable, Iterable, Iterator
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
Node = dict[str, Any]

SEMANTICS_DIR = "semantics"
RELEASE_ROOT = "docs/semantic-foundation"
STAGE_CONSUMER_PREFIX = "semantic_build_stage."
SCHEMA_DEFINITION = "l9.schema-definition/v1"

ARTIFACT_MODEL = "artifact_model.yaml"
CANONICAL_SOURCES = "canonical_sources.yaml"
COMPILATION_PROFILES = "compilation_profiles.yaml"
COMPILER_CONTRACT = "compiler_contract.yaml"
COMPILER_PASSES = "compiler_passes.yaml"
COMPILER_RECEIPT_SCHEMA = "compiler_receipt.schema.yaml"
CONFORMANCE_MODEL = "conformance_model.yaml"
DEPENDENCY_MODEL = "semantic_dependency_model.yaml"
GENERIC_COMPILER_MANIFEST = "generic_compiler_manifest.yaml"
INVARIANTS = "invariants.yaml"
IR_CATALOG = "ir_catalog.yaml"
PROJECTION_PROFILES = "projection_profiles.yaml"
SOLVER_CATALOG = "solver_catalog.yaml"
VOCABULARY = "vocabulary.yaml"
CONTRACTS = "contracts.yaml"

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

REF_TOKEN = re.compile(r"\bl9\.[a-z\d][a-z\d-]*/[a-z\d][a-z\d._-]*(?:@\d+)?")
INVARIANT_TOKEN = re.compile(r"\bL9-[A-Z]+-\d{3}\b")
FORMAT_ID = re.compile(r"l9\.([a-z\d-]+)/v\d+")
HANDLES_SELECTOR = re.compile(r'@\.handles contains "([^"]+)"')
ARRAY_ITEMS = "*"


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


def _nodes(value: Any) -> list[Node]:
    return [_dict(v) for v in _list(value)]


def _doc(docs: Docs, name: str) -> Doc:
    return docs.get(name, {})


def _format_key(format_id: Any) -> str | None:
    if not isinstance(format_id, str):
        return None
    m = FORMAT_ID.fullmatch(format_id)
    return m.group(1).replace("-", "_") if m else None


def profiles(docs: Docs) -> list[Node]:
    return _nodes(_doc(docs, COMPILATION_PROFILES).get("profiles"))


def stages(profile: Node) -> list[Node]:
    return _nodes(profile.get("stages"))


def all_stages(docs: Docs) -> Iterator[tuple[str, Node]]:
    for p in profiles(docs):
        for s in stages(p):
            yield str(p.get("id")), s


def vocabulary_stages(docs: Docs) -> list[Node]:
    return _nodes(_doc(docs, VOCABULARY).get("semantic_build_stages"))


def source_classes(docs: Docs) -> set[str]:
    return set(_dict(_doc(docs, PROJECTION_PROFILES).get("source_classes")))


def projection_profiles(docs: Docs) -> list[Node]:
    return _nodes(_doc(docs, PROJECTION_PROFILES).get("projection_profiles"))


def pass_operations(docs: Docs) -> set[str]:
    passes = _nodes(_doc(docs, COMPILER_PASSES).get("passes"))
    return {op for p in passes if isinstance(op := p.get("operation"), str)}


def compiler_operations(docs: Docs) -> list[str]:
    return _strs(_doc(docs, COMPILER_CONTRACT).get("operations"))


def receipt_operations(docs: Docs) -> set[str]:
    props = _dict(_doc(docs, COMPILER_RECEIPT_SCHEMA).get("properties"))
    return set(_strs(_dict(props.get("operation")).get("enum")))


def engine_operations(docs: Docs) -> dict[str, str]:
    """Map each operation declared by an engine contract to that contract."""
    return {
        op: name
        for name, doc in docs.items()
        if isinstance(op := doc.get("compiler_operation"), str)
    }


def solvers(docs: Docs) -> dict[str, Node]:
    out: dict[str, Node] = {}
    for s in _nodes(_doc(docs, SOLVER_CATALOG).get("solvers")):
        if isinstance(sid := s.get("id"), str):
            out[sid] = s
    return out


def all_stage_ids(docs: Docs) -> set[str]:
    return {sid for _, s in all_stages(docs) if isinstance(sid := s.get("id"), str)}


def ir_classes(docs: Docs) -> tuple[set[str], set[str]]:
    """Return (IR ids, IR semantic classes).

    An IR's class is its declared semantic_class; only an IR that declares none
    falls back to the class implied by its id.
    """
    ids: set[str] = set()
    classes: set[str] = set()
    for ir in _nodes(_doc(docs, IR_CATALOG).get("irs")):
        irid = ir.get("id")
        if not isinstance(irid, str):
            continue
        ids.add(irid)
        cls = ir.get("semantic_class")
        if isinstance(cls, str):
            classes.add(cls)
        elif (derived := _format_key(irid)) is not None:
            classes.add(derived)
    return ids, classes


def schemas(docs: Docs) -> dict[str, Doc]:
    """Schema documents by artifact_id."""
    return {
        str(d.get("artifact_id")): d
        for d in docs.values()
        if d.get("schema") == SCHEMA_DEFINITION
    }


def schema_format_keys(docs: Docs) -> dict[str, str]:
    """Artifact kind implied by each schema's `schema` const -> schema id."""
    out: dict[str, str] = {}
    for sid, schema in schemas(docs).items():
        const = _dict(_dict(schema.get("properties")).get("schema")).get("const")
        if (key := _format_key(const)) is not None:
            out[key] = sid
    return out


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


def walk_id_lists(node: Any, path: str) -> Iterator[tuple[str, list[Node]]]:
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


def duplicates(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    dups: set[str] = set()
    for v in values:
        (dups if v in seen else seen).add(v)
    return sorted(dups)


def has_cycle(edges: dict[str, set[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        state[n] = 1
        for m in edges.get(n, set()):
            if state.get(m) == 1 or (state.get(m) is None and visit(m)):
                return True
        state[n] = 2
        return False

    return any(state.get(n) is None and visit(n) for n in edges)


# ─── yaml_structure ──────────────────────────────────────────────────────────


def check_yaml_structure(docs: Docs) -> Errors:
    errors: Errors = []
    owners: dict[str, str] = {}
    for name, doc in docs.items():
        aid = doc.get("artifact_id")
        if not isinstance(aid, str):
            errors.append(f"{name}: missing artifact_id")
            continue
        if aid in owners:
            errors.append(f"{name}: artifact_id {aid} duplicates {owners[aid]}")
        owners[aid] = name
        for path, items in walk_id_lists(doc, name):
            if dups := duplicates(str(i["id"]) for i in items):
                errors.append(f"{path}: duplicate ids {dups}")
    return errors


# ─── operation_catalog / pass_closure ────────────────────────────────────────


def check_operation_catalog(docs: Docs) -> Errors:
    catalog_list = compiler_operations(docs)
    if not catalog_list:
        return [f"{COMPILER_CONTRACT}: no compiler operation catalog"]
    catalog = set(catalog_list)
    passes = pass_operations(docs)
    receipts = receipt_operations(docs)
    engines = engine_operations(docs)
    errors = [
        f"compiler operation '{op}' declared twice" for op in duplicates(catalog_list)
    ]
    errors += [
        f"compiler pass '{op}' is not a declared compiler operation"
        for op in sorted(passes - catalog)
    ]
    errors += [
        f"compiler receipt operation '{op}' is not a declared compiler operation"
        for op in sorted(receipts - catalog)
    ]
    errors += [
        f"compiler operation '{op}' cannot be receipted"
        for op in sorted(catalog - receipts)
    ]
    contract = _doc(docs, COMPILER_CONTRACT)
    required_for = _strs(_dict(contract.get("receipts")).get("required_for"))
    errors += [
        f"{COMPILER_CONTRACT} receipts.required_for '{op}' is not a declared compiler operation"
        for op in required_for
        if op not in catalog
    ]
    errors += [
        f"compiler operation '{op}' has no definition in {COMPILER_CONTRACT}"
        for op in catalog_list
        if "definition" not in _dict(contract.get(op))
    ]
    for op, owner in sorted(engines.items()):
        if op not in catalog:
            errors.append(
                f"{owner}: compiler_operation '{op}' is not a declared compiler operation"
            )
        if op in passes:
            errors.append(
                f"'{op}' is an engine operation ({owner}) and must not be a compiler pass"
            )
    errors += [
        f"non-pass compiler operation '{op}' is declared by no engine contract"
        for op in sorted(catalog - passes - set(engines))
    ]
    return errors


def _operation_errors(where: str, ops: Iterable[str], passes: set[str]) -> Errors:
    return [
        f"{where}: operation '{op}' is not an admitted compiler pass"
        for op in ops
        if op not in passes
    ]


def check_pass_closure(docs: Docs) -> Errors:
    passes = pass_operations(docs)
    if not passes:
        return [f"{COMPILER_PASSES}: no admitted pass operations"]
    errors: Errors = []
    for pid, s in all_stages(docs):
        errors += _operation_errors(
            f"{pid} stage {s.get('id')}", _strs(s.get("operations")), passes
        )
    for s in vocabulary_stages(docs):
        errors += _operation_errors(
            f"vocabulary.semantic_build_stages {s.get('id')}",
            _strs(s.get("operations")),
            passes,
        )
    for t in _nodes(_doc(docs, IR_CATALOG).get("allowed_transitions")):
        errors += _operation_errors(
            f"ir_catalog transition {t.get('from')} -> {t.get('to')}",
            _strs(t.get("operations")),
            passes,
        )
    return errors


# ─── solver_closure / validation_subjects ────────────────────────────────────


def _stage_solver(docs: Docs, pid: str, stage: Node) -> tuple[str, Node | None, Errors]:
    where = f"{pid} stage {stage.get('id')}"
    validation = _dict(stage.get("validation"))
    ref = validation.get("solver_ref")
    if not isinstance(ref, str):
        missing = (
            [f"{where}: validation required but no solver_ref"]
            if validation.get("required") is True
            else []
        )
        return where, None, missing
    solver = solvers(docs).get(ref)
    if solver is None:
        return (
            where,
            None,
            [f"{where}: solver_ref '{ref}' does not resolve in {SOLVER_CATALOG}"],
        )
    if solver.get("stage") != stage.get("id"):
        return (
            where,
            solver,
            [
                f"{where}: solver '{ref}' is registered for stage '{solver.get('stage')}'"
            ],
        )
    return where, solver, []


def check_solver_closure(docs: Docs) -> Errors:
    stage_ids = all_stage_ids(docs)
    catalog = solvers(docs)
    errors = [
        f"solver {sid}: registered stage '{s.get('stage')}' is not a compilation-profile stage"
        for sid, s in catalog.items()
        if s.get("stage") not in stage_ids
    ]
    for pid, s in all_stages(docs):
        errors += _stage_solver(docs, pid, s)[2]
    handled = {h for s in catalog.values() for h in _strs(s.get("handles"))}
    for pp in projection_profiles(docs):
        for text in walk_strings(pp.get("sources")):
            errors += [
                f"projection profile {pp.get('id')}: selector names solver class '{cls}' that no solver handles"
                for cls in HANDLES_SELECTOR.findall(text)
                if cls not in handled
            ]
    return errors


def _subject_errors(docs: Docs, pid: str, stage: Node) -> Errors:
    where, solver, _ = _stage_solver(docs, pid, stage)
    subjects = _strs(_dict(stage.get("validation")).get("subjects"))
    errors = (
        [f"{where}: required validation declares no subjects"] if not subjects else []
    )
    produced = set(_strs(stage.get("produces")))
    errors += [
        f"{where}: validation subject '{s}' is not produced by this stage"
        for s in subjects
        if s not in produced
    ]
    if solver is not None:
        handled = set(_strs(solver.get("handles")))
        errors += [
            f"{where}: validation subject '{s}' is not handled by solver '{solver.get('id')}'"
            for s in subjects
            if s not in handled
        ]
    return errors


def check_validation_subjects(docs: Docs) -> Errors:
    return [
        e
        for pid, s in all_stages(docs)
        if _dict(s.get("validation")).get("required") is True
        for e in _subject_errors(docs, pid, s)
    ]


# ─── stage_identity / stage_dataflow ─────────────────────────────────────────


def _stage_consumers(docs: Docs) -> set[str]:
    return {
        consumer.removeprefix(STAGE_CONSUMER_PREFIX)
        for pp in projection_profiles(docs)
        if isinstance(consumer := pp.get("consumer"), str)
        and consumer.startswith(STAGE_CONSUMER_PREFIX)
    }


def check_stage_identity(docs: Docs) -> Errors:
    stage_ids = all_stage_ids(docs)
    producers: dict[str, set[str]] = {}
    declared = [s for _, s in all_stages(docs)] + vocabulary_stages(docs)
    for s in declared:
        for out in _strs(s.get("produces")):
            producers.setdefault(out, set()).add(str(s.get("id")))
    errors = [
        f"vocabulary.semantic_build_stages '{s.get('id')}' is not a compilation-profile stage identity"
        for s in vocabulary_stages(docs)
        if s.get("id") not in stage_ids
    ]
    errors += [
        f"artifact '{out}' is produced under more than one stage identity: {sorted(ids)}"
        for out, ids in sorted(producers.items())
        if len(ids) > 1
    ]
    consumers = _stage_consumers(docs)
    errors += [
        f"stage '{sid}' has no stage projection profile ({STAGE_CONSUMER_PREFIX}{sid})"
        for sid in sorted(stage_ids - consumers)
    ]
    errors += [
        f"projection consumer {STAGE_CONSUMER_PREFIX}{sid} names no compilation-profile stage"
        for sid in sorted(consumers - stage_ids)
    ]
    return errors


def _declared_inputs(docs: Docs, profile: Node) -> set[str]:
    declared = set(STAGE_SPECIFIC_INPUTS) | source_classes(docs)
    if isinstance(profile.get("input_contract"), str):
        declared.add("node_spec")
    return declared


def _producer_index(pid: str, st: list[Node]) -> tuple[dict[str, int], Errors]:
    producer_at: dict[str, int] = {}
    errors: Errors = []
    for idx, s in enumerate(st):
        for out in _strs(s.get("produces")):
            if out in producer_at:
                errors.append(f"{pid}: '{out}' produced by more than one stage")
            producer_at.setdefault(out, idx)
    return producer_at, errors


def _consumption_errors(
    where: str,
    need: str,
    idx: int,
    producer_at: dict[str, int],
    declared: set[str],
    names: list[str],
) -> Errors:
    base = VALIDATED_STATE_INPUTS.get(need, need)
    if base in producer_at:
        src = producer_at[base]
        return (
            [
                f"{where}: consumes '{need}' produced by later-or-same stage '{names[src]}'"
            ]
            if src >= idx
            else []
        )
    if need in VALIDATED_STATE_INPUTS:
        return [f"{where}: '{need}' requires '{base}', which no stage produces"]
    if need not in declared:
        return [
            f"{where}: consumes '{need}', which no earlier stage produces and is not a declared input"
        ]
    return []


def _profile_dataflow(docs: Docs, profile: Node) -> Errors:
    pid = str(profile.get("id"))
    st = stages(profile)
    names = [str(s.get("id")) for s in st]
    errors = [f"{pid}: stage '{d}' declared more than once" for d in duplicates(names)]
    ordinals = [s.get("ordinal") for s in st]
    if ordinals != list(range(1, len(st) + 1)):
        errors.append(
            f"{pid}: stage ordinals {ordinals} are not 1..{len(st)} in declaration order"
        )
    producer_at, produce_errors = _producer_index(pid, st)
    errors += produce_errors
    external = STAGE_SPECIFIC_INPUTS | set(VALIDATED_STATE_INPUTS)
    errors += [
        f"{pid}: '{c}' is both a stage output and a declared external input"
        for c in sorted(external & set(producer_at))
    ]
    declared = _declared_inputs(docs, profile)
    edges: dict[str, set[str]] = {n: set() for n in names}
    for idx, s in enumerate(st):
        for need in _strs(s.get("consumes")):
            errors += _consumption_errors(
                f"{pid} stage {names[idx]}", need, idx, producer_at, declared, names
            )
            if (
                src := producer_at.get(VALIDATED_STATE_INPUTS.get(need, need))
            ) is not None:
                edges[names[idx]].add(names[src])
    if has_cycle(edges):
        errors.append(f"{pid}: stage dependency graph contains a cycle")
    return errors


def check_stage_dataflow(docs: Docs) -> Errors:
    return [e for p in profiles(docs) for e in _profile_dataflow(docs, p)]


# ─── ir_registration / derivation_inputs ─────────────────────────────────────


def check_ir_registration(docs: Docs) -> Errors:
    ir_ids, classes = ir_classes(docs)
    terms = set(_dict(_doc(docs, VOCABULARY).get("terms")))
    handled = {h for s in solvers(docs).values() for h in _strs(s.get("handles"))}
    registered = classes | terms | handled
    errors = [
        f"{pid} stage {s.get('id')}: produced IR '{out}' is not registered"
        for pid, s in all_stages(docs)
        for out in _strs(s.get("produces"))
        if out.endswith("_ir") and out not in registered
    ]
    for t in _nodes(_doc(docs, IR_CATALOG).get("allowed_transitions")):
        refs = [t.get("from"), t.get("to"), *_strs(t.get("requires_additional_inputs"))]
        errors += [
            f"ir_catalog transition references unregistered IR '{r}'"
            for r in refs
            if isinstance(r, str) and r not in ir_ids
        ]
    return errors


def _deriver_errors(where: str, st: list[Node], d: int, inputs: list[str]) -> Errors:
    index = {str(s.get("id")): i for i, s in enumerate(st)}
    consumed = set(_strs(st[d].get("consumes")))
    errors: Errors = []
    if "conformance_model" not in consumed:
        errors.append(
            f"{where}: derives conformance requirements without consuming conformance_model"
        )
    for name in inputs:
        src = index.get(name)
        if src is None:
            continue
        if src >= d:
            errors.append(
                f"{where}: derivation input '{name}' is produced by a later stage (ordinal {src + 1})"
            )
        elif not consumed & set(_strs(st[src].get("produces"))):
            errors.append(
                f"{where}: derivation input '{name}' is available but not consumed"
            )
    return errors


def check_derivation_inputs(docs: Docs) -> Errors:
    """conformance_model.requirement_derivation_inputs must exist before derivation."""
    model = _doc(docs, CONFORMANCE_MODEL)
    inputs = _strs(model.get("requirement_derivation_inputs"))
    output = model.get("output")
    known = source_classes(docs) | all_stage_ids(docs)
    errors = [
        f"conformance_model derivation input '{n}' resolves to no canonical source or stage identity"
        for n in inputs
        if n not in known
    ]
    for p in profiles(docs):
        st = stages(p)
        for d, s in enumerate(st):
            if output in _strs(s.get("produces")):
                errors += _deriver_errors(
                    f"{p.get('id')} stage {s.get('id')}", st, d, inputs
                )
    return errors


# ─── artifact_authority / schema_binding ─────────────────────────────────────


def _declares_artifact_types(doc: Doc) -> list[str]:
    """Top-level keys holding artifact-type specs (authority_class + required)."""
    return [
        key
        for key, value in doc.items()
        if (specs := _dict(value))
        and all(isinstance(v, dict) for v in specs.values())
        and any(
            "authority_class" in _dict(v) and "required" in _dict(v)
            for v in specs.values()
        )
    ]


def check_artifact_authority(docs: Docs) -> Errors:
    if ARTIFACT_MODEL not in docs:
        return [f"{ARTIFACT_MODEL} is missing: no canonical artifact model"]
    errors = [
        f"{name}.{key} declares artifact types; {ARTIFACT_MODEL} is the single canonical artifact model"
        for name, doc in sorted(docs.items())
        if name != ARTIFACT_MODEL
        for key in _declares_artifact_types(doc)
    ]
    registered = {
        _dict(s).get("path")
        for s in _list(_doc(docs, CANONICAL_SOURCES).get("sources"))
    }
    if f"{SEMANTICS_DIR}/{ARTIFACT_MODEL}" not in registered:
        errors.append(f"{ARTIFACT_MODEL} is not registered in {CANONICAL_SOURCES}")
    catalogs = _strs(
        _dict(_doc(docs, GENERIC_COMPILER_MANIFEST).get("requires")).get(
            "semantic_catalogs"
        )
    )
    if ARTIFACT_MODEL not in catalogs:
        errors.append(
            f"{ARTIFACT_MODEL} is not required by {GENERIC_COMPILER_MANIFEST}"
        )
    return errors


def resolve_schema_path(schema: Node, path: str) -> tuple[bool, bool]:
    """Return (declared, required) for a dotted schema path.

    A segment is declared when the parent lists it under `properties` or
    `required`; `*` steps into array items and counts as required only when the
    array demands at least one item.
    """
    node = schema
    required = True
    for segment in path.split("."):
        if segment == ARRAY_ITEMS:
            if node.get("type") != "array" or "items" not in node:
                return False, False
            min_items = node.get("min_items")
            required = required and isinstance(min_items, int) and min_items >= 1
            node = _dict(node.get("items"))
            continue
        props = _dict(node.get("properties"))
        listed = _strs(node.get("required"))
        if segment not in props and segment not in listed:
            return False, False
        required = required and segment in listed
        node = _dict(props.get(segment))
    return True, required


def _binding_errors(kind: str, spec: Node, schema_id: str, schema: Doc) -> Errors:
    where = f"artifact_model.{kind}"
    binding = _dict(spec.get("schema_binding"))
    fields = _strs(spec.get("required"))
    errors = [
        f"{where}: required '{f}' has no schema binding to {schema_id}"
        for f in fields
        if not _strs(binding.get(f))
    ]
    errors += [
        f"{where}: schema_binding '{k}' is not a required field of the artifact model"
        for k in binding
        if k not in fields
    ]
    for field in fields:
        for path in _strs(binding.get(field)):
            declared, required = resolve_schema_path(schema, path)
            if not declared:
                errors.append(
                    f"{where}.{field}: bound path '{path}' does not exist in {schema_id}"
                )
            elif not required:
                errors.append(
                    f"{where}.{field}: bound path '{path}' is not required by {schema_id}"
                )
    return errors


def check_schema_binding(docs: Docs) -> Errors:
    by_id = schemas(docs)
    implied = schema_format_keys(docs)
    errors: Errors = []
    for schema_id, schema in sorted(by_id.items()):
        props = _dict(schema.get("properties"))
        errors += [
            f"schema {schema_id}: required '{r}' is not a declared property"
            for r in _strs(schema.get("required"))
            if r not in props
        ]
    for kind, raw in _dict(_doc(docs, ARTIFACT_MODEL).get("artifacts")).items():
        spec = _dict(raw)
        ref = spec.get("schema_ref")
        if ref is None and kind in implied:
            errors.append(
                f"artifact_model.{kind}: schematized by {implied[kind]} but declares no schema_ref"
            )
            continue
        if ref is None:
            continue
        if not isinstance(ref, str) or ref not in by_id:
            errors.append(f"artifact_model.{kind}: schema_ref '{ref}' does not resolve")
            continue
        errors += _binding_errors(kind, spec, ref, by_id[ref])
    return errors


# ─── reference_closure ───────────────────────────────────────────────────────


def _ids_in(node: Any) -> Iterator[str]:
    """Yield every value declared under an id-bearing key, at any depth."""
    if isinstance(node, dict):
        for k, v in cast(dict[Any, Any], node).items():
            if k in ("id", "artifact_id", "family_id") and isinstance(v, str):
                yield v
            yield from _ids_in(v)
    elif isinstance(node, list):
        for v in cast(list[Any], node):
            yield from _ids_in(v)


def _declared_ids(docs: Docs) -> set[str]:
    declared: set[str] = set()
    for doc in docs.values():
        declared.update(_ids_in(doc))
        const = _dict(_dict(doc.get("properties")).get("schema")).get("const")
        declared.update(v for v in (doc.get("schema"), const) if isinstance(v, str))
    return declared


def _token_errors(docs: Docs) -> Errors:
    declared = _declared_ids(docs)
    invariant_ids = {
        str(i.get("id")) for i in _nodes(_doc(docs, INVARIANTS).get("invariants"))
    }
    errors: Errors = []
    for name, doc in sorted(docs.items()):
        for text in walk_strings(doc):
            errors += [
                f"{name}: reference '{t}' does not resolve to a declared id"
                for t in REF_TOKEN.findall(text)
                if t not in declared
            ]
            errors += [
                f"{name}: invariant reference '{t}' does not resolve"
                for t in INVARIANT_TOKEN.findall(text)
                if t not in invariant_ids
            ]
    return errors


def _document_ref_errors(docs: Docs) -> Errors:
    contract_ids = {
        str(c.get("id")) for c in _nodes(_doc(docs, CONTRACTS).get("contracts"))
    }
    errors: Errors = []
    for name, doc in sorted(docs.items()):
        errors += [
            f"{name}: governed_by contract '{r}' does not resolve"
            for r in _strs(_dict(doc.get("governed_by")).get("contracts"))
            if r not in contract_ids
        ]
        art = _dict(doc.get("canonical_source")).get("artifact")
        if isinstance(art, str) and art not in docs:
            errors.append(f"{name}: canonical_source.artifact '{art}' does not exist")
        for family in _dict(doc.get("receipts")).values():
            ref = _dict(family).get("schema_ref")
            if isinstance(ref, str) and ref not in docs:
                errors.append(f"{name}: schema_ref '{ref}' does not exist")
    return errors


def _profile_ref_errors(docs: Docs) -> Errors:
    contract_ids = {
        str(c.get("id")) for c in _nodes(_doc(docs, CONTRACTS).get("contracts"))
    }
    schema_ids = set(schemas(docs))
    errors: Errors = []
    for p in profiles(docs):
        for key, known in (
            ("input_contract", contract_ids),
            ("resolved_output_contract", contract_ids),
            ("input_schema", schema_ids),
            ("resolved_output_schema", schema_ids),
        ):
            ref = p.get(key)
            if isinstance(ref, str) and ref not in known:
                errors.append(f"{p.get('id')}: {key} '{ref}' does not resolve")
    return errors


def _source_errors(root: Path, docs: Docs) -> Errors:
    errors: Errors = []
    for src in _nodes(_doc(docs, CANONICAL_SOURCES).get("sources")):
        path = src.get("path")
        if not isinstance(path, str) or not (root / path).is_file():
            errors.append(
                f"canonical source {src.get('id')}: path '{path}' does not exist"
            )
    for cls, raw in _dict(
        _doc(docs, PROJECTION_PROFILES).get("source_classes")
    ).items():
        spec = _dict(raw)
        art = spec.get("canonical_artifact")
        if isinstance(art, str) and art not in docs:
            errors.append(
                f"projection source class '{cls}': canonical_artifact '{art}' does not exist"
            )
        elif not isinstance(art, str) and not isinstance(
            spec.get("canonical_owner"), str
        ):
            errors.append(
                f"projection source class '{cls}': declares neither canonical_artifact nor canonical_owner"
            )
    classes = source_classes(docs)
    for pp in projection_profiles(docs):
        errors += [
            f"projection profile {pp.get('id')}: source '{c}' is not a declared source class"
            for c in _dict(pp.get("sources"))
            if c not in classes
        ]
    return errors


def _manifest_file_errors(docs: Docs) -> Errors:
    errors: Errors = []
    engine = _dict(
        _doc(docs, PROJECTION_PROFILES).get("projection_engine_contract_ref")
    )
    art = engine.get("artifact")
    if engine and (not isinstance(art, str) or art not in docs):
        errors.append(f"projection_engine_contract_ref artifact '{art}' does not exist")
    elif engine and docs[str(art)].get("artifact_id") != engine.get("artifact_id"):
        errors.append(
            f"projection_engine_contract_ref artifact_id does not match {art}"
        )
    requires = _dict(_doc(docs, GENERIC_COMPILER_MANIFEST).get("requires"))
    for group, files in requires.items():
        errors += [
            f"{GENERIC_COMPILER_MANIFEST}.requires.{group}: '{f}' does not exist"
            for f in _strs(files)
            if f not in docs
        ]
    return errors


def check_reference_closure(root: Path, docs: Docs) -> Errors:
    return (
        _token_errors(docs)
        + _document_ref_errors(docs)
        + _profile_ref_errors(docs)
        + _source_errors(root, docs)
        + _manifest_file_errors(docs)
    )


# ─── dependency_closure ──────────────────────────────────────────────────────


def check_dependency_closure(docs: Docs) -> Errors:
    """depends_on entries are either references or subject coordinates.

    A reference names another dependency node or a canonical source class and
    must resolve. An entry shaped like a resolved-semantics identity
    (`*_resolution`, `*_closure`) is always a reference, so a drifted or
    retired node name fails closed. Remaining entries are coordinates of the
    dependent subject itself (refs, digests, identities) and are not
    cross-file references.
    """
    rules = _dict(_doc(docs, DEPENDENCY_MODEL).get("dependency_rules"))
    nodes = set(rules)
    classes = source_classes(docs)
    edges: dict[str, set[str]] = {}
    errors: Errors = []
    for node, spec in rules.items():
        deps = _strs(_dict(spec).get("depends_on"))
        if not deps:
            errors.append(f"dependency '{node}' declares no depends_on")
        edges[node] = {d for d in deps if d in nodes}
        errors += [
            f"dependency '{node}' depends on unknown dependency node '{d}'"
            for d in deps
            if d not in nodes
            and d not in classes
            and d.endswith(("_resolution", "_closure"))
        ]
    if has_cycle(edges):
        errors.append("semantic dependency graph contains a cycle")
    return errors


# ─── release_integrity ───────────────────────────────────────────────────────


def _hash_errors(root: Path, hashes: Path) -> tuple[set[str], Errors]:
    listed: set[str] = set()
    errors: Errors = []
    for line in hashes.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if not parts:
            continue
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
    return listed, errors


def check_release_integrity(root: Path) -> Errors:
    base = root / RELEASE_ROOT
    releases = sorted(p for p in base.glob("v*") if p.is_dir()) if base.is_dir() else []
    if len(releases) != 1:
        return [
            f"expected exactly one current release under {RELEASE_ROOT}/, found {[r.name for r in releases]}"
        ]
    rel = releases[0]
    hashes = rel / "HASHES.sha256"
    if not hashes.is_file():
        return [f"{rel}: HASHES.sha256 missing"]
    listed, errors = _hash_errors(root, hashes)
    semantic_files = {
        f"{SEMANTICS_DIR}/{p.name}" for p in (root / SEMANTICS_DIR).glob("*.yaml")
    }
    errors += [
        f"HASHES.sha256: canonical file '{m}' is not hashed"
        for m in sorted(semantic_files - listed)
    ]
    manifest = rel / "MANIFEST.md"
    if manifest.is_file():
        named = set(
            re.findall(
                r"`(semantics/[^`]+\.yaml)`", manifest.read_text(encoding="utf-8")
            )
        )
        errors += [
            f"MANIFEST.md and semantics/ disagree on '{f}'"
            for f in sorted(semantic_files ^ named)
        ]
    else:
        errors.append(f"{rel}: MANIFEST.md missing")
    for doc_name in ("README.md", "MANIFEST.md", "RELEASE_VALIDATION.md"):
        path = rel / doc_name
        if not path.is_file() or rel.name not in path.read_text(encoding="utf-8"):
            errors.append(
                f"{rel.name}/{doc_name}: missing or does not name release {rel.name}"
            )
    return errors


# ─── driver ──────────────────────────────────────────────────────────────────


def run_checks(root: Path, docs: Docs, load_errors: Errors) -> dict[str, Errors]:
    gates: dict[str, Callable[[], Errors]] = {
        "yaml_structure": lambda: load_errors + check_yaml_structure(docs),
        "operation_catalog": lambda: check_operation_catalog(docs),
        "pass_closure": lambda: check_pass_closure(docs),
        "solver_closure": lambda: check_solver_closure(docs),
        "validation_subjects": lambda: check_validation_subjects(docs),
        "stage_identity": lambda: check_stage_identity(docs),
        "stage_dataflow": lambda: check_stage_dataflow(docs),
        "ir_registration": lambda: check_ir_registration(docs),
        "derivation_inputs": lambda: check_derivation_inputs(docs),
        "artifact_authority": lambda: check_artifact_authority(docs),
        "schema_binding": lambda: check_schema_binding(docs),
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
