#!/usr/bin/env python3
"""Prepare the GT canonical candidate files on top of the exact SV #215 candidate.

Two stages, never combined:

* ``--stage core`` (default; successor release A). The target is a disposable
  clone at ``canonical_target`` on which the SV candidate applier from PR #215
  at its pinned head has already been run. Every SV-applied file must match the
  digest recorded in ``evidence/sv_alignment_binding.json``; nothing else may be
  dirty. GT core is then layered on: L9-GT-001, the GT core contract, twelve GT
  terms, the GT projection profile and its forbidden-constraint definition, the
  GT composition profile, both payload schemas and their manifest registration.
  The GT+SV dependent contract is NOT applied in this stage.

* ``--stage dependent`` (successor release B). Refuses unless the binding file
  records ``admitted_foundation_revision`` (set only by a reviewed commit after
  SV and GT core are admitted at one canonical revision), the checkout is clean
  at exactly that revision, and that revision carries the admitted SV model,
  SV contract, both SV invariants and the GT core. No flag bypasses this.

Dry-run by default. ``--apply --disposable`` writes local files only and refuses
the checkout that carries this pack. Every check runs on the fully assembled
candidate before any byte is written; writes are staged then renamed. The script
never commits, pushes, opens PRs, runs release gates or admits semantics.
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

ROOT = Path(__file__).resolve().parent
BINDING = json.loads(
    (ROOT / "evidence/sv_alignment_binding.json").read_text(encoding="utf-8")
)

CANONICAL_TARGET = BINDING["canonical_target"]
SV_CANDIDATE_HEAD = BINDING["sv_candidate"]["head"]
SV_APPLIED_SHA256 = BINDING["sv_applied_target_sha256"]
ADMITTED_FOUNDATION_REVISION = BINDING["admitted_foundation_revision"]

SV_NEW_INVARIANTS = frozenset(BINDING["sv_new_invariants"])
SV_LINEAGE_ONLY = frozenset(BINDING["sv_lineage_only_ids"])
SV_TERMS = tuple(BINDING["sv_vocabulary_terms"])
SV_MODEL_ID = BINDING["sv_model"]
SV_CONTRACT_ID = BINDING["sv_contract"]
SV_PROFILE_ID = BINDING["sv_projection"]
SV_COMPOSITION_ID = BINDING["sv_composition"]

GT_INVARIANT = "L9-GT-001"
GT_CORE_CONTRACT_ID = "l9.contract/strategic-interaction-assessment@1"
GT_DEPENDENT_CONTRACT_ID = "l9.contract/strategic-value-interaction-composition@1"
GT_PROFILE_ID = "l9.projection/strategic-planner-interaction@1"
GT_COMPOSITION_ID = "l9.compose/strategic-planner-interaction@1"
GT_OUTPUT = "l9.projection.strategic-planner-interaction/v1"
GT_COMPOSED_OUTPUT = "l9.composed-projection.strategic-planner-interaction/v1"
GT_FORBIDDEN = "sv_semantic_records_excluded_from_gt_projection"
GT_SOURCE_CLASSES = ("vocabulary", "invariants", "contracts")
GT_GOVERNING = (
    "L9-GT-001",
    "L9-AUTH-002",
    "L9-HARD-001",
    "L9-UNKNOWN-001",
    "L9-EVIDENCE-001",
    "L9-ASSURANCE-001",
)
GT_SCHEMA_FILES = (
    "strategic_interaction_projection.schema.yaml",
    "strategic_interaction_composition.schema.yaml",
)
SV_SCHEMA_FILES = (
    "strategic_planner_value_projection.schema.yaml",
    "strategic_planner_value_composition.schema.yaml",
)
INVARIANTS = "semantics/invariants.yaml"
CONTRACTS = "semantics/contracts.yaml"
VOCABULARY = "semantics/vocabulary.yaml"
PROJECTION_PROFILES = "semantics/projection_profiles.yaml"
COMPOSITION_PROFILES = "semantics/composition_profiles.yaml"
MANIFEST = "semantics/generic_compiler_manifest.yaml"
VALUE_MODEL = "semantics/strategic_value_model.yaml"
LEDGERS = {
    "invariants": INVARIANTS,
    "contracts": CONTRACTS,
    "vocabulary": VOCABULARY,
    "projection_profiles": PROJECTION_PROFILES,
    "composition_profiles": COMPOSITION_PROFILES,
    "model": VALUE_MODEL,
}
FORBIDDEN_OVERLAY = "overlays/projection_forbidden_constraint_additions.yaml"
INVARIANT_SELECTOR = re.compile(r'^\$\.invariants\[\?\(@\.id=="([^"]+)"\)\]$')
CONTRACT_SELECTOR = re.compile(r'^\$\.contracts\[\?\(@\.id=="([^"]+)"\)\]$')


def raw(name):
    return (ROOT / name).read_text(encoding="utf-8")


def overlay(name):
    return yaml.safe_load(raw(name))


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def one(text, anchor, replacement, path):
    if text.count(anchor) != 1:
        raise ValueError(
            f"{path}: expected one anchor {anchor!r}, found {text.count(anchor)}"
        )
    return text.replace(anchor, replacement, 1)


def unique_ids(rows, label):
    ids = [row["id"] for row in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"{label} duplicate IDs: {dupes}")
    return ids


def merge_list(base, extra, list_name):
    """Append an overlay's top-level list; reject duplicates inside and across."""
    old_ids = unique_ids(yaml.safe_load(base)[list_name], f"canonical {list_name}")
    new_ids = unique_ids(yaml.safe_load(extra)[list_name], f"overlay {list_name}")
    collisions = sorted(set(old_ids) & set(new_ids))
    if collisions:
        raise ValueError(f"overlay {list_name} collides with canonical: {collisions}")
    if not re.search(rf"^{list_name}:\n(?:- | {{2}})", base, flags=re.MULTILINE):
        raise ValueError(f"canonical {list_name} is not a top-level block list")
    tail = list(yaml.safe_load(base))[-1]
    if tail != list_name:
        raise ValueError(f"canonical {list_name} is not the final section ({tail})")
    return (
        base.rstrip()
        + "\n"
        + extra.split(list_name + ":", 1)[1].lstrip("\n").rstrip()
        + "\n"
    )


def update_contract_derivation(text, old_inv, new_inv, old_count, new_count):
    """Rebind contracts.yaml#derivation, verifying the old binding first."""
    old_digest, new_digest = sha256_text(old_inv), sha256_text(new_inv)
    derivation = yaml.safe_load(text)["derivation"]
    if derivation["source_digest_sha256"] != old_digest:
        raise ValueError(
            "stale contracts derivation digest "
            f"{derivation['source_digest_sha256']} != current invariants {old_digest}"
        )
    if derivation["source_invariant_count"] != old_count:
        raise ValueError(
            "contracts derivation count "
            f"{derivation['source_invariant_count']} != current invariants {old_count}"
        )
    text, n1 = re.subn(
        r"^( {2}source_digest_sha256: )[a-f0-9]{64}$",
        r"\g<1>" + new_digest,
        text,
        flags=re.MULTILINE,
    )
    text, n2 = re.subn(
        r"^( {2}source_invariant_count: )[0-9]+$",
        r"\g<1>" + str(new_count),
        text,
        flags=re.MULTILINE,
    )
    if (n1, n2) != (1, 1):
        raise ValueError("contracts derivation anchors not replaced exactly once")
    after = yaml.safe_load(text)["derivation"]
    if (after["source_digest_sha256"], after["source_invariant_count"]) != (
        new_digest,
        new_count,
    ):
        raise ValueError("contracts derivation not rebound to candidate invariants")
    return text


def rebind_source_artifacts(text, path, old, new):
    """Rebind ``derivation.source_artifacts`` entries naming a changed artifact.

    Same procedure as the SV #215 applier and Semantic Foundation v3.8.0
    (2ae5dfa): each recorded digest/item_count must equal the CURRENT canonical
    value before replacement; anything stale fails closed. Whether a derived
    ledger's content must change is an owner decision this does not make.
    """
    derivation = yaml.safe_load(text).get("derivation") or {}
    entries = [
        e for e in derivation.get("source_artifacts") or [] if e.get("artifact") in new
    ]
    if not entries:
        return text, []
    lines = text.split("\n")
    rebound = []
    for entry in entries:
        name = entry["artifact"]
        if entry.get("sha256") != old[name][0]:
            raise ValueError(f"{path}: stale derivation digest for {name}")
        if "item_count" in entry and entry["item_count"] != old[name][1]:
            raise ValueError(f"{path}: stale derivation item_count for {name}")
        starts = [
            i for i, line in enumerate(lines) if line.strip() == f"- artifact: {name}"
        ]
        if len(starts) != 1:
            raise ValueError(f"{path}: expected one derivation entry for {name}")
        i = starts[0] + 1
        indent = len(lines[starts[0]]) - len(lines[starts[0]].lstrip()) + 2
        replaced = set()
        while (
            i < len(lines)
            and len(lines[i]) - len(lines[i].lstrip()) >= indent
            and not lines[i].strip().startswith("- ")
        ):
            key = lines[i].strip().split(":", 1)[0]
            if key == "sha256":
                lines[i] = " " * indent + "sha256: " + new[name][0]
                replaced.add(key)
            elif key == "item_count":
                lines[i] = " " * indent + "item_count: " + str(new[name][1])
                replaced.add(key)
            i += 1
        expected = {"sha256"} | ({"item_count"} if "item_count" in entry else set())
        if replaced != expected:
            raise ValueError(f"{path}: derivation entry for {name} not rebound once")
        rebound.append(name)
    out = "\n".join(lines)
    check = {
        e["artifact"]: e for e in yaml.safe_load(out)["derivation"]["source_artifacts"]
    }
    for name in rebound:
        if check[name]["sha256"] != new[name][0]:
            raise ValueError(f"{path}: derivation rebind of {name} did not take effect")
    return out, rebound


def rebind_derived_ledgers(checkout, changed):
    """Propagate digest changes through every registered derivation record."""

    def stats(text, rel):
        key = {"invariants.yaml": "invariants", "contracts.yaml": "contracts"}.get(
            Path(rel).name
        )
        return sha256_text(text), (len(yaml.safe_load(text)[key]) if key else None)

    report, derived = {}, set()
    for _ in range(8):
        old, new = {}, {}
        for rel, text in changed.items():
            if (checkout / rel).exists():
                name = Path(rel).name
                old[name] = stats((checkout / rel).read_text(encoding="utf-8"), rel)
                new[name] = stats(text, rel)
        progressed = False
        for path in sorted((checkout / "semantics").glob("*.yaml")):
            rel = "semantics/" + path.name
            original = path.read_text(encoding="utf-8")
            base = changed.get(rel, original)
            moved = {k: v for k, v in new.items() if v != old[k]}
            _, names = rebind_source_artifacts(original, rel, old, moved)
            if not names:
                continue
            current = {
                e["artifact"]: e["sha256"]
                for e in yaml.safe_load(base)["derivation"]["source_artifacts"]
            }
            if all(current[n] == new[n][0] for n in names):
                continue
            if rel in changed and rel not in derived and changed[rel] != original:
                raise ValueError(f"{rel}: derived ledger is also a content destination")
            changed[rel], _ = rebind_source_artifacts(
                original, rel, old, {n: new[n] for n in names}
            )
            derived.add(rel)
            report[rel] = names
            progressed = True
        if not progressed:
            return report
    raise ValueError("derivation rebinding did not reach a fixpoint")


def git(checkout, *cmd):
    return subprocess.run(
        ["git", "-C", str(checkout), *cmd], capture_output=True, text=True, check=True
    ).stdout


def dirty_paths(checkout):
    out = git(checkout, "status", "--porcelain", "--untracked-files=all")
    return {line[3:] for line in out.splitlines() if line.strip()}


def verify_sv_applied_target(checkout):
    """The checkout must be canonical_target plus exactly the pinned SV application."""
    head = git(checkout, "rev-parse", "HEAD").strip()
    if head != CANONICAL_TARGET:
        raise ValueError(f"wrong target HEAD {head}; expected {CANONICAL_TARGET}")
    dirty = dirty_paths(checkout)
    if dirty != set(SV_APPLIED_SHA256):
        raise ValueError(
            "dirty paths are not exactly the SV #215 application: "
            f"missing={sorted(set(SV_APPLIED_SHA256) - dirty)} "
            f"extra={sorted(dirty - set(SV_APPLIED_SHA256))}"
        )
    for rel, expected in SV_APPLIED_SHA256.items():
        actual = hashlib.sha256((checkout / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"{rel}: SV-applied digest {actual} != pinned {expected}")


def verify_sv_core_present(docs):
    """Assert the SV candidate semantics GT depends on are present and reduced."""
    inv_ids = {r["id"] for r in docs["invariants"]["invariants"]}
    sv_ids = {i for i in inv_ids if i.startswith("L9-SV-")}
    if sv_ids != SV_NEW_INVARIANTS:
        raise ValueError(f"SV invariants must be exactly {sorted(SV_NEW_INVARIANTS)}")
    if SV_LINEAGE_ONLY & inv_ids:
        raise ValueError("lineage-only SV IDs present as invariants")
    if [c["id"] for c in docs["contracts"]["contracts"]].count(SV_CONTRACT_ID) != 1:
        raise ValueError("SV assessment contract must be present exactly once")
    missing = [t for t in SV_TERMS if t not in docs["vocabulary"]["terms"]]
    if missing or len(SV_TERMS) != 11:
        raise ValueError(f"SV vocabulary not exactly eleven present terms: {missing}")
    if docs["model"].get("artifact_id") != SV_MODEL_ID:
        raise ValueError("SV value model missing")
    profiles = docs["projection_profiles"]["projection_profiles"]
    sv_profile = [p for p in profiles if p["id"] == SV_PROFILE_ID]
    if len(sv_profile) != 1 or list(sv_profile[0]["sources"]) != list(
        BINDING["sv_source_classes"]
    ):
        raise ValueError("SV projection profile missing or not the five source classes")
    if [p["id"] for p in docs["composition_profiles"]["profiles"]].count(
        SV_COMPOSITION_ID
    ) != 1:
        raise ValueError("SV composition profile missing")


def _gt_profile(doc):
    rows = [p for p in doc["projection_profiles"] if p["id"] == GT_PROFILE_ID]
    if len(rows) != 1:
        raise ValueError("GT projection profile must exist exactly once")
    return rows[0]


def _verify_gt_law(docs):
    """One new invariant, the core contract over exactly the six governing IDs, no stage-B contract."""
    inv_ids = set(unique_ids(docs["invariants"]["invariants"], "invariants"))
    gt_new = {
        r["id"] for r in overlay("overlays/invariants_additions.yaml")["invariants"]
    }
    if gt_new != {GT_INVARIANT}:
        raise ValueError(f"GT must add exactly one invariant, got {sorted(gt_new)}")
    if not set(GT_GOVERNING) <= inv_ids:
        raise ValueError("GT governing invariants do not all resolve")
    contracts = docs["contracts"]["contracts"]
    if GT_DEPENDENT_CONTRACT_ID in unique_ids(contracts, "contracts"):
        raise ValueError(
            "the GT+SV dependent contract must not be applied in stage core"
        )
    core = [c for c in contracts if c["id"] == GT_CORE_CONTRACT_ID]
    if len(core) != 1:
        raise ValueError("GT core contract must exist exactly once")
    sources = list(core[0]["source_invariants"])
    if len(sources) != len(set(sources)) or set(sources) != set(GT_GOVERNING):
        raise ValueError(
            "GT core source_invariants must be exactly the six governing IDs"
        )
    gt_terms = list(overlay("overlays/vocabulary_additions.yaml")["terms"])
    if len(gt_terms) != 12 or set(gt_terms) & set(SV_TERMS):
        raise ValueError("GT must add twelve terms disjoint from SV terms")
    return sources, gt_terms


def _selected_invariants(profile):
    selected = []
    for selector in profile["sources"]["invariants"]["selectors"]:
        match = INVARIANT_SELECTOR.match(selector)
        if not match:
            raise ValueError(f"unsupported invariant selector {selector!r}")
        selected.append(match.group(1))
    return selected


def _verify_forbidden(pdoc, profile):
    """Every declared token has a registered criterion excluding exactly SV records."""
    if profile["forbidden"] != [GT_FORBIDDEN]:
        raise ValueError(
            "GT profile must declare exactly the registered forbidden token"
        )
    definitions = pdoc["forbidden_constraints"]["definitions"]
    for token in profile["forbidden"]:
        if token not in definitions:
            raise ValueError(f"forbidden token {token} has no registered criterion")
    expected = overlay(FORBIDDEN_OVERLAY)["forbidden_constraint_definitions"][
        GT_FORBIDDEN
    ]
    if definitions[GT_FORBIDDEN] != expected:
        raise ValueError("registered forbidden definition differs from overlay")
    rows = expected["excluded_selections"]
    excluded = {(e["source_class"], e["selector"]) for e in rows}
    want = (
        {("vocabulary", "$.terms." + t) for t in SV_TERMS}
        | {("invariants", f'$.invariants[?(@.id=="{i}")]') for i in SV_NEW_INVARIANTS}
        | {("contracts", f'$.contracts[?(@.id=="{SV_CONTRACT_ID}")]')}
    )
    if excluded != want or len(rows) != len(want):
        raise ValueError(
            "forbidden criterion must exclude exactly the SV-owned records"
        )


def _verify_gt_profiles(docs, core_sources, gt_terms):
    pdoc = docs["projection_profiles"]
    profile = _gt_profile(pdoc)
    if tuple(profile["sources"]) != GT_SOURCE_CLASSES:
        raise ValueError(
            "GT profile must select exactly vocabulary, invariants, contracts"
        )
    selected = _selected_invariants(profile)
    if (
        len(selected) != 6
        or len(set(selected)) != 6
        or set(selected) != set(core_sources)
    ):
        raise ValueError(
            "GT invariant selection must equal the core contract's six IDs"
        )
    contracts = set()
    for selector in profile["sources"]["contracts"]["selectors"]:
        match = CONTRACT_SELECTOR.match(selector)
        if not match:
            raise ValueError(f"unsupported contract selector {selector!r}")
        contracts.add(match.group(1))
    if contracts != {GT_CORE_CONTRACT_ID}:
        raise ValueError("GT profile must select only the GT core contract")
    if profile["sources"]["vocabulary"]["selectors"] != [
        "$.terms." + t for t in gt_terms
    ]:
        raise ValueError("GT vocabulary selection must be exactly the twelve GT terms")
    _verify_forbidden(pdoc, profile)
    if profile["output"]["schema"] != GT_OUTPUT:
        raise ValueError("GT profile output schema mismatch")
    comp = [
        p
        for p in docs["composition_profiles"]["profiles"]
        if p["id"] == GT_COMPOSITION_ID
    ]
    if len(comp) != 1 or comp[0]["composes"]["projection_profile"] != GT_PROFILE_ID:
        raise ValueError("GT composition profile missing or unbound")
    if comp[0]["output"]["schema"] != GT_COMPOSED_OUTPUT:
        raise ValueError("GT composition output schema mismatch")


def _schema_output_id(text):
    return (
        ((yaml.safe_load(text) or {}).get("properties") or {})
        .get("schema", {})
        .get("const")
    )


def _verify_schemas(assembled):
    """Registration once each, unique output-ID discovery, six-ID invariant closure."""
    registered = yaml.safe_load(assembled(MANIFEST))["requires"]["artifact_schemas"]
    if len(registered) != len(set(registered)):
        raise ValueError("duplicate artifact schema registration")
    for name in GT_SCHEMA_FILES + SV_SCHEMA_FILES:
        if registered.count(name) != 1:
            raise ValueError(f"schema must be registered exactly once: {name}")
    resolved = {}
    for output_id in (GT_OUTPUT, GT_COMPOSED_OUTPUT):
        hits = [
            n
            for n in registered
            if _schema_output_id(assembled("semantics/" + n)) == output_id
        ]
        if len(hits) != 1:
            raise ValueError(f"{output_id} must resolve to exactly one schema: {hits}")
        resolved[output_id] = hits[0]
    projection = yaml.safe_load(assembled("semantics/" + GT_SCHEMA_FILES[0]))
    composition = yaml.safe_load(assembled("semantics/" + GT_SCHEMA_FILES[1]))
    for label, descriptor in (
        ("projection", projection["properties"]["invariants"]),
        (
            "composition",
            composition["properties"]["invariants"]["properties"]["invariants"],
        ),
    ):
        enum = descriptor["items"]["properties"]["id"]["enum"]
        if descriptor["min_items"] != 6 or sorted(enum) != sorted(GT_GOVERNING):
            raise ValueError(f"{label} schema must pin the six governing IDs")
    return resolved


def verify_assembled(checkout, changed):
    for path, content in changed.items():
        if not isinstance(yaml.safe_load(content), dict):
            raise TypeError(f"bad YAML: {path}")

    def assembled(rel):
        if rel in changed:
            return changed[rel]
        return (checkout / rel).read_text(encoding="utf-8")

    docs = {key: yaml.safe_load(assembled(rel)) for key, rel in LEDGERS.items()}
    verify_sv_core_present(docs)
    core_sources, gt_terms = _verify_gt_law(docs)
    _verify_gt_profiles(docs, core_sources, gt_terms)
    return _verify_schemas(assembled)


def generate_core(checkout):
    def current(rel):
        return (checkout / rel).read_text(encoding="utf-8")

    changed = {}
    for name in GT_SCHEMA_FILES:
        dest = "semantics/" + name
        if (checkout / dest).exists():
            raise ValueError(f"{dest} already exists: re-resolve owner and target")
        changed[dest] = raw("semantics/" + name)

    p = INVARIANTS
    old_inv = current(p)
    old_count = len(unique_ids(yaml.safe_load(old_inv)["invariants"], "invariants"))
    inv = merge_list(old_inv, raw("overlays/invariants_additions.yaml"), "invariants")
    inv_count = len(yaml.safe_load(inv)["invariants"])
    if inv_count != old_count + 1:
        raise ValueError(f"invariant count {inv_count} != {old_count} + 1")
    changed[p] = inv

    p = CONTRACTS
    old_contracts = current(p)
    c = update_contract_derivation(old_contracts, old_inv, inv, old_count, inv_count)
    changed[p] = merge_list(c, raw("overlays/contracts_gt_core.yaml"), "contracts")
    if len(yaml.safe_load(changed[p])["contracts"]) != (
        len(yaml.safe_load(old_contracts)["contracts"]) + 1
    ):
        raise ValueError("contract count did not increase by exactly one")

    p = VOCABULARY
    v = current(p)
    incoming = overlay("overlays/vocabulary_additions.yaml")["terms"]
    clash = set(yaml.safe_load(v)["terms"]) & set(incoming)
    if clash:
        raise ValueError(f"vocabulary term collision: {sorted(clash)}")
    block = raw("overlays/vocabulary_additions.yaml").split("terms:\n", 1)[1]
    changed[p] = one(
        v, "\nrelationships:\n", "\n" + block.rstrip() + "\nrelationships:\n", p
    )
    if len(yaml.safe_load(changed[p])["terms"]) != len(
        yaml.safe_load(v)["terms"]
    ) + len(incoming):
        raise ValueError("vocabulary term count did not increase by exactly twelve")

    p = PROJECTION_PROFILES
    s = current(p)
    pdoc = yaml.safe_load(s)
    unique_ids(pdoc["projection_profiles"], "projection profiles")
    rows = overlay("overlays/projection_profile_additions.yaml")["projection_profiles"]
    unique_ids(rows, "overlay projection profiles")
    for row in rows:
        if row["id"] in {x["id"] for x in pdoc["projection_profiles"]}:
            raise ValueError("profile collision: " + row["id"])
        for source_class in row["sources"]:
            if source_class not in pdoc["source_classes"]:
                raise ValueError("undeclared source class " + source_class)
    definitions = pdoc["forbidden_constraints"]["definitions"]
    new_defs = overlay(FORBIDDEN_OVERLAY)["forbidden_constraint_definitions"]
    if set(new_defs) & set(definitions):
        raise ValueError("forbidden-constraint definition collision")
    if list(pdoc)[list(pdoc).index("forbidden_constraints") + 1] != "validation_rules":
        raise ValueError("forbidden_constraints is not followed by validation_rules")
    def_block = (
        raw(FORBIDDEN_OVERLAY)
        .split("forbidden_constraint_definitions:\n", 1)[1]
        .rstrip()
    )
    def_block = "\n".join(
        "  " + line if line else line for line in def_block.splitlines()
    )
    s = one(s, "\nvalidation_rules:\n", "\n" + def_block + "\nvalidation_rules:\n", p)
    profile_block = raw("overlays/projection_profile_additions.yaml").split(
        "projection_profiles:\n", 1
    )[1]
    changed[p] = one(
        s,
        "\nprojection_engine_contract_ref:\n",
        "\n" + profile_block.rstrip() + "\nprojection_engine_contract_ref:\n",
        p,
    )

    p = COMPOSITION_PROFILES
    cp = current(p)
    cdoc = yaml.safe_load(cp)
    unique_ids(cdoc["profiles"], "composition profiles")
    adds = overlay("overlays/composition_profile_additions.yaml")["profiles"]
    if len(adds) != 1 or adds[0]["id"] in {x["id"] for x in cdoc["profiles"]}:
        raise ValueError("composition profile collision or invalid overlay")
    if list(cdoc)[-1] != "profiles":
        raise ValueError("composition catalog does not end in its profiles list")
    comp_block = (
        raw("overlays/composition_profile_additions.yaml")
        .split("profiles:\n", 1)[1]
        .rstrip()
    )
    changed[p] = (
        cp.rstrip()
        + "\n"
        + "\n".join("  " + line if line else line for line in comp_block.splitlines())
        + "\n"
    )

    p = MANIFEST
    m = current(p)
    schemas = yaml.safe_load(m)["requires"]["artifact_schemas"]
    if any(name in schemas for name in GT_SCHEMA_FILES):
        raise ValueError("GT schema already registered")
    last = "  - " + schemas[-1] + "\n"
    changed[p] = one(m, last, last + "".join(f"  - {n}\n" for n in GT_SCHEMA_FILES), p)
    after = yaml.safe_load(changed[p])["requires"]["artifact_schemas"]
    if after != schemas + list(GT_SCHEMA_FILES):
        raise ValueError("manifest registration did not append exactly the GT schemas")

    rebound = rebind_derived_ledgers(checkout, changed)
    resolved = verify_assembled(checkout, changed)
    return changed, inv_count, rebound, resolved


def generate_dependent(checkout):
    if ADMITTED_FOUNDATION_REVISION is None:
        raise ValueError(
            "no admitted SV + GT-core foundation revision is recorded in "
            "evidence/sv_alignment_binding.json; the dependent contract cannot be prepared"
        )
    head = git(checkout, "rev-parse", "HEAD").strip()
    if head != ADMITTED_FOUNDATION_REVISION:
        raise ValueError(
            f"HEAD {head} != admitted foundation {ADMITTED_FOUNDATION_REVISION}"
        )
    if dirty_paths(checkout):
        raise ValueError("checkout not clean")

    def current(rel):
        return (checkout / rel).read_text(encoding="utf-8")

    docs = {key: yaml.safe_load(current(rel)) for key, rel in LEDGERS.items()}
    verify_sv_core_present(docs)
    inv_ids = {r["id"] for r in docs["invariants"]["invariants"]}
    contract_ids = [c["id"] for c in docs["contracts"]["contracts"]]
    if GT_INVARIANT not in inv_ids or contract_ids.count(GT_CORE_CONTRACT_ID) != 1:
        raise ValueError("GT core is not present at the admitted foundation")
    _gt_profile(docs["projection_profiles"])
    dependent = overlay("overlays/contracts_sv_dependent.yaml")["contracts"]
    if len(dependent) != 1 or dependent[0]["id"] != GT_DEPENDENT_CONTRACT_ID:
        raise ValueError("dependent overlay must carry exactly the GT+SV contract")
    unresolved = set(dependent[0]["source_invariants"]) - inv_ids
    if unresolved:
        raise ValueError(
            f"dependent contract cites absent invariants {sorted(unresolved)}"
        )
    if SV_LINEAGE_ONLY & set(dependent[0]["source_invariants"]):
        raise ValueError("dependent contract cites lineage-only SV IDs")
    p = CONTRACTS
    changed = {
        p: merge_list(
            current(p), raw("overlays/contracts_sv_dependent.yaml"), "contracts"
        )
    }
    rebound = rebind_derived_ledgers(checkout, changed)
    return changed, len(inv_ids), rebound, {}


def write_staged(checkout, proposed):
    target = Path(git(checkout, "rev-parse", "--show-toplevel").strip()).resolve()
    own = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if own and target == Path(own).resolve():
        raise ValueError("refusing --apply into the checkout that carries this pack")
    staged = []
    try:
        for rel, content in proposed.items():
            dst = checkout / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name("." + dst.name + ".gt-staged")
            tmp.write_text(content, encoding="utf-8")
            staged.append((tmp, dst))
    except OSError:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
        raise
    for tmp, dst in staged:
        os.replace(tmp, dst)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--stage", choices=("core", "dependent"), default="core")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--disposable",
        action="store_true",
        help="acknowledge that --checkout is a throwaway clone (self-declared)",
    )
    args = parser.parse_args(argv)
    checkout = Path(args.checkout).resolve()
    try:
        if args.stage == "core":
            verify_sv_applied_target(checkout)
            proposed, count, rebound, resolved = generate_core(checkout)
        else:
            proposed, count, rebound, resolved = generate_dependent(checkout)
        if args.apply:
            if not args.disposable:
                raise ValueError("--apply requires --disposable")
            write_staged(checkout, proposed)
        print(
            "STATUS="
            + ("LOCAL_FILES_WRITTEN_NOT_ADMITTED" if args.apply else "DRY_RUN_ONLY")
        )
        print("STAGE=" + args.stage)
        print("CANONICAL_TARGET=" + CANONICAL_TARGET)
        print("SV_CANDIDATE_HEAD=" + SV_CANDIDATE_HEAD)
        print("INVARIANT_COUNT=" + str(count))
        for path in sorted(proposed):
            print("PATH=" + path)
        for path, names in sorted(rebound.items()):
            print(f"DERIVATION_REBOUND={path}:{','.join(names)}")
        for output_id, name in sorted(resolved.items()):
            print(f"SCHEMA_RESOLVED={output_id}:{name}")
        if args.stage == "core":
            print(
                "DEPENDENT_GT_SV_CONTRACT=NOT_APPLIED_STAGE_B_REQUIRES_ADMITTED_FOUNDATION"
            )
        print("NATIVE_COMPILER_RECEIPTS=NOT_PRODUCED_BY_THIS_SCRIPT")
        return 0
    except (
        ValueError,
        TypeError,
        OSError,
        KeyError,
        AttributeError,
        yaml.YAMLError,
        subprocess.CalledProcessError,
    ) as exc:
        print("BLOCKED=" + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
