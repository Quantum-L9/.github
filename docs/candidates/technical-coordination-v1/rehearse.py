#!/usr/bin/env python3
"""Rehearse the technical-coordination pair with the pinned compiler; never admits anything.

This is the domain-projection-architecture-v1 rehearsal
(`docs/candidates/domain-projection-architecture-v1/rehearse.py`) run for one pair. It loads
that module and overrides only what differs: the base, the pair, the pack paths, the schema
file and artifact names (no `domain-` prefix) and the report schema.

The base is derived, not pinned to a branch commit that a squash merge would discard: it is
a parentless commit, with the precedent's fixed identity and dates, whose tree is the
`semantics/` tree of the checkout's HEAD without this pair's two payload schemas and their
`artifact_schemas` entries. Any commit that carries the approved `semantics/` tree, whatever
its history, therefore reproduces the same base and the same outputs. Every stage
(G1 grammars, G2 catalog, S synthesis, R registration with
`payload_validation.registered_schema_documents()`, P producer run twice) is the precedent's
own code. `--emit` writes the outputs; `--check` compares a fresh rehearsal with the commit.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

PACK = Path(__file__).resolve().parent
BASE_MODULE = PACK.parent / "domain-projection-architecture-v1" / "rehearse.py"

PAIR = "technical-coordination"
SCHEMA_FILES = tuple(
    f"{PAIR.replace('-', '_')}_{kind}.schema.yaml"
    for kind in ("projection", "composition")
)
MANIFEST = "semantics/generic_compiler_manifest.yaml"
REPORT_SCHEMA = "l9.candidate-rehearsal/technical-coordination-v1"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("domain_rehearsal", BASE_MODULE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"refusing: precedent rehearsal missing: {BASE_MODULE}")
    module = importlib.util.module_from_spec(spec)
    # The precedent pack is committed evidence; loading it must leave no residue there.
    previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def configure(base: Any) -> Any:
    """Point the precedent rehearsal at this pair; its stage code is unchanged."""
    base_register, base_rehearse = base._register, base.rehearse

    def register(dest: Path, synthesized: list[str], work: Path) -> dict[str, bytes]:
        from l9_semantic_compiler.passes import payload_validation

        render = payload_validation.registered_schema_documents

        def unprefixed(pair: dict, **ids: str) -> Any:
            return render(
                pair,
                **{
                    k: v.replace("l9.schema/domain-", "l9.schema/")
                    for k, v in ids.items()
                },
            )

        payload_validation.registered_schema_documents = unprefixed
        try:
            return base_register(dest, synthesized, work)
        finally:
            payload_validation.registered_schema_documents = render

    def clone_at_base(dest: Path) -> str:
        # The worktree starts empty and only the derived semantics tree is ever checked out,
        # so no other file of the source revision can reach a rehearsal commit.
        repo = base._repo_root()
        base._run(
            [
                "git",
                "clone",
                "-q",
                "--no-checkout",
                "--no-hardlinks",
                str(repo),
                str(dest),
            ]
        )
        source = base._git(repo, "rev-parse", "HEAD")
        base._git(dest, "read-tree", "--empty")
        base._git(dest, "read-tree", "--prefix=semantics/", f"{source}:semantics")
        for name in SCHEMA_FILES:
            base._git(
                dest, "rm", "-q", "--cached", "--ignore-unmatch", f"semantics/{name}"
            )
        manifest = dest / MANIFEST
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            "".join(
                line
                for line in base._run(
                    ["git", "-C", str(dest), "show", f"{source}:{MANIFEST}"]
                ).stdout.splitlines(True)
                if line.strip().removeprefix("- ") not in SCHEMA_FILES
            ),
            "utf-8",
        )
        base._git(dest, "add", "--", MANIFEST)
        tree = base._git(dest, "write-tree")
        commit = base._git(
            dest,
            "commit-tree",
            tree,
            "-m",
            f"rehearsal base: semantics without {PAIR} payload schemas",
        )
        base._git(dest, "checkout", "-q", "-f", "--detach", commit)
        return commit

    def rehearse(*args: Any) -> dict[str, Any]:
        result = base_rehearse(*args)
        result["report"]["schema"] = REPORT_SCHEMA
        return result

    base.PACK = PACK
    base.PACK_REL = "docs/candidates/technical-coordination-v1"
    base.PAIRS = (PAIR,)
    base._pack_dir = lambda name: f"docs/candidates/schema-grammar-{name}"
    base._schema_file = lambda name, kind: (
        f"{name.replace('-', '_')}_{kind}.schema.yaml"
    )
    base._clone_at_base = clone_at_base
    base._register = register
    base.rehearse = rehearse
    return base


if __name__ == "__main__":
    sys.exit(configure(_load_base()).main())
