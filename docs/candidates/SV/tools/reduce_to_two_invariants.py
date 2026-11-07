#!/usr/bin/env python3
"""Deterministic constitutional reduction of the PR #212 Strategic Value candidate.

Inputs (never modified):
  evidence/reduction-v1/donor/*                    frozen PR #212 bytes (85531616)
  evidence/reduction-v1/owner-disposition-ledger.yaml  development disposition

Outputs (candidate-package files only):
  overlays/invariants_additions.yaml
  overlays/contracts_additions.yaml
  overlays/projection_profile_additions.yaml
  semantics/strategic_value_model.yaml
  semantics/strategic_planner_value_projection.schema.yaml
  semantics/strategic_planner_value_composition.schema.yaml
  tests/falsification_cases.json

The transformation is a pure function of the donor bytes and the ledger, so
``--check`` proves the committed reduced files are exactly the declared
reduction and nothing else. It never touches a canonical checkout, never
commits, pushes, or admits anything.

Run:  python tools/reduce_to_two_invariants.py [--check]
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DONOR = ROOT / "evidence" / "reduction-v1" / "donor"
LEDGER = ROOT / "evidence" / "reduction-v1" / "owner-disposition-ledger.yaml"

DONOR_SHA256 = {
    "invariants_additions.yaml": "b259540393a1e30573e09317760ea9919ccc049f87a461a10c62c9bd26aa48f3",
    "contracts_additions.yaml": "b2aa7ac2f93b2cfe689d851fddc9adfdc6f618d95150f7cd5a69774d377c2f72",
    "projection_profile_additions.yaml": "ee3722c3178ab41c98f65ef76b11f6b268dd59eef59d2e2a5fe75b655a9e21c5",
    "strategic_value_model.yaml": "189e44474315ed5c5770a6d1246264297a0dddaf7d704f45d5a1611d7e237088",
    "strategic_planner_value_projection.schema.yaml": "10323a7b8bf729db1ef811e511ebd9c434477090d957a95178ae1a2fc4813730",
    "strategic_planner_value_composition.schema.yaml": "79643fb3c5031074d5b3153173329bcc10d3cffdf54050861f179fc714ea48dc",
    "falsification_cases.json.pr212": "ee597f3f8d8254254db787587f4ef01beb3dac20f69e67e5ff57601bb54fa819",
}

# Line widths at which each donor file round-trips byte-for-byte through
# yaml.safe_dump(sort_keys=False); keeping them makes the diff semantic only.
WIDTH = {
    "invariants_additions.yaml": 150,
    "contracts_additions.yaml": 150,
    "projection_profile_additions.yaml": 135,
    "strategic_value_model.yaml": 135,
    "strategic_planner_value_projection.schema.yaml": 108,
    "strategic_planner_value_composition.schema.yaml": 110,
}

KEPT = ("L9-SV-001", "L9-SV-002")
RELOCATED = tuple(f"L9-SV-{n:03d}" for n in range(15, 21))
LINEAGE_KEY = "relocated_additional_candidate_semantics"
RETAINED_KEY = "retained_former_candidate_semantics"
LINEAGE_FIELDS = (
    "source_candidate_id",
    "meaning",
    "disposition",
    "governing_invariants",
    "model_section",
    "contract_obligation",
    "when",
    "authority_status",
)


def dump(obj, width):
    return yaml.safe_dump(obj, sort_keys=False, width=width, allow_unicode=True)


def load_donor():
    donor = {}
    for name, digest in DONOR_SHA256.items():
        data = (DONOR / name).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != digest:
            raise ValueError(f"donor {name} digest {actual} != frozen {digest}")
        donor[name] = data.decode("utf-8")
        if (
            name in WIDTH
            and dump(yaml.safe_load(donor[name]), WIDTH[name]) != donor[name]
        ):
            raise ValueError(
                f"donor {name} no longer round-trips at width {WIDTH[name]}"
            )
    return donor


def load_ledger():
    ledger = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    ids = [row["candidate_id"] for row in ledger["dispositions"]]
    if ids != list(KEPT + RELOCATED):
        raise ValueError(
            f"ledger must disposition exactly {KEPT + RELOCATED}, got {ids}"
        )
    selected = ledger["selected_governing_invariants"]
    if len(selected) != 12 or len(set(selected)) != 12:
        raise ValueError(
            "ledger must select exactly twelve unique governing invariants"
        )
    if list(selected[:2]) != list(KEPT) or set(selected[2:]) != set(
        ledger["existing_governing_invariants"]
    ):
        raise ValueError(
            "ledger selection must be the two kept IDs plus the ten existing IDs"
        )
    for row in ledger["dispositions"]:
        if (
            row["owner_decision_ref"] is not None
            or row["owner_decision_status"] != "pending"
        ):
            raise ValueError(
                f"{row['candidate_id']}: development ledger cannot carry an owner decision"
            )
        for ref in row["governing_invariant_refs"]:
            if ref not in selected:
                raise ValueError(
                    f"{row['candidate_id']}: governing ref {ref} is not selected"
                )
    return ledger


def insert_after(mapping, anchor, key, value):
    if anchor not in mapping or key in mapping:
        raise ValueError(f"cannot insert {key} after {anchor}")
    out = {}
    for k, v in mapping.items():
        out[k] = v
        if k == anchor:
            out[key] = value
    return out


def lineage_records(ledger, donor_statements):
    rows = {r["candidate_id"]: r for r in ledger["dispositions"]}
    records = {}
    for cid in RELOCATED:
        row = rows[cid]
        records[cid] = {
            "source_candidate_id": cid,
            "meaning": donor_statements[cid],
            "disposition": row["disposition"],
            "governing_invariants": list(row["governing_invariant_refs"]),
            "model_section": row["model_section"],
            "contract_obligation": row["contract_obligation_refs"][0],
            "when": row["when"],
            "authority_status": ledger["relocation_authority_status"],
        }
    return records


def lineage_descriptor(records, selected):
    required = list(records)
    properties = {}
    for cid, rec in records.items():
        properties[cid] = {
            "type": "object",
            "required": list(LINEAGE_FIELDS),
            "properties": {
                "source_candidate_id": {"const": cid},
                "meaning": {"const": rec["meaning"]},
                "disposition": {"const": rec["disposition"]},
                "governing_invariants": {
                    "type": "array",
                    "min_items": 1,
                    "items": {"type": "string", "enum": list(selected)},
                },
                "model_section": {"const": rec["model_section"]},
                "contract_obligation": {"const": rec["contract_obligation"]},
                "when": {"const": rec["when"]},
                "authority_status": {"const": rec["authority_status"]},
            },
        }
    return {"type": "object", "required": required, "properties": properties}


def reduce(donor, ledger):
    selected = list(ledger["selected_governing_invariants"])
    rows = {r["candidate_id"]: r for r in ledger["dispositions"]}
    out = {}

    # 1. Invariant overlay: exactly two entries.
    inv = yaml.safe_load(donor["invariants_additions.yaml"])
    statements = {r["id"]: r["statement"] for r in inv["invariants"]}
    if set(statements) != set(KEPT + RELOCATED):
        raise ValueError(
            "donor invariant overlay is not the eight-ID PR #212 candidate"
        )
    kept_rows = []
    for row in inv["invariants"]:
        if row["id"] not in KEPT:
            continue
        row = dict(row)
        if row["id"] == "L9-SV-001":
            row["statement"] = rows["L9-SV-001"]["amended_statement"].strip()
        kept_rows.append(row)
    out["overlays/invariants_additions.yaml"] = dump(
        {"invariants": kept_rows}, WIDTH["invariants_additions.yaml"]
    )

    # 2. Assessment contract: twelve governing invariants, obligations untouched.
    con = yaml.safe_load(donor["contracts_additions.yaml"])
    if len(con["contracts"]) != 1:
        raise ValueError("donor contract overlay must hold one contract")
    con["contracts"][0]["source_invariants"] = selected
    out["overlays/contracts_additions.yaml"] = dump(
        con, WIDTH["contracts_additions.yaml"]
    )

    # 3. Model: governing law references plus the relocation lineage ledger.
    model = yaml.safe_load(donor["strategic_value_model.yaml"])
    model["governed_by"]["invariants"] = selected
    records = lineage_records(ledger, statements)
    model = insert_after(model, RETAINED_KEY, LINEAGE_KEY, records)
    out["semantics/strategic_value_model.yaml"] = dump(
        model, WIDTH["strategic_value_model.yaml"]
    )

    # 4. Projection profile: twelve invariant selectors, one new model selector.
    prof = yaml.safe_load(donor["projection_profile_additions.yaml"])
    p = prof["projection_profiles"][0]
    p["sources"]["invariants"]["selectors"] = [
        f'$.invariants[?(@.id=="{i}")]' for i in selected
    ]
    model_sel = p["sources"]["strategic_value_model"]["selectors"]
    anchor = model_sel.index("$." + RETAINED_KEY)
    model_sel.insert(anchor + 1, "$." + LINEAGE_KEY)
    out["overlays/projection_profile_additions.yaml"] = dump(
        prof, WIDTH["projection_profile_additions.yaml"]
    )

    # 5. Payload schemas regenerated from the selection and the lineage ledger.
    descriptor = lineage_descriptor(records, selected)
    ps = yaml.safe_load(donor["strategic_planner_value_projection.schema.yaml"])
    ps["properties"]["governed_by"]["properties"]["invariants"]["min_items"] = len(
        selected
    )
    ps["properties"]["governed_by"]["properties"]["invariants"]["items"]["enum"] = list(
        selected
    )
    ps["properties"]["invariants"]["min_items"] = len(selected)
    ps["properties"]["invariants"]["items"]["properties"]["id"]["enum"] = list(selected)
    ps["properties"] = insert_after(
        ps["properties"], RETAINED_KEY, LINEAGE_KEY, copy.deepcopy(descriptor)
    )
    out["semantics/strategic_planner_value_projection.schema.yaml"] = dump(
        ps, WIDTH["strategic_planner_value_projection.schema.yaml"]
    )

    cs = yaml.safe_load(donor["strategic_planner_value_composition.schema.yaml"])
    svm = cs["properties"]["strategic_value_model"]
    svm["properties"]["governed_by"]["properties"]["invariants"]["min_items"] = len(
        selected
    )
    svm["properties"]["governed_by"]["properties"]["invariants"]["items"]["enum"] = (
        list(selected)
    )
    req = svm["required"]
    req.insert(req.index(RETAINED_KEY) + 1, LINEAGE_KEY)
    svm["properties"] = insert_after(
        svm["properties"], RETAINED_KEY, LINEAGE_KEY, copy.deepcopy(descriptor)
    )
    cs["properties"]["invariants"]["properties"]["invariants"] = copy.deepcopy(
        ps["properties"]["invariants"]
    )
    out["semantics/strategic_planner_value_composition.schema.yaml"] = dump(
        cs, WIDTH["strategic_planner_value_composition.schema.yaml"]
    )

    # 6. Falsifier fixtures: candidate lineage, never a canonical invariant claim.
    fx = json.loads(donor["falsification_cases.json.pr212"])
    fx["description"] = (
        "Six independently executable contract falsifiers for the safeguards formerly proposed as "
        "L9-SV-015..020. Those IDs are historical candidate lineage, not admitted invariants; each "
        "case is bound to its governing invariants and assessment-contract obligation. Successful "
        "positive controls are declarations, not external numerical, calibration, or causal proof."
    )
    by_case = {
        r["falsifier_case_ref"]: r
        for r in ledger["dispositions"]
        if r["candidate_id"] in RELOCATED
    }
    cases = []
    for case in fx["cases"]:
        row = by_case[case["case_id"]]
        if case.pop("invariant_ref") != row["candidate_id"]:
            raise ValueError(f"{case['case_id']}: donor fixture lineage mismatch")
        if case["expected_failure"] != row["expected_negative_result"]:
            raise ValueError(f"{case['case_id']}: expected failure drift")
        rebuilt = {
            "case_id": case["case_id"],
            "origin_candidate_id": row["candidate_id"],
            "disposition": row["disposition"],
            "governing_invariants": list(row["governing_invariant_refs"]),
            "contract_obligation": row["contract_obligation_refs"][0],
        }
        rebuilt.update({k: v for k, v in case.items() if k != "case_id"})
        cases.append(rebuilt)
    lines = [
        "{",
        f'  "schema": {json.dumps(fx["schema"])},',
        f'  "description": {json.dumps(fx["description"])},',
        '  "cases": [',
    ]
    lines += [
        "    "
        + json.dumps(c, separators=(",", ":"))
        + ("," if i < len(cases) - 1 else "")
        for i, c in enumerate(cases)
    ]
    lines += ["  ]", "}", ""]
    out["tests/falsification_cases.json"] = "\n".join(lines)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed files equal the reduction",
    )
    args = parser.parse_args()
    try:
        produced = reduce(load_donor(), load_ledger())
    except (ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        print(f"BLOCKED={exc}", file=sys.stderr)
        return 2
    drift = []
    for rel, text in produced.items():
        path = ROOT / rel
        # JSON outputs are owned by the Biome formatter in CI, so they are compared
        # by parsed content; YAML outputs are compared byte for byte.
        same = path.exists() and (
            json.loads(path.read_text(encoding="utf-8")) == json.loads(text)
            if rel.endswith(".json")
            else path.read_text(encoding="utf-8") == text
        )
        if args.check:
            if not same:
                drift.append(rel)
        elif not same:
            path.write_text(text, encoding="utf-8")
        print(
            ("CHECK " if args.check else "WROTE ")
            + rel
            + " sha256="
            + hashlib.sha256(text.encode("utf-8")).hexdigest()
        )
    if drift:
        print("DRIFT=" + ",".join(drift), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
