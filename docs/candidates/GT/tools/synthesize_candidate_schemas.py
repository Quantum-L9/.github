#!/usr/bin/env python3
"""Run the real semantic compiler's candidate schema synthesis on the GT pack.

What this does, end to end:

1. Rebuilds the disposable authority rehearsal: clones ``--target-store`` at
   the binding's ``canonical_target`` (main, carrying the admitted SV foundation
   v3.32.0; the GT applier verifies the clean admitted semantics tree and the
   pinned SV-owned files), applies this GT pack's core stage with
   ``--apply --disposable``, and commits the result with a fixed identity and
   date, so the authority revision is reproducible.
2. Drafts one ``source_field_grammar_candidate`` per source class by
   *translating* the pack's hand-authored payload schema
   (``semantics/strategic_interaction_projection.schema.yaml``) into the
   compiler's grammar algebra, reconciled against the source document bytes at
   that revision. Every constraint is classified in
   ``synthesis/generated/constraint-ledger.json``:

   * ``carried``        - the hand-schema constraint holds for the source and is
                          kept verbatim (``required``/``const``/``enum``/
                          ``min_items``).
   * ``not_carried``    - the constraint describes the *selected payload* but is
                          false of the whole source document (for example an id
                          enum over the twelve filtered invariants). It is not
                          dropped from the pack: the hand-authored schema still
                          carries it. It is simply not expressible as a
                          source-field grammar.
   * ``structural_fill`` - a field present in a selected subtree that the hand
                          schema does not describe. The grammar algebra requires
                          every present field of a selected subtree to have a
                          descriptor, so a *type-only* descriptor is filled from
                          the source shape. Fills never add ``required``,
                          ``const``, ``enum`` or ``min_items``: observations do
                          not become normative constraints.

   A type conflict between the hand schema and the source, or a field with mixed
   JSON types (the algebra has no unions), is a hard failure, never papered over.
3. Writes the operation, dialect and binding catalog candidates, commits
   grammars (G1) and catalog (G2) into a governance object store with a fixed
   identity and date, and builds the ``schema-synthesize`` request with every
   input independently pinned.
4. Runs ``schema-synthesize`` and ``schema-candidate-check`` twice, asserts the
   two candidates are byte-identical, and runs ``schema-derive`` for the
   non-normative observation report.

None of this is owner review, canonical admission, registration or release.
The drafted grammars carry ``approval_status: candidate``, ``canonical: false``
and ``admission: not_granted``; the owner field names the *proposed* governing
owner and is caller-asserted. The compiler itself records that basis.

Usage (paths are illustrative):

    python tools/synthesize_candidate_schemas.py \
        --target-store /path/to/Quantum-L9/.github \
        --compiler-root /path/to/l9-semantic-compiler-engine \
        [--check]

``--check`` regenerates into a temporary directory and fails if any committed
file under ``synthesis/`` differs: YAML byte-for-byte, JSON by parsed content,
because Biome owns JSON layout in this repository. After a regeneration run
``biome format --write synthesis/generated``. The compiler's exact
``candidate.json`` bytes are bound by ``candidate_json_compiler_bytes_sha256`` in
``run-receipt.json``; ``schema-candidate-check`` accepts the formatted file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

PACK = Path(__file__).resolve().parents[1]
SYNTHESIS = PACK / "synthesis"
GOVERNANCE_DIR = "docs/candidates/GT/synthesis/governance"
BINDING = json.loads(
    (PACK / "evidence/sv_alignment_binding.json").read_text(encoding="utf-8")
)

REPOSITORY = "Quantum-L9/.github"
PROPOSED_OWNER = "Quantum-L9/.github"
COMPILER_REPOSITORY = "Quantum-L9/l9-semantic-compiler-engine"
PROJECTION_PROFILE = "l9.projection/strategic-planner-interaction@1"
COMPOSITION_PROFILE = "l9.compose/strategic-planner-interaction@1"
HAND_SCHEMA = "semantics/strategic_interaction_projection.schema.yaml"
OPERATION_REF = (
    "l9.operation/strategic-planner-interaction-schema-synthesis-candidate@1"
)
DIALECT_REF = "l9.schema-dialect/candidate-v2@1"
BINDINGS_REF = "l9.binding/strategic-planner-interaction-grammar-catalog-candidate@1"
PROTOCOL = "source-dispatched-candidate/v2"
OPERATORS = [
    "type",
    "fields",
    "items",
    "required",
    "const",
    "enum",
    "min_items",
    "additional_properties",
]
FIXED_IDENTITY = {
    "GIT_AUTHOR_NAME": "gt-candidate-synthesis",
    "GIT_AUTHOR_EMAIL": "gt-candidate-synthesis@example.invalid",
    "GIT_COMMITTER_NAME": "gt-candidate-synthesis",
    "GIT_COMMITTER_EMAIL": "gt-candidate-synthesis@example.invalid",
    "GIT_AUTHOR_DATE": "2026-11-08T00:00:00Z",
    "GIT_COMMITTER_DATE": "2026-11-08T00:00:00Z",
}
_FILTER = re.compile(r'^\$\.([A-Za-z_][A-Za-z0-9_]*)\[\?\(@\.id=="[^"]+"\)\]$')
_PATH = re.compile(r"^\$\.([A-Za-z_][A-Za-z0-9_]*)(?:\.([A-Za-z_][A-Za-z0-9_]*))?$")


class SynthesisError(RuntimeError):
    pass


# --------------------------------------------------------------------- utils


def sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical_json(value: Any, *, newline: bool) -> bytes:
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return data + (b"\n" if newline else b"")


def pretty_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode()


def dump_yaml(value: Any) -> bytes:
    return yaml.safe_dump(
        value, sort_keys=False, allow_unicode=True, width=4096, default_flow_style=False
    ).encode("utf-8")


def git(root: Path, *args: str, raw: bool = False) -> Any:
    env = {**os.environ, **FIXED_IDENTITY, "GIT_CONFIG_NOSYSTEM": "1"}
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        env=env,
    )
    return proc.stdout if raw else proc.stdout.decode().strip()


def show(root: Path, rev: str, path: str) -> bytes:
    return git(root, "show", f"{rev}:{path}", raw=True)


# --------------------------------------------------------- 1. rehearsal


def _apply(applier: Path, root: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(applier),
            "--checkout",
            str(root),
            "--apply",
            "--disposable",
        ],
        cwd=applier.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SynthesisError(f"{applier} failed: {proc.stderr.strip()[-600:]}")


def build_authority(target_store: Path, work: Path) -> tuple[Path, str]:
    base = BINDING["canonical_target"]
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise SynthesisError("binding canonical_target is not a full commit id")
    root = work / "authority"
    subprocess.run(
        ["git", "clone", "-q", "--no-checkout", str(target_store), str(root)],
        check=True,
    )
    git(root, "checkout", "-q", "--detach", base)
    _apply(PACK / "apply_to_pinned_checkout.py", root)
    git(root, "add", "--", "semantics")
    git(
        root,
        "commit",
        "-q",
        "-m",
        "rehearsal: apply GT core on the admitted SV foundation (local only, never pushed)",
    )
    return root, git(root, "rev-parse", "HEAD")


# ------------------------------------------------- 2. grammar translation


_PY_TYPE = {bool: "boolean", str: "string", int: "integer", float: "number"}


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if type(value) is dict:
        return "object"
    if type(value) is list:
        return "array"
    return _PY_TYPE[type(value)]


def _has_type(value: Any, kind: str) -> bool:
    if kind == "object":
        return type(value) is dict
    if kind == "array":
        return type(value) is list
    if kind == "string_list":
        return type(value) is list and all(type(v) is str for v in value)
    if kind == "number":
        return type(value) in (int, float)
    if kind == "null":
        return value is None
    return type(value) is {"string": str, "boolean": bool, "integer": int}[kind]


def _hand_type(hd: dict[str, Any], path: str) -> str:
    if "type" in hd:
        return hd["type"]
    if "const" in hd:
        return _PY_TYPE[type(hd["const"])]
    if "enum" in hd:
        kinds = {_PY_TYPE[type(v)] for v in hd["enum"]}
        if len(kinds) == 1:
            return kinds.pop()
    if "properties" in hd or "fields" in hd:
        return "object"
    if "items" in hd:
        return "array"
    raise SynthesisError(f"hand schema descriptor at {path} has no derivable type")


class Translator:
    def __init__(self, source_class: str) -> None:
        self.source_class = source_class
        self.ledger: list[dict[str, Any]] = []
        self.carried = 0

    def _log(self, path: str, action: str, constraint: str, **extra: Any) -> None:
        if action == "carried":
            self.carried += 1
        self.ledger.append(
            {
                "source_class": self.source_class,
                "path": path,
                "action": action,
                "constraint": constraint,
                **extra,
            }
        )

    def structural(self, values: list[Any], path: str) -> dict[str, Any]:
        kinds = {_json_type(v) for v in values}
        if kinds == {"integer", "number"}:
            kinds = {"number"}
        if len(kinds) != 1:
            raise SynthesisError(
                f"mixed JSON types at {path}: {sorted(kinds)} (no union in algebra)"
            )
        kind = kinds.pop()
        if kind == "object":
            keys: list[str] = []
            for v in values:
                keys.extend(k for k in v if k not in keys)
            if not keys:
                raise SynthesisError(
                    f"empty object at {path}: open empty object is unrestricted"
                )
            self._log(
                path,
                "v1_semantics",
                "additional_properties",
                value=True,
                reason="v1_objects_always_open",
            )
            return {
                "type": "object",
                "fields": {
                    k: self.structural([v[k] for v in values if k in v], f"{path}.{k}")
                    for k in keys
                },
                "additional_properties": True,
            }
        if kind == "array":
            items = [i for v in values for i in v]
            if not items:
                self._log(
                    path,
                    "structural_fill",
                    "items",
                    reason="vacuous_empty_array_items_string",
                )
                return {"type": "array", "items": {"type": "string"}}
            return {"type": "array", "items": self.structural(items, f"{path}[]")}
        return {"type": kind}

    def fill(self, values: list[Any], path: str) -> dict[str, Any]:
        self._log(path, "structural_fill", "type")
        return self.structural(values, path)

    def reconcile(
        self, hd: dict[str, Any] | None, values: list[Any], path: str
    ) -> dict[str, Any]:
        if hd is None:
            return self.fill(values, path)
        kind = _hand_type(hd, path)
        bad = [v for v in values if not _has_type(v, kind)]
        if bad:
            raise SynthesisError(
                f"type conflict at {path}: hand schema says {kind}, source has {_json_type(bad[0])}"
            )
        unsupported = set(hd) - {
            "type",
            "properties",
            "fields",
            "required",
            "const",
            "enum",
            "min_items",
            "items",
        }
        if unsupported:
            raise SynthesisError(
                f"unsupported hand-schema keywords at {path}: {sorted(unsupported)}"
            )
        out: dict[str, Any] = {"type": kind}
        if kind == "object":
            props = hd.get("properties", hd.get("fields")) or {}
            keys: list[str] = list(props)
            for v in values:
                keys.extend(k for k in v if k not in keys)
            fields: dict[str, Any] = {}
            for key in keys:
                present = [v[key] for v in values if key in v]
                if not present:
                    self._log(
                        f"{path}.{key}",
                        "not_carried",
                        "field",
                        reason="declared_but_absent_in_source",
                    )
                    continue
                fields[key] = self.reconcile(props.get(key), present, f"{path}.{key}")
            if not fields:
                raise SynthesisError(
                    f"empty object at {path}: open empty object is unrestricted"
                )
            out["fields"] = fields
            out["additional_properties"] = True
            self._log(
                path,
                "v1_semantics",
                "additional_properties",
                value=True,
                reason="v1_objects_always_open",
            )
            if "required" in hd:
                kept = []
                for key in hd["required"]:
                    if values and all(key in v for v in values):
                        kept.append(key)
                        self._log(f"{path}.{key}", "carried", "required")
                    else:
                        self._log(
                            f"{path}.{key}",
                            "not_carried",
                            "required",
                            reason="false_of_source",
                        )
                if kept:
                    out["required"] = kept
        elif kind in ("array", "string_list"):
            if kind == "array":
                items = [i for v in values for i in v]
                if items:
                    out["items"] = self.reconcile(hd.get("items"), items, f"{path}[]")
                elif "items" in hd:
                    out["items"] = self.reconcile_absent(hd["items"], f"{path}[]")
                else:
                    out["items"] = {"type": "string"}
                    self._log(
                        path,
                        "structural_fill",
                        "items",
                        reason="vacuous_empty_array_items_string",
                    )
            if "min_items" in hd:
                if all(len(v) >= hd["min_items"] for v in values):
                    out["min_items"] = hd["min_items"]
                    self._log(path, "carried", "min_items", value=hd["min_items"])
                else:
                    self._log(
                        path,
                        "not_carried",
                        "min_items",
                        value=hd["min_items"],
                        reason="false_of_source",
                    )
        else:
            if "const" in hd:
                if all(v == hd["const"] for v in values):
                    out["const"] = hd["const"]
                    self._log(path, "carried", "const", value=hd["const"])
                else:
                    self._log(
                        path,
                        "not_carried",
                        "const",
                        value=hd["const"],
                        reason="false_of_source",
                    )
            if "enum" in hd:
                if all(v in hd["enum"] for v in values):
                    out["enum"] = list(hd["enum"])
                    self._log(path, "carried", "enum", value=hd["enum"])
                else:
                    self._log(
                        path,
                        "not_carried",
                        "enum",
                        value=hd["enum"],
                        reason="false_of_source",
                    )
        return out

    def reconcile_absent(self, hd: dict[str, Any], path: str) -> dict[str, Any]:
        self._log(
            path, "not_carried", "items_constraints", reason="no_source_items_to_verify"
        )
        return (
            {"type": _hand_type(hd, path)}
            if _hand_type(hd, path) not in ("object", "array")
            else {"type": "string"}
        )


def selected_roots(selectors: list[str]) -> dict[str, set[str] | None]:
    """Root key -> None (whole subtree or filtered array) or the selected child keys."""
    roots: dict[str, set[str] | None] = {}
    for sel in selectors:
        m = _FILTER.match(sel)
        if m:
            roots[m.group(1)] = None
            continue
        m = _PATH.match(sel)
        if not m:
            raise SynthesisError(
                f"selector outside the translator's supported forms: {sel}"
            )
        root, child = m.group(1), m.group(2)
        if child is None:
            roots[root] = None
        else:
            existing = roots.setdefault(root, set())
            if existing is None:
                raise SynthesisError(f"overlapping selectors under $.{root}")
            existing.add(child)
    return roots


def draft_grammar(
    source_class: str,
    document: dict[str, Any],
    selectors: list[str],
    hand: dict[str, Any],
) -> tuple[dict[str, Any], Translator]:
    t = Translator(source_class)
    fields: dict[str, Any] = {}
    for root, children in selected_roots(selectors).items():
        if root not in document:
            raise SynthesisError(
                f"{source_class}: selected root $.{root} absent from source"
            )
        hd = hand.get(root)
        if children is None:
            fields[root] = t.reconcile(hd, [document[root]], f"$.{root}")
            continue
        value = document[root]
        if type(value) is not dict:
            raise SynthesisError(f"{source_class}: $.{root} is not a mapping")
        props = (hd or {}).get("properties", (hd or {}).get("fields")) or {}
        sub: dict[str, Any] = {}
        for child in sorted(children, key=list(value).index):
            if child not in value:
                raise SynthesisError(
                    f"{source_class}: selected $.{root}.{child} absent from source"
                )
            sub[child] = t.reconcile(
                props.get(child), [value[child]], f"$.{root}.{child}"
            )
        node: dict[str, Any] = {
            "type": "object",
            "fields": sub,
            "additional_properties": True,
        }
        t._log(
            f"$.{root}",
            "v1_semantics",
            "additional_properties",
            value=True,
            reason="v1_objects_always_open",
        )
        if hd is not None and "required" in hd:
            kept = []
            for key in hd["required"]:
                if key in value and key in sub:
                    kept.append(key)
                    t._log(f"$.{root}.{key}", "carried", "required")
                else:
                    t._log(
                        f"$.{root}.{key}",
                        "not_carried",
                        "required",
                        reason="false_of_source",
                    )
            if kept:
                node["required"] = kept
        fields[root] = node
    t._log(
        "$",
        "v1_semantics",
        "additional_properties",
        value=True,
        reason="v1_objects_always_open; unselected source fields remain outside the projection",
    )
    return {"type": "object", "fields": fields, "additional_properties": True}, t


# -------------------------------------------------------- 3. governance


def find_record(records: Any, ref: str) -> dict[str, Any]:
    if isinstance(records, dict):
        if records.get("id") == ref:
            return records
        records = list(records.values())
    if isinstance(records, list):
        for item in records:
            found = find_record(item, ref) if isinstance(item, (dict, list)) else None
            if found:
                return found
    return {}


def candidate_doc(kind: str, ref: str, **extra: Any) -> dict[str, Any]:
    return {
        "document_kind": kind,
        "artifact_id": ref,
        "owner": PROPOSED_OWNER,
        "approval_status": "candidate",
        "canonical": False,
        "admission": "not_granted",
        **extra,
    }


def compiler_identity(compiler_root: Path) -> dict[str, str]:
    revision = git(compiler_root, "rev-parse", "HEAD")
    listing = git(compiler_root, "ls-tree", "-r", revision, "--", "src")
    return {
        "repository": COMPILER_REPOSITORY,
        "revision": revision,
        # Caller-asserted: digest of the sorted src/ tree listing at the revision.
        "executable_digest": sha256(listing.encode()),
    }


def run_cli(compiler_root: Path, *args: str) -> tuple[int, bytes, bytes]:
    exe = compiler_root / ".venv" / "bin" / "l9-semantic-compiler"
    proc = subprocess.run([str(exe), *args], capture_output=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def generate(
    target_store: Path, compiler_root: Path, out: Path, work: Path
) -> dict[str, Any]:
    authority, rev = build_authority(target_store, work)

    def ydoc(path: str) -> Any:
        return yaml.safe_load(show(authority, rev, path))

    profiles = ydoc("semantics/projection_profiles.yaml")
    projection = find_record(profiles, PROJECTION_PROFILE)
    composition = find_record(
        ydoc("semantics/composition_profiles.yaml"), COMPOSITION_PROFILE
    )
    if not projection or not composition:
        raise SynthesisError("profile pair not found at the rehearsal revision")
    source_classes = profiles["source_classes"]
    sources_registry = {
        s["path"]: s["id"] for s in ydoc("semantics/canonical_sources.yaml")["sources"]
    }
    hand = ydoc(HAND_SCHEMA)["properties"]
    selector_raw = show(authority, rev, "semantics/selector_model.yaml")
    selector_ref = yaml.safe_load(selector_raw)["artifact_id"]

    gov = work / "governance"
    gov.mkdir()
    git(gov, "init", "-q")
    source_order = list(projection["sources"])
    specs, ledger, summary = [], [], {}
    for cls in source_order:
        path = "semantics/" + source_classes[cls]["canonical_artifact"]
        raw = show(authority, rev, path)
        selectors = list(projection["sources"][cls]["selectors"])
        grammar, t = draft_grammar(cls, yaml.safe_load(raw), selectors, hand)
        ledger.extend(t.ledger)
        summary[cls] = {
            a: sum(1 for e in t.ledger if e["action"] == a)
            for a in ("carried", "not_carried", "structural_fill", "v1_semantics")
        }
        gref = f"l9.grammar/strategic-planner-interaction-{cls.replace('_', '-')}-candidate@1"
        gpath = f"{GOVERNANCE_DIR}/grammars/{cls}.yaml"
        doc = candidate_doc(
            "source_field_grammar_candidate",
            gref,
            source_class=cls,
            source_ref=sources_registry[path],
            source_path=path,
            source_revision=rev,
            source_digest=sha256(raw),
            applies_to_selectors=selectors,
            grammar=grammar,
        )
        data = dump_yaml(doc)
        (gov / gpath).parent.mkdir(parents=True, exist_ok=True)
        (gov / gpath).write_bytes(data)
        specs.append(
            {
                "cls": cls,
                "ref": sources_registry[path],
                "path": path,
                "raw": raw,
                "selectors": selectors,
                "gref": gref,
                "gpath": gpath,
                "gdigest": sha256(data),
            }
        )
    git(gov, "add", "-A")
    git(gov, "commit", "-q", "-m", "G1: GT source-field grammar candidates")
    g1 = git(gov, "rev-parse", "HEAD")

    docs = {
        "operation.yaml": candidate_doc(
            "schema_synthesis_operation_candidate",
            OPERATION_REF,
            dialect_ref=DIALECT_REF,
        ),
        "dialect.yaml": candidate_doc(
            "schema_synthesis_dialect_candidate",
            DIALECT_REF,
            protocol=PROTOCOL,
            supported_operators=OPERATORS,
        ),
        "bindings.yaml": candidate_doc(
            "source_field_grammar_bindings_candidate",
            BINDINGS_REF,
            bindings=[
                {
                    "source_class": s["cls"],
                    "source_ref": s["ref"],
                    "source_path": s["path"],
                    "source_revision": rev,
                    "source_digest": sha256(s["raw"]),
                    "grammar_ref": s["gref"],
                    "grammar_path": s["gpath"],
                    "grammar_revision": g1,
                    "grammar_digest": s["gdigest"],
                    "grammar_owner": PROPOSED_OWNER,
                    "applies_to_selectors": s["selectors"],
                    "approval_status": "candidate",
                }
                for s in specs
            ],
        ),
    }
    pins = {}
    for name, doc in docs.items():
        data = dump_yaml(doc)
        (gov / GOVERNANCE_DIR / name).write_bytes(data)
        pins[name] = sha256(data)
    git(gov, "add", "-A")
    git(
        gov,
        "commit",
        "-q",
        "-m",
        "G2: GT operation, dialect and binding catalog candidates",
    )
    g2 = git(gov, "rev-parse", "HEAD")

    def pin(name: str, ref: str) -> dict[str, str]:
        return {
            "ref": ref,
            "path": f"{GOVERNANCE_DIR}/{name}",
            "owner": PROPOSED_OWNER,
            "digest": pins[name],
        }

    request = {
        "mode": "candidate",
        "authority": {
            "root": str(authority),
            "repository": REPOSITORY,
            "revision": rev,
        },
        "projection_profile": {
            "ref": PROJECTION_PROFILE,
            "digest": sha256(canonical_json(projection, newline=False)),
        },
        "composition_profile": {
            "ref": COMPOSITION_PROFILE,
            "digest": sha256(canonical_json(composition, newline=False)),
        },
        "selector_model": {
            "ref": selector_ref,
            "path": "semantics/selector_model.yaml",
            "digest": sha256(selector_raw),
        },
        "source_order": source_order,
        "sources": [
            {
                "source_class": s["cls"],
                "ref": s["ref"],
                "path": s["path"],
                "revision": rev,
                "digest": sha256(s["raw"]),
            }
            for s in specs
        ],
        "governance": {
            "root": str(gov),
            "repository": REPOSITORY,
            "revision": g2,
            "operation": pin("operation.yaml", OPERATION_REF),
            "dialect": pin("dialect.yaml", DIALECT_REF),
            "bindings": pin("bindings.yaml", BINDINGS_REF),
            "grammars": [
                {
                    "ref": s["gref"],
                    "path": s["gpath"],
                    "owner": PROPOSED_OWNER,
                    "digest": s["gdigest"],
                    "revision": g1,
                }
                for s in specs
            ],
        },
        "compiler": compiler_identity(compiler_root),
    }
    request_path = work / "request.json"
    request_path.write_bytes(pretty_json(request))

    runs = []
    for _ in range(2):
        code, stdout, stderr = run_cli(
            compiler_root, "schema-synthesize", str(request_path)
        )
        runs.append((code, stdout, stderr))
    code, candidate_raw, stderr = runs[0]
    receipt: dict[str, Any] = {
        "schema": "l9.gt.candidate-schema-synthesis-run/v1",
        "status": "candidate_not_admitted",
        "authority_repository": REPOSITORY,
        "authority_base_sha": git(authority, "rev-parse", "HEAD~1"),
        "authority_rehearsal_revision": rev,
        "authority_rehearsal_pushed": False,
        "authority_rehearsal_applies": [
            "GT pack core stage (docs/candidates/GT/apply_to_pinned_checkout.py)",
        ],
        "authority_semantics_tree_before_gt": git(
            authority, "rev-parse", "HEAD~1:semantics"
        ),
        "sv_admitted": {
            "release": BINDING["sv_admitted"]["release"],
            "admission_merge_commit": BINDING["sv_admitted"]["admission_merge_commit"],
            "admitted_semantics_tree": BINDING["sv_admitted"][
                "admitted_semantics_tree"
            ],
        },
        "governance_grammar_revision": g1,
        "governance_catalog_revision": g2,
        "governance_store": "local, rebuilt by this tool from synthesis/governance/ (never pushed)",
        "compiler": request["compiler"],
        "schema_synthesize_exit_codes": [r[0] for r in runs],
        "deterministic_replay": runs[0][1] == runs[1][1],
        "grammar_summary": summary,
        "owner_review": "not_performed",
        "admission": "not_granted",
    }
    if code != 0:
        receipt["schema_synthesize_stdout"] = candidate_raw.decode(errors="replace")[
            :20000
        ]
        receipt["schema_synthesize_stderr"] = stderr.decode(errors="replace")[:4000]
    (work / "candidate.json").write_bytes(candidate_raw)
    receipt["candidate_json_compiler_bytes_sha256"] = sha256(candidate_raw)
    check_code = None
    if code == 0:
        check_code, check_out, _ = run_cli(
            compiler_root, "schema-candidate-check", str(work / "candidate.json")
        )
        receipt["schema_candidate_check_exit_code"] = check_code
        receipt["schema_candidate_check"] = json.loads(check_out or b"null")
    derive_code, derive_out, _ = run_cli(
        compiler_root,
        "schema-derive",
        "--authority-root",
        str(authority),
        "--revision",
        rev,
        "--repository",
        REPOSITORY,
        "--profile",
        PROJECTION_PROFILE,
        "--composition-profile",
        COMPOSITION_PROFILE,
        "--observations-out",
        str(work / "observations.json"),
    )
    receipt["schema_derive_exit_code"] = derive_code

    # ---- write outputs (all machine paths replaced by placeholders)
    gen = out / "generated"
    gov_out = out / "governance"
    for d in (gen, gov_out):
        d.mkdir(parents=True, exist_ok=True)
    for path in sorted((gov / GOVERNANCE_DIR).rglob("*.yaml")):
        target = gov_out / path.relative_to(gov / GOVERNANCE_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    portable = json.loads(json.dumps(request))
    portable["authority"]["root"] = "<authority rehearsal store rebuilt by this tool>"
    portable["governance"]["root"] = "<governance store rebuilt by this tool>"
    (gen / "request.json").write_bytes(pretty_json(portable))
    (gen / "constraint-ledger.json").write_bytes(
        pretty_json(
            {
                "schema": "l9.gt.grammar-translation-ledger/v1",
                "hand_schema": HAND_SCHEMA,
                "summary": summary,
                "entries": ledger,
            }
        )
    )
    derive = json.loads(derive_out)
    derive["observations"]["path"] = "observations.json"
    (gen / "schema-derive-report.json").write_bytes(pretty_json(derive))
    shutil.copyfile(work / "observations.json", gen / "observations.json")
    if code == 0:
        candidate = json.loads(candidate_raw)
        (gen / "candidate.json").write_bytes(candidate_raw)
        names = {
            "projection_schema": "strategic_planner_interaction_projection.candidate.schema.json",
            "composition_schema": "strategic_planner_interaction_composition.candidate.schema.json",
        }
        receipt["outputs"] = {}
        for key, name in names.items():
            data = canonical_json(candidate[key], newline=True)
            (gen / name).write_bytes(data)
            receipt["outputs"][key] = {"path": name, "sha256": sha256(data)}
            if candidate["output_digests"][key] != sha256(data):
                raise SynthesisError(
                    f"extracted {key} does not match the candidate's output digest"
                )
        receipt["outputs"]["provenance"] = {
            "path": "candidate.json#/provenance",
            "sha256": candidate["output_digests"]["provenance"],
        }
        receipt["output_digests"] = candidate.get("output_digests")
    (gen / "run-receipt.json").write_bytes(pretty_json(receipt))
    return receipt


def _same(name: Path, committed: bytes | None, fresh: bytes | None) -> bool:
    """YAML byte-for-byte; JSON by parsed content (Biome owns JSON layout here)."""
    if committed is None or fresh is None:
        return committed == fresh
    if name.suffix == ".json":
        return json.loads(committed) == json.loads(fresh)
    return committed == fresh


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--target-store", required=True, type=Path)
    ap.add_argument("--compiler-root", required=True, type=Path)
    ap.add_argument(
        "--check",
        action="store_true",
        help="regenerate and compare with committed files",
    )
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="gt-synthesis-") as tmp:
        work = Path(tmp) / "work"
        work.mkdir()
        out = Path(tmp) / "out" if args.check else SYNTHESIS
        try:
            receipt = generate(
                args.target_store.resolve(),
                args.compiler_root.resolve(),
                out,
                work,
            )
        except (SynthesisError, subprocess.CalledProcessError) as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 2
        if args.check:
            drift = []
            for sub in ("governance", "generated"):
                committed = {
                    p.relative_to(SYNTHESIS / sub): p.read_bytes()
                    for p in (SYNTHESIS / sub).rglob("*")
                    if p.is_file()
                }
                fresh = {
                    p.relative_to(out / sub): p.read_bytes()
                    for p in (out / sub).rglob("*")
                    if p.is_file()
                }
                drift += [
                    f"{sub}/{k}"
                    for k in sorted(set(committed) | set(fresh))
                    if not _same(k, committed.get(k), fresh.get(k))
                ]
            if drift:
                print(
                    "FAIL: synthesis drift: " + ", ".join(map(str, drift)),
                    file=sys.stderr,
                )
                return 1
            print(
                "OK: committed synthesis outputs reproduce (YAML byte-for-byte, JSON by content)"
            )
        print(
            json.dumps(
                {
                    k: receipt[k]
                    for k in (
                        "schema_synthesize_exit_codes",
                        "deterministic_replay",
                        "grammar_summary",
                        "schema_derive_exit_code",
                    )
                },
                indent=2,
            )
        )
        return (
            0
            if receipt["schema_synthesize_exit_codes"][0] == 0
            and receipt["deterministic_replay"]
            else 3
        )


if __name__ == "__main__":
    sys.exit(main())
