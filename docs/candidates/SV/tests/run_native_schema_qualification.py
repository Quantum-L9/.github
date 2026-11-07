#!/usr/bin/env python3
"""Qualify real L9 compiler schema interpreter against exact candidate witnesses.

Run inside the actual pinned l9-semantic-compiler-engine environment, with its
Python package importable. Missing package is BLOCKED, never a silent skip/PASS.
Does not replace producer projection, receipts, source selection or admission.
"""

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REMOVED = [f"L9-SV-{n:03d}" for n in range(15, 21)]


def assert_check(violations, expected, label, checks):
    if bool(violations) != expected:
        raise AssertionError(
            f"{label}: violations={violations!r}, expected_violation={expected}"
        )
    checks.append(
        {"check": label, "expected_violation": expected, "observed": violations or None}
    )


def compiler_revision(module):
    src = Path(module.__file__).resolve()
    out = subprocess.run(
        ["git", "-C", str(src.parent), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    dirty = subprocess.run(
        ["git", "-C", str(src.parent), "status", "--porcelain", "--", "src"],
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "module_path": str(src),
        "git_head": out.stdout.strip() or "UNKNOWN",
        "src_dirty": bool(dirty.stdout.strip()) if out.returncode == 0 else "UNKNOWN",
    }


def main():
    try:
        import l9_semantic_compiler
        from l9_semantic_compiler.passes.validate import schema_violations
    except ImportError as exc:
        print(
            json.dumps(
                {
                    "result": "BLOCKED",
                    "reason": "REAL_COMPILER_NOT_IMPORTABLE",
                    "detail": str(exc),
                    "not_claimed": "native schema qualification",
                }
            )
        )
        return 2
    checks = []
    pro = yaml.safe_load(
        (ROOT / "semantics/strategic_planner_value_projection.schema.yaml").read_text()
    )
    com = yaml.safe_load(
        (ROOT / "semantics/strategic_planner_value_composition.schema.yaml").read_text()
    )
    model = yaml.safe_load((ROOT / "semantics/strategic_value_model.yaml").read_text())
    profile = yaml.safe_load(
        (ROOT / "overlays/projection_profile_additions.yaml").read_text()
    )["projection_profiles"][0]
    selected = {
        selector[2:]: deepcopy(model[selector[2:]])
        for selector in profile["sources"]["strategic_value_model"]["selectors"]
    }
    assert_check(
        schema_violations(selected, pro),
        False,
        "complete_reduced_model_selected_payload",
        checks,
    )
    for change in (False, 1):
        altered = deepcopy(selected)
        altered["valuation"]["accounting_partition_contract"]["normative_partition"][
            "mutually_exclusive_booking"
        ] = change
        assert_check(
            schema_violations(altered, pro),
            True,
            f"normative_boolean_cannot_be_{change!r}",
            checks,
        )
    no_ids = deepcopy(selected)
    no_ids["governed_by"]["invariants"] = []
    assert_check(
        schema_violations(no_ids, pro), True, "empty_min_items_with_array", checks
    )
    short = deepcopy(selected)
    short["governed_by"]["invariants"] = short["governed_by"]["invariants"][:11]
    assert_check(
        schema_violations(short, pro),
        True,
        "governed_by_requires_twelve_invariants",
        checks,
    )

    lineage = "relocated_additional_candidate_semantics"
    for label, mutate in (
        ("lineage_entry_missing", lambda p: p[lineage].pop("L9-SV-017")),
        (
            "lineage_authority_status_promoted",
            lambda p: p[lineage]["L9-SV-015"].__setitem__(
                "authority_status", "admitted_global_invariant"
            ),
        ),
        (
            "lineage_disposition_changed",
            lambda p: p[lineage]["L9-SV-019"].__setitem__("disposition", "KEEP"),
        ),
        (
            "lineage_governing_invariants_empty",
            lambda p: p[lineage]["L9-SV-020"].__setitem__("governing_invariants", []),
        ),
        (
            "lineage_governed_by_removed_candidate",
            lambda p: p[lineage]["L9-SV-016"].__setitem__(
                "governing_invariants", ["L9-SV-016"]
            ),
        ),
        (
            "lineage_meaning_not_string",
            lambda p: p[lineage]["L9-SV-018"].__setitem__("meaning", 18),
        ),
        (
            "lineage_source_id_swapped",
            lambda p: p[lineage]["L9-SV-015"].__setitem__(
                "source_candidate_id", "L9-SV-016"
            ),
        ),
    ):
        altered = deepcopy(selected)
        mutate(altered)
        assert_check(schema_violations(altered, pro), True, label, checks)

    invariant_rows = [
        {"id": i, "statement": "x", "scope": "global", "owner": "Quantum-L9/.github"}
        for i in model["governed_by"]["invariants"]
    ]
    assert_check(
        schema_violations({"invariants": invariant_rows}, pro),
        False,
        "twelve_invariant_records_positive",
        checks,
    )
    for removed in REMOVED:
        bad = deepcopy(invariant_rows)
        bad[0]["id"] = removed
        assert_check(
            schema_violations({"invariants": bad}, pro),
            True,
            f"removed_candidate_{removed}_rejected_as_invariant",
            checks,
        )
    assert_check(
        schema_violations({"invariants": invariant_rows[:11]}, pro),
        True,
        "eleven_invariant_records_rejected",
        checks,
    )

    terms = yaml.safe_load((ROOT / "overlays/vocabulary_additions.yaml").read_text())[
        "terms"
    ]
    vocab = {"terms": terms}
    assert_check(schema_violations(vocab, pro), False, "nested_terms_positive", checks)
    broken = deepcopy(vocab)
    broken["terms"]["strategic_value"]["definition"] = 9
    assert_check(
        schema_violations(broken, pro),
        True,
        "nested_terms_malformed_definition",
        checks,
    )
    assert_check(
        schema_violations({"strategic_value_model": selected}, com),
        True,
        "composition_missing_four_namespaces",
        checks,
    )
    composed_missing_lineage = {
        "strategic_value_model": {k: v for k, v in selected.items() if k != lineage}
    }
    violations = schema_violations(composed_missing_lineage, com)
    assert_check(
        violations, True, "composition_model_namespace_requires_lineage", checks
    )
    print(
        json.dumps(
            {
                "result": "NATIVE_SCHEMA_DIALECT_REGRESSIONS_PASS",
                "compiler": compiler_revision(l9_semantic_compiler),
                "check_count": len(checks),
                "checks": checks,
                "scope": "schema_violations_only_not_real_projections_or_receipts",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(
            json.dumps(
                {"result": "FAIL", "exception": type(exc).__name__, "detail": str(exc)},
                indent=2,
            )
        )
        sys.exit(1)
