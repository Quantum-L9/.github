#!/usr/bin/env python3
"""Rehearse the source-class dispatch candidate in a DISPOSABLE clone. Never admits.

Dry-run by default: prints the plan and exits. ``--disposable DIR`` clones this
repository into DIR (which must not exist and must lie outside this checkout),
pins it at BASE_SHA, and then, inside that clone only:

  A   applies the overlays under ``overlays/`` to ``semantics/``;
  G1  compiles one candidate source-field grammar per source class of each @2
      pair with the compiler's ``tools/build_schema_grammar_candidate.py``;
  G2  writes each pack's candidate operation, dialect and binding catalog;
  S   runs ``l9-semantic-compiler schema-synthesize`` per pair;
  R   renders registered output schemas with
      ``payload_validation.registered_schema_documents()`` and registers them;
  P   runs the real producer's ``project`` and ``compose`` per synthesized pair.

A, G1, G2 and R are commits made with a fixed identity and fixed dates, so their
ids reproduce from the same inputs. ``--emit`` copies the generated grammar
packs, registrations and evidence back into this checkout; ``--check`` compares
them instead (``*.json`` by parsed content, because the repository formats JSON
with Biome; every other file byte for byte) and exits 1 on any difference.

The compiler is the checkout at ``--compiler-root``; its HEAD must equal
``--compiler-revision`` (default: the revision recorded in MANIFEST.json).

This script never pushes, never opens a pull request, never touches this
checkout's ``semantics/``, and grants no admission, registration or release.
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

import yaml

BASE_SHA = "535400e8c4fb89771c9f08136b4c0309bb5f2a1d"
REPOSITORY = "Quantum-L9/.github"
PACK = Path(__file__).resolve().parent
PACK_REL = "docs/candidates/source-class-dispatch-v2"
PAIRS = ("identity-assurance", "strategic-planning-context", "strategic-metacognition")
IDENTITY = {
    "GIT_AUTHOR_NAME": "l9-candidate-rehearsal",
    "GIT_AUTHOR_EMAIL": "l9-candidate-rehearsal@invalid",
    "GIT_COMMITTER_NAME": "l9-candidate-rehearsal",
    "GIT_COMMITTER_EMAIL": "l9-candidate-rehearsal@invalid",
    "GIT_AUTHOR_DATE": "2026-11-08T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-11-08T00:00:00+00:00",
}


def _run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    env: dict | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        check=check,
    )


def _git(root: Path, *args: str) -> str:
    return _run(["git", "-C", str(root), *args], env=IDENTITY).stdout.strip()


def _commit(root: Path, message: str, *paths: str) -> str:
    _git(root, "add", "--", *paths)
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _yaml_load(path: Path) -> Any:
    return yaml.safe_load(path.read_text("utf-8"))


def _yaml_dump(path: Path, document: Any) -> None:
    path.write_text(
        yaml.safe_dump(document, sort_keys=False, width=100, allow_unicode=True),
        encoding="utf-8",
    )


def _repo_root() -> Path:
    return Path(
        _run(["git", "-C", str(PACK), "rev-parse", "--show-toplevel"]).stdout.strip()
    )


def _manifest() -> dict[str, Any]:
    return json.loads((PACK / "MANIFEST.json").read_text("utf-8"))


# -- A: overlays ------------------------------------------------------------------------------


def apply_overlays(root: Path) -> None:
    overlays = PACK / "overlays"
    sem = root / "semantics"
    pp = _yaml_load(sem / "projection_profiles.yaml")
    pp["projection_profiles"].extend(
        _yaml_load(overlays / "projection_profile_additions.yaml")["records"]
    )
    pp["validation_rules"].extend(
        _yaml_load(overlays / "projection_rule_additions.yaml")["records"]
    )
    _yaml_dump(sem / "projection_profiles.yaml", pp)
    cp = _yaml_load(sem / "composition_profiles.yaml")
    cp["profiles"].extend(
        _yaml_load(overlays / "composition_profile_additions.yaml")["records"]
    )
    cp["global_rules"].update(
        _yaml_load(overlays / "composition_global_rule_additions.yaml")["records"]
    )
    _yaml_dump(sem / "composition_profiles.yaml", cp)
    vocabulary = _yaml_load(sem / "vocabulary.yaml")
    vocabulary["terms"].update(
        _yaml_load(overlays / "vocabulary_additions.yaml")["records"]
    )
    _yaml_dump(sem / "vocabulary.yaml", vocabulary)


# -- G1, G2, S: compiler-driven ---------------------------------------------------------------


def _pack_dir(name: str) -> str:
    return f"docs/candidates/schema-grammar-{name}-v2"


def _compiler_env(compiler: Path) -> dict[str, str]:
    """Import the compiler from the pinned checkout, never from whatever is installed.

    An interpreter whose environment has the compiler installed (an editable
    install of another checkout, for example) would otherwise execute that code
    instead of ``--compiler-root``. PYTHONPATH precedes site-packages.
    """
    return {"PYTHONPATH": str(compiler / "src")}


_CLI = "import sys; from l9_semantic_compiler.cli import main; sys.exit(main(sys.argv[1:]))"
_WHERE = "import l9_semantic_compiler as m; print(m.__file__)"


def _tool(compiler: Path, python: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [str(python), str(compiler / "tools/build_schema_grammar_candidate.py"), *args],
        env=_compiler_env(compiler),
        check=False,
    )


def _cli(
    compiler: Path, python: Path, *args: str, check: bool = False
) -> subprocess.CompletedProcess[str]:
    return _run(
        [str(python), "-c", _CLI, *args], env=_compiler_env(compiler), check=check
    )


def _require_pinned_compiler(compiler: Path, python: Path) -> str:
    """Fail closed unless subprocesses and this process both import the pinned code."""
    expected = (compiler / "src/l9_semantic_compiler/__init__.py").resolve()
    executed = Path(
        _run([str(python), "-c", _WHERE], env=_compiler_env(compiler)).stdout.strip()
    ).resolve()
    if executed != expected:
        raise SystemExit(
            f"refusing: compiler subprocess imports {executed}, not {expected}"
        )
    sys.path.insert(0, str(compiler / "src"))
    import l9_semantic_compiler

    if Path(l9_semantic_compiler.__file__).resolve() != expected:
        raise SystemExit(
            f"refusing: rehearsal imports {l9_semantic_compiler.__file__}, not {expected}"
        )
    return "src/l9_semantic_compiler/__init__.py"


def _executable_digest(compiler: Path, revision: str) -> str:
    archive = subprocess.run(
        ["git", "-C", str(compiler), "archive", revision, "src"],
        capture_output=True,
        check=True,
    ).stdout
    import hashlib

    return "sha256:" + hashlib.sha256(archive).hexdigest()


def _deterministic_tar(members: dict[str, bytes]) -> bytes:
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name in sorted(members):
            info = tarfile.TarInfo(name)
            info.size = len(members[name])
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(members[name]))
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0, filename="") as gz:
        gz.write(raw.getvalue())
    return out.getvalue()


def _clone_at_base(dest: Path) -> None:
    source = _repo_root()
    _run(
        [
            "git",
            "clone",
            "-q",
            "--no-checkout",
            "--no-hardlinks",
            str(source),
            str(dest),
        ]
    )
    _git(dest, "checkout", "-q", "--detach", BASE_SHA)


def _new_report(compiler: Path, revision: str) -> dict[str, Any]:
    return {
        "schema": "l9.candidate-rehearsal/source-class-dispatch-v2",
        "admission": "not_granted",
        "base": {"repository": REPOSITORY, "revision": BASE_SHA},
        "compiler": {
            "repository": "Quantum-L9/l9-semantic-compiler-engine",
            "revision": revision,
            "executable_digest": _executable_digest(compiler, revision),
            "executable_digest_basis": "sha256 of git archive <revision> src",
        },
        "commits": {},
        "pairs": {},
    }


def _draft_grammars(
    dest: Path, compiler: Path, python: Path, authority: str, report: dict[str, Any]
) -> None:
    """G1 inputs: one candidate grammar per source class of each pair."""
    for name in PAIRS:
        proc = _tool(
            compiler,
            python,
            "grammars",
            "--github-root",
            str(dest),
            "--authority-revision",
            authority,
            "--projection",
            f"l9.projection/{name}@2",
            "--composition",
            f"l9.compose/{name}@2",
        )
        if proc.returncode not in (0, 3):
            raise SystemExit(f"grammars failed for {name}: {proc.stderr[-600:]}")
        draft = _yaml_load(dest / _pack_dir(name) / "grammar-draft-report.yaml")
        report["pairs"][name] = {
            "grammars_written": len(draft["written"]),
            "inexpressible": draft["inexpressible"],
            "grammars_exit": proc.returncode,
        }


def _write_catalogs(dest: Path, compiler: Path, python: Path, grammars: str) -> None:
    """G2 inputs: each pack's candidate operation, dialect and binding catalog."""
    for name in PAIRS:
        proc = _tool(
            compiler,
            python,
            "catalog",
            "--github-root",
            str(dest),
            "--pack-dir",
            _pack_dir(name),
            "--grammar-revision",
            grammars,
        )
        if proc.returncode:
            raise SystemExit(f"catalog failed for {name}: {proc.stderr[-400:]}")


def _synthesis_entry(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if result.returncode == 0:
        return {"synthesis_exit": 0, "synthesis": "candidate_pair_produced"}
    diagnostic = (
        json.loads(result.stdout)
        if result.stdout.strip().startswith("{")
        else {"stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]}
    )
    return {
        "synthesis_exit": result.returncode,
        "synthesis": "BLOCKED",
        "synthesis_diagnostic": diagnostic,
    }


def _synthesize(
    dest: Path,
    compiler: Path,
    python: Path,
    governance: str,
    report: dict[str, Any],
    work: Path,
) -> tuple[list[str], dict[str, bytes]]:
    """S: pinned request and schema-synthesize per pair; a failure is recorded, never hidden."""
    members: dict[str, bytes] = {}
    synthesized: list[str] = []
    for name in PAIRS:
        request = work / f"request-{name}.yaml"
        proc = _tool(
            compiler,
            python,
            "request",
            "--github-root",
            str(dest),
            "--pack-dir",
            _pack_dir(name),
            "--governance-revision",
            governance,
            "--compiler-revision",
            report["compiler"]["revision"],
            "--compiler-executable-digest",
            report["compiler"]["executable_digest"],
            "--output",
            str(request),
        )
        if proc.returncode:
            raise SystemExit(f"request failed for {name}: {proc.stderr[-400:]}")
        text = request.read_text("utf-8").replace(str(dest), "<disposable>")
        members[f"request-{name}.yaml"] = text.encode()
        result = _cli(compiler, python, "schema-synthesize", str(request))
        report["pairs"][name].update(_synthesis_entry(result))
        if result.returncode == 0:
            (work / f"pair-{name}.json").write_text(result.stdout, encoding="utf-8")
            members[f"pair-{name}.json"] = result.stdout.encode()
            synthesized.append(name)
    return synthesized, members


def _register(dest: Path, synthesized: list[str], work: Path) -> dict[str, bytes]:
    """R inputs: rendered registrations, registered in the rehearsal clone only."""
    from l9_semantic_compiler.passes.payload_validation import (
        registered_schema_documents,
    )

    registered: dict[str, bytes] = {}
    manifest_path = dest / "semantics/generic_compiler_manifest.yaml"
    manifest = _yaml_load(manifest_path)
    for name in synthesized:
        pair = json.loads((work / f"pair-{name}.json").read_text("utf-8"))
        documents = registered_schema_documents(
            pair,
            owner=REPOSITORY,
            projection_artifact_id=f"l9.schema/{name}-projection@2",
            composition_artifact_id=f"l9.schema/{name}-composition@2",
        )
        for kind, document in zip(("projection", "composition"), documents):
            # canonical: true only so the rehearsal's CanonicalAuthority can load it;
            # admission stays not_granted and nothing registers it on main.
            document = {"canonical": True, **document}
            filename = f"{name.replace('-', '_')}_{kind}_v2.schema.yaml"
            raw = yaml.safe_dump(
                document, sort_keys=False, width=100, allow_unicode=True
            ).encode()
            (dest / "semantics" / filename).write_bytes(raw)
            manifest["requires"]["artifact_schemas"].append(filename)
            registered[filename] = raw
    _yaml_dump(manifest_path, manifest)
    return registered


def rehearse(dest: Path, compiler: Path, revision: str, python: Path) -> dict[str, Any]:
    executed = _require_pinned_compiler(compiler, python)
    _clone_at_base(dest)
    report = _new_report(compiler, revision)
    report["compiler"]["executed_module"] = executed
    commits = report["commits"]
    apply_overlays(dest)
    commits["A_overlays_applied"] = _commit(
        dest, "rehearsal A: apply candidate overlays (not admitted)", "semantics"
    )
    _draft_grammars(dest, compiler, python, commits["A_overlays_applied"], report)
    commits["G1_grammars"] = _commit(
        dest, "rehearsal G1: candidate source-field grammars", "docs/candidates"
    )
    _write_catalogs(dest, compiler, python, commits["G1_grammars"])
    commits["G2_catalog"] = _commit(
        dest,
        "rehearsal G2: candidate operation, dialect and binding catalog",
        "docs/candidates",
    )
    work = dest / ".rehearsal"
    work.mkdir()
    synthesized, synthesis_members = _synthesize(
        dest, compiler, python, commits["G2_catalog"], report, work
    )
    report["synthesis_archive"] = "evidence/synthesis.tar.gz"
    registered = _register(dest, synthesized, work)
    commits["R_registrations"] = _commit(
        dest, "rehearsal R: register rendered candidate output schemas", "semantics"
    )
    producer_members: dict[str, bytes] = {}
    for name in synthesized:
        report["pairs"][name]["producer"] = _produce(
            dest,
            commits["R_registrations"],
            name,
            lambda *args: _cli(compiler, python, *args),
            work,
            producer_members,
        )
    report["producer_archive"] = "evidence/producer.tar.gz"
    shutil.rmtree(work)
    return {
        "report": report,
        "registered": registered,
        "synthesis_tar": _deterministic_tar(synthesis_members),
        "producer_tar": _deterministic_tar(producer_members),
    }


def _produce(
    root: Path,
    revision: str,
    name: str,
    cli: Any,
    work: Path,
    members: dict[str, bytes],
) -> dict[str, Any]:
    spec = {"repository": REPOSITORY, "root": str(root), "revision": revision}
    located = cli(
        "projection-coordinates",
        "--authority-root",
        str(root),
        "--revision",
        revision,
        "--repository",
        REPOSITORY,
        "--profile",
        f"l9.projection/{name}@2",
    )
    if located.returncode:
        raise SystemExit(
            f"projection-coordinates failed for {name}: {located.stderr[-400:]}"
        )
    coords = yaml.safe_load(located.stdout)
    out = work / f"producer-{name}"
    request = work / f"project-{name}.json"
    request.write_text(
        json.dumps(
            {
                "schema": "l9.semantic-projection-request/v1",
                "authority": spec,
                "projection_profile": coords["projection_profile"],
                "sources": coords["sources"],
                "output_root": str(out / "projections"),
            }
        )
    )
    project = cli("project", str(request))
    artifacts = sorted((out / "projections").rglob("*.projection.json"))
    profile = _composition_coordinate(root, revision, name)
    request = work / f"compose-{name}.json"
    request.write_text(
        json.dumps(
            {
                "schema": "l9.semantic-composition-request/v1",
                "authority": spec,
                "composition_profile": profile,
                "components": [str(p) for p in artifacts],
                "output_root": str(out / "composed"),
            }
        )
    )
    compose = cli("compose", str(request))
    summary: dict[str, Any] = {
        "project_exit": project.returncode,
        "compose_exit": compose.returncode,
        "receipts": {},
    }
    for path in sorted(out.rglob("*.json")):
        members[f"{name}/{path.relative_to(out)}"] = path.read_bytes()
        if path.parent.name != "receipts":
            continue
        receipt = json.loads(path.read_text("utf-8"))
        basis = receipt["verification_basis"]
        criterion = basis["criteria"].get("payload_schema", {})
        summary["receipts"][receipt["exact_subject_ref"]] = {
            "operation": receipt["operation"],
            "result": receipt["result"],
            "coverage": basis["coverage"],
            "unresolved_criteria": basis["unresolved_criteria"],
            "selection_equivalence": basis["criteria"]
            .get("selection_equivalence", {})
            .get("status"),
            "payload_schema": criterion.get("status"),
            "payload_schema_id": criterion.get("schema"),
            "dispatch_basis": criterion.get("dispatch_basis"),
        }
    for path in artifacts:
        artifact = json.loads(path.read_text("utf-8"))
        payload = artifact["payload"]
        ref = f"l9.projection/{name}@2#{artifact['source_ref']}"
        summary["receipts"].setdefault(ref, {})["payload_schema_field"] = (
            payload.get("schema") if isinstance(payload, dict) else None
        )
    return summary


def _composition_coordinate(root: Path, revision: str, name: str) -> dict[str, str]:
    from l9_semantic_compiler.engine.registry import CanonicalAuthority

    profile = CanonicalAuthority(root, revision, repository=REPOSITORY).resolve_profile(
        f"l9.compose/{name}@2"
    )
    return {"ref": profile.ref, "digest": profile.digest}


# -- emit / check -----------------------------------------------------------------------------


def _outputs(dest: Path, result: dict[str, Any]) -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for name in PAIRS:
        pack = dest / _pack_dir(name)
        for path in sorted(p for p in pack.rglob("*") if p.is_file()):
            outputs[str(path.relative_to(dest))] = path.read_bytes()
    for filename, raw in result["registered"].items():
        outputs[f"{PACK_REL}/overlays/registered_schemas/{filename}"] = raw
    outputs[f"{PACK_REL}/evidence/rehearsal.json"] = (
        json.dumps(result["report"], indent="\t", sort_keys=True) + "\n"
    ).encode()
    outputs[f"{PACK_REL}/evidence/synthesis.tar.gz"] = result["synthesis_tar"]
    outputs[f"{PACK_REL}/evidence/producer.tar.gz"] = result["producer_tar"]
    return outputs


def _same(rel: str, expected: bytes, observed: bytes) -> bool:
    if rel.endswith(".json"):
        return json.loads(expected) == json.loads(observed)
    return expected == observed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--disposable", type=Path, help="new directory outside this checkout"
    )
    parser.add_argument("--compiler-root", type=Path)
    parser.add_argument("--compiler-revision")
    parser.add_argument(
        "--compiler-python", type=Path, help="default: <compiler-root>/.venv/bin/python"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser


def _disposable(repo: Path, requested: Path) -> Path:
    dest = requested.resolve()
    if dest.exists():
        raise SystemExit(f"refusing: {dest} exists; the disposable clone must be new")
    if dest == repo or repo in dest.parents:
        raise SystemExit(
            "refusing: the disposable clone must lie outside this checkout"
        )
    return dest


def _pinned_compiler(args: argparse.Namespace) -> tuple[Path, str, Path]:
    if args.compiler_root is None:
        raise SystemExit("--compiler-root is required")
    compiler = args.compiler_root.resolve()
    revision = args.compiler_revision or _manifest()["compiler"]["revision"]
    head = _run(["git", "-C", str(compiler), "rev-parse", "HEAD"]).stdout.strip()
    if head != revision:
        raise SystemExit(
            f"refusing: compiler HEAD {head} != pinned revision {revision}"
        )
    # absolute(), not resolve(): resolving the venv symlink would leave the venv.
    python = (args.compiler_python or compiler / ".venv/bin/python").absolute()
    return compiler, revision, python


def _emit(repo: Path, outputs: dict[str, bytes]) -> int:
    for rel, raw in outputs.items():
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    print(f"emitted {len(outputs)} files")
    return 0


def _check(repo: Path, outputs: dict[str, bytes]) -> int:
    differing = [
        rel
        for rel, raw in outputs.items()
        if not (repo / rel).is_file() or not _same(rel, (repo / rel).read_bytes(), raw)
    ]
    for rel in differing:
        print(f"DIFF {rel}")
    print(f"checked {len(outputs)} files, {len(differing)} differing")
    return 1 if differing else 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.disposable is None:
        print(__doc__)
        print(f"dry run: base {BASE_SHA}; pairs {', '.join(PAIRS)}; nothing written")
        return 0
    repo = _repo_root().resolve()
    dest = _disposable(repo, args.disposable)
    compiler, revision, python = _pinned_compiler(args)
    result = rehearse(dest, compiler, revision, python)
    outputs = _outputs(dest, result)
    if args.emit:
        return _emit(repo, outputs)
    if args.check:
        return _check(repo, outputs)
    print(json.dumps(result["report"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
