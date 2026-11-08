"""Admission-closure gate for new Quantum-L9/.github semantics.

Walks one subject (new invariants, vocabulary terms, contracts, canonical sources, source
classes, projection profiles, composition profiles, payload schemas) up a fixed ladder and
reports the highest rung every lower rung supports:

  INCOMPLETE          a subject item is missing from a registration surface at HEAD
  REGISTERED          registered at HEAD, but the native validator fails or the highest
                      release record does not cover the subject's files at their current bytes
  RELEASED_CANDIDATE  validator passes and the highest release record covers the subject,
                      but no admitted release covers it unchanged on main and at HEAD
  ADMITTED            the commit that admitted a release (status line flipped to ADMITTED,
                      ADR accepted for exactly that version) is on main, that release's record
                      is unedited since, it covered the subject, and the subject's records and
                      ledger bytes are identical at admission, on main and at HEAD
  DOWNSTREAM_USABLE   ADMITTED, the subject names at least one profile, and the real compiler
                      projects every subject projection profile over exactly its pinned sources
                      and composes every subject composition profile to PASS at a clean
                      checkout whose HEAD is main

UNRESOLVED (exit 2) means an input, a git read or the compiler's output could not be read or
was malformed; it is never reported as a rung.

Usage:
  python3 check_admission_closure.py --checkout REPO --subject SUBJECT.json
      [--require registered|released|admitted|downstream]
      [--compiler-src ENGINE_CHECKOUT --output-root DIR] [--main-ref origin/main]

Exit codes: 0 the verdict reached --require, 1 it did not, 2 UNRESOLVED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
ADMITTED_STATUS = re.compile(r"^Status:\s*\*\*ADMITTED\b[^*]*\*\*")


class InputError(Exception):
    """A required input is missing, unreadable or malformed: UNRESOLVED, never a rung."""


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
            if not path.exists():
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
        try:
            value = yaml.safe_load(data)
        except yaml.YAMLError as exc:
            raise InputError(f"{self.label()}:{rel} is not YAML: {exc}") from exc
        if not isinstance(value, dict):
            raise InputError(f"{self.label()}:{rel} is not a mapping")
        return value


def digest(value: Any) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- subject


def load_subject(path: Path) -> dict[str, list[str]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise InputError(f"unreadable subject {path}: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema") != SUBJECT_SCHEMA:
        raise InputError(f"subject must declare schema {SUBJECT_SCHEMA}")
    unknown = sorted(set(raw) - {"schema", "description", *ITEM_KINDS})
    if unknown:
        raise InputError(f"subject has unknown keys {unknown}")
    subject: dict[str, list[str]] = {}
    for kind in ITEM_KINDS:
        items = raw.get(kind, [])
        if not isinstance(items, list) or not all(
            isinstance(i, str) and i for i in items
        ):
            raise InputError(f"subject.{kind} must be a list of non-empty strings")
        if len(set(items)) != len(items):
            raise InputError(f"subject.{kind} repeats an item")
        subject[kind] = items
    if not any(subject.values()):
        raise InputError("subject names no items")
    return subject


def _sources(tree: Tree) -> dict[str, dict[str, Any]]:
    entries = tree.yaml("semantics/canonical_sources.yaml").get("sources") or []
    return {e["id"]: e for e in entries if isinstance(e, dict) and "id" in e}


def _class_artifacts(tree: Tree) -> dict[str, str]:
    classes = (
        tree.yaml("semantics/projection_profiles.yaml").get("source_classes") or {}
    )
    return {
        cls: f"semantics/{decl['canonical_artifact']}"
        for cls, decl in classes.items()
        if isinstance(decl, dict) and isinstance(decl.get("canonical_artifact"), str)
    }


def subject_files(tree: Tree, subject: dict[str, list[str]]) -> list[str]:
    """Every semantics/ file whose bytes carry a subject item."""
    files = {f"semantics/{KIND_LEDGER[k]}" for k, items in subject.items() if items}
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


def _schema_consts(tree: Tree, artifact_schemas: list[str]) -> dict[str, str]:
    """output.schema value -> registered schema file whose properties.schema.const declares it."""
    consts: dict[str, str] = {}
    for name in artifact_schemas:
        data = tree.read(f"semantics/{name}")
        if data is None:
            continue
        try:
            doc = yaml.safe_load(data)
        except yaml.YAMLError as exc:
            raise InputError(
                f"{tree.label()}:semantics/{name} is not YAML: {exc}"
            ) from exc
        const = (((doc or {}).get("properties") or {}).get("schema") or {}).get("const")
        if isinstance(const, str):
            consts[const] = name
    return consts


def registration(tree: Tree, subject: dict[str, list[str]]) -> dict[str, Any]:
    """Every subject item registered on every surface it needs, in one tree.

    ``records`` captures what admission must keep identical: each item's record and the
    bytes of each file that is itself a subject item (model ledgers, schemas).
    """
    gaps: list[str] = []
    records: dict[str, Any] = {}
    invariant_entries = tree.yaml("semantics/invariants.yaml").get("invariants") or []
    terms = tree.yaml("semantics/vocabulary.yaml").get("terms") or {}
    contracts = tree.yaml("semantics/contracts.yaml").get("contracts") or []
    sources = _sources(tree)
    profiles_doc = tree.yaml("semantics/projection_profiles.yaml")
    classes = profiles_doc.get("source_classes") or {}
    projections = profiles_doc.get("projection_profiles") or []
    compositions = (
        tree.yaml("semantics/composition_profiles.yaml").get("profiles") or []
    )
    requires = (
        tree.yaml("semantics/generic_compiler_manifest.yaml").get("requires") or {}
    )
    artifact_schemas = list(requires.get("artifact_schemas") or [])
    catalogs = set(requires.get("semantic_catalogs") or [])
    consts = _schema_consts(tree, artifact_schemas)

    def unique(kind: str, ident: str, entries: list[Any]) -> dict[str, Any] | None:
        found = [e for e in entries if isinstance(e, dict) and e.get("id") == ident]
        if len(found) != 1:
            gaps.append(f"{kind} {ident}: defined {len(found)} times")
            return None
        records[f"{kind}:{ident}"] = found[0]
        return found[0]

    def file_record(key: str, rel: str) -> bool:
        data = tree.read(rel)
        if data is None:
            return False
        records[key] = sha_bytes(data)
        return True

    for ident in subject["invariants"]:
        unique("invariant", ident, invariant_entries)
    for term in subject["vocabulary_terms"]:
        if term not in terms:
            gaps.append(f"vocabulary term {term}: absent from vocabulary.yaml terms")
        else:
            records[f"term:{term}"] = terms[term]
    for ident in subject["contracts"]:
        unique("contract", ident, contracts)
    for ref in subject["canonical_sources"]:
        entry = sources.get(ref)
        if entry is None:
            gaps.append(
                f"canonical source {ref}: not registered in canonical_sources.yaml"
            )
            continue
        records[f"source:{ref}"] = entry
        path = entry.get("path")
        if not isinstance(path, str) or not file_record(f"source_file:{ref}", path):
            gaps.append(f"canonical source {ref}: path {path} does not exist")
        elif Path(path).name not in catalogs:
            gaps.append(
                f"canonical source {ref}: {Path(path).name} not in semantic_catalogs"
            )
        if entry.get("projection_allowed") is not True:
            gaps.append(f"canonical source {ref}: projection_allowed is not true")
    for cls in subject["source_classes"]:
        decl = classes.get(cls)
        artifact = (decl or {}).get("canonical_artifact")
        if not artifact:
            gaps.append(
                f"source class {cls}: not declared in projection_profiles source_classes"
            )
            continue
        records[f"source_class:{cls}"] = decl
        rel = f"semantics/{artifact}"
        if not any(e.get("path") == rel for e in sources.values()):
            gaps.append(f"source class {cls}: {rel} is not a registered source")
        elif not file_record(f"source_class_file:{cls}", rel):
            gaps.append(f"source class {cls}: {rel} does not exist")
    for ref in subject["projection_profiles"]:
        profile = unique("projection profile", ref, projections)
        if profile is None:
            continue
        for cls in profile.get("sources") or {}:
            if cls not in classes:
                gaps.append(f"projection profile {ref}: source class {cls} undeclared")
        schema = (profile.get("output") or {}).get("schema")
        if schema not in consts:
            gaps.append(
                f"projection profile {ref}: no registered schema declares {schema}"
            )
    for ref in subject["composition_profiles"]:
        profile = unique("composition profile", ref, compositions)
        if profile is None:
            continue
        composes = (profile.get("composes") or {}).get("projection_profile")
        if composes not in _ids(projections):
            gaps.append(
                f"composition profile {ref}: composes unknown profile {composes}"
            )
        schema = (profile.get("output") or {}).get("schema")
        if schema not in consts:
            gaps.append(
                f"composition profile {ref}: no registered schema declares {schema}"
            )
    for name in subject["schemas"]:
        if name not in artifact_schemas:
            gaps.append(
                f"schema {name}: not in generic_compiler_manifest artifact_schemas"
            )
        if not file_record(f"schema:{name}", f"semantics/{name}"):
            gaps.append(f"schema {name}: semantics/{name} does not exist")
        elif name not in consts.values():
            gaps.append(f"schema {name}: no properties.schema.const declared")
    return {"status": "pass" if not gaps else "fail", "gaps": gaps, "records": records}


# --------------------------------------------------------------------------- releases


def release_versions(tree: Tree) -> list[str]:
    names = [n for n in tree.listdir(RELEASES) if VERSION_DIR.match(n)]
    return sorted(
        names, key=lambda n: tuple(int(x) for x in VERSION_DIR.match(n).groups())
    )


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
            if pattern.match(line):
                return name
    return None


def release_coverage(tree: Tree, version: str, files: list[str]) -> dict[str, Any]:
    gaps: list[str] = []
    manifest_raw = tree.read(f"{RELEASES}/{version}/MANIFEST.md")
    hashes_raw = tree.read(f"{RELEASES}/{version}/HASHES.sha256")
    if manifest_raw is None or hashes_raw is None:
        return {
            "status": "fail",
            "gaps": [f"{version}: MANIFEST.md or HASHES.sha256 missing"],
        }
    manifest = manifest_raw.decode("utf-8", "replace")
    hashes: dict[str, str] = {}
    for line in hashes_raw.decode("utf-8", "replace").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2:
            hashes[parts[1].strip().removeprefix("./")] = parts[0]
    for rel in files:
        if f"`{rel}`" not in manifest:
            gaps.append(f"{version}: MANIFEST.md does not list `{rel}`")
        data = tree.read(rel)
        if rel not in hashes:
            gaps.append(f"{version}: HASHES.sha256 has no entry for {rel}")
        elif data is None or sha_bytes(data) != hashes[rel]:
            gaps.append(f"{version}: {rel} bytes differ from the release hash")
    return {"status": "pass" if not gaps else "fail", "gaps": gaps}


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
    """Highest admitted release on main that covered the subject, and currentness."""
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
        commit = admission_commit(repo, main.ref, version)
        entry["admission_commit"] = commit
        if commit is None:
            entry["reason"] = "no commit on main flips this release to ADMITTED"
            continue
        later = git_out(
            repo,
            "log",
            "--format=%H",
            f"{commit}..{main.ref}",
            "--",
            f"{RELEASES}/{version}",
        )
        if later:
            entry["reason"] = f"release record edited after admission: {later.split()}"
            continue
        at_release = Tree(repo, commit)
        reg = registration(at_release, subject)
        if reg["status"] != "pass":
            entry["registered_at_admission"] = False
            continue
        coverage = release_coverage(
            at_release, version, subject_files(at_release, subject)
        )
        entry["release_coverage"] = coverage
        if coverage["status"] != "pass":
            continue
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
    return [
        {
            "ref": a.get("ref"),
            "result": a.get("result"),
            "path": a.get("path"),
            "unresolved": a.get("unresolved_criteria") or [],
        }
        for a in arts
    ]


def _request_path(output_root: Path, ref: str, kind: str) -> Path:
    path = (
        output_root
        / "requests"
        / (re.sub(r"[^A-Za-z0-9_.-]", "_", ref) + f".{kind}.yaml")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def downstream(
    repo: Path, compiler_src: Path, output_root: Path, subject: dict[str, list[str]]
) -> dict[str, Any]:
    """Run the real compiler at the checkout's HEAD; every artifact must PASS."""
    if not subject["projection_profiles"] and not subject["composition_profiles"]:
        return {
            "status": "not_applicable",
            "reason": "the subject names no profile to compile",
        }
    if not (compiler_src / "src" / "l9_semantic_compiler").is_dir():
        raise InputError(
            f"{compiler_src} is not an l9-semantic-compiler-engine checkout"
        )
    if git_out(repo, "status", "--porcelain", "--untracked-files=no"):
        return {
            "status": "fail",
            "reason": "checkout has tracked changes; compile a clean revision",
        }
    revision = git_out(repo, "rev-parse", "HEAD")
    authority = {"repository": REPOSITORY, "root": str(repo), "revision": revision}
    output_root.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {"projections": {}, "compositions": {}}
    produced: dict[str, list[str]] = {}
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
            and all(a["result"] == "pass" for a in arts)
        )
        failed |= not ok
        produced[ref] = [a["path"] for a in arts if a["path"]]
        results["projections"][ref] = {
            "exit": done.returncode,
            "result": doc.get("result"),
            "covers_pinned_sources": covered,
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
        components = produced.get(composes or "")
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
            and arts[0]["result"] == "pass"
        )
        failed |= not ok
        results["compositions"][ref] = {
            "exit": done.returncode,
            "result": doc.get("result"),
            "artifacts": arts,
        }
    return {"status": "fail" if failed else "pass", "revision": revision, **results}


# --------------------------------------------------------------------------- verdict


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


def evaluate(
    repo: Path,
    subject: dict[str, list[str]],
    main_ref: str,
    compiler_src: Path | None = None,
    output_root: Path | None = None,
) -> dict[str, Any]:
    head = Tree(repo)
    main_revision = resolve_commit(repo, main_ref)
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "repository": REPOSITORY,
        "head": git_out(repo, "rev-parse", "HEAD"),
        "main_ref": main_ref,
        "main_revision": main_revision,
        "subject": subject,
    }
    reg = registration(head, subject)
    report["registration"] = {"status": reg["status"], "gaps": reg["gaps"]}
    verdict = "INCOMPLETE"
    if reg["status"] == "pass":
        verdict = "REGISTERED"
        report["validator"] = run_validator(repo)
        versions = release_versions(head)
        if not versions:
            raise InputError(f"no release directory under {RELEASES}")
        highest = versions[-1]
        report["release"] = {
            "version": highest,
            "release_status": release_status(head, highest),
            **release_coverage(head, highest, subject_files(head, subject)),
        }
        if (
            report["validator"]["status"] == "pass"
            and report["release"]["status"] == "pass"
        ):
            verdict = "RELEASED_CANDIDATE"
            report["admission"] = admission(repo, main_ref, subject, reg["records"])
            if report["admission"]["status"] == "pass":
                verdict = "ADMITTED"
    if compiler_src is not None:
        if output_root is None:
            raise InputError("--compiler-src needs --output-root")
        report["downstream"] = downstream(repo, compiler_src, output_root, subject)
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
            args.compiler_src,
            args.output_root,
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
