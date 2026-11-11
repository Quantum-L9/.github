#!/usr/bin/env python3
"""Rehearse the eight v1 domain pairs with the pinned compiler; never admits anything.

Clones this repository into a disposable directory at BASE_SHA (the commit that
carries the domain profiles but no payload schemas), then, with the compiler
imported only from --compiler-root:

  G1  drafts one candidate source-field grammar per source class of each pair;
  G2  writes each pack's candidate operation, dialect and binding catalog;
  S   pins a request and runs schema-synthesize per pair;
  R   renders the registered output schemas with
      payload_validation.registered_schema_documents() and registers them;
  P   projects and composes every pair twice from the R commit and records
      whether the two runs are byte-identical.

A failure is recorded in the report, never hidden. `--emit` writes the grammar
packs, the registered schemas (into semantics/ and the compiler manifest) and
the evidence; `--check` compares a fresh rehearsal with what is committed.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
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

BASE_SHA = "c2185b0"
REPOSITORY = "Quantum-L9/.github"
PACK = Path(__file__).resolve().parent
PACK_REL = "docs/candidates/domain-projection-architecture-v1"
COMPILER_REVISION = "eeac5d28f9f1a44e72287190b9087d06aeb4d574"
PAIRS = (
    "architecture",
    "strategic-value",
    "signals",
    "governance",
    "evidence-provenance",
    "contracts-conformance",
    "capabilities-dependencies",
    "identity-attribution",
)
IDENTITY = {
    "GIT_AUTHOR_NAME": "l9-candidate-rehearsal",
    "GIT_AUTHOR_EMAIL": "l9-candidate-rehearsal@invalid",
    "GIT_COMMITTER_NAME": "l9-candidate-rehearsal",
    "GIT_COMMITTER_EMAIL": "l9-candidate-rehearsal@invalid",
    "GIT_AUTHOR_DATE": "2026-11-11T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-11-11T00:00:00+00:00",
}
_CLI = "import sys; from l9_semantic_compiler.cli import main; sys.exit(main(sys.argv[1:]))"
_WHERE = "import l9_semantic_compiler as m; print(m.__file__)"


def _run(
    cmd: list[str], *, env: dict | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
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


def _pack_dir(name: str) -> str:
    return f"docs/candidates/schema-grammar-domain-{name}"


def _schema_file(name: str, kind: str) -> str:
    return f"domain_{name.replace('-', '_')}_{kind}.schema.yaml"


def _env(compiler: Path) -> dict[str, str]:
    return {"PYTHONPATH": str(compiler / "src")}


def _tool(compiler: Path, python: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(
        [str(python), str(compiler / "tools/build_schema_grammar_candidate.py"), *args],
        env=_env(compiler),
        check=False,
    )


def _cli(compiler: Path, python: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run([str(python), "-c", _CLI, *args], env=_env(compiler), check=False)


def _require_pinned_compiler(compiler: Path, python: Path) -> str:
    expected = (compiler / "src/l9_semantic_compiler/__init__.py").resolve()
    executed = Path(
        _run([str(python), "-c", _WHERE], env=_env(compiler)).stdout.strip()
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


def _repo_root() -> Path:
    return Path(
        _run(["git", "-C", str(PACK), "rev-parse", "--show-toplevel"]).stdout.strip()
    )


def _clone_at_base(dest: Path) -> str:
    _run(
        [
            "git",
            "clone",
            "-q",
            "--no-checkout",
            "--no-hardlinks",
            str(_repo_root()),
            str(dest),
        ]
    )
    _git(dest, "checkout", "-q", "--detach", BASE_SHA)
    return _git(dest, "rev-parse", "HEAD")


def _draft_grammars(
    dest: Path, compiler: Path, python: Path, authority: str, report: dict[str, Any]
) -> None:
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
            f"l9.projection/{name}@1",
            "--composition",
            f"l9.compose/{name}@1",
            "--pack-dir",
            _pack_dir(name),
        )
        if proc.returncode not in (0, 3):
            raise SystemExit(f"grammars failed for {name}: {proc.stderr[-800:]}")
        draft = _yaml_load(dest / _pack_dir(name) / "grammar-draft-report.yaml")
        report["pairs"][name] = {
            "projection": f"l9.projection/{name}@1",
            "composition": f"l9.compose/{name}@1",
            "grammars_written": len(draft["written"]),
            "inexpressible": draft["inexpressible"],
            "grammars_exit": proc.returncode,
        }


def _write_catalogs(dest: Path, compiler: Path, python: Path, grammars: str) -> None:
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
            raise SystemExit(f"catalog failed for {name}: {proc.stderr[-600:]}")


def _synthesize(
    dest: Path,
    compiler: Path,
    python: Path,
    governance: str,
    report: dict[str, Any],
    work: Path,
) -> tuple[list[str], dict[str, bytes]]:
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
            raise SystemExit(f"request failed for {name}: {proc.stderr[-600:]}")
        members[f"request-{name}.yaml"] = (
            request.read_text("utf-8").replace(str(dest), "<disposable>").encode()
        )
        result = _cli(compiler, python, "schema-synthesize", str(request))
        if result.returncode == 0:
            (work / f"pair-{name}.json").write_text(result.stdout, encoding="utf-8")
            members[f"pair-{name}.json"] = result.stdout.encode()
            synthesized.append(name)
            report["pairs"][name].update(
                {"synthesis_exit": 0, "synthesis": "candidate_pair_produced"}
            )
        else:
            report["pairs"][name].update(
                {
                    "synthesis_exit": result.returncode,
                    "synthesis": "BLOCKED",
                    "synthesis_diagnostic": {
                        "stdout": result.stdout[-3000:],
                        "stderr": result.stderr[-3000:],
                    },
                }
            )
    return synthesized, members


def _register(dest: Path, synthesized: list[str], work: Path) -> dict[str, bytes]:
    from l9_semantic_compiler.passes.payload_validation import (
        registered_schema_documents,
    )

    registered: dict[str, bytes] = {}
    manifest_path = dest / "semantics/generic_compiler_manifest.yaml"
    text = manifest_path.read_text("utf-8")
    # Idempotent: drop any domain schema registration the base already carries, then register once.
    names = {_schema_file(n, k) for n in PAIRS for k in ("projection", "composition")}
    text = "".join(
        line
        for line in text.splitlines(True)
        if line.strip().removeprefix("- ") not in names
    )
    anchor = "  - strategic_planning_context_projection_v2.schema.yaml\n"
    if text.count(anchor) != 1:
        raise SystemExit(
            "cannot locate the artifact_schemas anchor in the compiler manifest"
        )
    added = ""
    for name in synthesized:
        pair = json.loads((work / f"pair-{name}.json").read_text("utf-8"))
        documents = registered_schema_documents(
            pair,
            owner=REPOSITORY,
            projection_artifact_id=f"l9.schema/domain-{name}-projection@1",
            composition_artifact_id=f"l9.schema/domain-{name}-composition@1",
        )
        for kind, document in zip(("projection", "composition"), documents):
            document = {"canonical": True, **document}
            filename = _schema_file(name, kind)
            raw = yaml.safe_dump(
                document, sort_keys=False, width=100, allow_unicode=True
            ).encode()
            (dest / "semantics" / filename).write_bytes(raw)
            added += f"  - {filename}\n"
            registered[filename] = raw
    manifest_path.write_text(text.replace(anchor, anchor + added), "utf-8")
    registered["generic_compiler_manifest.yaml"] = manifest_path.read_bytes()
    return registered


def _coordinate(root: Path, revision: str, ref: str) -> dict[str, str]:
    from l9_semantic_compiler.engine.registry import CanonicalAuthority

    profile = CanonicalAuthority(root, revision, repository=REPOSITORY).resolve_profile(
        ref
    )
    return {"ref": profile.ref, "digest": profile.digest}


def _produce_once(
    root: Path, revision: str, name: str, cli: Any, out: Path
) -> tuple[dict[str, Any], dict[str, bytes]]:
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
        f"l9.projection/{name}@1",
    )
    if located.returncode:
        raise SystemExit(
            f"projection-coordinates failed for {name}: {located.stderr[-600:]}"
        )
    coords = yaml.safe_load(located.stdout)
    out.mkdir(parents=True)
    request = out / "project-request.json"
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
    request = out / "compose-request.json"
    request.write_text(
        json.dumps(
            {
                "schema": "l9.semantic-composition-request/v1",
                "authority": spec,
                "composition_profile": _coordinate(
                    root, revision, f"l9.compose/{name}@1"
                ),
                "components": [str(p) for p in artifacts],
                "output_root": str(out / "composed"),
            }
        )
    )
    compose = cli("compose", str(request))
    summary: dict[str, Any] = {
        "project_exit": project.returncode,
        "compose_exit": compose.returncode,
        "project_stderr": project.stderr[-1500:] if project.returncode else "",
        "compose_stderr": compose.stderr[-1500:] if compose.returncode else "",
        "receipts": {},
    }
    members: dict[str, bytes] = {}
    for path in sorted(p for p in out.rglob("*.json") if "request" not in p.name):
        members[str(path.relative_to(out))] = path.read_bytes()
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
            "dispatch_basis": criterion.get("dispatch_basis"),
        }
    return summary, members


def _produce(
    root: Path,
    revision: str,
    name: str,
    cli: Any,
    work: Path,
    members: dict[str, bytes],
) -> dict[str, Any]:
    first, run1 = _produce_once(root, revision, name, cli, work / f"producer-{name}-1")
    _, run2 = _produce_once(root, revision, name, cli, work / f"producer-{name}-2")
    for rel, raw in run1.items():
        members[f"{name}/{rel}"] = raw
    first["replay"] = {
        "files": len(run1),
        "byte_identical": run1 == run2,
        "differing": sorted(
            k for k in set(run1) | set(run2) if run1.get(k) != run2.get(k)
        ),
    }
    first["all_pass"] = bool(first["receipts"]) and all(
        r.get("result") == "pass" and not r.get("unresolved_criteria")
        for r in first["receipts"].values()
    )
    return first


def rehearse(dest: Path, compiler: Path, revision: str, python: Path) -> dict[str, Any]:
    executed = _require_pinned_compiler(compiler, python)
    base = _clone_at_base(dest)
    report: dict[str, Any] = {
        "schema": "l9.candidate-rehearsal/domain-projection-architecture-v1",
        "admission": "not_granted",
        "base": {"repository": REPOSITORY, "revision": base},
        "compiler": {
            "repository": "Quantum-L9/l9-semantic-compiler-engine",
            "revision": revision,
            "executable_digest": _executable_digest(compiler, revision),
            "executable_digest_basis": "sha256 of git archive <revision> src",
            "executed_module": executed,
        },
        "commits": {},
        "pairs": {},
    }
    commits = report["commits"]
    _draft_grammars(dest, compiler, python, base, report)
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
    registered = _register(dest, synthesized, work)
    commits["R_registrations"] = _commit(
        dest, "rehearsal R: register rendered domain output schemas", "semantics"
    )
    producer_members: dict[str, bytes] = {}
    for name in synthesized:
        report["pairs"][name]["producer"] = _produce(
            dest,
            commits["R_registrations"],
            name,
            lambda *a: _cli(compiler, python, *a),
            work,
            producer_members,
        )
    shutil.rmtree(work)
    report["synthesis_archive"] = f"{PACK_REL}/evidence/synthesis.tar.gz"
    report["producer_archive"] = f"{PACK_REL}/evidence/producer.tar.gz"
    return {
        "report": report,
        "registered": registered,
        "synthesis_tar": _deterministic_tar(synthesis_members),
        "producer_tar": _deterministic_tar(producer_members),
    }


def _outputs(dest: Path, result: dict[str, Any]) -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    for name in PAIRS:
        pack = dest / _pack_dir(name)
        for path in sorted(p for p in pack.rglob("*") if p.is_file()):
            outputs[str(path.relative_to(dest))] = path.read_bytes()
    for filename, raw in result["registered"].items():
        outputs[f"semantics/{filename}"] = raw
    outputs[f"{PACK_REL}/evidence/rehearsal.json"] = (
        json.dumps(result["report"], indent="\t", sort_keys=True) + "\n"
    ).encode()
    outputs[f"{PACK_REL}/evidence/synthesis.tar.gz"] = result["synthesis_tar"]
    outputs[f"{PACK_REL}/evidence/producer.tar.gz"] = result["producer_tar"]
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--disposable",
        type=Path,
        required=True,
        help="new directory outside this checkout",
    )
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument(
        "--compiler-python", type=Path, help="default: <compiler-root>/.venv/bin/python"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--emit", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    repo = _repo_root().resolve()
    dest = args.disposable.resolve()
    if dest.exists() or dest == repo or repo in dest.parents:
        raise SystemExit(
            "refusing: --disposable must be a new directory outside this checkout"
        )
    compiler = args.compiler_root.resolve()
    head = _run(["git", "-C", str(compiler), "rev-parse", "HEAD"]).stdout.strip()
    if head != COMPILER_REVISION:
        raise SystemExit(
            f"refusing: compiler HEAD {head} != pinned revision {COMPILER_REVISION}"
        )
    python = (args.compiler_python or compiler / ".venv/bin/python").absolute()
    result = rehearse(dest, compiler, COMPILER_REVISION, python)
    outputs = _outputs(dest, result)
    if args.emit:
        for rel, raw in outputs.items():
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        print(f"emitted {len(outputs)} files")
        return 0
    if args.check:
        differing = [
            rel
            for rel, raw in outputs.items()
            if not (repo / rel).is_file() or (repo / rel).read_bytes() != raw
        ]
        for rel in differing:
            print(f"DIFF {rel}")
        print(f"checked {len(outputs)} files, {len(differing)} differing")
        return 1 if differing else 0
    print(json.dumps(result["report"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
