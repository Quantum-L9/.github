#!/usr/bin/env python3
"""Rehearse the technical-coordination pair with the pinned compiler; never admits anything.

This is the domain-projection-architecture-v1 rehearsal
(`docs/candidates/domain-projection-architecture-v1/rehearse.py`) run for one pair. It loads
that module and overrides only what differs: the base commit (which carries the
technical-coordination profile pair but no payload schemas), the pair, the pack paths, the
schema file and artifact names (no `domain-` prefix) and the report schema. Every stage
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

BASE_SHA = "62e20d48e8e61c130d460ba9e0b88e20283f5de2"
PAIR = "technical-coordination"
REPORT_SCHEMA = "l9.candidate-rehearsal/technical-coordination-v1"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("domain_rehearsal", BASE_MODULE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"refusing: precedent rehearsal missing: {BASE_MODULE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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

    def rehearse(*args: Any) -> dict[str, Any]:
        result = base_rehearse(*args)
        result["report"]["schema"] = REPORT_SCHEMA
        return result

    base.BASE_SHA = BASE_SHA
    base.PACK = PACK
    base.PACK_REL = "docs/candidates/technical-coordination-v1"
    base.PAIRS = (PAIR,)
    base._pack_dir = lambda name: f"docs/candidates/schema-grammar-{name}"
    base._schema_file = lambda name, kind: (
        f"{name.replace('-', '_')}_{kind}.schema.yaml"
    )
    base._register = register
    base.rehearse = rehearse
    return base


if __name__ == "__main__":
    sys.exit(configure(_load_base()).main())
