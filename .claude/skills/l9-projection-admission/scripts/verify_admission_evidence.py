"""Admission evidence and producer evidence for Quantum-L9/.github semantics.

Two independent verifications, both read-only and fail-closed:

1. Admission evidence (`release_admission`, `decision_scope`). An admitted status line and an
   ADR that says `Accepted` only nominate a release. Admission is established when, at the
   commit that first flipped the release to ADMITTED:
     - the release record is unedited since, and its full SC-008 inventory verifies there;
     - an ADR accepting exactly that version already existed, is listed in the ADR index,
       is hashed by the release at its bytes, and is unedited since on main;
     - the ADR's subject table binds the approved `semantics/` tree, and that tree is the
       admission commit's `semantics/` tree; it names the release and the target class
       (canonical global semantics); it carries a decision reference;
     - every identity that release introduced (absent or different at the prior admitted
       release) and that the subject contains is named in the ADR.
   Parsing a record cannot prove that its author held authority. The evidence binds the
   decision record to the exact subject; the decision itself stays the owner's.

2. Producer evidence (`verify_outputs`, `compare_runs`). The compiler's own `result: pass`
   is not taken on trust: every emitted projection, composition and receipt is re-read from
   its bytes and checked for digests, provenance, exact source coverage, exact id-record
   selection, payload schema (the compiler's native interpreter plus strict Boolean typing)
   and receipt binding; negative controls prove the checks reject corrupted artifacts; two
   runs must be byte-identical.

Usage (admission evidence for one subject):
  python3 verify_admission_evidence.py --checkout REPO --subject SUBJECT.json
      --release vX.Y.Z [--main-ref origin/main]

Exit codes: 0 established, 1 not established, 2 UNRESOLVED.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import check_admission_closure as cac

EVIDENCE_SCHEMA = "l9.projection-admission-evidence/v1"
TARGET_AUTHORITY_CLASS = "canonical global semantics"
PROJECTION_ENVELOPE = "l9.projection-artifact/v1"
COMPOSITION_ENVELOPE = "l9.composed-projection/v1"
PASSING_CRITERIA = {"pass", "not_applicable"}
# A decision reference names where the decision was given: a governed session, or a pull
# request or issue. An arbitrary URL is not one.
DECISION_REF = re.compile(
    r"(session_[A-Za-z0-9]{8,}|Quantum-L9/[\w.-]+#\d+"
    r"|https://github\.com/[\w.-]+/[\w.-]+/(?:pull|issues)/\d+)"
)
SHA40 = re.compile(r"\b[0-9a-f]{40}\b")


# --------------------------------------------------------------------------- ADR reading


def _cell(text: str, label: str) -> str | None:
    """The value cell of a two-column Markdown table row whose label matches."""
    pattern = re.compile(rf"^\|\s*{label}\s*\|(?P<value>.*)\|\s*$", re.IGNORECASE)
    for line in text.splitlines():
        match = pattern.match(line)
        if match:
            return match["value"]
    return None


def _status_paragraph(text: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("**Status:**"):
            block = []
            for follow in lines[index:]:
                if not follow.strip() or follow.startswith("#"):
                    break
                block.append(follow)
            return " ".join(block)
    return ""


def _names(text: str, name: str) -> bool:
    """`name` occurs as a whole identifier: not inside a longer id, path or file name."""
    inner = r"A-Za-z0-9_@/"
    pattern = rf"(?<![{inner}.-]){re.escape(name)}(?![{inner}-])(?!\.[A-Za-z0-9])"
    return re.search(pattern, text) is not None


def _admitted_block(text: str) -> str:
    """The ADR's "Admitted definitions" block, up to the next heading.

    Naming an identity anywhere else (evidence, limitations, exclusions) is not admitting it.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^(#+\s*)?Admitted definitions\b", line.strip(), re.IGNORECASE):
            block = []
            for follow in lines[index + 1 :]:
                if follow.startswith("#"):
                    break
                block.append(follow)
            return "\n".join(block)
    return ""


def _later_commits(repo: Path, commit: str, main: str, path: str) -> list[str]:
    """Mainline commits after `commit` that touch `path` (see `cac.admission_commit`)."""
    return cac.git_out(
        repo, "log", "--first-parent", "--format=%H", f"{commit}..{main}", "--", path
    ).split()


# --------------------------------------------------------------------------- admission


def release_admission(repo: Path, main: cac.Tree, version: str) -> dict[str, Any]:
    """Subject-independent admission evidence for one release on main."""
    gaps: list[str] = []
    proof: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "admission_release": version,
        "target_authority_class": None,
        "authorized_decision_ref": [],
        "admission_commit": None,
        "admitted_semantics_tree": None,
        "candidate_revision": [],
        "adr": None,
    }

    def done() -> dict[str, Any]:
        proof["status"] = "pass" if not gaps else "fail"
        proof["gaps"] = gaps
        return proof

    commit = cac.admission_commit(repo, main.ref, version)
    if commit is None:
        gaps.append(f"{version}: no commit on main flips this release to ADMITTED")
        return done()
    proof["admission_commit"] = commit
    later = _later_commits(repo, commit, main.ref, f"{cac.RELEASES}/{version}")
    if later:
        gaps.append(f"{version}: release record edited after admission: {later}")
    at = cac.Tree(repo, commit)
    inventory = cac.release_inventory(at, version)
    if inventory["status"] != "pass":
        gaps += [f"at admission commit: {g}" for g in inventory["gaps"][:10]]
    adr = cac.accepted_adr(at, version)
    if adr is None:
        gaps.append(
            f"{version}: no ADR accepting exactly this version existed at the admission "
            f"commit {commit[:12]}"
        )
        return done()
    proof["adr"] = adr
    adr_path = f"docs/adr/{adr}"
    raw = at.read(adr_path)
    if raw is None:
        raise cac.InputError(f"{adr_path} listed at {commit[:12]} but unreadable")
    text = raw.decode("utf-8", "replace")
    if main.read(adr_path) != raw or _later_commits(repo, commit, main.ref, adr_path):
        gaps.append(f"{adr}: edited or removed on main after the admission commit")
    hashes_raw = at.read(f"{cac.RELEASES}/{version}/HASHES.sha256") or b""
    hashes, _ = cac._hash_lines(hashes_raw, version)
    if hashes.get(f"./{adr_path}") != cac.sha_bytes(raw):
        gaps.append(f"{adr}: not hashed by {version} at its admission bytes")
    number = re.match(r"(ADR-\d+)", adr)
    index = (at.read("docs/adr/README.md") or b"").decode("utf-8", "replace")
    if number is None or not re.search(rf"^- {number.group(1)}:", index, re.MULTILINE):
        gaps.append(f"{adr}: not listed in docs/adr/README.md at the admission commit")
    tree_cell = _cell(text, r"Approved semantic tree")
    actual_tree = cac.git_out(repo, "rev-parse", f"{commit}:semantics")
    if tree_cell is None or not SHA40.search(tree_cell):
        gaps.append(f"{adr}: the subject table binds no approved semantics/ tree")
    else:
        hashes_named = SHA40.findall(tree_cell)
        approved = hashes_named[0]
        proof["admitted_semantics_tree"] = approved
        if approved != actual_tree:
            gaps.append(
                f"{adr}: approved semantics/ tree {approved[:12]} is not the admission "
                f"commit's tree {actual_tree[:12]}"
            )
        for named in hashes_named[1:]:
            if (
                cac.run_git(repo, "cat-file", "-e", f"{named}^{{commit}}").returncode
                != 0
            ):
                proof["candidate_revision"].append({"commit": named, "resolved": False})
                continue
            carries = cac.git_out(repo, "rev-parse", f"{named}:semantics") == approved
            proof["candidate_revision"].append(
                {"commit": named, "resolved": True, "carries_approved_tree": carries}
            )
            if not carries:
                gaps.append(
                    f"{adr}: names candidate {named[:12]}, which does not carry the "
                    "approved semantics/ tree"
                )
    release_cell = _cell(text, r"Release")
    if release_cell is None or not _names(release_cell, version):
        gaps.append(f"{adr}: the subject table does not name release {version}")
    target_cell = _cell(text, r"Target class(?: and authority)?")
    target = re.sub(r"[*_`]", "", target_cell or "").strip().lower()
    if not target.startswith(TARGET_AUTHORITY_CLASS):
        gaps.append(
            f"{adr}: the subject table does not name the target authority class"
        )
    else:
        proof["target_authority_class"] = "canonical_global_semantics"
    refs = sorted(
        set(DECISION_REF.findall(_status_paragraph(text) + "\n" + (target_cell or "")))
    )
    proof["authorized_decision_ref"] = refs
    if not refs:
        gaps.append(f"{adr}: the decision record carries no decision reference")
    return done()


def _predecessor_state(
    repo: Path, main: cac.Tree, version: str, commit: str
) -> tuple[str | None, str | None]:
    """The state this release's delta is measured from, and the release that recorded it.

    It is the admission commit of the highest *admitted* release below `version`, so an
    unadmitted candidate in between can never stand in for admitted law. Only when no lower
    release was admitted (the first admission under this record shape, v3.28.0 here) is it
    the last commit, up to `commit`, that recorded the release directly below.
    """
    older = [
        v
        for v in cac.release_versions(main)
        if cac.version_key(v) < cac.version_key(version)
    ]
    for prior in reversed(older):
        if cac.release_status(main, prior) == "ADMITTED":
            return prior, cac.admission_commit(repo, main.ref, prior)
    if not older:
        return None, None
    prior = older[-1]
    last = cac.git_out(
        repo, "log", "-1", "--format=%H", commit, "--", f"{cac.RELEASES}/{prior}"
    )
    return prior, last or None


def _introduced(
    prior_tree: cac.Tree | None,
    subject: dict[str, list[str]],
    records: dict[str, Any],
) -> list[str]:
    """Subject record keys this release introduced: absent or different before it.

    Dependency records (`dep:`) are not identities of the subject; a changed dependency is
    a subject of its own and is caught by closure before admission.
    """
    prior_records: dict[str, Any] = {}
    if prior_tree is not None:
        prior_records = cac.registration(prior_tree, subject)["records"]
    return sorted(
        key
        for key, value in records.items()
        if not key.startswith("dep:")
        and cac.digest(prior_records.get(key)) != cac.digest(value)
    )


def _profiles(tree: cac.Tree | None) -> dict[str, Any]:
    if tree is None:
        return {}
    reg = cac.Registration(tree, {k: [] for k in (*cac.ITEM_KINDS, "revisions")})
    return {p.get("id"): p for p in reg.projections + reg.compositions}


def _covering_names(
    key: str, at: cac.Tree, prior_tree: cac.Tree | None, subject: dict[str, list[str]]
) -> set[str]:
    """Names whose presence in the admitted-definitions block covers one identity.

    Profiles admitted together as a pair cover each other: a composition is covered by the
    projection profile it composes only when that projection profile is new or changed in
    the same release, never by a mention of an already-admitted one. A payload schema is
    covered by its artifact id, its output schema id, or a name covering its profile. A
    ledger content change is covered by its source id or file.
    """
    kind, _, ident = key.partition(":")
    names = {ident}
    reg = cac.Registration(at, subject)
    now = _profiles(at)
    before = _profiles(prior_tree)

    def introduced(ref: str) -> bool:
        return ref in now and cac.digest(before.get(ref)) != cac.digest(now[ref])

    def profile_names(ref: str) -> set[str]:
        found = {ref}
        composes = ((now.get(ref) or {}).get("composes") or {}).get(
            "projection_profile"
        )
        if isinstance(composes, str) and introduced(composes):
            found.add(composes)
        return found

    if kind == "composition profile":
        names |= profile_names(ident)
    elif kind == "schema":
        doc = reg.schemas["docs"].get(ident) or {}
        const = cac.schema_identity(doc)
        names |= {doc.get("artifact_id"), const} - {None}
        for ref, profile in now.items():
            if (
                const is not None
                and (profile.get("output") or {}).get("schema") == const
            ):
                names |= profile_names(ref) if introduced(ref) else {ref}
    elif kind == "source_file":
        path = (reg.sources.get(ident) or {}).get("path")
        names |= {path, Path(path).name} if isinstance(path, str) else set()
    elif kind == "source_class_file":
        artifact = (reg.classes.get(ident) or {}).get("canonical_artifact")
        names |= (
            {artifact, f"semantics/{artifact}"} if isinstance(artifact, str) else set()
        )
    return {n for n in names if isinstance(n, str)}


def decision_scope(
    repo: Path,
    main: cac.Tree,
    version: str,
    proof: dict[str, Any],
    subject: dict[str, list[str]],
    records: dict[str, Any],
) -> dict[str, Any]:
    """The ADR's admitted definitions name every subject identity the release introduced."""
    commit = proof["admission_commit"]
    at = cac.Tree(repo, commit)
    text = (at.read(f"docs/adr/{proof['adr']}") or b"").decode("utf-8", "replace")
    block = _admitted_block(text)
    prior, prior_commit = _predecessor_state(repo, main, version, commit)
    prior_tree = cac.Tree(repo, prior_commit) if prior_commit else None
    introduced = _introduced(prior_tree, subject, records)
    gaps = [
        f"{proof['adr']}: its admitted definitions do not name {key}, which {version} "
        "introduced; the decision does not cover it"
        for key in introduced
        if not any(
            _names(block, n) for n in _covering_names(key, at, prior_tree, subject)
        )
    ]
    return {
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "introduced": introduced,
        "predecessor_release": prior,
        "decision_scope": sorted({k.partition(":")[2] for k in introduced}),
        "subject_digest": cac.digest(records),
    }


# --------------------------------------------------------------------------- producer


_NATIVE = (
    "import json, sys\n"
    "from l9_semantic_compiler.passes.validate import schema_violations\n"
    "batch = json.load(sys.stdin)\n"
    "print(json.dumps([schema_violations(i['value'], i['schema']) for i in batch]))\n"
)


_NATIVE_STRICT = (
    "import json, sys\n"
    "from l9_semantic_compiler.engine.errors import SemanticCompilerError\n"
    "from l9_semantic_compiler.passes.schema_candidate_v2 import validate_descriptor_payload\n"
    "out = []\n"
    "for i in json.load(sys.stdin):\n"
    "    try:\n"
    "        validate_descriptor_payload(i['descriptor'], i['value'])\n"
    "        out.append([])\n"
    "    except SemanticCompilerError as exc:\n"
    "        out.append([f'{exc.code}: {exc} {exc.diagnostics}'])\n"
    "print(json.dumps(out))\n"
)


def native_strict_violations(
    compiler_src: Path, batch: list[tuple[Any, Any]]
) -> list[list[str]]:
    """The compiler's strict single-descriptor interpreter over (value, descriptor) pairs.

    A compiler that predates the source-class dispatch protocol has no such interpreter:
    the import fails and the run is unresolved, never a pass.
    """
    if not batch:
        return []
    done = subprocess.run(
        [sys.executable, "-c", _NATIVE_STRICT],
        input=json.dumps([{"value": v, "descriptor": d} for v, d in batch]),
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=str(compiler_src / "src")),
        check=False,
    )
    try:
        result = json.loads(done.stdout)
    except ValueError:
        result = None
    if (
        done.returncode != 0
        or not isinstance(result, list)
        or len(result) != len(batch)
    ):
        raise cac.InputError(
            "the compiler's strict descriptor interpreter could not run: "
            + done.stderr.strip()[-300:]
        )
    return result


def source_class_schema_gaps(
    ref: str,
    payload: Any,
    schema: dict[str, Any],
    compiler_src: Path,
    *,
    source: tuple[Any, Any] | None,
) -> list[str]:
    """Dispatch by the verified source class (projection) or exact namespaces (composition).

    `source` is the (source class, source ref) the authority binds a projection's source
    to. For a composition it is None and every namespace is checked by its own shape.
    No field of the payload chooses the descriptor.
    """
    shapes = {
        s.get("source_class"): s
        for s in schema.get("source_shapes") or []
        if isinstance(s, dict)
    }
    if source is not None:
        cls, source_ref = source
        shape = shapes.get(cls)
        if shape is None or shape.get("source_ref") != source_ref:
            return [
                (
                    f"{ref}: source {source_ref} ({cls}) is not a source shape of its "
                    "registered output schema"
                )
            ]
        pairs = [(cls, payload, shape.get("descriptor"))]
    else:
        if not isinstance(payload, dict) or set(payload) != set(shapes):
            observed = sorted(payload) if isinstance(payload, dict) else None
            return [
                (
                    f"{ref}: payload namespaces {observed} are not exactly the "
                    f"schema's source classes {sorted(map(str, shapes))}"
                )
            ]
        pairs = [(cls, payload[cls], shapes[cls].get("descriptor")) for cls in shapes]
    results = native_strict_violations(compiler_src, [(v, d) for _, v, d in pairs])
    return [
        f"{ref}: payload schema (native strict, {cls}): {violation}"
        for (cls, _, _), found in zip(pairs, results)
        for violation in found
    ]


def native_schema_violations(
    compiler_src: Path, batch: list[tuple[Any, Any]]
) -> list[list[str]]:
    """The compiler's own schema interpreter over (value, descriptor) pairs."""
    if not batch:
        return []
    done = subprocess.run(
        [sys.executable, "-c", _NATIVE],
        input=json.dumps([{"value": v, "schema": s} for v, s in batch]),
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONPATH=str(compiler_src / "src")),
        check=False,
    )
    try:
        result = json.loads(done.stdout)
    except ValueError:
        result = None
    if (
        done.returncode != 0
        or not isinstance(result, list)
        or len(result) != len(batch)
    ):
        raise cac.InputError(
            "the compiler's native schema interpreter could not run: "
            + done.stderr.strip()[-300:]
        )
    return result


def strict_const_violations(value: Any, descriptor: Any, path: str = "$") -> list[str]:
    """Typed const/enum equality the native interpreter does not enforce.

    Python's `==` makes `1 == True` and `0 == False`, so a payload carrying 1 where a
    normative Boolean constant is declared passes `schema_violations`. Booleans and numbers
    are distinct here.
    """
    if not isinstance(descriptor, dict):
        return []

    def same(a: Any, b: Any) -> bool:
        return isinstance(a, bool) == isinstance(b, bool) and a == b

    found: list[str] = []
    if "const" in descriptor and not same(value, descriptor["const"]):
        found.append(f"{path}: not the typed const {descriptor['const']!r}")
    enum = descriptor.get("enum")
    if isinstance(enum, list) and not any(same(value, e) for e in enum):
        found.append(f"{path}: not a typed member of the declared enum")
    fields = descriptor.get("fields")
    if fields is None:
        fields = descriptor.get("properties")
    if isinstance(value, dict) and isinstance(fields, dict):
        for key, child in fields.items():
            if key in value and value[key] is not None:
                found += strict_const_violations(value[key], child, f"{path}.{key}")
    items = descriptor.get("items")
    if isinstance(value, list) and isinstance(items, dict):
        for index, item in enumerate(value):
            found += strict_const_violations(item, items, f"{path}[{index}]")
    return found


def _read_json(
    path: Any, what: str, gaps: list[str]
) -> tuple[dict[str, Any] | None, bytes]:
    if not isinstance(path, str) or not Path(path).is_file():
        gaps.append(f"{what}: emitted file {path} does not exist")
        return None, b""
    raw = Path(path).read_bytes()
    try:
        doc = json.loads(raw)
    except ValueError:
        gaps.append(f"{what}: {path} is not JSON")
        return None, raw
    if not isinstance(doc, dict):
        gaps.append(f"{what}: {path} is not a JSON object")
        return None, raw
    return doc, raw


def _self_digest(doc: dict[str, Any], field: str) -> str:
    return cac.digest({k: v for k, v in doc.items() if k != field})


def check_receipt(
    receipt: dict[str, Any] | None,
    what: str,
    *,
    output: dict[str, Any],
    profile: dict[str, Any],
    inputs: list[dict[str, Any]],
    stated_digest: Any = None,
) -> list[str]:
    """A receipt that binds exactly this output, profile and inputs, complete and passing."""
    if receipt is None:
        return [f"{what}: no readable receipt"]
    gaps = []
    if receipt.get("receipt_digest") != _self_digest(receipt, "receipt_digest"):
        gaps.append(f"{what}: receipt_digest does not match the receipt's bytes")
    if stated_digest is not None and receipt.get("receipt_digest") != stated_digest:
        gaps.append(
            f"{what}: receipt digest differs from the one the compiler reported"
        )
    if receipt.get("result") != "pass":
        gaps.append(f"{what}: receipt result is {receipt.get('result')}")
    basis = receipt.get("verification_basis") or {}
    if basis.get("coverage") != "complete":
        gaps.append(
            f"{what}: receipt coverage is {basis.get('coverage')}, not complete"
        )
    if basis.get("unresolved_criteria") != []:
        gaps.append(
            f"{what}: receipt unresolved_criteria is {basis.get('unresolved_criteria')}"
        )
    criteria = basis.get("criteria")
    if not isinstance(criteria, dict) or not criteria:
        gaps.append(f"{what}: receipt states no criteria")
    else:
        bad = sorted(
            k
            for k, v in criteria.items()
            if not isinstance(v, dict) or v.get("status") not in PASSING_CRITERIA
        )
        if bad:
            gaps.append(f"{what}: receipt criteria not passing: {bad}")
    if receipt.get("output") != output:
        gaps.append(f"{what}: receipt output {receipt.get('output')} is not {output}")
    if receipt.get("profile") != profile:
        gaps.append(f"{what}: receipt profile is not {profile}")
    stated = sorted(json.dumps(i, sort_keys=True) for i in receipt.get("inputs") or [])
    if stated != sorted(json.dumps(i, sort_keys=True) for i in inputs):
        gaps.append(f"{what}: receipt inputs are not exactly {inputs}")
    return gaps


class ProjectionContext:
    """Everything a projection artifact must agree with, read from the authority tree."""

    def __init__(self, tree: cac.Tree, revision: str, profile: dict[str, Any]) -> None:
        self.revision = revision
        self.profile = profile
        self.profile_digest = cac.digest(profile)
        sources, _ = cac.source_registry(tree)
        classes = cac._class_artifacts(tree)
        self.by_source: dict[str, dict[str, Any]] = {}
        for cls, spec in (profile.get("sources") or {}).items():
            rel = classes.get(cls)
            owners = [e for e in sources.values() if e.get("path") == rel]
            data = tree.read(rel) if rel else None
            if len(owners) != 1 or data is None:
                raise cac.InputError(
                    f"source class {cls} does not resolve at {tree.label()}"
                )
            self.by_source[owners[0]["id"]] = {
                "class": cls,
                "path": rel,
                "digest": "sha256:" + cac.sha_bytes(data),
                "document": cac.parse_yaml_mapping(data, rel),
                "selectors": list((spec or {}).get("selectors") or []),
            }
        schema_id = (profile.get("output") or {}).get("schema")
        names = cac.schema_registry(tree)["consts"].get(schema_id) or []
        self.schema = (
            cac.schema_registry(tree)["docs"][names[0]] if len(names) == 1 else None
        )


def check_projection(
    doc: dict[str, Any] | None, ctx: ProjectionContext, ref: str, compiler_src: Path
) -> list[str]:
    """One projection artifact, from its own content, against the authority tree."""
    if doc is None:
        return [f"{ref}: no readable artifact"]
    gaps = []
    profile_ref = ctx.profile.get("id")
    if doc.get("schema") != PROJECTION_ENVELOPE:
        gaps.append(f"{ref}: envelope schema is {doc.get('schema')}")
    if doc.get("projection_digest") != _self_digest(doc, "projection_digest"):
        gaps.append(f"{ref}: projection_digest does not match the artifact's content")
    if doc.get("projection_profile_ref") != profile_ref:
        gaps.append(f"{ref}: projection_profile_ref is not {profile_ref}")
    if doc.get("projection_profile_digest") != ctx.profile_digest:
        gaps.append(f"{ref}: profile digest is not the digest of {profile_ref} at HEAD")
    source = ctx.by_source.get(doc.get("source_ref"))
    if source is None or ref != f"{profile_ref}#{doc.get('source_ref')}":
        gaps.append(
            f"{ref}: source {doc.get('source_ref')} is not one this profile selects"
        )
        return gaps
    if doc.get("source_digest") != source["digest"]:
        gaps.append(
            f"{ref}: source_digest is not the digest of {source['path']} at HEAD"
        )
    payload = doc.get("payload")
    if not isinstance(payload, dict):
        return [*gaps, f"{ref}: payload is not a mapping"]
    try:
        expected = cac.select_payload(source["document"], source["selectors"])
    except cac.SelectorError as exc:
        return [*gaps, f"{ref}: the declared selection does not resolve: {exc}"]
    if payload != expected:
        missing = sorted(k for k in expected if k not in payload)
        extra = sorted(k for k in payload if k not in expected)
        differing = sorted(
            k for k in expected if k in payload and payload[k] != expected[k]
        )
        gaps.append(
            f"{ref}: payload is not exactly the declared selection of {source['path']} "
            f"(missing {missing}, extra {extra}, differing {differing})"
        )
    gaps += _schema_gaps(
        ref,
        payload,
        ctx.schema,
        compiler_src,
        source=(source["class"], doc.get("source_ref")),
    )
    return gaps


def _schema_gaps(
    ref: str,
    payload: Any,
    schema: Any,
    compiler_src: Path,
    *,
    source: tuple[Any, Any] | None = None,
) -> list[str]:
    if schema is None:
        return [
            f"{ref}: the profile's output schema does not resolve to one registered schema"
        ]
    if isinstance(schema, dict) and schema.get("schema") == cac.SOURCE_CLASS_SCHEMA:
        return source_class_schema_gaps(
            ref, payload, schema, compiler_src, source=source
        )
    gaps = [
        f"{ref}: payload schema: {v}" for v in strict_const_violations(payload, schema)
    ]
    gaps += [
        f"{ref}: payload schema (native): {v}"
        for v in native_schema_violations(compiler_src, [(payload, schema)])[0]
    ]
    return gaps


def check_composition(
    doc: dict[str, Any] | None,
    record: dict[str, Any],
    ref: str,
    projections: dict[str, dict[str, Any]],
    schema: Any,
    compiler_src: Path,
    classes: dict[str, str],
) -> list[str]:
    """One composed artifact against its verified components and its profile.

    `classes` maps each verified projection ref to the source class its source is bound to
    in the registry, so a component cannot relabel its own namespace.
    """
    if doc is None:
        return [f"{ref}: no readable artifact"]
    gaps = []
    if doc.get("schema") != COMPOSITION_ENVELOPE:
        gaps.append(f"{ref}: envelope schema is {doc.get('schema')}")
    if doc.get("composition_digest") != _self_digest(doc, "composition_digest"):
        gaps.append(f"{ref}: composition_digest does not match the artifact's content")
    profile = {"ref": record.get("id"), "digest": cac.digest(record)}
    if doc.get("composition_profile") != profile:
        gaps.append(
            f"{ref}: composition_profile is not {profile['ref']} at its HEAD digest"
        )
    components = doc.get("components")
    if not isinstance(components, list) or not all(
        isinstance(c, dict) for c in components
    ):
        return [*gaps, f"{ref}: components is not a list of mappings"]
    proj_refs = [c.get("projection_ref") for c in components]
    if len(set(proj_refs)) != len(proj_refs):
        gaps.append(f"{ref}: a component appears more than once")
    if set(proj_refs) != set(projections):
        gaps.append(
            f"{ref}: components {sorted(map(str, proj_refs))} are not exactly the verified "
            f"projections {sorted(projections)}"
        )
    for component in components:
        source = projections.get(component.get("projection_ref"))
        if source is None:
            continue
        for field, value in (
            ("projection_digest", source.get("projection_digest")),
            ("source_ref", source.get("source_ref")),
            ("source_digest", source.get("source_digest")),
        ):
            if field in component and component[field] != value:
                gaps.append(
                    f"{ref}: component {component['projection_ref']} {field} differs"
                )
        if component.get("projection_digest") != source.get("projection_digest"):
            gaps.append(
                f"{ref}: component {component['projection_ref']} digest differs"
            )
    if record.get("merge_strategy") != cac.NAMESPACED_MERGE:
        # A deep-merge payload cannot be recomputed independently here: fail closed.
        return [
            *gaps,
            (
                f"{ref}: only a source-class-namespaced composition can be verified "
                "independently"
            ),
        ]
    labels = [c.get("source_class") for c in components]
    if len(set(labels)) != len(labels):
        gaps.append(f"{ref}: a source class namespace is filled twice")
    expected_payload = {}
    for component in components:
        proj = component.get("projection_ref")
        true_class = classes.get(proj)
        if proj in projections and component.get("source_class") != true_class:
            gaps.append(
                f"{ref}: component {proj} claims source class "
                f"{component.get('source_class')}, but its source is bound to {true_class}"
            )
        if proj in projections and true_class is not None:
            expected_payload[true_class] = projections[proj].get("payload")
    if doc.get("payload") != expected_payload:
        gaps.append(
            f"{ref}: payload is not exactly each verified component's payload under its "
            "registered source class"
        )
    gaps += _schema_gaps(ref, doc.get("payload"), schema, compiler_src)
    return gaps


def verify_outputs(
    tree: cac.Tree,
    revision: str,
    compiler_src: Path,
    subject: dict[str, list[str]],
    run: dict[str, Any],
) -> dict[str, Any]:
    """Every artifact and receipt of one producer run, verified from its bytes."""
    gaps: list[str] = []
    reg = cac.Registration(tree, subject)
    projections_by_id = {p.get("id"): p for p in reg.projections}
    compositions_by_id = {p.get("id"): p for p in reg.compositions}
    verified: dict[str, dict[str, dict[str, Any]]] = {}
    contexts: dict[str, ProjectionContext] = {}
    for ref, outcome in run["projections"].items():
        profile = projections_by_id.get(ref)
        if profile is None or "artifacts" not in outcome:
            gaps.append(f"{ref}: no artifacts to verify")
            continue
        ctx = ProjectionContext(tree, revision, profile)
        contexts[ref] = ctx
        expected = {f"{ref}#{s}" for s in ctx.by_source}
        emitted = {a["ref"] for a in outcome["artifacts"]}
        if emitted != expected:
            gaps.append(
                f"{ref}: emitted {sorted(map(str, emitted))}, but the profile's registered "
                f"sources are {sorted(expected)}"
            )
        pinned = {
            s.get("ref"): s.get("digest")
            for s in (outcome.get("pins") or {}).get("sources", [])
        }
        verified[ref] = {}
        for art in outcome["artifacts"]:
            what = str(art["ref"])
            doc, raw = _read_json(art["path"], what, gaps)
            if (
                raw
                and "sha256:" + hashlib.sha256(raw).hexdigest() != art["content_digest"]
            ):
                gaps.append(
                    f"{what}: delivered bytes differ from the reported content_digest"
                )
            if doc is not None and doc.get("projection_digest") != art["digest"]:
                gaps.append(
                    f"{what}: reported digest is not the artifact's projection_digest"
                )
            gaps += check_projection(doc, ctx, what, compiler_src)
            if doc is None:
                continue
            source = ctx.by_source.get(doc.get("source_ref")) or {}
            if pinned.get(doc.get("source_ref")) != source.get("digest"):
                gaps.append(
                    f"{what}: compiler pinned a source digest that is not HEAD's"
                )
            receipt, _ = _read_json(art["receipt_path"], f"{what} receipt", gaps)
            gaps += check_receipt(
                receipt,
                f"{what} receipt",
                output={"ref": what, "digest": doc.get("projection_digest")},
                profile={"ref": ref, "digest": ctx.profile_digest},
                inputs=[
                    {
                        "ref": doc.get("source_ref"),
                        "digest": source.get("digest"),
                        "revision": revision,
                        "path": source.get("path"),
                    }
                ],
                stated_digest=art["receipt_digest"],
            )
            verified[ref][what] = doc
    composed: dict[str, dict[str, Any]] = {}
    for ref, outcome in run["compositions"].items():
        record = compositions_by_id.get(ref)
        if record is None or not outcome.get("artifacts"):
            gaps.append(f"{ref}: no artifacts to verify")
            continue
        components = verified.get(outcome.get("composes"), {})
        classes = _component_classes(components, contexts.get(outcome.get("composes")))
        schema_id = (record.get("output") or {}).get("schema")
        names = reg.schemas["consts"].get(schema_id) or []
        schema = reg.schemas["docs"][names[0]] if len(names) == 1 else None
        art = outcome["artifacts"][0]
        what = str(art["ref"])
        doc, raw = _read_json(art["path"], what, gaps)
        if raw and "sha256:" + hashlib.sha256(raw).hexdigest() != art["content_digest"]:
            gaps.append(
                f"{what}: delivered bytes differ from the reported content_digest"
            )
        if doc is not None and doc.get("composition_digest") != art["digest"]:
            gaps.append(
                f"{what}: reported digest is not the artifact's composition_digest"
            )
        gaps += check_composition(
            doc, record, what, components, schema, compiler_src, classes
        )
        if doc is None:
            continue
        receipt, _ = _read_json(art["receipt_path"], f"{what} receipt", gaps)
        gaps += check_receipt(
            receipt,
            f"{what} receipt",
            output={"ref": what, "digest": doc.get("composition_digest")},
            profile={"ref": ref, "digest": cac.digest(record)},
            inputs=[
                {"ref": c.get("projection_ref"), "digest": c.get("projection_digest")}
                for c in doc.get("components") or []
                if isinstance(c, dict)
            ],
            stated_digest=art["receipt_digest"],
        )
        composed[ref] = {
            "doc": doc,
            "record": record,
            "schema": schema,
            "what": what,
            "classes": classes,
        }
    controls = negative_controls(verified, contexts, composed, compiler_src)
    gaps += [
        f"negative control accepted: {name}" for name, ok in controls.items() if not ok
    ]
    return {
        "status": "pass" if not gaps else "fail",
        "gaps": gaps,
        "verified_projections": sum(len(v) for v in verified.values()),
        "verified_compositions": len(composed),
        "negative_controls": controls,
    }


def _component_classes(
    components: dict[str, dict[str, Any]], ctx: ProjectionContext | None
) -> dict[str, str]:
    """Each verified projection's source class, from the registry, not from the artifact."""
    if ctx is None:
        return {}
    return {
        ref: ctx.by_source[doc["source_ref"]]["class"]
        for ref, doc in components.items()
        if doc.get("source_ref") in ctx.by_source
    }


def _alter_first_scalar(value: Any) -> bool:
    """Change the first scalar leaf in place (depth first); False when there is none."""
    items = (
        list(value.items())
        if isinstance(value, dict)
        else list(enumerate(value))
        if isinstance(value, list)
        else []
    )
    for key, child in items:
        if isinstance(child, (dict, list)):
            if _alter_first_scalar(child):
                return True
        elif not isinstance(child, bool) and isinstance(child, (int, float)):
            value[key] = child + 1
            return True
        elif isinstance(child, str):
            value[key] = child + " (altered)"
            return True
        elif isinstance(child, bool):
            value[key] = not child
            return True
    return False


def _resealed(doc: dict[str, Any], field: str) -> dict[str, Any]:
    doc[field] = _self_digest(doc, field)
    return doc


def _drop_required_field(payload: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Remove one schema-required, non-id field from the first record of a typed list."""
    for key, child in (schema.get("properties") or {}).items():
        items = child.get("items") if isinstance(child, dict) else None
        records = payload.get(key)
        if not isinstance(items, dict) or not isinstance(records, list) or not records:
            continue
        first = records[0]
        for field in items.get("required") or []:
            if field != "id" and isinstance(first, dict) and field in first:
                del first[field]
                return True
    return False


def _projection_controls(
    original: dict[str, Any], ctx: ProjectionContext
) -> list[tuple[str, dict[str, Any], str]]:
    """(name, corrupted artifact, the gap text that must reject it), one per mechanism."""
    zero = "sha256:" + "0" * 64
    controls = []
    doc = copy.deepcopy(original)
    doc["source_digest"] = zero
    controls.append(
        ("source digest", _resealed(doc, "projection_digest"), "source_digest")
    )
    doc = copy.deepcopy(original)
    doc["projection_profile_digest"] = zero
    controls.append(
        ("profile digest", _resealed(doc, "projection_digest"), "profile digest")
    )
    doc = copy.deepcopy(original)
    doc["payload"] = {**doc["payload"], "__forged__": 1}
    controls.append(("unsealed edit", doc, "projection_digest does not match"))
    root = next(
        (k for k, v in original["payload"].items() if isinstance(v, list) and v), None
    )
    if root is not None:
        doc = copy.deepcopy(original)
        doc["payload"][root] = doc["payload"][root][1:]
        controls.append(
            (
                "selected record dropped",
                _resealed(doc, "projection_digest"),
                "declared selection",
            )
        )
    doc = copy.deepcopy(original)
    if _alter_first_scalar(doc["payload"]):
        controls.append(
            (
                "selected value altered",
                _resealed(doc, "projection_digest"),
                "declared selection",
            )
        )
    if ctx.schema is not None:
        doc = copy.deepcopy(original)
        if _drop_required_field(doc["payload"], ctx.schema):
            controls.append(
                (
                    "schema required field",
                    _resealed(doc, "projection_digest"),
                    "payload schema",
                )
            )
    return controls


def _composition_controls(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any], str]]:
    controls = []
    corrupted = copy.deepcopy(doc)
    corrupted["components"].append(copy.deepcopy(corrupted["components"][0]))
    controls.append(
        (
            "duplicate component",
            _resealed(corrupted, "composition_digest"),
            "more than once",
        )
    )
    if len(doc["components"]) > 1:
        corrupted = copy.deepcopy(doc)
        corrupted["components"].pop()
        controls.append(
            (
                "missing component",
                _resealed(corrupted, "composition_digest"),
                "not exactly",
            )
        )
    if len(doc["components"]) > 1:
        corrupted = copy.deepcopy(doc)
        first, second = corrupted["components"][0], corrupted["components"][1]
        first["source_class"], second["source_class"] = (
            second["source_class"],
            first["source_class"],
        )
        controls.append(
            (
                "namespace relabelled",
                _resealed(corrupted, "composition_digest"),
                "claims source class",
            )
        )
    corrupted = copy.deepcopy(doc)
    payload = corrupted.get("payload")
    if isinstance(payload, dict) and _alter_first_scalar(payload):
        controls.append(
            (
                "namespace payload altered",
                _resealed(corrupted, "composition_digest"),
                "payload is not exactly",
            )
        )
    corrupted = copy.deepcopy(doc)
    corrupted["components"][0]["projection_digest"] = "sha256:" + "0" * 64
    controls.append(
        (
            "component digest",
            _resealed(corrupted, "composition_digest"),
            "digest differs",
        )
    )
    return controls


def negative_controls(
    verified: dict[str, dict[str, dict[str, Any]]],
    contexts: dict[str, ProjectionContext],
    composed: dict[str, dict[str, Any]],
    compiler_src: Path,
) -> dict[str, bool]:
    """Corrupt one mechanism at a time, re-seal the digest, and require rejection by it.

    True means the verifier rejected the corrupted artifact through the targeted check. A
    control whose precondition is absent (no list-valued selection, one component, no
    required non-id field) is not run.
    """
    results: dict[str, bool] = {}
    for ref, docs in verified.items():
        if not docs:
            continue
        for what in sorted(docs):
            for name, corrupted, marker in _projection_controls(
                docs[what], contexts[ref]
            ):
                gaps = check_projection(corrupted, contexts[ref], what, compiler_src)
                results[f"{what}: {name}"] = any(marker in g for g in gaps)
    for ref, item in composed.items():
        composes = (item["record"].get("composes") or {}).get("projection_profile")
        components = verified.get(composes, {})
        for name, corrupted, marker in _composition_controls(item["doc"]):
            gaps = check_composition(
                corrupted,
                item["record"],
                item["what"],
                components,
                item["schema"],
                compiler_src,
                item["classes"],
            )
            results[f"{ref}: {name}"] = any(marker in g for g in gaps)
    return results


def compare_runs(first: Path, second: Path) -> dict[str, Any]:
    """Two producer runs must emit the same normative files with the same bytes.

    `requests/` is the gate's own input to each run (it names its output root), not output.
    """

    def files(root: Path) -> dict[str, str]:
        return {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file() and p.relative_to(root).parts[0] != "requests"
        }

    a, b = files(first), files(second)
    differing = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    only_first = sorted(set(a) - set(b))
    only_second = sorted(set(b) - set(a))
    ok = bool(a) and not differing and not only_first and not only_second
    return {
        "status": "pass" if ok else "fail",
        "files": len(a),
        "differing": differing,
        "only_in_first": only_first,
        "only_in_second": only_second,
    }


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--subject", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--main-ref", default="origin/main")
    args = parser.parse_args(argv)
    try:
        repo = args.checkout.resolve()
        subject = cac.load_subject(args.subject)
        main_tree = cac.Tree(repo, args.main_ref)
        if args.release not in cac.release_versions(main_tree):
            raise cac.InputError(f"{args.release} is not a release on {args.main_ref}")
        proof = release_admission(repo, main_tree, args.release)
        if proof["status"] == "pass":
            at = cac.Tree(repo, proof["admission_commit"])
            reg = cac.registration(at, subject)
            if reg["status"] != "pass":
                proof["gaps"].append(
                    "the subject is not registered at the admission commit"
                )
            else:
                scope = decision_scope(
                    repo, main_tree, args.release, proof, subject, reg["records"]
                )
                proof["decision_scope"] = scope
                proof["subject_digest"] = scope["subject_digest"]
                proof["gaps"] += scope["gaps"]
            proof["status"] = "pass" if not proof["gaps"] else "fail"
    except cac.InputError as exc:
        print(
            json.dumps(
                {"schema": EVIDENCE_SCHEMA, "status": "UNRESOLVED", "reason": str(exc)}
            )
        )
        return 2
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if proof["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
