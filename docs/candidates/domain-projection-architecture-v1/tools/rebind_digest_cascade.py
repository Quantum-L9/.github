#!/usr/bin/env python3
"""Rebind the derivation digest cascade from final bytes, in the documented order.

Order (registration-surfaces.md): contracts.yaml#derivation, then
capabilities.yaml, lifecycle.yaml and receipt_catalog.yaml derivation
source_artifacts. Only the recorded sha256 and item counts change; every other
byte is preserved. `--check` exits 1 when any recorded coordinate is stale.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import yaml

SEM = Path(__file__).resolve().parents[4] / "semantics"
COLLECTION = {
    "invariants.yaml": "invariants",
    "contracts.yaml": "contracts",
    "capabilities.yaml": "capabilities",
}
ORDER = (
    "contracts.yaml",
    "capabilities.yaml",
    "lifecycle.yaml",
    "receipt_catalog.yaml",
)


def sha(name: str) -> str:
    return hashlib.sha256((SEM / name).read_bytes()).hexdigest()


def count(name: str) -> int:
    return len(yaml.safe_load((SEM / name).read_text("utf-8"))[COLLECTION[name]])


def rebind(name: str) -> str:
    text = (SEM / name).read_text("utf-8")
    derivation = yaml.safe_load(text)["derivation"]
    if "source_artifact" in derivation:  # contracts.yaml shape
        src = derivation["source_artifact"]
        text = text.replace(derivation["source_digest_sha256"], sha(src), 1)
        text = re.sub(
            r"(\n  source_invariant_count: )\d+", rf"\g<1>{count(src)}", text, count=1
        )
        return text
    for entry in derivation["source_artifacts"]:
        art = entry["artifact"]
        text = text.replace(entry["sha256"], sha(art), 1)
        if "item_count" in entry:
            pattern = rf"(artifact: {re.escape(art)}\n(?:[ \t]+(?!- ).*\n)*?[ \t]+item_count: )\d+"
            text, n = re.subn(pattern, rf"\g<1>{count(art)}", text, count=1)
            if n != 1:
                raise SystemExit(f"{name}: cannot locate item_count for {art}")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale = []
    for name in ORDER:
        new = rebind(name)
        if new != (SEM / name).read_text("utf-8"):
            stale.append(name)
            if args.write:
                (SEM / name).write_text(new, "utf-8")
    for name in stale:
        print(("rebound " if args.write else "STALE ") + f"semantics/{name}")
    return 1 if (stale and args.check) else 0


if __name__ == "__main__":
    sys.exit(main())
