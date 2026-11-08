"""Rung-by-rung tests for check_admission_closure.py on a synthetic semantics repository.

Each test builds a small git repository shaped like Quantum-L9/.github (ledgers registered as
canonical sources, an SC-008-complete release record, an ADR that binds the approved
`semantics/` tree, a stand-in validator and Makefile whose exit codes the test controls)
and moves exactly one fact to show which rung it decides. A stand-in producer writes real
artifact and receipt files so downstream verification has bytes to check.

This module also holds the fixture the other two test modules import.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_admission_closure as cac

SUBJECT = {
    "schema": cac.SUBJECT_SCHEMA,
    "invariants": ["L9-X-001"],
    "vocabulary_terms": ["x_term"],
    "contracts": ["l9.contract/x@1"],
    "canonical_sources": ["l9.source/x-model@1"],
    "source_classes": ["x_model"],
    "projection_profiles": ["l9.projection/x@1"],
    "composition_profiles": ["l9.compose/x@1"],
    "schemas": ["x_projection.schema.yaml", "x_composition.schema.yaml"],
}
# With no admitted base, every registered ledger is a new identity too.
FIRST_ADMISSION = dict(
    SUBJECT,
    canonical_sources=[
        "l9.source/invariants@1",
        "l9.source/vocabulary@1",
        "l9.source/contracts@1",
        "l9.source/projection-profiles@1",
        "l9.source/x-model@1",
    ],
)
# Every name a decision covering the whole fixture subject must state.
ALL_NAMES = [
    *FIRST_ADMISSION["canonical_sources"],
    "L9-X-001",
    "x_term",
    "l9.contract/x@1",
    "l9.source/x-model@1",
    "x_model",
    "l9.projection/x@1",
    "l9.compose/x@1",
]

SOURCES = (
    ("invariants", "invariants.yaml"),
    ("vocabulary", "vocabulary.yaml"),
    ("contracts", "contracts.yaml"),
    ("projection-profiles", "projection_profiles.yaml"),
    ("x-model", "x_model.yaml"),
)


def canonical_sources(entries=SOURCES, extra=""):
    text = "sources:\n"
    for name, path in entries:
        text += (
            f"- id: l9.source/{name}@1\n  path: semantics/{path}\n  format: yaml\n"
            "  canonical: true\n  projection_allowed: true\n  derivation_allowed: false\n"
        )
    return text + extra


def manifest(schemas=("x_projection.schema.yaml", "x_composition.schema.yaml")):
    catalogs = ", ".join(p for _, p in SOURCES)
    return (
        f"requires:\n  semantic_catalogs: [{catalogs}]\n"
        f"  artifact_schemas: [{', '.join(schemas)}]\n"
    )


PROFILE = (
    "- id: l9.projection/x@1\n  class: consumer\n  consumer: x-consumer\n"
    "  purpose: project x\n  sources:\n    x_model:\n      selectors:\n"
    '      - $.value\n      - $.records[?(@.id=="r1")]\n'
    "  output:\n    schema: l9.projection.x/v1\n"
)
PROFILES_HEAD = (
    "profile_classes:\n  consumer:\n    definition: for one consumer\n"
    "forbidden_constraints:\n  criterion_language:\n    name: l9.forbidden-constraint\n"
    "    version: 1\n  definitions: {}\n"
    "source_classes:\n  x_model:\n    canonical_artifact: x_model.yaml\n"
)
COMPOSITION = (
    "- id: l9.compose/x@1\n  purpose: compose x\n  accepts: [projection_artifact]\n"
    "  composes:\n    projection_profile: l9.projection/x@1\n  merge_strategy:\n"
    "    placement: source_class_namespace\n    source_coverage: exact\n"
    "    duplicate_source: conflict\n    semantic_identity_collision: require_equivalence\n"
    "  conflict_result: invalid\n  output:\n    schema: l9.composed-projection.x/v1\n"
)

LEDGERS = {
    "invariants.yaml": (
        "invariants:\n- id: L9-X-001\n  statement: x holds\n  scope: global\n"
        "  owner: Quantum-L9/.github\n"
    ),
    "vocabulary.yaml": "terms:\n  x_term:\n    semantic_class: concept\n    definition: an x\n",
    "contracts.yaml": (
        "contracts:\n- id: l9.contract/x@1\n  purpose: x\n  scope: global\n"
        "  owner: Quantum-L9/.github\n  source_invariants: [L9-X-001]\n"
    ),
    "canonical_sources.yaml": canonical_sources(),
    "x_model.yaml": (
        "artifact_id: l9.x/global@1\nvalue: 1\nrecords:\n- id: r1\n  v: 1\n- id: r2\n  v: 2\n"
    ),
    "projection_profiles.yaml": PROFILES_HEAD + "projection_profiles:\n" + PROFILE,
    "composition_profiles.yaml": "profiles:\n" + COMPOSITION,
    "generic_compiler_manifest.yaml": manifest(),
    "x_projection.schema.yaml": (
        "schema: l9.schema-definition/v1\nartifact_id: l9.schema/x-projection@1\n"
        "governed_by:\n  projection_profile_ref: l9.projection/x@1\ntype: object\n"
        "properties:\n  schema:\n    const: l9.projection.x/v1\n  value:\n    type: integer\n"
        "  records:\n    type: array\n    min_items: 1\n    items:\n      type: object\n"
        "      required: [id, v]\n      properties:\n        id:\n          type: string\n"
        "        v:\n          type: integer\n"
    ),
    "x_composition.schema.yaml": (
        "schema: l9.schema-definition/v1\nartifact_id: l9.schema/x-composition@1\n"
        "governed_by:\n  composition_profile_ref: l9.compose/x@1\ntype: object\n"
        "properties:\n  schema:\n    const: l9.composed-projection.x/v1\n"
        "  x_model:\n    type: object\n"
    ),
}

VALIDATOR = (
    "import pathlib, sys\n"
    "sys.exit(int(pathlib.Path(__file__).with_name('exit_code').read_text()))\n"
)
MAKEFILE = (
    "validate check test:\n\t@exit $$(cat scripts/make_$@ 2>/dev/null || echo 0)\n"
)
ADMITTED = "**ADMITTED ADDITIVE SUCCESSOR** ({adr}, 2026-11-08)"
CANDIDATE = "**ADDITIVE SUCCESSOR CANDIDATE**"


# --------------------------------------------------------------------------- stand-in producer

FAKE_VALIDATE = '''
def schema_violations(value, descriptor, path="$"):
    """A small stand-in for the compiler's interpreter: const, type, required, fields, items."""
    if not isinstance(descriptor, dict):
        return []
    if "const" in descriptor and value != descriptor["const"]:
        return [path + ": const"]
    kind = descriptor.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if kind in types and not isinstance(value, types[kind]):
        return [path + ": expected " + kind]
    if kind == "object":
        for name in descriptor.get("required", []):
            if name not in value:
                return [path + "." + name + ": required"]
        for key, child in (descriptor.get("properties") or {}).items():
            if key in value:
                found = schema_violations(value[key], child, path + "." + key)
                if found:
                    return found
    if kind == "array":
        if len(value) < descriptor.get("min_items", 0):
            return [path + ": min_items"]
        for i, item in enumerate(value):
            found = schema_violations(item, descriptor.get("items") or {}, path + f"[{i}]")
            if found:
                return found
    return []
'''

FAKE_COMPILER = """
import hashlib, json, os, pathlib, random, sys, yaml

MODE = pathlib.Path(__file__).with_name("mode").read_text().strip()
ZERO = "sha256:" + "0" * 64


def digest(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode()).hexdigest()


def seal(doc, field):
    doc[field] = digest({k: v for k, v in doc.items() if k != field})
    return doc


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, sort_keys=True, indent=2) + "\\n").encode()
    path.write_bytes(data)
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load(root, rel):
    return yaml.safe_load(open(os.path.join(root, rel)))


def sources_of(root, ref):
    pp = load(root, "semantics/projection_profiles.yaml")
    profile = [p for p in pp["projection_profiles"] if p["id"] == ref][0]
    registry = load(root, "semantics/canonical_sources.yaml")["sources"]
    out = []
    for cls, spec in profile["sources"].items():
        path = "semantics/" + pp["source_classes"][cls]["canonical_artifact"]
        sid = [s["id"] for s in registry if s["path"] == path][0]
        raw = open(os.path.join(root, path), "rb").read()
        out.append((cls, sid, path, raw, spec["selectors"]))
    return profile, out


def select(document, selectors):
    payload = {}
    for selector in selectors:
        if "[?(" in selector:
            coll = selector[2:selector.index("[")]
            want = selector.split('"')[1]
            payload.setdefault(coll, []).extend(
                r for r in document[coll] if r.get("id") == want)
        else:
            payload[selector[2:]] = document[selector[2:]]
    return payload


def receipt(out, subject, output, profile, inputs, unresolved):
    doc = {"schema": "l9.compiler-receipt/v1", "exact_subject_ref": subject,
           "result": "pass", "output": output, "profile": profile, "inputs": inputs,
           "verification_basis": {"coverage": "complete", "unresolved_criteria": unresolved,
                                  "criteria": {"selection_equivalence": {"status": "pass"}}}}
    seal(doc, "receipt_digest")
    path = out / "receipts" / (doc["receipt_digest"].split(":")[1] + ".json")
    if MODE != "no-receipt":
        write(path, doc)
    return str(path), doc["receipt_digest"]


def entry(ref, art_digest, path, content, rpath, rdigest, unresolved):
    item = {"ref": ref, "digest": art_digest, "path": str(path), "content_digest": content,
            "receipt_path": rpath, "receipt_digest": rdigest, "result": "pass"}
    if MODE != "omit-unresolved":
        item["unresolved_criteria"] = unresolved
    return item


cmd = sys.argv[1]
if MODE == "garbage":
    print("not yaml: [unbalanced")
    sys.exit(0)
if cmd == "projection-coordinates":
    args = dict(zip(sys.argv[2::2], sys.argv[3::2]))
    profile, sources = sources_of(args["--authority-root"], args["--profile"])
    print(yaml.safe_dump({
        "projection_profile": {"ref": profile["id"], "digest": digest(profile)},
        "sources": [{"ref": s[1], "digest": "sha256:" + hashlib.sha256(s[3]).hexdigest()}
                    for s in sources]}))
elif cmd == "project":
    req = yaml.safe_load(open(sys.argv[2]))
    root, out = req["authority"]["root"], pathlib.Path(req["output_root"])
    ref = req["projection_profile"]["ref"]
    profile, sources = sources_of(root, ref)
    unresolved = ["declared_constraint:rules:r"] if MODE == "unresolved" else []
    arts = []
    for cls, sid, path, raw, selectors in sources:
        if MODE == "wrong-source":
            sid = "l9.source/other@1"
        payload = select(yaml.safe_load(raw), selectors)
        if MODE == "bad-payload":
            payload["records"][0]["v"] = "not-an-integer"
        art = {"schema": "l9.projection-artifact/v1", "source_ref": sid,
               "source_digest": ZERO if MODE == "bad-source-digest"
               else "sha256:" + hashlib.sha256(raw).hexdigest(),
               "projection_profile_ref": ref, "projection_profile_digest": digest(profile),
               "payload": payload,
               "generated_by": {"compiler": "fake", "nonce": random.random()
                                if MODE == "nondeterministic" else 0}}
        seal(art, "projection_digest")
        if MODE == "stale-digest":
            art["payload"]["value"] = 999
        target = out / ref.replace("/", "_") / (sid.replace("/", "_") + ".projection.json")
        content = write(target, art)
        full = ref + "#" + sid
        rpath, rdigest = receipt(out, full, {"ref": full, "digest": art["projection_digest"]},
                                 {"ref": ref, "digest": digest(profile)},
                                 [{"ref": sid, "digest": art["source_digest"],
                                   "revision": req["authority"]["revision"], "path": path}],
                                 unresolved)
        arts.append(entry(full, art["projection_digest"], target, content, rpath, rdigest,
                          unresolved))
    print(yaml.safe_dump({"status": "succeeded", "result": "pass", "artifacts": arts}))
elif cmd == "compose":
    req = yaml.safe_load(open(sys.argv[2]))
    root, out = req["authority"]["root"], pathlib.Path(req["output_root"])
    ref = req["composition_profile"]["ref"]
    record = [p for p in load(root, "semantics/composition_profiles.yaml")["profiles"]
              if p["id"] == ref][0]
    _, sources = sources_of(root, record["composes"]["projection_profile"])
    cls_of = {s[1]: s[0] for s in sources}
    components, payload = [], {}
    for path in req["components"]:
        art = json.load(open(path))
        cls = cls_of.get(art["source_ref"], "unknown")
        components.append({"projection_ref": art["projection_profile_ref"] + "#" + art["source_ref"],
                           "projection_digest": art["projection_digest"], "source_class": cls,
                           "source_ref": art["source_ref"], "source_digest": art["source_digest"]})
        payload[cls] = art["payload"]
    if MODE == "dup-component":
        components.append(dict(components[0]))
    composed = {"schema": "l9.composed-projection/v1",
                "composition_profile": {"ref": ref, "digest": digest(record)},
                "components": components, "payload": payload}
    seal(composed, "composition_digest")
    full = ref + "#" + record["composes"]["projection_profile"]
    target = out / "composed" / (full.replace("/", "_") + ".composed.json")
    content = write(target, composed)
    rpath, rdigest = receipt(out, full, {"ref": full, "digest": composed["composition_digest"]},
                             {"ref": ref, "digest": digest(record)},
                             [{"ref": c["projection_ref"], "digest": c["projection_digest"]}
                              for c in components], [])
    print(yaml.safe_dump({"status": "succeeded", "result": "pass", "artifacts": [
        entry(full, composed["composition_digest"], target, content, rpath, rdigest, [])]}))
"""


def fake_compiler(root: Path, mode: str) -> Path:
    """A stand-in l9-semantic-compiler-engine git checkout whose output the test controls."""
    engine = root / "engine"
    pkg = engine / "src" / "l9_semantic_compiler"
    (pkg / "passes").mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "__main__.py").write_text(FAKE_COMPILER, encoding="utf-8")
    (pkg / "passes" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "passes" / "validate.py").write_text(FAKE_VALIDATE, encoding="utf-8")
    if not (engine / ".git").exists():
        git = Repo(engine)
        git.git("init", "-q")
        git.git("config", "user.email", "fixture@example.invalid")
        git.git("config", "user.name", "fixture")
        git.git("add", "-A")
        git.git("commit", "-q", "-m", "engine")
    (pkg / "mode").write_text(
        mode, encoding="utf-8"
    )  # untracked: mode never dirties HEAD
    return engine


# --------------------------------------------------------------------------- fixture repository


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def semantics_tree(self) -> str:
        self.git("add", "-A", "semantics")
        return self.git("write-tree", "--prefix=semantics/")

    def adr(
        self,
        number: int,
        version: str,
        names,
        *,
        tree=None,
        status=None,
        release_row=True,
        target_row=True,
        decision_ref=True,
        index=True,
    ) -> str:
        """An ADR in the ADR-025 shape: status, subject table, admitted definitions."""
        name = f"ADR-{number:03d}-admit-{version}.md"
        ref = " The owner decided in session `session_fixture000001` (Quantum-L9/.github#1)."
        line = (
            status
            or f"**Status:** Accepted for semantic-foundation {version}.{ref if decision_ref else ''}"
        )
        rows = "| Item | Value |\n|---|---|\n"
        if release_row:
            rows += f"| Release | Semantic Foundation **{version}** |\n"
        rows += f"| Approved semantic tree | `semantics/` tree `{tree or self.semantics_tree()}` |\n"
        if target_row:
            rows += "| Target class and authority | Canonical global semantics. The owner holds it. |\n"
        body = f"# ADR-{number:03d}\n\n{line}\n\n## Subject\n\n{rows}\nAdmitted definitions:\n\n"
        body += "".join(f"- `{n}`\n" for n in names)
        self.write(f"docs/adr/{name}", body)
        if index:
            entries = [
                ln
                for ln in self._index_lines()
                if not ln.startswith(f"- ADR-{number:03d}:")
            ]
            entries.append(f"- ADR-{number:03d}: Admit {version}")
            self.write(
                "docs/adr/README.md", "# ADRs\n\n" + "\n".join(sorted(entries)) + "\n"
            )
        elif not (self.root / "docs/adr/README.md").exists():
            self.write("docs/adr/README.md", "# ADRs\n")
        return name

    def _index_lines(self):
        path = self.root / "docs/adr/README.md"
        if not path.exists():
            return []
        return [ln for ln in path.read_text().splitlines() if ln.startswith("- ADR-")]

    def release(self, version: str, status: str, *, omit=()) -> None:
        """A release record in the SC-008 shape, hashed last, over the full inventory."""
        base = f"docs/semantic-foundation/{version}"
        files = sorted(
            f"semantics/{p.name}" for p in (self.root / "semantics").glob("*.yaml")
        )
        adrs = sorted(p.name for p in (self.root / "docs/adr").glob("ADR-*.md"))
        manifest_text = (
            f"# Manifest\n\nThis release contains **{len(files)}** canonical semantic YAML files"
            f" and contains **{len(adrs)}** accepted ADRs.\n\n"
            + "".join(f"- `{f}`\n" for f in files)
        )
        self.write(f"{base}/MANIFEST.md", manifest_text)
        self.write(f"{base}/README.md", f"# {version}\n\nStatus: {status}\n")
        self.write(f"{base}/RELEASE_VALIDATION.md", f"# {version} validation\n")
        entries = [f"./{f}" for f in files]
        entries += [f"./docs/adr/{a}" for a in adrs] + ["./docs/adr/README.md"]
        lines = []
        for entry in entries:
            data = (self.root / entry[2:]).read_bytes()
            lines.append(f"{hashlib.sha256(data).hexdigest()}  {entry}\n")
        for doc in ("MANIFEST.md", "README.md", "RELEASE_VALIDATION.md"):
            data = (self.root / base / doc).read_bytes()
            lines.append(f"{hashlib.sha256(data).hexdigest()}  ./{doc}\n")
        lines = [ln for ln in lines if ln.split()[1] not in omit]
        self.write(
            f"{base}/HASHES.sha256", "".join(sorted(lines, key=lambda x: x.split()[1]))
        )

    def admit(self, version: str, number: int, names, **adr) -> str:
        name = self.adr(number, version, names, **adr)
        self.release(version, ADMITTED.format(adr=f"ADR-{number:03d}"))
        return name

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        return self.git("rev-parse", "HEAD")


def build(root: Path, *, status=None, adr_version="v1.0.0"):
    """v1.0.0 admitted (ADR-001 binds its tree and names every subject identity)."""
    root.mkdir(parents=True, exist_ok=True)
    repo = Repo(root)
    repo.git("init", "-q")
    repo.git("config", "user.email", "fixture@example.invalid")
    repo.git("config", "user.name", "fixture")
    for name, text in LEDGERS.items():
        repo.write(f"semantics/{name}", text)
    repo.write("scripts/validate-semantics.py", VALIDATOR)
    repo.write("scripts/exit_code", "0")
    repo.write("Makefile", MAKEFILE)
    repo.adr(1, adr_version, ALL_NAMES)
    repo.release("v1.0.0", status or ADMITTED.format(adr="ADR-001"))
    repo.commit("release v1.0.0")
    return repo


class _Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = build(self.tmp / "repo")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def verdict(self, subject=None, **kwargs):
        return cac.evaluate(
            self.repo.root,
            subject or cac.load_subject(self._subject()),
            "origin/main",
            **kwargs,
        )

    def _subject(self, body=None):
        path = self.tmp / "subject.json"
        path.write_text(json.dumps(body or SUBJECT), encoding="utf-8")
        return path

    def subject(self, **items):
        return cac.load_subject(self._subject({"schema": cac.SUBJECT_SCHEMA, **items}))

    def rebuild(self, **kwargs):
        shutil.rmtree(self.repo.root)
        self.repo = build(self.repo.root, **kwargs)

    def candidate(self, version="v1.1.0", commit=True):
        """Cut the successor as a candidate over the current semantics."""
        self.repo.release(version, CANDIDATE)
        if commit:
            self.repo.commit(f"candidate {version}")

    def downstream(self, mode, subject=None):
        return cac.downstream(
            self.repo.root,
            fake_compiler(self.tmp, mode),
            self.tmp / "out",
            subject or cac.load_subject(self._subject()),
        )


# --------------------------------------------------------------------------- the ladder


class Ladder(_Fixture):
    def test_admitted_and_current_reaches_admitted(self):
        report = self.verdict()
        self.assertEqual(report["verdict"], "ADMITTED", json.dumps(report, indent=1))
        self.assertEqual(report["admission"]["release"], "v1.0.0")
        self.assertEqual(report["admission"]["adr"], "ADR-001-admit-v1.0.0.md")
        self.assertEqual(report["admission"]["changed_on_main_since_admission"], [])
        self.assertEqual(report["admission"]["changed_at_head_since_admission"], [])
        evidence = report["admission"]["evidence"]
        self.assertEqual(
            evidence["admitted_semantics_tree"],
            self.repo.git("rev-parse", "HEAD:semantics"),
        )
        self.assertEqual(
            evidence["target_authority_class"], "canonical_global_semantics"
        )
        self.assertIn("session_fixture000001", evidence["authorized_decision_ref"])

    def test_unregistered_schema_is_incomplete(self):
        self.repo.write(
            "semantics/generic_compiler_manifest.yaml",
            manifest(("x_projection.schema.yaml",)),
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        gaps = "\n".join(report["registration"]["gaps"])
        self.assertIn(
            "schema x_composition.schema.yaml: not in generic_compiler_manifest", gaps
        )
        self.assertIn(
            "composition profile l9.compose/x@1: no registered schema declares", gaps
        )

    def test_undeclared_source_class_is_incomplete(self):
        text = LEDGERS["projection_profiles.yaml"].replace(
            "x_model:\n    canonical_artifact", "y:\n    canonical_artifact"
        )
        self.repo.write("semantics/projection_profiles.yaml", text)
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn(
            "source class x_model: not declared",
            "\n".join(report["registration"]["gaps"]),
        )

    def test_source_missing_from_semantic_catalogs_is_incomplete(self):
        self.repo.write(
            "semantics/generic_compiler_manifest.yaml",
            manifest().replace(", x_model.yaml]", "]"),
        )
        self.assertEqual(self.verdict()["verdict"], "INCOMPLETE")

    def test_duplicate_invariant_is_incomplete(self):
        self.repo.write(
            "semantics/invariants.yaml",
            LEDGERS["invariants.yaml"] + "- id: L9-X-001\n  statement: again\n",
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn(
            "invariant L9-X-001: defined 2 times", report["registration"]["gaps"]
        )

    def test_failing_validator_stops_at_registered(self):
        self.repo.write("scripts/exit_code", "1")
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertEqual(report["validator"]["status"], "fail")

    def test_bytes_drifting_from_release_stop_at_registered(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "v1.0.0: semantics/x_model.yaml bytes differ from the release hash",
            report["release"]["gaps"],
        )

    def test_candidate_release_stops_at_released_candidate(self):
        self.rebuild(status=CANDIDATE)
        report = self.verdict(cac.load_subject(self._subject(FIRST_ADMISSION)))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )
        self.assertEqual(report["release"]["release_status"], "CANDIDATE")
        self.assertEqual(report["release"]["status"], "pass")
        self.assertEqual(report["scope"]["status"], "pass")

    def test_admitted_status_without_matching_adr_is_not_admitted(self):
        self.rebuild(adr_version="v9.9.9")
        report = self.verdict(cac.load_subject(self._subject(FIRST_ADMISSION)))
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertIsNone(report["admission"]["tried"][0]["adr"])

    def test_record_changed_after_admission_is_not_admitted(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("purpose: x", "purpose: x, revised"),
        )
        self.candidate()
        subject = dict(SUBJECT, revisions=["contracts:l9.contract/x@1"])
        report = self.verdict(cac.load_subject(self._subject(subject)))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )
        self.assertEqual(report["release"]["version"], "v1.1.0")
        self.assertIn(
            "contract:l9.contract/x@1",
            report["admission"]["changed_on_main_since_admission"],
        )

    def test_later_admitted_release_takes_over(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("purpose: x", "purpose: x, revised"),
        )
        self.repo.admit("v1.1.0", 2, ["l9.contract/x@1"])
        self.repo.commit("admit v1.1.0")
        report = self.verdict()
        self.assertEqual(report["verdict"], "ADMITTED", json.dumps(report, indent=1))
        self.assertEqual(report["admission"]["release"], "v1.1.0")
        self.assertEqual(
            report["admission"]["decision_scope"]["introduced"],
            ["contract:l9.contract/x@1"],
        )

    def test_uncommitted_registration_is_not_admitted_on_main(self):
        # A new invariant registered and released in the working tree only: main never saw it.
        self.repo.write(
            "semantics/invariants.yaml",
            LEDGERS["invariants.yaml"]
            + "- id: L9-X-002\n  statement: y\n  scope: global\n  owner: Quantum-L9/.github\n",
        )
        self.repo.admit("v1.1.0", 2, ["L9-X-002"])
        report = self.verdict(self.subject(invariants=["L9-X-002"]))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )
        self.assertEqual(report["admission"]["status"], "fail")


class InputsAndExitCodes(_Fixture):
    def run_main(self, *extra, subject=None):
        return cac.main(
            [
                "--checkout",
                str(self.repo.root),
                "--subject",
                str(self._subject(subject)),
                *extra,
            ]
        )

    def test_exit_zero_when_required_rung_reached(self):
        self.assertEqual(self.run_main("--require", "registered"), 0)
        self.assertEqual(self.run_main("--require", "admitted"), 0)

    def test_exit_one_when_required_rung_not_reached(self):
        self.repo.write("scripts/exit_code", "1")
        self.assertEqual(self.run_main("--require", "released"), 1)

    def test_downstream_requirement_without_compiler_is_unresolved(self):
        self.assertEqual(self.run_main("--require", "downstream"), 2)

    def test_missing_main_ref_is_unresolved(self):
        self.assertEqual(self.run_main("--main-ref", "origin/nope"), 2)

    def test_missing_validator_is_unresolved(self):
        (self.repo.root / "scripts" / "validate-semantics.py").unlink()
        self.assertEqual(self.run_main(), 2)

    def test_missing_makefile_is_unresolved(self):
        (self.repo.root / "Makefile").unlink()
        self.assertEqual(self.run_main(), 2)

    def test_malformed_subjects_are_unresolved(self):
        for body in (
            {"schema": "other"},
            {"schema": cac.SUBJECT_SCHEMA},
            {"schema": cac.SUBJECT_SCHEMA, "invariants": ["A", "A"]},
            {"schema": cac.SUBJECT_SCHEMA, "profiles": ["x"]},
            {"schema": cac.SUBJECT_SCHEMA, "invariants": "L9-X-001"},
            {"schema": cac.SUBJECT_SCHEMA, "invariants": ["A"], "revisions": ["A"]},
            {
                "schema": cac.SUBJECT_SCHEMA,
                "invariants": ["A"],
                "revisions": ["invariants:B"],
            },
        ):
            self.assertEqual(self.run_main(subject=body), 2, body)

    def test_downstream_refuses_a_dirty_checkout(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        result = self.downstream("pass")
        self.assertEqual(result["status"], "fail")
        self.assertIn("tracked changes", result["reason"])


class ReviewRegressions(_Fixture):
    """One test per false-PASS or swallowed-UNRESOLVED path found in the first review."""

    def test_source_file_changed_on_main_after_admission_is_not_admitted(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        self.candidate()
        report = self.verdict(self.subject(canonical_sources=["l9.source/x-model@1"]))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )
        self.assertIn(
            "source_file:l9.source/x-model@1",
            report["admission"]["changed_on_main_since_admission"],
        )

    def test_source_class_file_is_covered_and_compared(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        self.candidate()
        report = self.verdict(self.subject(source_classes=["x_model"]))
        self.assertIn(
            "source_class_file:x_model",
            report["admission"]["changed_on_main_since_admission"],
        )
        # The changed ledger is its canonical source, which this subject leaves out.
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "scope closure: canonical_sources:l9.source/x-model@1 is new or changed",
            "\n".join(report["scope"]["gaps"]),
        )

    def test_uncommitted_edit_to_admitted_term_is_not_admitted(self):
        self.repo.write(
            "semantics/vocabulary.yaml",
            "terms:\n  x_term:\n    semantic_class: concept\n    definition: a different x\n",
        )
        self.candidate(commit=False)
        subject = dict(SUBJECT, revisions=["vocabulary_terms:x_term"])
        report = self.verdict(cac.load_subject(self._subject(subject)))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )
        self.assertIn(
            "term:x_term", report["admission"]["changed_at_head_since_admission"]
        )

    def test_release_record_edited_after_admission_is_not_admitted(self):
        self.repo.write(
            "semantics/vocabulary.yaml",
            "terms:\n  x_term:\n    semantic_class: concept\n    definition: a different x\n",
        )
        self.repo.release("v1.0.0", ADMITTED.format(adr="ADR-001"))
        self.repo.commit("rewrite the admitted release record in place")
        # The voided admission leaves no admitted base, so the subject is the first one.
        report = self.verdict(cac.load_subject(self._subject(FIRST_ADMISSION)))
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertIn(
            "edited after admission", report["admission"]["tried"][0]["reason"]
        )

    def test_status_lines_that_merely_mention_admitted_are_not_admitted(self):
        for line in (
            "Status: not yet ADMITTED",
            "Status: UNADMITTED draft",
            "Status: WITHDRAWN (was ADMITTED in error)",
            "Status: Admitted? No, awaiting owner",
            "Status: **ADDITIVE SUCCESSOR CANDIDATE**",
        ):
            self.repo.write(
                "docs/semantic-foundation/v1.0.0/README.md", f"# v\n\n{line}\n"
            )
            self.assertNotEqual(
                cac.release_status(cac.Tree(self.repo.root), "v1.0.0"), "ADMITTED", line
            )
        self.repo.write(
            "docs/semantic-foundation/v1.0.0/README.md",
            "# v\n\nStatus: **ADMITTED ADDITIVE SUCCESSOR** (ADR-001, 2026-11-08).\n",
        )
        self.assertEqual(
            cac.release_status(cac.Tree(self.repo.root), "v1.0.0"), "ADMITTED"
        )

    def test_adr_must_accept_exactly_this_version(self):
        tree = cac.Tree(self.repo.root)
        name = "docs/adr/ADR-001-admit-v1.0.0.md"
        rejected = (
            "**Status:** Accepted for semantic-foundation v3.21.0; it supersedes the v1.0.0 draft",
            "**Status:** Accepted for v3.0.0. Not accepted for v1.0.0.",
            "**Status:** Accepted for semantic-foundation v1.0.0-rc1 candidate",
            "**Status:** Accepted for semantic-foundation v1.0.0.1",
            "**Status:** Accepted for semantic-foundation v1.0.0 candidate. Admission is the gate.",
        )
        for line in rejected:
            self.repo.write(name, f"# ADR-001\n\n{line}\n")
            self.assertIsNone(cac.accepted_adr(tree, "v1.0.0"), line)
        self.repo.write(
            name,
            "# ADR-001\n\n**Status:** Accepted for semantic-foundation v1.0.0. The owner admitted it.\n",
        )
        self.assertEqual(cac.accepted_adr(tree, "v1.0.0"), "ADR-001-admit-v1.0.0.md")

    def test_downstream_without_profiles_is_not_applicable(self):
        report = cac.evaluate(
            self.repo.root,
            self.subject(invariants=["L9-X-001"]),
            "origin/main",
            self.tmp / "nonexistent-engine",
            self.tmp / "out",
        )
        self.assertEqual(report["downstream"]["status"], "not_applicable")
        self.assertEqual(report["verdict"], "ADMITTED")

    def test_missing_compiler_checkout_is_unresolved(self):
        code = cac.main(
            ["--checkout", str(self.repo.root), "--subject", str(self._subject()),
             "--require", "downstream", "--compiler-src", str(self.tmp / "nonexistent-engine"),
             "--output-root", str(self.tmp / "out")]
        )  # fmt: skip
        self.assertEqual(code, 2)

    def test_malformed_compiler_output_is_unresolved(self):
        code = cac.main(
            ["--checkout", str(self.repo.root), "--subject", str(self._subject()),
             "--require", "downstream", "--compiler-src", str(fake_compiler(self.tmp, "garbage")),
             "--output-root", str(self.tmp / "out")]
        )  # fmt: skip
        self.assertEqual(code, 2)

    def test_projection_not_covering_its_pinned_sources_fails(self):
        result = self.downstream("wrong-source")
        self.assertEqual(result["status"], "fail")
        self.assertFalse(
            result["projections"]["l9.projection/x@1"]["covers_pinned_sources"]
        )

    def test_stub_compiler_pass_reaches_downstream_usable(self):
        report = self.verdict(
            compiler_src=fake_compiler(self.tmp, "pass"), output_root=self.tmp / "out"
        )
        self.assertEqual(
            report["verdict"], "DOWNSTREAM_USABLE", json.dumps(report, indent=1)
        )
        controls = report["downstream"]["verification"]["negative_controls"]
        self.assertTrue(controls and all(controls.values()), controls)
        self.assertEqual(report["downstream"]["deterministic_replay"]["status"], "pass")

    def test_malformed_schema_file_is_unresolved(self):
        self.repo.write(
            "semantics/x_projection.schema.yaml", "properties: [unbalanced\n"
        )
        with self.assertRaises(cac.InputError):
            self.verdict()

    def test_unresolvable_ref_is_unresolved(self):
        with self.assertRaises(cac.InputError):
            cac.Tree(self.repo.root, "no-such-ref")


# --------------------------------------------------------------------------- closure review


class RegistrationHardening(_Fixture):
    """Registries are never resolved by position, and each kind meets its own policy."""

    def gaps(self, subject=None):
        report = self.verdict(subject)
        self.assertEqual(report["verdict"], "INCOMPLETE", json.dumps(report, indent=1))
        return "\n".join(report["registration"]["gaps"])

    def test_two_schemas_declaring_one_output_identity_are_incomplete(self):
        self.repo.write(
            "semantics/x_projection_copy.schema.yaml",
            LEDGERS["x_projection.schema.yaml"],
        )
        self.repo.write(
            "semantics/generic_compiler_manifest.yaml",
            manifest(
                (
                    "x_projection.schema.yaml",
                    "x_composition.schema.yaml",
                    "x_projection_copy.schema.yaml",
                )
            ),
        )
        self.assertIn(
            "output schema identity l9.projection.x/v1 is declared by 2 registered schemas",
            self.gaps(),
        )

    def test_two_sources_sharing_one_identity_are_incomplete(self):
        self.repo.write(
            "semantics/canonical_sources.yaml",
            canonical_sources(SOURCES + (("x-model", "x_copy.yaml"),)),
        )
        gaps = self.gaps()
        self.assertIn("id l9.source/x-model@1 is registered 2 times", gaps)

    def test_two_sources_sharing_one_path_are_incomplete(self):
        self.repo.write(
            "semantics/canonical_sources.yaml",
            canonical_sources(SOURCES + (("x-alias", "x_model.yaml"),)),
        )
        self.assertIn("path semantics/x_model.yaml is registered by", self.gaps())

    def test_source_class_bound_to_an_unprojectable_source_is_incomplete(self):
        self.repo.write(
            "semantics/canonical_sources.yaml",
            canonical_sources().replace(
                "path: semantics/x_model.yaml\n  format: yaml\n  canonical: true\n"
                "  projection_allowed: true",
                "path: semantics/x_model.yaml\n  format: yaml\n  canonical: true\n"
                "  projection_allowed: false",
            ),
        )
        self.assertIn(
            "source class x_model: source l9.source/x-model@1 is not projection_allowed",
            self.gaps(self.subject(source_classes=["x_model"])),
        )

    def test_profile_selecting_a_missing_record_is_incomplete(self):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace('"r1"', '"r9"'),
        )
        self.assertIn('selector $.records[?(@.id=="r9")] selects nothing', self.gaps())

    def test_profile_selecting_a_missing_source_class_is_incomplete(self):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace(
                "  sources:\n    x_model:", "  sources:\n    y_model:"
            ),
        )
        self.assertIn("source class y_model undeclared", self.gaps())

    def test_selector_outside_the_grammar_is_incomplete(self):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace("$.value", "$..value"),
        )
        self.assertIn("outside the l9.selector/v1 grammar", self.gaps())

    def test_contract_referencing_an_undefined_invariant_is_incomplete(self):
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"].replace("[L9-X-001]", "[L9-X-001, L9-X-404]"),
        )
        self.assertIn("source invariant L9-X-404 is not defined", self.gaps())

    def test_invariant_duplicating_governing_law_is_incomplete(self):
        self.repo.write(
            "semantics/invariants.yaml",
            LEDGERS["invariants.yaml"]
            + "- id: L9-X-002\n  statement: X  holds\n  scope: global\n  owner: o\n",
        )
        self.assertIn(
            "duplicates the governing statement",
            self.gaps(self.subject(invariants=["L9-X-002"])),
        )

    def test_schema_bound_to_another_profile_is_incomplete(self):
        self.repo.write(
            "semantics/x_projection.schema.yaml",
            LEDGERS["x_projection.schema.yaml"].replace(
                "projection_profile_ref: l9.projection/x@1",
                "projection_profile_ref: l9.projection/other@1",
            ),
        )
        self.assertIn("is governed_by", self.gaps())

    def test_existing_admitted_profile_changed_in_place_is_a_version_integrity_failure(
        self,
    ):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace(
                "purpose: project x", "purpose: project x, revised"
            ),
        )
        self.candidate()
        self.assertIn("immutable (PROJECTION-013)", self.gaps())

    def test_undefined_forbidden_category_is_reported_unresolvable_not_hidden(self):
        self.repo.write(
            "semantics/projection_profiles.yaml",
            LEDGERS["projection_profiles.yaml"].replace(
                "  output:\n    schema: l9.projection.x/v1\n",
                "  output:\n    schema: l9.projection.x/v1\n  forbidden: [no_such_criterion]\n",
            ),
        )
        report = cac.registration(
            cac.Tree(self.repo.root), cac.load_subject(self._subject())
        )
        self.assertIn(
            "no_such_criterion", "\n".join(report["unresolvable_declarations"])
        )


class QualificationGates(_Fixture):
    def test_failing_make_target_stops_at_registered(self):
        for target in cac.MAKE_GATES:
            self.repo.write(f"scripts/make_{target}", "1")
            report = self.verdict()
            self.assertEqual(report["verdict"], "REGISTERED", target)
            self.assertNotEqual(report["make"][target]["exit"], 0)
            self.repo.write(f"scripts/make_{target}", "0")

    def test_release_missing_required_inventory_stops_at_registered(self):
        # The candidate hashes every subject file but omits the ADR index.
        self.repo.release("v1.1.0", CANDIDATE, omit=("./docs/adr/README.md",))
        self.repo.commit("candidate v1.1.0")
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "v1.1.0: HASHES.sha256 omits ./docs/adr/README.md",
            report["release"]["gaps"],
        )

    def test_editing_an_admitted_release_at_head_fails_the_sequence(self):
        self.repo.write(
            "docs/semantic-foundation/v1.0.0/RELEASE_VALIDATION.md", "edited\n"
        )
        self.candidate(commit=False)
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "release v1.0.0 is immutable on main but differs at HEAD",
            report["release"]["gaps"],
        )

    def test_two_new_releases_fail_the_sequence(self):
        self.repo.release("v1.1.0", CANDIDATE)
        self.repo.release("v1.2.0", CANDIDATE)
        report = self.verdict()
        self.assertIn("cut exactly one successor", "\n".join(report["release"]["gaps"]))


class ScopeClosure(_Fixture):
    def add_invariant(self, ident="L9-X-002", statement="y holds"):
        self.repo.write(
            "semantics/invariants.yaml",
            self.repo.read("semantics/invariants.yaml")
            + f"- id: {ident}\n  statement: {statement}\n  scope: global\n  owner: o\n",
        )

    def test_affected_invariant_omitted_from_subject_fails_scope_closure(self):
        self.add_invariant()
        self.repo.write(
            "semantics/vocabulary.yaml",
            LEDGERS["vocabulary.yaml"]
            + "  y_term:\n    semantic_class: concept\n    definition: y\n",
        )
        self.candidate()
        report = self.verdict(self.subject(vocabulary_terms=["y_term"]))
        self.assertEqual(report["verdict"], "REGISTERED", json.dumps(report, indent=1))
        self.assertIn(
            "scope closure: invariants:L9-X-002 is new or changed since the admitted base "
            "but omitted from the subject",
            report["scope"]["gaps"],
        )

    def test_complete_subject_passes_scope_closure(self):
        self.add_invariant()
        self.candidate()
        report = self.verdict(self.subject(invariants=["L9-X-002"]))
        self.assertEqual(
            report["verdict"], "RELEASED_CANDIDATE", json.dumps(report, indent=1)
        )

    def test_contract_referencing_an_unadmitted_invariant_fails_semantic_closure(self):
        self.add_invariant()
        self.repo.write(
            "semantics/contracts.yaml",
            LEDGERS["contracts.yaml"]
            + "- id: l9.contract/y@1\n  purpose: y\n  scope: global\n  owner: o\n"
            "  source_invariants: [L9-X-002]\n",
        )
        self.candidate()
        report = self.verdict(self.subject(contracts=["l9.contract/y@1"]))
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "semantic closure: contracts:l9.contract/y@1 depends on invariants:L9-X-002, "
            "which is neither admitted at the base nor in the subject",
            report["scope"]["gaps"],
        )

    def test_term_silently_redefining_an_admitted_term_fails_semantic_ownership(self):
        self.repo.write(
            "semantics/vocabulary.yaml",
            "terms:\n  x_term:\n    semantic_class: concept\n    definition: not an x\n",
        )
        self.candidate()
        report = self.verdict(self.subject(vocabulary_terms=["x_term"]))
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "semantic ownership: vocabulary_terms:x_term redefines an admitted identity "
            "without a declared revision",
            report["scope"]["gaps"],
        )


class DownstreamQualification(_Fixture):
    def test_pass_with_unresolved_criteria_is_not_downstream_usable(self):
        result = self.downstream("unresolved")
        self.assertEqual(result["status"], "fail")
        arts = result["projections"]["l9.projection/x@1"]["artifacts"]
        self.assertEqual(arts[0]["result"], "pass")
        self.assertTrue(arts[0]["unresolved"])

    def test_pass_without_an_unresolved_list_is_not_downstream_usable(self):
        self.assertEqual(self.downstream("omit-unresolved")["status"], "fail")

    def test_artifact_digest_not_matching_its_file_fails(self):
        result = self.downstream("stale-digest")
        self.assertEqual(result["status"], "fail")
        self.assertIn(
            "projection_digest does not match",
            "\n".join(result["verification"]["gaps"]),
        )

    def test_malformed_nested_payload_fails_the_payload_schema(self):
        result = self.downstream("bad-payload")
        self.assertEqual(result["status"], "fail")
        self.assertIn("payload schema", "\n".join(result["verification"]["gaps"]))

    def test_wrong_source_digest_fails(self):
        result = self.downstream("bad-source-digest")
        self.assertIn(
            "source_digest is not the digest", "\n".join(result["verification"]["gaps"])
        )

    def test_unreadable_receipt_is_never_pass(self):
        result = self.downstream("no-receipt")
        self.assertEqual(result["status"], "fail")
        self.assertIn("receipt", "\n".join(result["verification"]["gaps"]))

    def test_duplicate_component_fails(self):
        result = self.downstream("dup-component")
        self.assertIn("more than once", "\n".join(result["verification"]["gaps"]))

    def test_nondeterministic_producer_fails_replay(self):
        result = self.downstream("nondeterministic")
        self.assertEqual(result["deterministic_replay"]["status"], "fail")
        self.assertEqual(result["status"], "fail")

    def test_dirty_compiler_is_not_an_exact_revision(self):
        engine = fake_compiler(self.tmp, "pass")
        (engine / "src" / "l9_semantic_compiler" / "__init__.py").write_text(
            "# edited\n"
        )
        result = cac.downstream(
            self.repo.root, engine, self.tmp / "out", cac.load_subject(self._subject())
        )
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["compiler"]["dirty"])

    def test_required_compiler_revision_must_match(self):
        engine = fake_compiler(self.tmp, "pass")
        result = cac.downstream(
            self.repo.root,
            engine,
            self.tmp / "out",
            cac.load_subject(self._subject()),
            compiler_revision="HEAD~0",
        )
        self.assertEqual(result["status"], "pass", json.dumps(result, indent=1))

    def test_compiler_without_git_history_is_unresolved(self):
        engine = fake_compiler(self.tmp, "pass")
        shutil.rmtree(engine / ".git")
        with self.assertRaises(cac.InputError):
            cac.downstream(
                self.repo.root,
                engine,
                self.tmp / "out",
                cac.load_subject(self._subject()),
            )


# --------------------------------------------------------------------------- real repository


def _real_prerequisites():
    """The real repository history and producer, or the reason they are unavailable.

    These tests need commits c6ee11d (the v3.28.0 admission) and 9488d8f in this
    repository's object store, an l9-semantic-compiler-engine git checkout
    (L9_SEMANTIC_COMPILER_SRC, else a sibling of this checkout), node for `make test`, and
    PyYAML. A synthetic fixture cannot stand in: the point is the real ADR, release history
    and producer. Absent prerequisites are reported as skips, never as passes.
    """
    here = Path(__file__).resolve().parents[4]
    for sha in ("c6ee11d", "9488d8f", "453701a"):
        if (
            subprocess.run(
                ["git", "-C", str(here), "cat-file", "-e", f"{sha}^{{commit}}"],
                capture_output=True,
                check=False,
            ).returncode
            != 0
        ):
            return None, None, f"commit {sha} is not in {here}"
    engine = Path(
        os.environ.get(
            "L9_SEMANTIC_COMPILER_SRC", here.parent / "l9-semantic-compiler-engine"
        )
    )
    if not (engine / "src" / "l9_semantic_compiler").is_dir():
        return None, None, f"no l9-semantic-compiler-engine checkout at {engine}"
    if shutil.which("node") is None or shutil.which("make") is None:
        return None, None, "make test needs node and make"
    return here, engine, None


class RealRepository(unittest.TestCase):
    """The known admitted pair stays usable; staged candidates are never reported admitted."""

    @classmethod
    def setUpClass(cls):
        cls.here, cls.engine, reason = _real_prerequisites()
        if reason:
            raise unittest.SkipTest(reason)
        cls.tmp = Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def clone_at(self, sha):
        root = self.tmp / f"clone-{sha}"
        if not root.exists():
            subprocess.run(
                ["git", "clone", "-q", str(self.here), str(root)], check=True
            )
            subprocess.run(
                ["git", "-C", str(root), "checkout", "-q", "--detach", sha], check=True
            )
        return root

    def subject(self, **items):
        path = self.tmp / "subject.json"
        path.write_text(json.dumps({"schema": cac.SUBJECT_SCHEMA, **items}))
        return cac.load_subject(path)

    def test_admitted_authority_resolution_pair_is_downstream_usable(self):
        root = self.clone_at("9488d8f")
        report = cac.evaluate(
            root,
            self.subject(
                projection_profiles=["l9.projection/authority-resolution@1"],
                composition_profiles=["l9.compose/authority-resolution@1"],
                schemas=[
                    "authority_resolution_projection.schema.yaml",
                    "authority_resolution_composition.schema.yaml",
                ],
            ),
            "9488d8f",
            self.engine,
            self.tmp / "out",
        )
        self.assertEqual(
            report["verdict"], "DOWNSTREAM_USABLE", json.dumps(report, indent=1)[:4000]
        )
        self.assertEqual(report["admission"]["release"], "v3.28.0")
        self.assertEqual(
            report["admission"]["evidence"]["admitted_semantics_tree"],
            "7c6f35ddc701e6913c78054745e1e2179775299f",
        )
        self.assertEqual(
            report["downstream"]["verification"]["verified_projections"], 4
        )
        self.assertEqual(
            report["downstream"]["verification"]["verified_compositions"], 1
        )

    def test_staged_sv_invariant_is_not_admitted_on_main(self):
        root = self.clone_at("9488d8f")
        report = cac.evaluate(root, self.subject(invariants=["L9-SV-001"]), "9488d8f")
        self.assertEqual(report["verdict"], "INCOMPLETE")

    def test_candidate_only_profile_is_never_admitted_before_its_release(self):
        # 453701a: the v3.28.0 pair qualified as a candidate, before ADR-025 admitted it.
        root = self.clone_at("453701a")
        report = cac.evaluate(
            root,
            self.subject(projection_profiles=["l9.projection/authority-resolution@1"]),
            "453701a",
        )
        self.assertNotIn(report["verdict"], ("ADMITTED", "DOWNSTREAM_USABLE"))
        self.assertEqual(report["admission"]["status"], "fail")


if __name__ == "__main__":
    unittest.main()
