"""Admission-closure gate for new Quantum-L9/.github semantics.

Walks one subject (new invariants, vocabulary terms, contracts, canonical sources, source
classes, projection profiles, composition profiles, payload schemas) up a fixed ladder and
reports the highest rung every lower rung supports:

  INCOMPLETE          a subject item is missing from a registration surface at HEAD, a
                      registry is ambiguous (duplicate source id or path, duplicate output
                      schema id), a type-specific admission rule fails, or an admitted profile
                      version was edited in place
  REGISTERED          registered at HEAD, but a qualification gate fails: the native validator,
                      `make validate`, `make check` or `make test`; the highest release record
                      (subject coverage and the complete SC-008 inventory); the release
                      sequence; or the subject's closure against the admitted base (an omitted
                      affected identity, an undeclared revision, an unadmitted dependency)
  RELEASED_CANDIDATE  every gate above passes, but no admitted release covers the subject
  ADMITTED            the commit that admitted a release is on main, its release record is
                      unedited since and its full inventory verifies there, its ADR existed and
                      was accepted at that commit and is unedited since, the ADR binds the
                      approved `semantics/` tree, the release, the target class, a decision
                      reference and every identity that release introduced, and the subject's
                      records are identical at admission, on main and at HEAD
  DOWNSTREAM_USABLE   ADMITTED, the subject names at least one profile, HEAD is main, and the
                      real compiler at an exact clean revision projects and composes every
                      subject profile to PASS with empty unresolved criteria, twice with
                      byte-identical output, and every emitted artifact and receipt verifies
                      independently (digests, provenance, exact coverage, payload schema),
                      with negative controls rejected

UNRESOLVED (exit 2) means an input, a git read, the compiler's output or a required tool could
not be read or was malformed; it is never reported as a rung.

The gate is evidence. It never admits anything and never writes canonical files.

Usage:
  python3 check_admission_closure.py --checkout REPO --subject SUBJECT.json
      [--require registered|released|admitted|downstream]
      [--compiler-src ENGINE_CHECKOUT --output-root DIR [--compiler-revision SHA]]
      [--main-ref origin/main]

Exit codes: 0 the verdict reached --require, 1 it did not, 2 UNRESOLVED.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

SUBJECT_SCHEMA = "l9.projection-admission-subject/v1"
REPORT_SCHEMA = "l9.projection-admission-closure/v1"
REPOSITORY = "Quantum-L9/.github"
LADDER = [
    "INCOMPLETE",
    "REGISTERED",
    "RELEASED_CANDIDATE",
    "ADMITTED",
    "DOWNSTREAM_USABLE",
]
REQUIRE = {
    "registered": "REGISTERED",
    "released": "RELEASED_CANDIDATE",
    "admitted": "ADMITTED",
    "downstream": "DOWNSTREAM_USABLE",
}
ITEM_KINDS = (
    "invariants",
    "vocabulary_terms",
    "contracts",
    "canonical_sources",
    "source_classes",
    "projection_profiles",
    "composition_profiles",
    "schemas",
)
# The ledger file that holds each kind of item; a release must cover it at current bytes.
KIND_LEDGER = {
    "invariants": "invariants.yaml",
    "vocabulary_terms": "vocabulary.yaml",
    "contracts": "contracts.yaml",
    "canonical_sources": "canonical_sources.yaml",
    "source_classes": "projection_profiles.yaml",
    "projection_profiles": "projection_profiles.yaml",
    "composition_profiles": "composition_profiles.yaml",
    "schemas": "generic_compiler_manifest.yaml",
}
RELEASES = "docs/semantic-foundation"
VERSION_DIR = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
# The only admitted form in use: "Status: **ADMITTED ADDITIVE SUCCESSOR** (ADR-025, ...)".
ADMITTED_STATUS = re.compile(r"^Status:\s*\*\*ADMITTED(?: [A-Z][A-Z ]*)?\*\*")
MAKE_GATES = ("validate", "check", "test")
# Words that turn an "Accepted for vX" status line into something other than acceptance.
NOT_ACCEPTED = re.compile(
    r"\bcandidate\b|does not admit|not admitted|not accepted|pending|withdrawn|superseded",
    re.IGNORECASE,
)
# Quoted words are the owner's, reported verbatim ("The GT candidate IS to be admitted"),
# and code spans are names; neither is the record's own disclaimer of acceptance.
QUOTED = re.compile(r'"[^"\n]*"|\u201c[^\u201d\n]*\u201d|`[^`\n]*`')

# Identity shapes for new subject items (all ids on main at 9488d8f conform).
PROJECTION_ID = re.compile(r"^l9\.projection/[a-z0-9][a-z0-9.-]*@([1-9]\d*)$")
COMPOSITION_ID = re.compile(r"^l9\.compose/[a-z0-9][a-z0-9.-]*@([1-9]\d*)$")
CONTRACT_ID = re.compile(r"^l9\.contract/[a-z0-9][a-z0-9.-]*@[1-9]\d*$")
SCHEMA_DEFINITION = "l9.schema-definition/v1"
# A registered payload schema of the source-class dispatch protocol (compiler 0.10.0,
# l9_semantic_compiler/passes/payload_validation.py). Its identity is its own `schema_id`,
# never a `properties.schema.const` marker, and it carries one descriptor per source class.
SOURCE_CLASS_SCHEMA = "l9.source-class-payload-schema/v1"
SOURCE_CLASS_DISPATCH = {"protocol": "l9.payload-validation/source-class-dispatch@1"}
SOURCE_CLASS_KINDS = {
    "projection": "projection_payload_schema",
    "composition": "composition_payload_schema",
}
# Keys of the legacy union grammar a source-class registration must not carry.
LEGACY_GRAMMAR_KEYS = {
    "type",
    "properties",
    "fields",
    "required",
    "items",
    "const",
    "enum",
}
# Profile fields compiler 0.10.0 evaluates mechanically, and fields it can only report as
# unresolved (l9_semantic_compiler/passes/projection.py _PROJECTION_*, _COMPOSITION_*).
PROJECTION_FIELDS = {
    "id",
    "class",
    "consumer",
    "purpose",
    "sources",
    "output",
    "successor_of",
    "breaking_changes",
    "payload_validation",
    "forbidden",
    "rules",
}
COMPOSITION_FIELDS = {
    "id",
    "purpose",
    "accepts",
    "composes",
    "merge_strategy",
    "conflict_result",
    "output",
    "payload_validation",
    "required_provenance",
}
NAMESPACED_MERGE = {
    "placement": "source_class_namespace",
    "source_coverage": "exact",
    "duplicate_source": "conflict",
    "semantic_identity_collision": "require_equivalence",
}
DEEP_MERGE = {
    "mappings": "deep_merge_if_disjoint",
    "sequences": "preserve_source_order",
    "scalar_collision": "conflict",
    "semantic_identity_collision": "require_equivalence",
}


class InputError(Exception):
    """A required input is missing, unreadable or malformed: UNRESOLVED, never a rung."""


class SelectorError(Exception):
    """A selector is outside the l9.selector/v1 grammar or does not fit its source."""


# --------------------------------------------------------------------------- git and trees


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def git_out(repo: Path, *args: str) -> str:
    """Stdout of a git command that must succeed; any failure is UNRESOLVED."""
    done = run_git(repo, *args)
    if done.returncode != 0:
        raise InputError(f"git {' '.join(args)} failed: {done.stderr.strip()[:200]}")
    return done.stdout.strip()


def resolve_commit(repo: Path, ref: str) -> str:
    done = run_git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if done.returncode != 0:
        raise InputError(f"{ref} does not resolve to a commit; fetch it first")
    return done.stdout.strip()


class Tree:
    """Read files from the working tree (ref None) or from a resolved git commit.

    A path that does not exist reads as None; any other read failure is UNRESOLVED.
    """

    def __init__(self, repo: Path, ref: str | None = None) -> None:
        self.repo = repo
        self.ref = resolve_commit(repo, ref) if ref is not None else None

    def label(self) -> str:
        return self.ref[:12] if self.ref else "WORKTREE"

    def _exists(self, rel: str) -> bool:
        return run_git(self.repo, "cat-file", "-e", f"{self.ref}:{rel}").returncode == 0

    def read(self, rel: str) -> bytes | None:
        if self.ref is None:
            path = self.repo / rel
            if not path.is_file():
                return None
            try:
                return path.read_bytes()
            except OSError as exc:
                raise InputError(f"cannot read {rel}: {exc}") from exc
        if not self._exists(rel):
            return None
        done = subprocess.run(
            ["git", "-C", str(self.repo), "show", f"{self.ref}:{rel}"],
            capture_output=True,
            check=False,
        )
        if done.returncode != 0:
            raise InputError(f"git show {self.label()}:{rel} failed")
        return done.stdout

    def listdir(self, rel: str) -> list[str]:
        if self.ref is None:
            path = self.repo / rel
            return sorted(p.name for p in path.iterdir()) if path.is_dir() else []
        if not self._exists(rel):
            return []
        return sorted(
            git_out(self.repo, "ls-tree", "--name-only", f"{self.ref}:{rel}").split()
        )

    def yaml(self, rel: str) -> dict[str, Any]:
        data = self.read(rel)
        if data is None:
            raise InputError(f"{self.label()}:{rel} is missing")
        return parse_yaml_mapping(data, f"{self.label()}:{rel}")

    def yaml_or_empty(self, rel: str) -> dict[str, Any]:
        """A ledger that may be absent (an empty base): absent reads as {}."""
        data = self.read(rel)
        return {} if data is None else parse_yaml_mapping(data, f"{self.label()}:{rel}")


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that refuses a repeated mapping key instead of keeping the last one."""


def _unique_mapping(loader: _UniqueKeyLoader, node: Any, deep: bool = False) -> Any:
    loader.flatten_mapping(node)
    seen: set[Any] = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate mapping key {key!r}", key_node.start_mark
            )
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping
)


def load_yaml(data: bytes | str) -> Any:
    """Parse YAML; a duplicated key raises yaml.YAMLError rather than silently collapsing."""
    return yaml.load(
        data, Loader=_UniqueKeyLoader
    )  # SafeLoader subclass: no arbitrary objects


def parse_yaml_mapping(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = load_yaml(data)
    except yaml.YAMLError as exc:
        raise InputError(f"{label} is not YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{label} is not a mapping")
    return value


def digest(value: Any) -> str:
    """The compiler's canonical-JSON digest (engine/canonical.py)."""
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def version_key(name: str) -> tuple[int, ...]:
    match = VERSION_DIR.match(name)
    if match is None:
        raise InputError(f"{name} is not a release version")
    return tuple(int(x) for x in match.groups())


# --------------------------------------------------------------------------- subject


def load_subject(path: Path) -> dict[str, list[str]]:
    """The declared subject: one list per kind, plus `revisions` (`<kind>:<id>` entries).

    A revision names an identity that already exists in the admitted base and whose meaning
    this admission changes on purpose. A changed identity left undeclared is a silent
    reinterpretation and fails the subject's closure.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"unreadable subject {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SUBJECT_SCHEMA:
        raise InputError(f"subject must declare schema {SUBJECT_SCHEMA}")
    unknown = sorted(set(raw) - {"schema", "description", "revisions", *ITEM_KINDS})
    if unknown:
        raise InputError(f"subject has unknown keys {unknown}")
    subject: dict[str, list[str]] = {}
    for kind in (*ITEM_KINDS, "revisions"):
        items = raw.get(kind, [])
        if not isinstance(items, list) or not all(
            isinstance(i, str) and i for i in items
        ):
            raise InputError(f"subject.{kind} must be a list of non-empty strings")
        if len(set(items)) != len(items):
            raise InputError(f"subject.{kind} repeats an item")
        subject[kind] = items
    if not any(subject[k] for k in ITEM_KINDS):
        raise InputError("subject names no items")
    for entry in subject["revisions"]:
        kind, _, ident = entry.partition(":")
        if kind not in ITEM_KINDS or not ident:
            raise InputError(f"subject.revisions entry {entry} is not <kind>:<id>")
        if ident not in subject[kind]:
            raise InputError(
                f"subject.revisions entry {entry} is not also listed in subject.{kind}"
            )
    return subject


# --------------------------------------------------------------------------- selectors
#
# The l9.selector/v1 grammar (semantics/selector_model.yaml), with the compiler's semantics
# (l9_semantic_compiler/engine/selectors.py): every selector is required, a filter that
# matches nothing or a [*] over a non-empty list that reaches nothing is unresolved.

_FILTER = re.compile(
    r"^\$\.(?P<collection>[A-Za-z0-9_-]+)\[\?\(@\.(?P<field>[A-Za-z0-9_-]+)\s*"
    r'(?P<op>==|contains)\s*"(?P<value>[^"]*)"\)\]$'
)
_SEGMENT = re.compile(r"^(?P<key>[A-Za-z0-9_-]+)(?P<all>\[\*\])?$")


def parse_selector(selector: Any) -> list[tuple[str, ...]]:
    if not isinstance(selector, str):
        raise SelectorError("selector is not a string")
    if selector == "$":
        return []
    match = _FILTER.match(selector)
    if match:
        return [
            ("field", match["collection"]),
            ("filter", match["field"], match["op"], match["value"]),
        ]
    if not selector.startswith("$."):
        raise SelectorError("selector is outside the l9.selector/v1 grammar")
    steps: list[tuple[str, ...]] = []
    for token in selector[2:].split("."):
        seg = _SEGMENT.match(token)
        if not seg:
            raise SelectorError("selector is outside the l9.selector/v1 grammar")
        steps.append(("field", seg["key"]))
        if seg["all"]:
            steps.append(("all",))
    return steps


def _matches(item: dict[str, Any], field: str, op: str, expected: str) -> bool:
    actual = item.get(field)
    if op == "==":
        return actual == expected
    return expected in actual if isinstance(actual, (list, str)) else False


def resolve_selector(document: Any, steps: list[tuple[str, ...]]) -> bool:
    """True when the selector selects something; raises SelectorError on a type mismatch."""
    if not steps:
        return True
    step, rest = steps[0], steps[1:]
    if step[0] == "field":
        if not isinstance(document, dict) or step[1] not in document:
            return False
        return resolve_selector(document[step[1]], rest)
    if not isinstance(document, list):
        raise SelectorError("selector expects a list")
    if step[0] == "all":
        reached = [resolve_selector(item, rest) for item in document]
        return not document or any(reached)
    _, field, op, expected = step
    return any(
        isinstance(item, dict) and _matches(item, field, op, expected)
        for item in document
    )


_WHOLE = True


def _mask(value: Any, steps: list[tuple[str, ...]]) -> Any:
    """The compiler's selection mask: _WHOLE, a {member: mask} dict, or None when absent."""
    if not steps:
        return _WHOLE
    step, rest = steps[0], steps[1:]
    if step[0] == "field":
        if not isinstance(value, dict) or step[1] not in value:
            return None
        child = _mask(value[step[1]], rest)
        return None if child is None else {step[1]: child}
    if not isinstance(value, list):
        raise SelectorError("selector expects a list")
    members: dict[Any, Any] = {}
    if step[0] == "all":
        for index, item in enumerate(value):
            child = _mask(item, rest)
            if child is not None:
                members[index] = child
        return None if value and not members else members
    _, field, op, expected = step
    for index, item in enumerate(value):
        if isinstance(item, dict) and _matches(item, field, op, expected):
            members[index] = _WHOLE
    return members or None


def _merge_mask(existing: Any, new: Any) -> Any:
    if existing is _WHOLE or new is _WHOLE:
        return _WHOLE
    if existing is None:
        return new
    for key, value in new.items():
        existing[key] = _merge_mask(existing.get(key), value)
    return existing


def _apply(value: Any, mask: Any) -> Any:
    if mask is _WHOLE:
        return copy.deepcopy(value)
    if isinstance(value, dict):
        return {key: _apply(value[key], sub) for key, sub in mask.items()}
    return [_apply(value[index], mask[index]) for index in sorted(mask)]


def select_payload(document: Any, selectors: list[str]) -> Any:
    """The exact record-preserving payload the selectors select from `document`.

    An independent re-implementation of the compiler's `select_records`: the union of every
    selected path, each collection item one record carrying exactly its selected fields, in
    source order. Raises SelectorError when a selector is unresolved.
    """
    mask: Any = None
    for selector in selectors:
        selected = _mask(document, parse_selector(selector))
        if selected is None:
            raise SelectorError(f"missing required selector result: {selector}")
        mask = _merge_mask(mask, selected)
    if mask is None:
        raise SelectorError("selection requires a non-empty selector list")
    return _apply(document, mask)


# --------------------------------------------------------------------------- registries


def source_registry(tree: Tree) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Unique canonical sources by id, and every ambiguity in the registry.

    A duplicated id or path is never resolved by position: the duplicated id is left out of
    the returned map, so every lookup of it fails, and the ambiguity is reported.
    """
    doc = tree.yaml_or_empty("semantics/canonical_sources.yaml")
    entries = [e for e in doc.get("sources") or [] if isinstance(e, dict)]
    problems: list[str] = []
    by_id: dict[str, list[dict[str, Any]]] = {}
    by_path: dict[str, list[str]] = {}
    for entry in entries:
        ident = entry.get("id")
        if not isinstance(ident, str) or not ident:
            problems.append("canonical source registry: an entry has no id")
            continue
        by_id.setdefault(ident, []).append(entry)
        if isinstance(entry.get("path"), str):
            by_path.setdefault(entry["path"], []).append(ident)
    for ident, found in sorted(by_id.items()):
        if len(found) > 1:
            problems.append(
                f"canonical source registry: id {ident} is registered {len(found)} times"
            )
    for path, ids in sorted(by_path.items()):
        if len(ids) > 1:
            problems.append(
                f"canonical source registry: path {path} is registered by {sorted(ids)}"
            )
    unique = {i: f[0] for i, f in by_id.items() if len(f) == 1}
    return unique, problems


def _sources(tree: Tree) -> dict[str, dict[str, Any]]:
    return source_registry(tree)[0]


def schema_registry(tree: Tree) -> dict[str, Any]:
    """Registered payload/envelope schemas: files, their documents, and const -> files."""
    requires = (
        tree.yaml_or_empty("semantics/generic_compiler_manifest.yaml").get("requires")
        or {}
    )
    files = list(requires.get("artifact_schemas") or [])
    problems: list[str] = []
    for name in sorted({f for f in files if files.count(f) > 1}):
        problems.append(f"artifact_schemas lists {name} {files.count(name)} times")
    docs: dict[str, dict[str, Any]] = {}
    consts: dict[str, list[str]] = {}
    for name in dict.fromkeys(files):
        data = tree.read(f"semantics/{name}")
        if data is None:
            continue
        try:
            doc = load_yaml(data)
        except yaml.YAMLError as exc:
            raise InputError(
                f"{tree.label()}:semantics/{name} is not YAML: {exc}"
            ) from exc
        if not isinstance(doc, dict):
            raise InputError(f"{tree.label()}:semantics/{name} is not a mapping")
        docs[name] = doc
        const = schema_identity(doc)
        if const is not None:
            consts.setdefault(const, []).append(name)
    for const, names in sorted(consts.items()):
        if len(names) > 1:
            problems.append(
                f"output schema identity {const} is declared by {len(names)} registered "
                f"schemas {sorted(names)}"
            )
    return {
        "files": files,
        "docs": docs,
        "consts": consts,
        "catalogs": set(requires.get("semantic_catalogs") or []),
        "problems": problems,
    }


def schema_identity(doc: Any) -> str | None:
    """The output-schema identity a registered payload schema declares.

    A source-class registration names itself with `schema_id`; a schema-definition
    document is identified by its `properties.schema.const` marker.
    """
    if not isinstance(doc, dict):
        return None
    if doc.get("schema") == SOURCE_CLASS_SCHEMA:
        sid = doc.get("schema_id")
        return sid if isinstance(sid, str) and sid.strip() else None
    const = ((doc.get("properties") or {}).get("schema") or {}).get("const")
    return const if isinstance(const, str) else None


def _schema_consts(tree: Tree, artifact_schemas: list[str]) -> dict[str, str]:
    """output.schema value -> the one registered schema declaring it (ambiguous ones omitted)."""
    del artifact_schemas  # the registry is read whole so a duplicate cannot hide
    reg = schema_registry(tree)
    return {c: names[0] for c, names in reg["consts"].items() if len(names) == 1}


def _class_artifacts(tree: Tree) -> dict[str, str]:
    classes = (
        tree.yaml_or_empty("semantics/projection_profiles.yaml").get("source_classes")
        or {}
    )
    return {
        cls: f"semantics/{decl['canonical_artifact']}"
        for cls, decl in classes.items()
        if isinstance(decl, dict) and isinstance(decl.get("canonical_artifact"), str)
    }


def subject_files(tree: Tree, subject: dict[str, list[str]]) -> list[str]:
    """Every semantics/ file whose bytes carry a subject item."""
    files = {f"semantics/{KIND_LEDGER[k]}" for k in ITEM_KINDS if subject[k]}
    files |= {f"semantics/{name}" for name in subject["schemas"]}
    sources = _sources(tree)
    for ref in subject["canonical_sources"]:
        if ref in sources and isinstance(sources[ref].get("path"), str):
            files.add(sources[ref]["path"])
    artifacts = _class_artifacts(tree)
    files |= {artifacts[c] for c in subject["source_classes"] if c in artifacts}
    return sorted(files)


# --------------------------------------------------------------------------- registration


def _ids(entries: Any) -> list[str]:
    return [e.get("id") for e in entries or [] if isinstance(e, dict)]


def _nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class Registration:
    """Every subject item registered on every surface it needs, in one tree.

    ``records`` captures what admission must keep identical: each item's record and the bytes
    of each file that is itself a subject item (model ledgers, schemas). ``unresolvable``
    lists declarations compiler 0.10.0 can only report as unresolved: they do not block
    registration, but they keep a profile's downstream result `unknown`, never PASS.
    """

    def __init__(self, tree: Tree, subject: dict[str, list[str]]) -> None:
        self.tree = tree
        self.subject = subject
        self.gaps: list[str] = []
        self.records: dict[str, Any] = {}
        self.unresolvable: list[str] = []
        self.invariants = [
            e
            for e in tree.yaml_or_empty("semantics/invariants.yaml").get("invariants")
            or []
            if isinstance(e, dict)
        ]
        self.terms = tree.yaml_or_empty("semantics/vocabulary.yaml").get("terms") or {}
        self.contracts = [
            e
            for e in tree.yaml_or_empty("semantics/contracts.yaml").get("contracts")
            or []
            if isinstance(e, dict)
        ]
        self.sources, source_problems = source_registry(tree)
        self.profiles_doc = tree.yaml_or_empty("semantics/projection_profiles.yaml")
        self.classes = self.profiles_doc.get("source_classes") or {}
        self.projections = [
            p
            for p in self.profiles_doc.get("projection_profiles") or []
            if isinstance(p, dict)
        ]
        self.compositions = [
            p
            for p in tree.yaml_or_empty("semantics/composition_profiles.yaml").get(
                "profiles"
            )
            or []
            if isinstance(p, dict)
        ]
        self.schemas = schema_registry(tree)
        forbidden = self.profiles_doc.get("forbidden_constraints") or {}
        self.forbidden_defs = set((forbidden.get("definitions") or {}).keys())
        # Registry ambiguity blocks every subject: resolution by position is not resolution.
        self.gaps += source_problems + self.schemas["problems"]

    # ------------------------------------------------------------------ helpers

    def unique(
        self, kind: str, ident: str, entries: list[Any]
    ) -> dict[str, Any] | None:
        found = [e for e in entries if e.get("id") == ident]
        if len(found) != 1:
            self.gaps.append(f"{kind} {ident}: defined {len(found)} times")
            return None
        self.records[f"{kind}:{ident}"] = found[0]
        return found[0]

    def dependency_file(self, rel: str) -> None:
        data = self.tree.read(rel)
        self.records[f"dep:file:{rel}"] = None if data is None else sha_bytes(data)

    def projection_dependencies(self, profile: dict[str, Any]) -> None:
        """Bytes a projection's meaning depends on: its sources, schema and criteria."""
        for cls in profile.get("sources") or {}:
            artifact = (self.classes.get(cls) or {}).get("canonical_artifact")
            if isinstance(artifact, str):
                self.dependency_file(f"semantics/{artifact}")
        schema_id = (profile.get("output") or {}).get("schema")
        names = (
            self.schemas["consts"].get(schema_id)
            if isinstance(schema_id, str)
            else None
        )
        for name in names or []:
            self.dependency_file(f"semantics/{name}")
        definitions = (self.profiles_doc.get("forbidden_constraints") or {}).get(
            "definitions"
        ) or {}
        for token in profile.get("forbidden") or []:
            self.records[f"dep:forbidden:{token}"] = definitions.get(token)

    def file_record(self, key: str, rel: str) -> bool:
        data = self.tree.read(rel)
        if data is None:
            return False
        self.records[key] = sha_bytes(data)
        return True

    def projectable_source(self, rel: str, who: str) -> dict[str, Any] | None:
        """The one registered source at `rel`, canonical, projectable and in the catalogs."""
        found = [e for e in self.sources.values() if e.get("path") == rel]
        if len(found) != 1:
            self.gaps.append(
                f"{who}: {rel} is bound to {len(found)} registered sources, not exactly one"
            )
            return None
        entry = found[0]
        if entry.get("canonical") is not True:
            self.gaps.append(f"{who}: source {entry['id']} is not canonical: true")
        if entry.get("projection_allowed") is not True:
            self.gaps.append(f"{who}: source {entry['id']} is not projection_allowed")
        if Path(rel).name not in self.schemas["catalogs"]:
            self.gaps.append(f"{who}: {Path(rel).name} is not in semantic_catalogs")
        return entry

    def output_schema(self, who: str, profile: dict[str, Any]) -> str | None:
        schema = (profile.get("output") or {}).get("schema")
        names = self.schemas["consts"].get(schema) if isinstance(schema, str) else None
        if not names:
            self.gaps.append(f"{who}: no registered schema declares {schema}")
            return None
        if len(names) > 1:
            return None  # already reported as a registry ambiguity
        doc = self.schemas["docs"][names[0]]
        governed = doc.get("governed_by")
        if isinstance(governed, dict) and profile.get("id") not in governed.values():
            self.gaps.append(
                f"{who}: schema {names[0]} is governed_by {governed}, not this profile"
            )
        return names[0]

    # ------------------------------------------------------------------ kinds

    def invariant(self, ident: str) -> None:
        entry = self.unique("invariant", ident, self.invariants)
        if entry is None:
            return
        if not _nonempty_str(entry.get("statement")):
            self.gaps.append(f"invariant {ident}: no statement")
        if entry.get("scope") != "global":
            self.gaps.append(f"invariant {ident}: scope is not global")
        if not _nonempty_str(entry.get("owner")):
            self.gaps.append(f"invariant {ident}: no owner")
        statement = " ".join(str(entry.get("statement", "")).split()).lower()
        twins = [
            e.get("id")
            for e in self.invariants
            if e is not entry
            and statement
            and " ".join(str(e.get("statement", "")).split()).lower() == statement
        ]
        if twins:
            self.gaps.append(
                f"invariant {ident}: duplicates the governing statement of {twins}"
            )

    def term(self, term: str) -> None:
        record = self.terms.get(term)
        if not isinstance(record, dict):
            self.gaps.append(
                f"vocabulary term {term}: absent from vocabulary.yaml terms"
            )
            return
        self.records[f"term:{term}"] = record
        if isinstance(record.get("subtype_of"), str):
            self.records[f"dep:term:{record['subtype_of']}"] = self.terms.get(
                record["subtype_of"]
            )
        if isinstance(record.get("detailed_model"), str):
            self.dependency_file(f"semantics/{record['detailed_model']}")
        if not _nonempty_str(record.get("definition")):
            self.gaps.append(f"vocabulary term {term}: no definition")
        if not _nonempty_str(record.get("semantic_class")):
            self.gaps.append(f"vocabulary term {term}: no semantic_class")
        parent = record.get("subtype_of")
        if parent is not None and parent not in self.terms:
            self.gaps.append(
                f"vocabulary term {term}: subtype_of {parent} is not a term"
            )
        model = record.get("detailed_model")
        if model is not None and not any(
            e.get("path") == f"semantics/{model}" for e in self.sources.values()
        ):
            self.gaps.append(
                f"vocabulary term {term}: detailed_model {model} is not a registered source"
            )

    def contract(self, ident: str) -> None:
        entry = self.unique("contract", ident, self.contracts)
        if entry is None:
            return
        if not CONTRACT_ID.match(ident):
            self.gaps.append(f"contract {ident}: id is not l9.contract/<name>@<N>")
        for field in ("purpose", "scope", "owner"):
            if not _nonempty_str(entry.get(field)):
                self.gaps.append(f"contract {ident}: no {field}")
        refs = entry.get("source_invariants")
        if not isinstance(refs, list) or not refs:
            self.gaps.append(f"contract {ident}: no source_invariants")
            return
        known = set(_ids(self.invariants))
        for ref in refs:
            found = [e for e in self.invariants if e.get("id") == ref]
            self.records[f"dep:invariant:{ref}"] = found[0] if len(found) == 1 else None
        for ref in refs:
            if ref not in known:
                self.gaps.append(
                    f"contract {ident}: source invariant {ref} is not defined"
                )

    def canonical_source(self, ref: str) -> None:
        entry = self.sources.get(ref)
        if entry is None:
            self.gaps.append(
                f"canonical source {ref}: not registered exactly once in canonical_sources.yaml"
            )
            return
        self.records[f"source:{ref}"] = entry
        path = entry.get("path")
        if not isinstance(path, str) or not self.file_record(
            f"source_file:{ref}", path
        ):
            self.gaps.append(f"canonical source {ref}: path {path} does not exist")
            return
        self.projectable_source(path, f"canonical source {ref}")

    def source_class(self, cls: str) -> None:
        decl = self.classes.get(cls)
        artifact = (decl or {}).get("canonical_artifact")
        if not artifact:
            self.gaps.append(
                f"source class {cls}: not declared in projection_profiles source_classes"
            )
            return
        self.records[f"source_class:{cls}"] = decl
        rel = f"semantics/{artifact}"
        if self.projectable_source(rel, f"source class {cls}") is None:
            return
        if not self.file_record(f"source_class_file:{cls}", rel):
            self.gaps.append(f"source class {cls}: {rel} does not exist")

    def projection_profile(self, ref: str) -> None:
        profile = self.unique("projection profile", ref, self.projections)
        if profile is None:
            return
        who = f"projection profile {ref}"
        if not PROJECTION_ID.match(ref):
            self.gaps.append(f"{who}: id is not l9.projection/<name>@<N>")
        unknown = sorted(set(profile) - PROJECTION_FIELDS)
        if unknown:
            self.gaps.append(f"{who}: fields {unknown} are refused by the compiler")
        if profile.get("class") not in (self.profiles_doc.get("profile_classes") or {}):
            self.gaps.append(
                f"{who}: class {profile.get('class')} is not a profile class"
            )
        if profile.get("class") == "consumer" and not _nonempty_str(
            profile.get("consumer")
        ):
            self.gaps.append(f"{who}: a consumer-class profile names no consumer")
        if not _nonempty_str(profile.get("purpose")):
            self.gaps.append(f"{who}: no purpose")
        sources = profile.get("sources")
        if not isinstance(sources, dict) or not sources:
            self.gaps.append(f"{who}: selects no source class")
            sources = {}
        for cls, spec in sources.items():
            self._profile_source(who, cls, spec)
        self.payload_validation(
            who, profile, "projection", self.output_schema(who, profile)
        )
        self.projection_dependencies(profile)
        for token in profile.get("forbidden") or []:
            if token not in self.forbidden_defs:
                self.unresolvable.append(
                    f"{who}: forbidden category {token} has no criterion in "
                    "forbidden_constraints.definitions (PROJECTION-016: unresolved)"
                )
        for rule in profile.get("rules") or []:
            self.unresolvable.append(f"{who}: declared rule {rule} has no criterion")
        for key in sorted(k for k in profile.get("output") or {} if k != "schema"):
            self.unresolvable.append(
                f"{who}: output.{key} is not realized by projection"
            )
        predecessor = profile.get("successor_of")
        if predecessor is not None:
            prior = [p for p in self.projections if p.get("id") == predecessor]
            if len(prior) != 1:
                self.gaps.append(
                    f"{who}: successor_of {predecessor} is not one profile"
                )
            elif (prior[0].get("class"), prior[0].get("consumer")) != (
                profile.get("class"),
                profile.get("consumer"),
            ):
                self.gaps.append(
                    f"{who}: a successor keeps its predecessor's class and consumer "
                    "(PROJECTION-014)"
                )

    def _profile_source(self, who: str, cls: str, spec: Any) -> None:
        decl = self.classes.get(cls)
        artifact = (decl or {}).get("canonical_artifact")
        if not artifact:
            self.gaps.append(f"{who}: source class {cls} undeclared")
            return
        rel = f"semantics/{artifact}"
        if self.projectable_source(rel, f"{who}: source class {cls}") is None:
            return
        selectors = (spec or {}).get("selectors") if isinstance(spec, dict) else None
        if not isinstance(selectors, list) or not selectors:
            self.gaps.append(f"{who}: source class {cls} declares no selectors")
            return
        data = self.tree.read(rel)
        if data is None:
            self.gaps.append(f"{who}: source class {cls}: {rel} does not exist")
            return
        document = parse_yaml_mapping(data, f"{self.tree.label()}:{rel}")
        for selector in selectors:
            try:
                resolved = resolve_selector(document, parse_selector(selector))
            except SelectorError as exc:
                self.gaps.append(f"{who}: selector {selector} on {cls}: {exc}")
                continue
            if not resolved:
                self.gaps.append(
                    f"{who}: selector {selector} selects nothing in {rel} "
                    "(missing_required_selector_result_is_invalid)"
                )

    def composition_profile(self, ref: str) -> None:
        profile = self.unique("composition profile", ref, self.compositions)
        if profile is None:
            return
        who = f"composition profile {ref}"
        if not COMPOSITION_ID.match(ref):
            self.gaps.append(f"{who}: id is not l9.compose/<name>@<N>")
        unknown = sorted(set(profile) - COMPOSITION_FIELDS)
        if unknown:
            self.gaps.append(f"{who}: fields {unknown} are refused by the compiler")
        if profile.get("accepts") != ["projection_artifact"]:
            self.gaps.append(f"{who}: accepts is not [projection_artifact]")
        if profile.get("conflict_result") != "invalid":
            self.gaps.append(f"{who}: conflict_result is not invalid")
        strategy = profile.get("merge_strategy")
        composes = (profile.get("composes") or {}).get("projection_profile")
        if strategy == NAMESPACED_MERGE:
            if composes is None:
                self.gaps.append(f"{who}: a namespaced composition names no profile")
        elif strategy != DEEP_MERGE:
            self.gaps.append(f"{who}: merge_strategy is not a supported exact strategy")
        if composes is not None and _ids(self.projections).count(composes) != 1:
            self.gaps.append(f"{who}: composes unknown profile {composes}")
        elif composes is not None:
            composed = next(p for p in self.projections if p.get("id") == composes)
            self.records[f"dep:projection profile:{composes}"] = composed
            self.projection_dependencies(composed)
        self.payload_validation(
            who, profile, "composition", self.output_schema(who, profile)
        )
        for value in profile.get("required_provenance") or []:
            self.unresolvable.append(
                f"{who}: required_provenance {value} has no criterion in compiler 0.10.0"
            )

    def payload_validation(
        self, who: str, profile: dict[str, Any], kind: str, name: str | None
    ) -> None:
        """Source-class dispatch is declared exactly when the output schema realizes it."""
        declared = profile.get("payload_validation")
        doc = self.schemas["docs"].get(name) if name else None
        realizes = isinstance(doc, dict) and doc.get("schema") == SOURCE_CLASS_SCHEMA
        if declared is None:
            if realizes:
                self.gaps.append(
                    f"{who}: output schema {name} is a source-class registration, but the "
                    "profile declares no payload_validation"
                )
            return
        if declared != SOURCE_CLASS_DISPATCH:
            self.gaps.append(
                f"{who}: payload_validation {declared} is not a protocol compiler 0.10.0 "
                f"realizes ({SOURCE_CLASS_DISPATCH})"
            )
            return
        if doc is None:
            return  # the unresolved output schema is already a gap
        if not realizes:
            self.gaps.append(
                f"{who}: declares source-class dispatch, but its output schema {name} is "
                f"not a {SOURCE_CLASS_SCHEMA} registration"
            )
            return
        if doc.get("document_kind") != SOURCE_CLASS_KINDS[kind]:
            self.gaps.append(
                f"{who}: output schema {name} is a {doc.get('document_kind')}, not a "
                f"{SOURCE_CLASS_KINDS[kind]}"
            )
        target = profile
        if kind == "composition":
            composes = (profile.get("composes") or {}).get("projection_profile")
            found = [p for p in self.projections if p.get("id") == composes]
            if len(found) != 1:
                return  # already reported by the composition check
            target = found[0]
            if target.get("payload_validation") != SOURCE_CLASS_DISPATCH:
                self.gaps.append(
                    f"{who}: composes {composes}, which does not declare the same "
                    "payload_validation protocol"
                )
        shapes = [s for s in doc.get("source_shapes") or [] if isinstance(s, dict)]
        classes = list(target.get("sources") or {})
        if [s.get("source_class") for s in shapes] != classes:
            self.gaps.append(
                f"{who}: output schema {name} covers source classes "
                f"{[s.get('source_class') for s in shapes]}, not exactly {classes} in order"
            )
            return
        for shape in shapes:
            artifact = (self.classes.get(shape["source_class"]) or {}).get(
                "canonical_artifact"
            )
            owners = [
                e.get("id")
                for e in self.sources.values()
                if e.get("path") == f"semantics/{artifact}"
            ]
            if owners != [shape.get("source_ref")]:
                self.gaps.append(
                    f"{who}: output schema {name} binds source class "
                    f"{shape['source_class']} to {shape.get('source_ref')}, not the "
                    f"registered source {owners}"
                )

    def _source_class_schema(self, name: str, doc: dict[str, Any]) -> None:
        legacy = sorted(set(doc) & LEGACY_GRAMMAR_KEYS)
        if legacy:
            self.gaps.append(
                f"schema {name}: a source-class registration carries the legacy union "
                f"grammar keys {legacy}"
            )
        if doc.get("payload_validation") != SOURCE_CLASS_DISPATCH:
            self.gaps.append(
                f"schema {name}: payload_validation is not {SOURCE_CLASS_DISPATCH}"
            )
        if doc.get("document_kind") not in SOURCE_CLASS_KINDS.values():
            self.gaps.append(
                f"schema {name}: document_kind {doc.get('document_kind')} is not one of "
                f"{sorted(SOURCE_CLASS_KINDS.values())}"
            )
        governed = doc.get("governed_by")
        if not isinstance(governed, dict) or len(governed) != 1:
            self.gaps.append(
                f"schema {name}: governed_by must name exactly one profile"
            )
        if not _nonempty_str(doc.get("descriptor_dialect")):
            self.gaps.append(f"schema {name}: no descriptor_dialect")
        shapes = doc.get("source_shapes")
        if not isinstance(shapes, list) or not shapes:
            self.gaps.append(f"schema {name}: source_shapes is not a non-empty list")
            return
        seen: set[Any] = set()
        for index, shape in enumerate(shapes):
            if (
                not isinstance(shape, dict)
                or set(shape) != {"source_class", "source_ref", "descriptor"}
                or not _nonempty_str(shape.get("source_class"))
                or not _nonempty_str(shape.get("source_ref"))
                or not isinstance(shape.get("descriptor"), dict)
            ):
                self.gaps.append(f"schema {name}: source_shapes[{index}] is malformed")
                continue
            if shape["source_class"] in seen:
                self.gaps.append(
                    f"schema {name}: source class {shape['source_class']} appears twice"
                )
            seen.add(shape["source_class"])

    def schema(self, name: str) -> None:
        files = self.schemas["files"]
        if name not in files:
            self.gaps.append(
                f"schema {name}: not in generic_compiler_manifest artifact_schemas"
            )
        if not self.file_record(f"schema:{name}", f"semantics/{name}"):
            self.gaps.append(f"schema {name}: semantics/{name} does not exist")
            return
        doc = self.schemas["docs"].get(name)
        if doc is None:
            return
        if doc.get("schema") == SOURCE_CLASS_SCHEMA:
            self._source_class_schema(name, doc)
        elif doc.get("schema") != SCHEMA_DEFINITION:
            self.gaps.append(f"schema {name}: schema is not {SCHEMA_DEFINITION}")
        if not _nonempty_str(doc.get("artifact_id")):
            self.gaps.append(f"schema {name}: no artifact_id")
        const = schema_identity(doc)
        if const is None:
            self.gaps.append(
                f"schema {name}: no schema_id declared"
                if doc.get("schema") == SOURCE_CLASS_SCHEMA
                else f"schema {name}: no properties.schema.const declared"
            )
            return
        outputs = [
            p.get("id")
            for p in self.projections + self.compositions
            if (p.get("output") or {}).get("schema") == const
        ]
        if len(outputs) != 1:
            self.gaps.append(
                f"schema {name}: {const} is the output of {len(outputs)} profiles, "
                "not exactly one"
            )

    def run(self) -> dict[str, Any]:
        for ident in self.subject["invariants"]:
            self.invariant(ident)
        for term in self.subject["vocabulary_terms"]:
            self.term(term)
        for ident in self.subject["contracts"]:
            self.contract(ident)
        for ref in self.subject["canonical_sources"]:
            self.canonical_source(ref)
        for cls in self.subject["source_classes"]:
            self.source_class(cls)
        for ref in self.subject["projection_profiles"]:
            self.projection_profile(ref)
        for ref in self.subject["composition_profiles"]:
            self.composition_profile(ref)
        for name in self.subject["schemas"]:
            self.schema(name)
        return {
            "status": "pass" if not self.gaps else "fail",
            "gaps": self.gaps,
            "records": self.records,
            "unresolvable_declarations": self.unresolvable,
        }


def registration(tree: Tree, subject: dict[str, list[str]]) -> dict[str, Any]:
    return Registration(tree, subject).run()


# --------------------------------------------------------------------------- releases


def release_versions(tree: Tree) -> list[str]:
    names = [n for n in tree.listdir(RELEASES) if VERSION_DIR.match(n)]
    return sorted(names, key=version_key)


def release_status(tree: Tree, version: str) -> str:
    data = tree.read(f"{RELEASES}/{version}/README.md")
    if data is None:
        return "MISSING"
    for line in data.decode("utf-8", "replace").splitlines():
        if line.startswith("Status:"):
            if ADMITTED_STATUS.match(line):
                return "ADMITTED"
            return "CANDIDATE" if "CANDIDATE" in line.upper() else "OTHER"
    return "OTHER"


def accepted_adr(tree: Tree, version: str) -> str | None:
    """The ADR whose status accepts exactly this version, not a candidate of it."""
    pattern = re.compile(
        r"^\*\*Status:\*\*\s*Accepted for (?:semantic-foundation )?"
        + re.escape(version)
        + r"(?![\w-]|\.\w)(?!\s+candidate)"
    )
    for name in tree.listdir("docs/adr"):
        if not name.startswith("ADR-"):
            continue
        data = tree.read(f"docs/adr/{name}")
        if data is None:
            raise InputError(f"docs/adr/{name} listed but unreadable")
        for line in data.decode("utf-8", "replace").splitlines()[:8]:
            if pattern.match(line) and not NOT_ACCEPTED.search(QUOTED.sub("", line)):
                return name
    return None


def _hash_lines(raw: bytes, version: str) -> tuple[dict[str, str], list[str]]:
    hashes: dict[str, str] = {}
    gaps: list[str] = []
    for number, line in enumerate(raw.decode("utf-8", "replace").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            gaps.append(f"{version}: HASHES.sha256 line {number} is malformed")
            continue
        if parts[1] in hashes:
            gaps.append(f"{version}: HASHES.sha256 lists {parts[1]} twice")
        hashes[parts[1]] = parts[0]
    return hashes, gaps


def release_coverage(tree: Tree, version: str, files: list[str]) -> dict[str, Any]:
    """The release record covers each subject file at its current bytes."""
    gaps: list[str] = []
    manifest_raw = tree.read(f"{RELEASES}/{version}/MANIFEST.md")
    hashes_raw = tree.read(f"{RELEASES}/{version}/HASHES.sha256")
    if manifest_raw is None or hashes_raw is None:
        return {
            "status": "fail",
            "gaps": [f"{version}: MANIFEST.md or HASHES.sha256 missing"],
        }
    manifest = manifest_raw.decode("utf-8", "replace")
    raw_hashes, _ = _hash_lines(hashes_raw, version)
    hashes = {k.removeprefix("./"): v for k, v in raw_hashes.items()}
    for rel in files:
        if f"`{rel}`" not in manifest:
            gaps.append(f"{version}: MANIFEST.md does not list `{rel}`")
        data = tree.read(rel)
        if rel not in hashes:
            gaps.append(f"{version}: HASHES.sha256 has no entry for {rel}")
        elif data is None or sha_bytes(data) != hashes[rel]:
            gaps.append(f"{version}: {rel} bytes differ from the release hash")
    return {"status": "pass" if not gaps else "fail", "gaps": gaps}


def release_inventory(tree: Tree, version: str) -> dict[str, Any]:
    """SC-008 at any tree: the release record covers the complete canonical inventory.

    Every `semantics/*.yaml` is listed and counted, every ADR is counted, and every file of
    the expected inventory (semantics, ADRs, the ADR index, the release's own Markdown) is
    hashed at its bytes in this tree; no recorded entry is dangling or stale.
    """
    base = f"{RELEASES}/{version}"
    manifest_raw = tree.read(f"{base}/MANIFEST.md")
    hashes_raw = tree.read(f"{base}/HASHES.sha256")
    if manifest_raw is None or hashes_raw is None:
        return {
            "status": "fail",
            "gaps": [f"{version}: MANIFEST.md or HASHES.sha256 missing"],
        }
    manifest = manifest_raw.decode("utf-8", "replace")
    recorded, gaps = _hash_lines(hashes_raw, version)
    semantics = sorted(
        f"semantics/{n}" for n in tree.listdir("semantics") if n.endswith(".yaml")
    )
    listed = set(re.findall(r"`(semantics/[^`]+\.yaml)`", manifest))
    gaps += [f"{version}: MANIFEST.md omits {p}" for p in semantics if p not in listed]
    gaps += [
        f"{version}: MANIFEST.md lists {p}, which does not exist"
        for p in sorted(listed - set(semantics))
    ]
    count = re.search(r"contains \*\*(\d+)\*\* canonical semantic YAML files", manifest)
    if count is None or int(count.group(1)) != len(semantics):
        gaps.append(
            f"{version}: MANIFEST.md canonical file count is not {len(semantics)}"
        )
    adrs = [
        n
        for n in tree.listdir("docs/adr")
        if n.startswith("ADR-") and n.endswith(".md")
    ]
    adr_count = re.search(r"contains \*\*(\d+)\*\* accepted ADRs", manifest)
    if adr_count is None or int(adr_count.group(1)) != len(adrs):
        gaps.append(f"{version}: MANIFEST.md accepted ADR count is not {len(adrs)}")
    expected = {f"./{p}" for p in semantics}
    expected |= {f"./docs/adr/{n}" for n in adrs}
    expected.add("./docs/adr/README.md")
    expected |= {f"./{n}" for n in tree.listdir(base) if n.endswith(".md")}
    gaps += [
        f"{version}: HASHES.sha256 omits {e}" for e in sorted(expected - set(recorded))
    ]
    for entry, value in sorted(recorded.items()):
        rel = entry.removeprefix("./")
        target = rel if rel.startswith(("semantics/", "docs/")) else f"{base}/{rel}"
        data = tree.read(target)
        if data is None:
            gaps.append(
                f"{version}: HASHES.sha256 hashes {entry}, which does not exist"
            )
        elif sha_bytes(data) != value:
            gaps.append(f"{version}: {entry} bytes differ from the release hash")
    return {
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "semantic_files": len(semantics),
        "hashed_files": len(recorded),
    }


def _release_files(tree: Tree, version: str) -> dict[str, str | None]:
    base = f"{RELEASES}/{version}"
    files: dict[str, str | None] = {}
    for name in tree.listdir(base):
        data = tree.read(f"{base}/{name}")
        files[name] = None if data is None else sha_bytes(data)
    return files


def release_sequence(head: Tree, main: Tree) -> dict[str, Any]:
    """Release history is append-only and a new release is the next one in sequence.

    Every release directory on main survives at HEAD, an admitted one byte for byte; only
    the highest unadmitted candidate on main may still change (it is folded into, with the
    owner). At most one new directory exists at HEAD, numbered above every release on main.
    """
    gaps: list[str] = []
    on_main = release_versions(main)
    at_head = release_versions(head)
    open_candidate = (
        on_main[-1]
        if on_main and release_status(main, on_main[-1]) != "ADMITTED"
        else None
    )
    for version in on_main:
        if version not in at_head:
            gaps.append(f"release {version} exists on main but not at HEAD")
            continue
        if version == open_candidate:
            continue
        if _release_files(main, version) != _release_files(head, version):
            gaps.append(f"release {version} is immutable on main but differs at HEAD")
    for tree, where in ((main, "main"), (head, "HEAD")):
        odd = [n for n in tree.listdir(RELEASES) if not VERSION_DIR.match(n)]
        if odd:
            gaps.append(f"{RELEASES} on {where} holds non-version entries {odd}")
    new = [v for v in at_head if v not in on_main]
    if len(new) > 1:
        gaps.append(
            f"HEAD cuts {len(new)} new releases {new}; cut exactly one successor"
        )
    if on_main and new and version_key(new[0]) <= version_key(on_main[-1]):
        gaps.append(f"new release {new[0]} does not follow {on_main[-1]}")
    return {
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "new_releases": new,
        "open_candidate_on_main": open_candidate,
    }


def admission_commit(repo: Path, main: str, version: str) -> str | None:
    """The oldest commit on main whose release README carries the ADMITTED status line."""
    log = git_out(
        repo,
        "log",
        "--format=%H",
        "--reverse",
        main,
        "--",
        f"{RELEASES}/{version}/README.md",
    )
    for commit in log.split():
        if release_status(Tree(repo, commit), version) == "ADMITTED":
            return commit
    return None


def _drift(admitted: dict[str, Any], other: dict[str, Any]) -> list[str]:
    return sorted(k for k, v in admitted.items() if digest(other.get(k)) != digest(v))


def admission(
    repo: Path,
    main_ref: str,
    subject: dict[str, list[str]],
    head_records: dict[str, Any],
) -> dict[str, Any]:
    """Highest admitted release on main that covered the subject, and currentness.

    An admitted status line and an accepted ADR only nominate a release. Admission is
    established by `verify_admission_evidence.release_admission` (history and decision
    binding) and `verify_admission_evidence.decision_scope` (the ADR names what that
    release introduced), then the subject's records must be unchanged since.
    """
    import verify_admission_evidence as evidence  # local: it imports this module

    main = Tree(repo, main_ref)
    main_reg = registration(main, subject)
    tried: list[dict[str, Any]] = []
    for version in reversed(release_versions(main)):
        status = release_status(main, version)
        adr = accepted_adr(main, version)
        entry: dict[str, Any] = {
            "release": version,
            "release_status": status,
            "adr": adr,
        }
        tried.append(entry)
        if status != "ADMITTED" or adr is None:
            continue
        proof = evidence.release_admission(repo, main, version)
        entry["admission_commit"] = proof.get("admission_commit")
        entry["evidence"] = proof
        if proof["status"] != "pass":
            entry["reason"] = "; ".join(proof["gaps"])
            continue
        commit = proof["admission_commit"]
        at_release = Tree(repo, commit)
        reg = registration(at_release, subject)
        if reg["status"] != "pass":
            entry["registered_at_admission"] = False
            entry["reason"] = "subject not registered at the admission commit"
            continue
        coverage = release_coverage(
            at_release, version, subject_files(at_release, subject)
        )
        entry["release_coverage"] = coverage
        if coverage["status"] != "pass":
            entry["reason"] = "the admitted release did not cover the subject"
            continue
        scope = evidence.decision_scope(
            repo, main, version, proof, subject, reg["records"]
        )
        entry["decision_scope"] = scope
        if scope["status"] != "pass":
            entry["reason"] = "; ".join(scope["gaps"])
            continue
        entry["subject_digest"] = digest(reg["records"])
        entry["changed_on_main_since_admission"] = _drift(
            reg["records"], main_reg["records"]
        )
        entry["changed_at_head_since_admission"] = _drift(reg["records"], head_records)
        current = (
            main_reg["status"] == "pass"
            and not entry["changed_on_main_since_admission"]
            and not entry["changed_at_head_since_admission"]
        )
        entry["current"] = current
        return {"status": "pass" if current else "fail", **entry, "tried": tried}
    return {
        "status": "fail",
        "reason": "no admitted release on main covers the subject",
        "tried": tried,
    }


# --------------------------------------------------------------------------- downstream


def _compiler(compiler_src: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(compiler_src / "src"))
    return subprocess.run(
        [sys.executable, "-m", "l9_semantic_compiler", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _mapping(stdout: str, what: str) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(stdout)
    except yaml.YAMLError as exc:
        raise InputError(f"compiler {what} output is not YAML: {exc}") from exc
    if not isinstance(doc, dict):
        raise InputError(f"compiler {what} output is not a mapping")
    return doc


def _artifacts(doc: dict[str, Any], what: str) -> list[dict[str, Any]]:
    arts = doc.get("artifacts")
    if not isinstance(arts, list) or not all(isinstance(a, dict) for a in arts):
        raise InputError(f"compiler {what} output has no artifacts list")
    out = []
    for a in arts:
        unresolved = a.get("unresolved_criteria")
        if unresolved is not None and not isinstance(unresolved, list):
            raise InputError(f"compiler {what} unresolved_criteria is not a list")
        out.append(
            {
                "ref": a.get("ref"),
                "result": a.get("result"),
                "path": a.get("path"),
                "digest": a.get("digest"),
                "content_digest": a.get("content_digest"),
                "receipt_path": a.get("receipt_path"),
                "receipt_digest": a.get("receipt_digest"),
                # Absent is not empty: a PASS must state its empty unresolved list.
                "unresolved": unresolved,
            }
        )
    return out


def _artifact_passes(art: dict[str, Any]) -> bool:
    return art["result"] == "pass" and art["unresolved"] == []


def _request_path(output_root: Path, ref: str, kind: str) -> Path:
    path = (
        output_root
        / "requests"
        / (re.sub(r"[^A-Za-z0-9_.-]", "_", ref) + f".{kind}.yaml")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def compiler_identity(compiler_src: Path, expected: str | None) -> dict[str, Any]:
    """The exact producer revision; a dirty or unidentifiable checkout is not exact."""
    if not (compiler_src / "src" / "l9_semantic_compiler").is_dir():
        raise InputError(
            f"{compiler_src} is not an l9-semantic-compiler-engine checkout"
        )
    top = run_git(compiler_src, "rev-parse", "--show-toplevel")
    if (
        top.returncode != 0
        or Path(top.stdout.strip()).resolve() != compiler_src.resolve()
    ):
        raise InputError(
            f"{compiler_src} is not a git checkout; its revision is unknown"
        )
    revision = git_out(compiler_src, "rev-parse", "HEAD")
    # Untracked files count: an untracked module under src/ would shadow an import.
    dirty = bool(
        git_out(compiler_src, "status", "--porcelain", "--untracked-files=all")
    )
    gaps = []
    if dirty:
        gaps.append(
            "compiler checkout has tracked or untracked changes; it is not an exact revision"
        )
    if expected is not None and resolve_commit(compiler_src, expected) != revision:
        gaps.append(f"compiler HEAD {revision[:12]} is not the required {expected}")
    return {"revision": revision, "dirty": dirty, "gaps": gaps}


def _produce(
    repo: Path,
    compiler_src: Path,
    output_root: Path,
    subject: dict[str, list[str]],
    revision: str,
) -> dict[str, Any]:
    """One producer run: coordinates, project, compose. Returns stdout facts per profile."""
    authority = {"repository": REPOSITORY, "root": str(repo), "revision": revision}
    output_root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"projections": {}, "compositions": {}}
    produced: dict[str, list[dict[str, Any]]] = {}
    failed = False
    for ref in subject["projection_profiles"]:
        coords = _compiler(
            compiler_src,
            ["projection-coordinates", "--authority-root", str(repo), "--revision", revision,
             "--repository", REPOSITORY, "--profile", ref],
        )  # fmt: skip
        if coords.returncode != 0:
            results["projections"][ref] = {
                "result": "coordinates_failed",
                "stderr": coords.stderr[-400:],
            }
            failed = True
            continue
        pins = _mapping(coords.stdout, "projection-coordinates")
        if not isinstance(pins.get("projection_profile"), dict) or not isinstance(
            pins.get("sources"), list
        ):
            raise InputError(
                "projection-coordinates output lacks projection_profile or sources"
            )
        request = {
            "schema": "l9.semantic-projection-request/v1",
            "authority": authority,
            "projection_profile": pins["projection_profile"],
            "sources": pins["sources"],
            "output_root": str(output_root),
        }
        path = _request_path(output_root, ref, "project")
        path.write_text(yaml.safe_dump(request), encoding="utf-8")
        done = _compiler(compiler_src, ["project", str(path)])
        doc = _mapping(done.stdout, "project")
        arts = _artifacts(doc, "project")
        expected = sorted(
            f"{ref}#{s.get('ref')}" for s in pins["sources"] if isinstance(s, dict)
        )
        covered = sorted(a["ref"] for a in arts) == expected
        ok = (
            done.returncode == 0
            and doc.get("result") == "pass"
            and covered
            and all(_artifact_passes(a) for a in arts)
        )
        failed |= not ok
        produced[ref] = arts
        results["projections"][ref] = {
            "exit": done.returncode,
            "result": doc.get("result"),
            "covers_pinned_sources": covered,
            "pins": pins,
            "artifacts": arts,
        }
    compositions = (
        Tree(repo).yaml("semantics/composition_profiles.yaml").get("profiles") or []
    )
    for ref in subject["composition_profiles"]:
        record = next(
            (p for p in compositions if isinstance(p, dict) and p.get("id") == ref),
            None,
        )
        composes = ((record or {}).get("composes") or {}).get("projection_profile")
        components = [a["path"] for a in produced.get(composes or "", []) if a["path"]]
        if record is None or not components:
            results["compositions"][ref] = {
                "result": "not_composable",
                "reason": f"its projection profile {composes} was not projected in this run",
            }
            failed = True
            continue
        request = {
            "schema": "l9.semantic-composition-request/v1",
            "authority": authority,
            "composition_profile": {"ref": ref, "digest": digest(record)},
            "components": sorted(components),
            "output_root": str(output_root),
        }
        path = _request_path(output_root, ref, "compose")
        path.write_text(yaml.safe_dump(request), encoding="utf-8")
        done = _compiler(compiler_src, ["compose", str(path)])
        doc = _mapping(done.stdout, "compose")
        arts = _artifacts(doc, "compose")
        ok = (
            done.returncode == 0
            and doc.get("result") == "pass"
            and len(arts) == 1
            and _artifact_passes(arts[0])
        )
        failed |= not ok
        results["compositions"][ref] = {
            "exit": done.returncode,
            "result": doc.get("result"),
            "composes": composes,
            "artifacts": arts,
        }
    results["status"] = "fail" if failed else "pass"
    return results


def downstream(
    repo: Path,
    compiler_src: Path,
    output_root: Path,
    subject: dict[str, list[str]],
    compiler_revision: str | None = None,
) -> dict[str, Any]:
    """Run the real compiler twice at the checkout's HEAD and verify what it emitted.

    PASS needs: an exact clean compiler revision; every artifact `result: pass` with an
    explicitly empty `unresolved_criteria`; exact coverage of the profile's registered
    sources; every artifact and receipt verified from its bytes; both runs byte-identical;
    and every negative control rejected by the verifier.
    """
    import verify_admission_evidence as evidence  # local: it imports this module

    if not subject["projection_profiles"] and not subject["composition_profiles"]:
        return {
            "status": "not_applicable",
            "reason": "the subject names no profile to compile",
        }
    compiler = compiler_identity(compiler_src, compiler_revision)
    if git_out(repo, "status", "--porcelain", "--untracked-files=no"):
        return {
            "status": "fail",
            "reason": "checkout has tracked changes; compile a clean revision",
            "compiler": compiler,
        }
    revision = git_out(repo, "rev-parse", "HEAD")
    for run in ("run-1", "run-2"):
        if (output_root / run).exists():
            shutil.rmtree(output_root / run)
    first = _produce(repo, compiler_src, output_root / "run-1", subject, revision)
    second = _produce(repo, compiler_src, output_root / "run-2", subject, revision)
    verification = evidence.verify_outputs(
        Tree(repo), revision, compiler_src, subject, first
    )
    replay = evidence.compare_runs(output_root / "run-1", output_root / "run-2")
    failed = (
        bool(compiler["gaps"])
        or first["status"] != "pass"
        or second["status"] != "pass"
        or verification["status"] != "pass"
        or replay["status"] != "pass"
    )
    return {
        "status": "fail" if failed else "pass",
        "revision": revision,
        "compiler": compiler,
        "projections": first["projections"],
        "compositions": first["compositions"],
        "second_run_status": second["status"],
        "verification": verification,
        "deterministic_replay": replay,
    }


# --------------------------------------------------------------------------- qualification


def run_validator(repo: Path) -> dict[str, Any]:
    script = repo / "scripts" / "validate-semantics.py"
    if not script.is_file():
        raise InputError("scripts/validate-semantics.py is missing from the checkout")
    done = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    fails = [ln for ln in done.stdout.splitlines() if ln.startswith("FAIL")]
    return {
        "status": "pass" if done.returncode == 0 else "fail",
        "exit": done.returncode,
        "fail_lines": fails[:20],
    }


def run_make_gates(repo: Path) -> dict[str, Any]:
    """The repository's own qualification: `make validate`, `make check`, `make test`."""
    if shutil.which("make") is None:
        raise InputError("make is not installed; the repository gates cannot run")
    if not (repo / "Makefile").is_file():
        raise InputError("the checkout has no Makefile; its gates cannot run")
    results: dict[str, Any] = {}
    for target in MAKE_GATES:
        done = subprocess.run(
            ["make", "--no-print-directory", target],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        results[target] = {
            "exit": done.returncode,
            "tail": (done.stdout + done.stderr).strip().splitlines()[-5:],
        }
    status = "pass" if all(r["exit"] == 0 for r in results.values()) else "fail"
    return {"status": status, **results}


def version_integrity(
    head: Tree, base: Tree | None, subject: dict[str, list[str]]
) -> list[str]:
    """An admitted profile version is immutable (PROJECTION-013): a change needs `@N+1`."""
    if base is None:
        return []
    gaps: list[str] = []
    for kind, ledger, key in (
        ("projection_profiles", "projection_profiles.yaml", "projection_profiles"),
        ("composition_profiles", "composition_profiles.yaml", "profiles"),
    ):
        admitted = {
            p.get("id"): p
            for p in base.yaml_or_empty(f"semantics/{ledger}").get(key) or []
            if isinstance(p, dict)
        }
        current = {
            p.get("id"): p
            for p in head.yaml_or_empty(f"semantics/{ledger}").get(key) or []
            if isinstance(p, dict)
        }
        for ref in subject[kind]:
            if (
                ref in admitted
                and ref in current
                and digest(admitted[ref]) != digest(current[ref])
            ):
                gaps.append(
                    f"{kind} {ref}: admitted at {base.label()} and edited in place; "
                    "an existing version is immutable (PROJECTION-013), register @N+1"
                )
    return gaps


def evaluate(
    repo: Path,
    subject: dict[str, list[str]],
    main_ref: str,
    compiler_src: Path | None = None,
    output_root: Path | None = None,
    compiler_revision: str | None = None,
    admitted_base_version: str | None = None,
) -> dict[str, Any]:
    import discover_admission_subject as discover  # local: it imports this module

    head = Tree(repo)
    main_tree = Tree(repo, main_ref)
    main_revision = main_tree.ref
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "repository": REPOSITORY,
        "head": git_out(repo, "rev-parse", "HEAD"),
        "main_ref": main_ref,
        "main_revision": main_revision,
        "subject": subject,
    }
    base = (
        discover.named_admitted_base(repo, main_tree, admitted_base_version)
        if admitted_base_version is not None
        else discover.admitted_base(repo, main_tree)
    )
    report["admitted_base"] = {k: v for k, v in base.items() if k != "tree"}
    reg = registration(head, subject)
    reg["gaps"] += version_integrity(head, base.get("tree"), subject)
    reg["status"] = "pass" if not reg["gaps"] else "fail"
    report["registration"] = {
        "status": reg["status"],
        "gaps": reg["gaps"],
        "unresolvable_declarations": reg["unresolvable_declarations"],
    }
    verdict = "INCOMPLETE"
    if reg["status"] == "pass":
        verdict = "REGISTERED"
        report["validator"] = run_validator(repo)
        report["make"] = run_make_gates(repo)
        versions = release_versions(head)
        if not versions:
            raise InputError(f"no release directory under {RELEASES}")
        highest = versions[-1]
        coverage = release_coverage(head, highest, subject_files(head, subject))
        inventory = release_inventory(head, highest)
        sequence = release_sequence(head, main_tree)
        report["release"] = {
            "version": highest,
            "release_status": release_status(head, highest),
            "status": "pass"
            if all(x["status"] == "pass" for x in (coverage, inventory, sequence))
            else "fail",
            "gaps": coverage["gaps"] + inventory["gaps"] + sequence["gaps"],
            "inventory": {k: v for k, v in inventory.items() if k != "gaps"},
            "sequence": {k: v for k, v in sequence.items() if k != "gaps"},
        }
        qualified = (
            report["validator"]["status"] == "pass"
            and report["make"]["status"] == "pass"
            and report["release"]["status"] == "pass"
        )
        report["admission"] = admission(repo, main_ref, subject, reg["records"])
        if qualified and report["admission"]["status"] == "pass":
            verdict = "ADMITTED"
        elif qualified:
            # Not admitted: the subject must be the complete, closed change since the
            # admitted base before an owner can be asked to decide it.
            report["scope"] = discover.scope_check(
                discover.discover(repo, base.get("tree"), head), subject
            )
            if report["scope"]["status"] == "pass":
                verdict = "RELEASED_CANDIDATE"
    if compiler_src is not None:
        if output_root is None:
            raise InputError("--compiler-src needs --output-root")
        report["downstream"] = downstream(
            repo, compiler_src, output_root, subject, compiler_revision
        )
        report["downstream"]["head_is_main"] = report["head"] == main_revision
        if (
            verdict == "ADMITTED"
            and report["downstream"]["status"] == "pass"
            and report["downstream"]["head_is_main"]
        ):
            verdict = "DOWNSTREAM_USABLE"
    report["verdict"] = verdict
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--require", choices=sorted(REQUIRE), default="admitted")
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--compiler-src", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--compiler-revision")
    parser.add_argument(
        "--admitted-base",
        metavar="VERSION",
        help="measure scope from this ADMITTED release; its evidence gaps are reported",
    )
    args = parser.parse_args(argv)
    try:
        if args.require == "downstream" and args.compiler_src is None:
            raise InputError("--require downstream needs --compiler-src")
        repo = args.checkout.resolve()
        top = run_git(repo, "rev-parse", "--show-toplevel")
        if top.returncode != 0 or top.stdout.strip() != str(repo):
            raise InputError(f"{repo} is not the top of a git checkout")
        report = evaluate(
            repo,
            load_subject(args.subject),
            args.main_ref,
            args.compiler_src.resolve() if args.compiler_src else None,
            args.output_root.resolve() if args.output_root else None,
            args.compiler_revision,
            args.admitted_base,
        )
    except InputError as exc:
        print(
            json.dumps(
                {"schema": REPORT_SCHEMA, "verdict": "UNRESOLVED", "reason": str(exc)}
            )
        )
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    reached = LADDER.index(report["verdict"]) >= LADDER.index(REQUIRE[args.require])
    return 0 if reached else 1


if __name__ == "__main__":
    sys.exit(main())
