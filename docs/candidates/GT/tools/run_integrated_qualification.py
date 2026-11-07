#!/usr/bin/env python3
"""Run the REAL semantic compiler over an integrated SV + GT-core rehearsal revision.

Inputs are explicit: ``--authority-root`` (a local clone whose ``--revision``
carries the SV #215 application plus this pack's stage-core application),
``--compiler-src`` (``l9-semantic-compiler-engine/src``) and ``--out`` (a new
empty directory). For each profile the producer is asked for coordinates, then
projects every declared source class and composes the results; the whole run is
performed twice and the outputs compared byte for byte.

Writes ``summary.json`` plus the raw producer output under ``--out``. It does not
commit, push, publish or admit anything; producer receipts bind only to the
local rehearsal revision named in the summary.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

_FULL_SHA = re.compile(r"[0-9a-f]{40}")


def checked_revision(value):
    """A revision argument must be one full commit SHA, never an option or a ref expression."""
    match = _FULL_SHA.fullmatch(value or "")
    if match is None:
        raise ValueError(f"revision must be a 40-hex commit SHA, got {value!r}")
    return match.group(0)


def checked_directory(value, *, required=()):
    """An existing directory, symlinks resolved, holding every ``required`` entry."""
    path = Path(os.path.realpath(value))
    if not path.is_dir() or any(not (path / name).exists() for name in required):
        raise ValueError(f"{value!r} is not a directory holding {list(required)}")
    return path


def confined(value):
    """A file path that resolves inside the current working directory."""
    base = os.path.realpath(os.getcwd())
    path = os.path.realpath(value)
    if os.path.commonpath([base, path]) != base:
        raise ValueError(f"{value!r} resolves outside the working directory {base}")
    return Path(path)


PROFILES = {
    "gt": {
        "profile": "l9.projection/strategic-planner-interaction@1",
        "composition": "l9.compose/strategic-planner-interaction@1",
        "classes": ("vocabulary", "invariants", "contracts"),
    },
    "sv": {
        "profile": "l9.projection/strategic-planner-value@1",
        "composition": "l9.compose/strategic-planner-value@1",
        "classes": (
            "strategic_value_model",
            "vocabulary",
            "invariants",
            "contracts",
            "authority_model",
        ),
    },
}


def cli(env, *args):
    # S8705: argv list, no shell; revision passes checked_revision() (40-hex SHA)
    # and directories pass checked_directory().
    proc = subprocess.run(  # NOSONAR
        [sys.executable, "-m", "l9_semantic_compiler", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def coordinates(env, root, revision, profile, source_class):
    rc, out, err = cli(
        env,
        "projection-coordinates",
        "--authority-root",
        str(root),
        "--revision",
        revision,
        "--repository",
        "Quantum-L9/.github",
        "--profile",
        profile,
        "--source-class",
        source_class,
    )
    if rc != 0:
        raise RuntimeError(
            f"coordinates {profile} {source_class}: rc={rc} {err[-400:]}"
        )
    request = yaml.safe_load(out)
    request["schema"] = "l9.semantic-projection-request/v1"
    request["authority"]["root"] = str(root)
    return request


def run_once(env, root, revision, out):
    # S8707: operator CLI path, realpath-confined to the working directory.
    out.mkdir(parents=True)  # NOSONAR
    requests = out / "requests"
    requests.mkdir()
    results = {}
    for key, spec in PROFILES.items():
        artifacts = []
        for source_class in spec["classes"]:
            request = coordinates(env, root, revision, spec["profile"], source_class)
            request["output_root"] = str(out)
            path = requests / f"{key}.{source_class}.request.yaml"
            path.write_text(yaml.safe_dump(request, sort_keys=True), encoding="utf-8")
            rc, stdout, stderr = cli(env, "project", str(path))
            (requests / f"{key}.{source_class}.result.yaml").write_text(
                stdout, encoding="utf-8"
            )
            result = yaml.safe_load(stdout) or {}
            arts = result.get("artifacts") or []
            results[f"{key}:{source_class}"] = {
                "exit_code": rc,
                "status": result.get("status"),
                "result": result.get("result"),
                "artifacts": [
                    {
                        "ref": a.get("ref"),
                        "result": a.get("result"),
                        "digest": a.get("digest"),
                        "unresolved_criteria": a.get("unresolved_criteria"),
                    }
                    for a in arts
                ],
                "stderr_tail": stderr.strip()[-400:],
            }
            artifacts.extend(a["path"] for a in arts if a.get("path"))
        compose = {
            "schema": "l9.semantic-composition-request/v1",
            "authority": {
                "repository": "Quantum-L9/.github",
                "revision": revision,
                "root": str(root),
            },
            "composition_profile": {
                "ref": spec["composition"],
                "digest": composition_digest(root, revision, spec["composition"]),
            },
            "components": sorted(artifacts),
            "output_root": str(out),
        }
        path = requests / f"{key}.compose.request.yaml"
        path.write_text(yaml.safe_dump(compose, sort_keys=True), encoding="utf-8")
        rc, stdout, stderr = cli(env, "compose", str(path))
        (requests / f"{key}.compose.result.yaml").write_text(stdout, encoding="utf-8")
        result = yaml.safe_load(stdout) or {}
        results[f"{key}:compose"] = {
            "exit_code": rc,
            "status": result.get("status"),
            "result": result.get("result"),
            "artifacts": [
                {
                    "ref": a.get("ref"),
                    "result": a.get("result"),
                    "digest": a.get("digest"),
                    "unresolved_criteria": a.get("unresolved_criteria"),
                }
                for a in result.get("artifacts") or []
            ],
            "component_count": len(artifacts),
            "stderr_tail": stderr.strip()[-400:],
        }
    return results


def composition_digest(root, revision, ref):
    """Digest of one composition profile record, computed by the producer's own function."""
    from l9_semantic_compiler.engine.registry import profile_digest

    # S8705: argv list, no shell; revision passes checked_revision() (40-hex SHA)
    # and directories pass checked_directory().
    text = subprocess.run(  # NOSONAR
        [
            "git",
            "-C",
            str(root),
            "show",
            f"{revision}:semantics/composition_profiles.yaml",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    rows = [r for r in yaml.safe_load(text)["profiles"] if r.get("id") == ref]
    if len(rows) != 1:
        raise RuntimeError(f"composition profile {ref} not found exactly once")
    return profile_digest(rows[0])


EXPECTED_SV_COMPOSITION_UNRESOLVED = frozenset(
    "declared_constraint:required_provenance:" + name
    for name in (
        "composition_profile_digest",
        "composition_profile_ref",
        "source_projection_digests",
        "source_projection_refs",
    )
)


def acceptance(results):
    """Every projection and the GT composition must pass with exit 0.

    The one admitted deviation is the SV composition returning ``unknown``
    (exit 3) on exactly its four ``required_provenance`` declarations, an open
    owner decision in PR #215. Anything else is a qualification failure.
    """
    failures = []
    for key, row in sorted(results.items()):
        artifacts = row["artifacts"]
        unresolved = {c for a in artifacts for c in (a["unresolved_criteria"] or [])}
        if key == "sv:compose" and (row["exit_code"], row["result"]) == (3, "unknown"):
            if unresolved != EXPECTED_SV_COMPOSITION_UNRESOLVED:
                failures.append(
                    f"{key}: unknown on unexpected criteria {sorted(unresolved)}"
                )
            continue
        if (row["exit_code"], row["status"], row["result"]) != (0, "succeeded", "pass"):
            failures.append(
                f"{key}: exit={row['exit_code']} status={row['status']} result={row['result']}"
            )
        elif len(artifacts) != 1 or artifacts[0]["result"] != "pass" or unresolved:
            failures.append(f"{key}: artifact not a single unconditional pass")
    expected = {f"gt:{c}" for c in (*PROFILES["gt"]["classes"], "compose")} | {
        f"sv:{c}" for c in (*PROFILES["sv"]["classes"], "compose")
    }
    if set(results) != expected:
        failures.append(f"result keys {sorted(results)} != expected {sorted(expected)}")
    return failures


def tree_digests(base):
    digests = {}
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        rel = path.relative_to(base).as_posix()
        if rel.startswith("requests/"):
            continue
        digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--authority-root", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--compiler-src", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        revision = checked_revision(args.revision)
        root = checked_directory(args.authority_root, required=(".git", "semantics"))
        compiler_src = checked_directory(
            args.compiler_src, required=("l9_semantic_compiler",)
        )
        out = confined(args.out)
    except ValueError as exc:
        print("BLOCKED=" + str(exc), file=sys.stderr)
        return 2
    if out.exists() and any(out.iterdir()):
        print("BLOCKED=--out must be a new or empty directory", file=sys.stderr)
        return 2
    env = dict(os.environ, PYTHONPATH=str(compiler_src))
    sys.path.insert(0, env["PYTHONPATH"])
    try:
        run1 = run_once(env, root, revision, out / "run1")
        run2 = run_once(env, root, revision, out / "run2")
    except (RuntimeError, ImportError, subprocess.SubprocessError) as exc:
        print("BLOCKED=" + str(exc), file=sys.stderr)
        return 2
    d1, d2 = tree_digests(out / "run1"), tree_digests(out / "run2")
    compiler_rev = subprocess.run(
        [
            "git",
            "-C",
            str(compiler_src.parent),
            "rev-parse",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    summary = {
        "schema": "l9.gt.integrated-qualification/v2",
        "authority_revision": revision,
        # S8705: argv list, no shell; revision passes checked_revision() (40-hex SHA)
        # and directories pass checked_directory().
        "authority_tree": subprocess.run(  # NOSONAR
            ["git", "-C", str(root), "rev-parse", revision + "^{tree}"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip(),
        "compiler_revision": compiler_rev,
        "acceptance_failures": acceptance(run1),
        "run1": run1,
        "run2_equal_results": run1 == run2,
        "run1_output_digests": d1,
        "byte_identical_outputs": d1 == d2 and bool(d1),
    }
    # S8707: operator CLI path, realpath-confined to the working directory.
    (out / "summary.json").write_text(  # NOSONAR
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k != "run1_output_digests"}, indent=2
        )
    )
    accepted = (
        not summary["acceptance_failures"]
        and summary["run2_equal_results"]
        and summary["byte_identical_outputs"]
    )
    print("QUALIFICATION=" + ("ACCEPTED" if accepted else "REJECTED"), file=sys.stderr)
    return 0 if accepted else 1


if __name__ == "__main__":
    sys.exit(main())
