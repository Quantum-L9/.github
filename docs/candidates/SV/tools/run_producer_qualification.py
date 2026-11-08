#!/usr/bin/env python3
"""Run the real producer for the Strategic Value candidate at one exact authority revision.

At a clean checkout's HEAD, with the l9-semantic-compiler-engine checkout given, this runs:

  1. one projection per source class of l9.projection/strategic-planner-value@1 (pinned by
     ``projection-coordinates --source-class``), each kept as requests/<class>.{coords,request,result}.yaml
  2. the composition l9.compose/strategic-planner-value@1 over those five artifacts
     (requests/compose.{request,result}.yaml); the composition profile pin is the canonical-JSON
     sha256 of its catalog record, the rule the compiler applies
  3. the regression composition l9.compose/stage-context@1 over the
     l9.projection/gar-architecture-observer@1 artifacts (requests/stage_context.*), because
     it declares the same four required_provenance tokens

It writes summary.json and exits 0 only when every SV projection and the SV composition PASS
and every required_provenance criterion of both compositions is ``pass``. A missing input or
malformed producer output is UNRESOLVED (exit 2).

Usage: run_producer_qualification.py --checkout AUTH --compiler-src ENGINE --out DIR
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

REPOSITORY = "Quantum-L9/.github"
PROFILE = "l9.projection/strategic-planner-value@1"
COMPOSITION = "l9.compose/strategic-planner-value@1"
REGRESSION_PROFILE = "l9.projection/gar-architecture-observer@1"
REGRESSION_COMPOSITION = "l9.compose/stage-context@1"
CLASSES = (
    "strategic_value_model",
    "vocabulary",
    "invariants",
    "contracts",
    "authority_model",
)
PROVENANCE = "declared_constraint:required_provenance:"


class Unresolved(Exception):
    pass


def canonical_digest(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


class Producer:
    def __init__(self, checkout: Path, compiler_src: Path, out: Path) -> None:
        self.checkout, self.out = checkout, out
        self.env = dict(os.environ, PYTHONPATH=str(compiler_src / "src"))
        self.revision = self._git("rev-parse", "HEAD")
        self.requests = out / "requests"
        self.requests.mkdir(parents=True, exist_ok=False)

    def _git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(self.checkout), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        if done.returncode != 0:
            raise Unresolved(f"git {' '.join(args)} failed")
        return done.stdout.strip()

    def cli(self, *args: str) -> tuple[int, dict]:
        done = subprocess.run(
            [sys.executable, "-m", "l9_semantic_compiler", *args],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )
        try:
            doc = yaml.safe_load(done.stdout)
        except yaml.YAMLError as exc:
            raise Unresolved(f"{args[0]} output is not YAML: {exc}") from exc
        if not isinstance(doc, dict):
            raise Unresolved(f"{args[0]} output is not a mapping: {done.stderr[-300:]}")
        return done.returncode, doc

    def authority(self) -> dict:
        return {
            "repository": REPOSITORY,
            "root": str(self.checkout),
            "revision": self.revision,
        }

    def project(self, name: str, profile: str, source_class: str | None) -> dict:
        args = ["projection-coordinates", "--authority-root", str(self.checkout), "--revision",
                self.revision, "--repository", REPOSITORY, "--profile", profile]  # fmt: skip
        if source_class:
            args += ["--source-class", source_class]
        rc, pins = self.cli(*args)
        if rc != 0:
            raise Unresolved(
                f"projection-coordinates {profile} {source_class}: exit {rc}"
            )
        (self.requests / f"{name}.coords.yaml").write_text(yaml.safe_dump(pins))
        request = {
            "schema": "l9.semantic-projection-request/v1",
            "authority": self.authority(),
            "projection_profile": pins["projection_profile"],
            "sources": pins["sources"],
            "output_root": str(self.out),
        }
        if "source_classes" in pins:
            # A --source-class pin restricts the request; the request must carry it.
            request["source_classes"] = pins["source_classes"]
        path = self.requests / f"{name}.request.yaml"
        path.write_text(yaml.safe_dump(request))
        rc, result = self.cli("project", str(path))
        (self.requests / f"{name}.result.yaml").write_text(yaml.safe_dump(result))
        return {"exit": rc, **result}

    def compose(self, name: str, ref: str, components: list[str]) -> dict:
        catalog = yaml.safe_load(
            (self.checkout / "semantics/composition_profiles.yaml").read_text()
        )
        record = next(p for p in catalog["profiles"] if p["id"] == ref)
        request = {
            "schema": "l9.semantic-composition-request/v1",
            "authority": self.authority(),
            "composition_profile": {"ref": ref, "digest": canonical_digest(record)},
            "components": sorted(components),
            "output_root": str(self.out),
        }
        path = self.requests / f"{name}.request.yaml"
        path.write_text(yaml.safe_dump(request))
        rc, result = self.cli("compose", str(path))
        (self.requests / f"{name}.result.yaml").write_text(yaml.safe_dump(result))
        return {"exit": rc, **result}


def provenance_status(out: Path, result: dict) -> dict:
    arts = result.get("artifacts") or []
    if len(arts) != 1 or not arts[0].get("receipt"):
        receipts = sorted((out / "receipts").glob("*.json"))
        matches = [
            json.loads(p.read_text())
            for p in receipts
            if json.loads(p.read_text()).get("output", {}).get("digest")
            == (arts[0] if arts else {}).get("digest")
        ]
        if len(matches) != 1:
            raise Unresolved("composition receipt not found exactly once")
        receipt = matches[0]
    else:
        receipt = json.loads(Path(arts[0]["receipt"]).read_text())
    criteria = receipt["verification_basis"]["criteria"]
    return {
        k.removeprefix(PROVENANCE): v["status"]
        for k, v in criteria.items()
        if k.startswith(PROVENANCE)
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--compiler-src", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        checkout = args.checkout.resolve()
        compiler = args.compiler_src.resolve()
        if not (compiler / "src" / "l9_semantic_compiler").is_dir():
            raise Unresolved(
                f"{compiler} is not an l9-semantic-compiler-engine checkout"
            )
        producer = Producer(checkout, compiler, args.out.resolve())
        if producer._git("status", "--porcelain", "--untracked-files=no"):
            raise Unresolved("authority checkout has tracked changes")
        summary = {
            "schema": "l9.sv-producer-qualification/v1",
            "authority": producer.authority() | {"root": None},
            "compiler_revision": subprocess.run(
                ["git", "-C", str(compiler), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
            "projections": {},
        }
        components = []
        for cls in CLASSES:
            result = producer.project(cls, PROFILE, cls)
            arts = result.get("artifacts") or []
            summary["projections"][cls] = {
                "exit": result["exit"],
                "result": result.get("result"),
                "artifacts": [
                    {
                        "ref": a.get("ref"),
                        "digest": a.get("digest"),
                        "result": a.get("result"),
                    }
                    for a in arts
                ],
            }
            components += [a["path"] for a in arts if a.get("path")]
        comp = producer.compose("compose", COMPOSITION, components)
        summary["composition"] = {
            "exit": comp["exit"],
            "result": comp.get("result"),
            "digest": [a.get("digest") for a in comp.get("artifacts") or []],
            "required_provenance": provenance_status(producer.out, comp),
        }
        # The regression runs in its own output root so the SV run directory holds exactly the
        # SV projections, their composition and their receipts.
        regression = Producer(
            checkout, compiler, producer.out / "stage-context-regression"
        )
        gar = regression.project("gar", REGRESSION_PROFILE, None)
        stage = regression.compose(
            "stage_context",
            REGRESSION_COMPOSITION,
            [a["path"] for a in gar.get("artifacts") or [] if a.get("path")],
        )
        summary["stage_context_regression"] = {
            "exit": stage["exit"],
            "result": stage.get("result"),
            "required_provenance": provenance_status(regression.out, stage),
        }
        ok = (
            all(
                p["exit"] == 0 and p["result"] == "pass" and p["artifacts"]
                for p in summary["projections"].values()
            )
            and summary["composition"]["exit"] == 0
            and summary["composition"]["result"] == "pass"
            and set(summary["composition"]["required_provenance"].values()) == {"pass"}
            and len(summary["composition"]["required_provenance"]) == 4
            and set(summary["stage_context_regression"]["required_provenance"].values())
            == {"pass"}
            and len(summary["stage_context_regression"]["required_provenance"]) == 4
        )
        summary["result"] = "PASS" if ok else "FAIL"
        (producer.out / "summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0 if ok else 1
    except Unresolved as exc:
        print(json.dumps({"result": "UNRESOLVED", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
