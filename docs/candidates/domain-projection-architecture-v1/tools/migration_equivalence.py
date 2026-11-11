#!/usr/bin/env python3
"""WP-09: old/new selection difference for every binding that names predecessors.

S_old is the set of nodes the predecessor profiles select; S_new is the union of
the nodes selected by every domain the binding requires or may activate. Nodes
are compared by (source class, exact path in the source ledger), all resolved at
one revision, with the RC-034 selector evaluator. An old node is covered when a
new node is it or contains it; a new node is added when no old node is it or
contains it. Missing nodes carry no disposition: every one stays `undisposed`
until an owner records one, which is why each such binding declares
`predecessor_migration_dispositions` unresolved. `--check` exits 1 when the
committed receipt differs from a fresh computation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs/candidates/domain-projection-architecture-v1/evidence/migration_equivalence.json"


def _validator():
    spec = importlib.util.spec_from_file_location("validate_semantics", ROOT / "scripts/validate-semantics.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load(name: str):
    return yaml.safe_load((ROOT / "semantics" / name).read_text("utf-8"))


def _render(path: tuple) -> str:
    out = "$"
    for part in path:
        out += f"[{part}]" if isinstance(part, int) else f".{part}"
    return out


def _label(document: object, path: tuple) -> str:
    """Path with list indexes replaced by the record id when it has one."""
    out, node = "$", document
    for part in path:
        node = node[part]
        if isinstance(part, int):
            out += f'[?(@.id=="{node["id"]}")]' if isinstance(node, dict) and "id" in node else f"[{part}]"
        else:
            out += f".{part}"
    return out


def compute() -> dict:
    v = _validator()
    catalog = _load("projection_profiles.yaml")
    profiles = {p["id"]: p for p in catalog["projection_profiles"]}
    docs = {}
    for name, entry in catalog["source_classes"].items():
        artifact = entry.get("canonical_artifact") if isinstance(entry, dict) else None
        if artifact and (ROOT / "semantics" / artifact).is_file():
            docs[name] = _load(artifact)

    def nodes(profile_ids: list[str]) -> set[tuple]:
        found: set[tuple] = set()
        for pid in profile_ids:
            for source_class, spec in (profiles[pid].get("sources") or {}).items():
                for selector in spec.get("selectors") or []:
                    for path, _ in v._rc034_nodes(docs.get(source_class), selector) or []:
                        found.add((source_class, path))
        return found

    def covered(node: tuple, by: set[tuple]) -> bool:
        cls, path = node
        return any(c == cls and path[: len(p)] == p for c, p in by)

    revision = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    receipt = {
        "schema": "l9.candidate-evidence/domain-migration-equivalence-v1",
        "admission": "not_granted",
        "basis": "nodes resolved at one revision of semantics/; comparison by source class and exact ledger path",
        "bindings": {},
    }
    for binding in _load("domain_consumer_bindings.yaml")["bindings"]:
        old_ids = binding.get("predecessor_profiles") or []
        if not old_ids:
            continue
        new_ids = list(binding["requires"]) + [c["profile"] for c in binding.get("conditional") or []]
        s_old, s_new = nodes(old_ids), nodes(new_ids)
        missing = sorted((c, p) for c, p in s_old if not covered((c, p), s_new))
        added = sorted((c, p) for c, p in s_new if not covered((c, p), s_old))
        receipt["bindings"][binding["id"]] = {
            "predecessor_profiles": old_ids,
            "bound_domains": new_ids,
            "old_nodes": len(s_old),
            "new_nodes": len(s_new),
            "missing_count": len(missing),
            "added_count": len(added),
            "missing": [
                {"source_class": c, "node": _label(docs[c], p), "disposition": "undisposed"} for c, p in missing
            ],
            "added_by_source_class": {
                c: sum(1 for cc, _ in added if cc == c) for c in sorted({cc for cc, _ in added})
            },
            "migration_ready": not missing,
        }
    receipt["source_revision_note"] = f"computed at a checkout whose HEAD was {revision[:12]} or a descendant with identical semantics/"
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    receipt = compute()
    receipt.pop("source_revision_note")
    text = json.dumps(receipt, indent="\t", sort_keys=True) + "\n"
    if args.write:
        OUT.write_text(text, "utf-8")
        for bid, entry in receipt["bindings"].items():
            print(f"{bid}: old {entry['old_nodes']} new {entry['new_nodes']} missing {entry['missing_count']} added {entry['added_count']}")
        return 0
    same = OUT.is_file() and OUT.read_text("utf-8") == text
    print("migration equivalence receipt " + ("current" if same else "STALE"))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
