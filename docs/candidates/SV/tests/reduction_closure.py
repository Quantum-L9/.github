"""Shared closure model for the two-invariant Strategic Value reduction.

Expected identities are derived from the development disposition ledger
(evidence/reduction-v1/owner-disposition-ledger.yaml); actual identities are
parsed from the candidate source files. ``closure_violations`` compares the
two and returns every mismatch, so negative tests can mutate a parsed copy and
prove each obligation is mechanically enforced.
"""

import copy
import hashlib
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "evidence" / "reduction-v1" / "owner-disposition-ledger.yaml"
DONOR = ROOT / "evidence" / "reduction-v1" / "donor"
LINEAGE = "relocated_additional_candidate_semantics"
RETAINED = "retained_former_candidate_semantics"
SELECTOR = re.compile(r'^\$\.invariants\[\?\(@\.id=="([^"]+)"\)\]$')
SOURCE_CLASSES = [
    "strategic_value_model",
    "vocabulary",
    "invariants",
    "contracts",
    "authority_model",
]


def read_yaml(rel, base=ROOT):
    return yaml.safe_load((base / rel).read_text(encoding="utf-8"))


def ledger():
    return yaml.safe_load(LEDGER_PATH.read_text(encoding="utf-8"))


def expected():
    led = ledger()
    rows = led["dispositions"]
    return {
        "new_ids": {r["candidate_id"] for r in rows if r["disposition"] == "KEEP"},
        "existing_ids": set(led["existing_governing_invariants"]),
        "selected_ids": set(led["selected_governing_invariants"]),
        "relocated": {r["candidate_id"]: r for r in rows if r["disposition"] != "KEEP"},
        "retained_former": {f"L9-SV-{n:03d}" for n in range(3, 15)},
        "authority_status": led["relocation_authority_status"],
    }


def load_sources():
    return {
        "invariants": read_yaml("overlays/invariants_additions.yaml")["invariants"],
        "contract": read_yaml("overlays/contracts_additions.yaml")["contracts"][0],
        "model": read_yaml("semantics/strategic_value_model.yaml"),
        "catalog": read_yaml("overlays/projection_profile_additions.yaml"),
        "composition": read_yaml("overlays/composition_profile_additions.yaml")[
            "profiles"
        ][0],
        "projection_schema": read_yaml(
            "semantics/strategic_planner_value_projection.schema.yaml"
        ),
        "composition_schema": read_yaml(
            "semantics/strategic_planner_value_composition.schema.yaml"
        ),
        "fixtures": json.loads(
            (ROOT / "tests" / "falsification_cases.json").read_text(encoding="utf-8")
        ),
    }


def donor_statements():
    return {
        r["id"]: r["statement"]
        for r in read_yaml("invariants_additions.yaml", DONOR)["invariants"]
    }


def profile(src):
    return src["catalog"]["projection_profiles"][0]


def selected_invariant_ids(src):
    out = []
    for selector in profile(src)["sources"]["invariants"]["selectors"]:
        match = SELECTOR.match(selector)
        out.append(match.group(1) if match else selector)
    return out


def walk(obj, path=()):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield path + (str(key),), str(key)
            yield from walk(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk(value, path + (str(index),))
    else:
        yield path, obj


def _exact(violations, label, actual_list, wanted):
    if len(actual_list) != len(set(actual_list)):
        violations.append(f"{label}: duplicate IDs {sorted(actual_list)}")
    if set(actual_list) != wanted:
        violations.append(
            f"{label}: missing {sorted(wanted - set(actual_list))} "
            f"extra {sorted(set(actual_list) - wanted)}"
        )


def closure_violations(src):
    exp = expected()
    v = []
    removed = set(exp["relocated"])

    overlay_ids = [r["id"] for r in src["invariants"]]
    _exact(v, "proposed overlay", overlay_ids, exp["new_ids"])
    if (
        len(exp["new_ids"]) != 2
        or len(exp["existing_ids"]) != 10
        or len(exp["selected_ids"]) != 12
    ):
        v.append("ledger cardinality is not 2 new + 10 existing = 12 selected")
    _exact(
        v,
        "model governed_by.invariants",
        list(src["model"]["governed_by"]["invariants"]),
        exp["selected_ids"],
    )
    _exact(
        v,
        "contract source_invariants",
        list(src["contract"]["source_invariants"]),
        exp["selected_ids"],
    )
    _exact(
        v,
        "profile invariant selectors",
        selected_invariant_ids(src),
        exp["selected_ids"],
    )

    ps, cs = src["projection_schema"], src["composition_schema"]
    for label, desc in (
        ("projection schema", ps["properties"]["invariants"]),
        (
            "composition schema",
            cs["properties"]["invariants"]["properties"]["invariants"],
        ),
    ):
        _exact(
            v,
            f"{label} invariant enum",
            list(desc["items"]["properties"]["id"]["enum"]),
            exp["selected_ids"],
        )
        if desc.get("min_items") != 12:
            v.append(f"{label} invariant min_items {desc.get('min_items')} != 12")
    if (
        ps["properties"]["invariants"]
        != cs["properties"]["invariants"]["properties"]["invariants"]
    ):
        v.append("projection and composition invariant descriptors differ")
    for label, gov in (
        ("projection", ps["properties"]["governed_by"]),
        (
            "composition",
            cs["properties"]["strategic_value_model"]["properties"]["governed_by"],
        ),
    ):
        if gov["properties"]["invariants"].get("min_items") != 12:
            v.append(f"{label} schema governed_by.invariants min_items != 12")
        _exact(
            v,
            f"{label} schema governed_by.invariants enum",
            list(gov["properties"]["invariants"].get("items", {}).get("enum", [])),
            exp["selected_ids"],
        )

    # Lineage ledgers: exact coverage, verbatim meaning, live destinations.
    if set(src["model"].get(RETAINED, {})) != exp["retained_former"]:
        v.append("retained_former_candidate_semantics is not exactly L9-SV-003..014")
    lineage = src["model"].get(LINEAGE, {})
    if set(lineage) != removed:
        v.append(f"{LINEAGE} keys {sorted(lineage)} != {sorted(removed)}")
    requires = src["contract"]["requires"]
    statements = donor_statements()
    for cid, row in exp["relocated"].items():
        rec = lineage.get(cid)
        if rec is None:
            continue
        want = {
            "source_candidate_id": cid,
            "meaning": statements[cid],
            "disposition": row["disposition"],
            "governing_invariants": row["governing_invariant_refs"],
            "model_section": row["model_section"],
            "contract_obligation": row["contract_obligation_refs"][0],
            "when": row["when"],
            "authority_status": exp["authority_status"],
        }
        for key, value in want.items():
            if rec.get(key) != value:
                v.append(f"{cid}.{key} does not match ledger/donor")
        node = src["model"]
        for part in row["model_section"].split("."):
            if not isinstance(node, dict) or part not in node:
                v.append(f"{cid}: model section {row['model_section']} missing")
                break
            node = node[part]
        else:
            if not node:
                v.append(f"{cid}: model section {row['model_section']} is empty")
        for ob in row["contract_obligation_refs"]:
            if ob not in requires:
                v.append(f"{cid}: contract obligation {ob} missing from requires")
        for ref in row["governing_invariant_refs"]:
            if ref not in exp["selected_ids"]:
                v.append(f"{cid}: governing ref {ref} not selected")
    for cid, row in exp["relocated"].items():
        if row["candidate_id"] == "L9-SV-020":
            for ref in ("L9-EVIDENCE-001", "L9-ASSURANCE-001"):
                if ref not in src["model"]["governed_by"]["invariants"]:
                    v.append(f"L9-SV-020 reuse requires {ref} in model governance")

    # Removed candidate IDs: lineage-only contexts.
    permitted = {
        "model": [(LINEAGE,)],
        "contract": [],
        "profile": [],
        "invariants": [],
        "projection_schema": [("properties", LINEAGE)],
        "composition_schema": [
            ("properties", "strategic_value_model", "properties", LINEAGE)
        ],
    }
    targets = {
        "model": src["model"],
        "contract": src["contract"],
        "profile": profile(src),
        "invariants": src["invariants"],
        "projection_schema": ps,
        "composition_schema": cs,
    }
    for label, obj in targets.items():
        for path, value in walk(obj):
            if (
                isinstance(value, str)
                and any(cid in value for cid in removed)
                and not any(path[: len(p)] == p for p in permitted[label])
            ):
                v.append(
                    f"{label}: removed candidate ID in normative context {'/'.join(path)}"
                )

    # Projection/composition shape closure.
    prof = profile(src)
    if list(prof["sources"]) != SOURCE_CLASSES:
        v.append("profile source classes drifted")
    if cs["required"] != SOURCE_CLASSES or set(cs["properties"]) - {"schema"} != set(
        SOURCE_CLASSES
    ):
        v.append(
            "composition schema namespaces are not exactly the five source classes"
        )
    model_keys = [s[2:] for s in prof["sources"]["strategic_value_model"]["selectors"]]
    if len(model_keys) != len(set(model_keys)):
        v.append("duplicate model selectors")
    svm = cs["properties"]["strategic_value_model"]
    for key in model_keys:
        if key not in src["model"]:
            v.append(f"model selector {key} does not resolve")
        if key not in ps["properties"] or key not in svm["properties"]:
            v.append(f"model selector {key} absent from a payload schema")
    if set(svm["required"]) != set(model_keys):
        v.append("composition model namespace required keys != model selectors")
    for label, desc in (
        ("projection", ps["properties"].get(LINEAGE)),
        ("composition", svm["properties"].get(LINEAGE)),
    ):
        if not desc or set(desc.get("required", [])) != set(lineage):
            v.append(f"{label} schema lineage required != model lineage keys")
            continue
        for cid in lineage:
            entry = desc["properties"][cid]["properties"]
            if (
                entry["source_candidate_id"].get("const") != cid
                or entry["authority_status"].get("const") != exp["authority_status"]
                or entry["disposition"].get("const")
                != exp["relocated"][cid]["disposition"]
            ):
                v.append(f"{label} schema lineage {cid} constants drifted")
            for field in ("meaning", "model_section", "contract_obligation", "when"):
                if entry[field].get("const") != lineage[cid].get(field):
                    v.append(
                        f"{label} schema lineage {cid}.{field} not pinned to model"
                    )
            gi = entry["governing_invariants"]
            if gi.get("type") != "array" or gi.get("min_items", 0) < 1:
                v.append(
                    f"{label} schema lineage {cid} governing_invariants accepts empty array"
                )
            _exact(
                v,
                f"{label} schema lineage {cid} governing_invariants enum",
                list(gi.get("items", {}).get("enum", [])),
                exp["selected_ids"],
            )

    # Normative booleans must be pinned to their source truth.
    for label, schema, prefix in (
        ("projection", ps, ("properties",)),
        ("composition", cs, ("properties", "strategic_value_model", "properties")),
    ):
        for path, node in _dict_nodes(schema):
            if node.get("type") != "boolean" or path[: len(prefix)] != prefix:
                continue
            value = src["model"]
            for key in path[len(prefix) :]:
                if key != "properties":
                    value = value[key]
            if node.get("const") is not value:
                v.append(
                    f"{label} schema boolean {'/'.join(path)} not pinned to source {value!r}"
                )

    # Falsifier fixtures carry lineage, never an invariant claim.
    for case in src["fixtures"]["cases"]:
        if "invariant_ref" in case or "source_invariant" in case:
            v.append(f"{case['case_id']}: fixture still claims a source invariant")
        row = exp["relocated"].get(case.get("origin_candidate_id"))
        if (
            row is None
            or row["falsifier_case_ref"] != case["case_id"]
            or case["governing_invariants"] != row["governing_invariant_refs"]
            or case["contract_obligation"] != row["contract_obligation_refs"][0]
            or case["disposition"] != row["disposition"]
        ):
            v.append(f"{case['case_id']}: fixture lineage does not match ledger")
    return v


def _dict_nodes(obj, path=()):
    if isinstance(obj, dict):
        yield path, obj
        for key, value in obj.items():
            yield from _dict_nodes(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _dict_nodes(value, path + (str(index),))


def mutated(src, fn):
    out = copy.deepcopy(src)
    fn(out)
    return out


PRODUCER_RECEIPT_KEYS = {
    "schema",
    "receipt_type",
    "producer_identity",
    "governing_coordinates",
    "inputs",
    "output",
    "profile",
    "verification_basis",
    "result",
    "receipt_digest",
}


def producer_receipt_problems(receipt):
    """Structural provenance gate: a local falsifier result is not a producer receipt."""
    problems = []
    if not isinstance(receipt, dict):
        return ["not a mapping"]
    missing = PRODUCER_RECEIPT_KEYS - set(receipt)
    if missing:
        problems.append(f"missing producer fields {sorted(missing)}")
    if receipt.get("schema") != "l9.compiler-receipt/v1":
        problems.append("schema is not l9.compiler-receipt/v1")
    if receipt.get("receipt_type") != "l9.receipt/compilation@1":
        problems.append("receipt_type is not a compilation receipt")
    if (receipt.get("producer_identity") or {}).get(
        "compiler"
    ) != "l9-semantic-compiler":
        problems.append("producer is not the L9 semantic compiler")
    if "assurance" in receipt and "LOCAL" in str(receipt["assurance"]):
        problems.append("self-declared local assurance")
    return problems


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checksum_mismatches(root):
    """The package checksum gate: every SHA256SUMS.txt entry must hash to its bytes."""
    root = Path(root)
    bad = []
    for line in (root / "SHA256SUMS.txt").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        path = root / rel
        if not path.exists() or sha256_file(path) != digest:
            bad.append(rel)
    return bad
