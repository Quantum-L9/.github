#!/usr/bin/env python3
"""Prepare the proposed Strategic Value canonical files in a CLEAN pinned local checkout.

Dry-run by default. ``--apply --disposable`` writes local files only, into a
throwaway clone or worktree pinned at BASE_SHA, and refuses the checkout that
carries this candidate pack. It NEVER commits, pushes, opens PRs,
runs release gates, or admits semantics. Every check runs on the fully
assembled candidate before any byte is written; a failed check writes nothing,
and writes are staged then renamed so an I/O failure while staging leaves the
checkout untouched (a failure during the final renames is reported, not hidden).
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

BASE_SHA = "020a94bea86e7c5c5e4107da7014ec259508f397"
ROOT = Path(__file__).resolve().parent

MODEL_ARTIFACT_ID = "l9.strategic.value@1"
CONTRACT_ID = "l9.contract/strategic-value-assessment@1"
PROFILE_ID = "l9.projection/strategic-planner-value@1"
COMPOSITION_ID = "l9.compose/strategic-planner-value@1"
SOURCE_ID = "l9.source/strategic-value-model@1"
PROJECTION_SCHEMA_ARTIFACT = "l9.schema/strategic-planner-value-projection@1"
PROJECTION_OUTPUT = "l9.projection.strategic-planner-value/v1"
COMPOSITION_OUTPUT = "l9.composed-projection.strategic-planner-value/v1"
SCHEMA_FILES = (
    "strategic_planner_value_projection.schema.yaml",
    "strategic_planner_value_composition.schema.yaml",
)

NEW_INVARIANTS = frozenset({"L9-SV-001", "L9-SV-002"})
EXISTING_GOVERNING = frozenset(
    {
        "L9-AUTH-001",
        "L9-AUTH-002",
        "L9-HARD-001",
        "L9-UNKNOWN-001",
        "L9-STRATEGY-001",
        "L9-PROJECTION-001",
        "L9-PROV-001",
        "L9-EVIDENCE-001",
        "L9-ASSURANCE-001",
        "L9-COORD-001",
    }
)
SELECTED = NEW_INVARIANTS | EXISTING_GOVERNING
# Former candidate IDs: permitted only as historical lineage, never as a
# normative invariant reference, selector, or schema enum value.
REMOVED_CANDIDATES = frozenset(f"L9-SV-{n:03d}" for n in range(15, 21))
INVARIANT_SELECTOR = re.compile(r'^\$\.invariants\[\?\(@\.id=="([^"]+)"\)\]$')


def one(text, anchor, replacement, path):
    if text.count(anchor) != 1:
        raise ValueError(
            f"{path}: expected one anchor {anchor!r}, found {text.count(anchor)}"
        )
    return text.replace(anchor, replacement, 1)


def raw(name):
    return (ROOT / name).read_text(encoding="utf-8")


def unique_ids(rows, label):
    ids = [row["id"] for row in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"{label} duplicate IDs: {dupes}")
    return ids


def merge_list(base, extra, list_name):
    old_ids = unique_ids(
        yaml.safe_load(base)[list_name], f"existing canonical {list_name}"
    )
    new_ids = unique_ids(
        yaml.safe_load(extra)[list_name], f"candidate overlay {list_name}"
    )
    collisions = sorted(set(old_ids) & set(new_ids))
    if collisions:
        raise ValueError(
            f"candidate {list_name} collides with canonical IDs: {collisions}"
        )
    return (
        base.rstrip()
        + "\n"
        + extra.split(list_name + ":", 1)[1].lstrip("\n").rstrip()
        + "\n"
    )


def selector_ids(selectors):
    ids = []
    for selector in selectors:
        match = INVARIANT_SELECTOR.match(selector)
        if not match:
            raise ValueError(f"unsupported invariant selector {selector!r}")
        ids.append(match.group(1))
    return ids


def exact_selection(ids, label):
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label}: duplicate selected invariant IDs")
    if set(ids) != SELECTED or len(ids) != 12:
        raise ValueError(
            f"{label}: expected the twelve governing IDs, got {sorted(ids)}"
        )


def update_derivation(
    contracts_text, old_invariant_bytes, new_invariant_bytes, old_count, new_count
):
    """Rebind the contract derivation record, verifying the old binding first."""
    old_digest = hashlib.sha256(old_invariant_bytes).hexdigest()
    new_digest = hashlib.sha256(new_invariant_bytes).hexdigest()
    found = re.findall(
        r"^  source_digest_sha256: ([a-f0-9]{64})$", contracts_text, flags=re.MULTILINE
    )
    if len(found) != 1:
        raise ValueError(
            f"contracts derivation digest anchor: expected one, found {len(found)}"
        )
    if found[0] != old_digest:
        raise ValueError(
            f"stale contracts derivation digest {found[0]} != current invariants {old_digest}"
        )
    counts = re.findall(
        r"^  source_invariant_count: ([0-9]+)$", contracts_text, flags=re.MULTILINE
    )
    if len(counts) != 1 or int(counts[0]) != old_count:
        raise ValueError(
            f"contracts derivation count {counts} does not match current invariants {old_count}"
        )
    text, n1 = re.subn(
        r"^(  source_digest_sha256: )[a-f0-9]{64}$",
        r"\g<1>" + new_digest,
        contracts_text,
        count=1,
        flags=re.MULTILINE,
    )
    text, n2 = re.subn(
        r"^(  source_invariant_count: )[0-9]+$",
        r"\g<1>" + str(new_count),
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if (n1, n2) != (1, 1):
        raise ValueError("contracts derivation update did not occur exactly once")
    derivation = yaml.safe_load(text)["derivation"]
    if (
        derivation["source_digest_sha256"] != new_digest
        or derivation["source_invariant_count"] != new_count
    ):
        raise ValueError(
            "contracts derivation record not rebound to candidate invariants"
        )
    return text


def rebind_source_artifacts(text, path, old, new):
    """Rebind ``derivation.source_artifacts`` entries naming a changed artifact.

    ``old``/``new`` map artifact filename -> (sha256, item_count). Each entry's
    recorded digest (and item_count, when present) must equal the CURRENT
    canonical value before it is replaced; anything stale fails closed. This
    mirrors the derivation-digest refresh of Semantic Foundation v3.8.0
    (commit 2ae5dfa), which added an invariant without changing the content of
    the derived ledgers. Whether a derived ledger's content must also change is
    an owner decision this utility does not make.
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
            raise ValueError(
                f"{path}: stale derivation digest for {name}: {entry.get('sha256')} != {old[name][0]}"
            )
        if "item_count" in entry and entry["item_count"] != old[name][1]:
            raise ValueError(f"{path}: stale derivation item_count for {name}")
        starts = [
            i for i, line in enumerate(lines) if line.strip() == f"- artifact: {name}"
        ]
        if len(starts) != 1:
            raise ValueError(
                f"{path}: expected one derivation entry for {name}, found {len(starts)}"
            )
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
            raise ValueError(
                f"{path}: derivation entry for {name} not rebound exactly once"
            )
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
        doc = yaml.safe_load(text)
        key = {"invariants.yaml": "invariants", "contracts.yaml": "contracts"}.get(
            Path(rel).name
        )
        count = len(doc[key]) if key else None
        return hashlib.sha256(text.encode("utf-8")).hexdigest(), count

    report = {}
    derived = set()
    for _ in range(8):
        old, new = {}, {}
        for rel, text in changed.items():
            name = Path(rel).name
            if (checkout / rel).exists():
                old[name] = stats((checkout / rel).read_text(encoding="utf-8"), rel)
                new[name] = stats(text, rel)
        progressed = False
        for path in sorted((checkout / "semantics").glob("*.yaml")):
            rel = "semantics/" + path.name
            base = changed.get(rel, path.read_text(encoding="utf-8"))
            original = path.read_text(encoding="utf-8")
            # Verify against the canonical bytes, then apply to the candidate text.
            _, names = rebind_source_artifacts(
                original, rel, old, {k: v for k, v in new.items() if v != old[k]}
            )
            if not names:
                continue
            current = {
                e["artifact"]: e["sha256"]
                for e in yaml.safe_load(base)["derivation"]["source_artifacts"]
            }
            if all(current[n] == new[n][0] for n in names):
                continue
            candidate, _ = rebind_source_artifacts(
                original, rel, old, {n: new[n] for n in names}
            )
            if rel in changed and rel not in derived and changed[rel] != original:
                raise ValueError(
                    f"{rel}: derived ledger is also a content destination; refuse to merge edits"
                )
            changed[rel] = candidate
            derived.add(rel)
            report[rel] = names
            progressed = True
        if not progressed:
            return report
    raise ValueError("derivation rebinding did not reach a fixpoint")


def walk_strings(obj, path=()):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield path + (str(key),), str(key)
            yield from walk_strings(value, path + (str(key),))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk_strings(value, path + (str(index),))
    elif isinstance(obj, str):
        yield path, obj


def check_removed_ids_are_lineage_only(label, obj, permitted_prefixes):
    for path, text in walk_strings(obj):
        if any(cid in text for cid in REMOVED_CANDIDATES) and not any(
            path[: len(prefix)] == prefix for prefix in permitted_prefixes
        ):
            raise ValueError(
                f"{label}: removed candidate ID in normative context {'/'.join(path)}"
            )


def verify_assembled(changed):
    for path, content in changed.items():
        obj = yaml.safe_load(content)
        if obj is None or not isinstance(obj, dict):
            raise ValueError(f"bad YAML: {path}")

    invariants = yaml.safe_load(changed["semantics/invariants.yaml"])["invariants"]
    inv_ids = set(unique_ids(invariants, "assembled invariants"))
    proposed = {
        row["id"]
        for row in yaml.safe_load(raw("overlays/invariants_additions.yaml"))[
            "invariants"
        ]
    }
    if proposed != NEW_INVARIANTS:
        raise ValueError(
            f"expected exactly two new Strategic Value invariants, got {sorted(proposed)}"
        )
    missing = SELECTED - inv_ids
    if missing:
        raise ValueError(
            f"selected invariant IDs do not resolve in candidate: {sorted(missing)}"
        )
    leaked = REMOVED_CANDIDATES & inv_ids
    if leaked:
        raise ValueError(
            f"removed candidate IDs present as invariants: {sorted(leaked)}"
        )

    contracts = yaml.safe_load(changed["semantics/contracts.yaml"])
    unique_ids(contracts["contracts"], "assembled contracts")
    contract_ids = {row["id"] for row in contracts["contracts"]}
    value_contract = [c for c in contracts["contracts"] if c["id"] == CONTRACT_ID]
    if len(value_contract) != 1:
        raise ValueError("assessment contract missing or duplicated")
    exact_selection(
        list(value_contract[0]["source_invariants"]), "contract source_invariants"
    )

    model = yaml.safe_load(changed["semantics/strategic_value_model.yaml"])
    if model["artifact_id"] != MODEL_ARTIFACT_ID:
        raise ValueError(
            f"model artifact_id {model['artifact_id']!r} != {MODEL_ARTIFACT_ID!r}"
        )
    exact_selection(
        list(model["governed_by"]["invariants"]), "model governed_by.invariants"
    )
    for ref in model["governed_by"]["contracts"]:
        if ref not in contract_ids:
            raise ValueError(f"model governing contract does not resolve: {ref}")
    check_removed_ids_are_lineage_only(
        "model", model, [("relocated_additional_candidate_semantics",)]
    )

    profiles = yaml.safe_load(changed["semantics/projection_profiles.yaml"])
    candidates = [x for x in profiles["projection_profiles"] if x["id"] == PROFILE_ID]
    if len(candidates) != 1:
        raise ValueError("profile generation failed")
    profile = candidates[0]
    for source_class in profile["sources"]:
        if source_class not in profiles["source_classes"]:
            raise ValueError("unregistered projection source class " + source_class)
    if list(profile["sources"]) != [
        "strategic_value_model",
        "vocabulary",
        "invariants",
        "contracts",
        "authority_model",
    ]:
        raise ValueError("profile must select exactly the five declared source classes")
    exact_selection(
        selector_ids(profile["sources"]["invariants"]["selectors"]),
        "profile invariant selectors",
    )
    for selector in profile["sources"]["contracts"]["selectors"]:
        ref = selector.split('"')[1]
        if ref not in contract_ids:
            raise ValueError(f"profile contract selector does not resolve: {ref}")
    model_keys = [
        s[2:] for s in profile["sources"]["strategic_value_model"]["selectors"]
    ]
    if any(k not in model for k in model_keys) or len(model_keys) != len(
        set(model_keys)
    ):
        raise ValueError("model selectors must each resolve exactly one top-level key")
    check_removed_ids_are_lineage_only("profile", profile, [])

    composer = yaml.safe_load(changed["semantics/composition_profiles.yaml"])
    unique_ids(composer["profiles"], "assembled composition profiles")
    selected = [x for x in composer["profiles"] if x["id"] == COMPOSITION_ID]
    if (
        len(selected) != 1
        or selected[0]["composes"]["projection_profile"] != PROFILE_ID
    ):
        raise ValueError(
            "composition profile missing or not bound to projection profile"
        )
    if selected[0]["output"]["schema"] != COMPOSITION_OUTPUT:
        raise ValueError("composition output schema mismatch")

    sources = yaml.safe_load(changed["semantics/canonical_sources.yaml"])["sources"]
    if [s["id"] for s in sources].count(SOURCE_ID) != 1:
        raise ValueError("value-model canonical source must be registered exactly once")

    manifest = yaml.safe_load(changed["semantics/generic_compiler_manifest.yaml"])
    for name in SCHEMA_FILES:
        if manifest["requires"]["artifact_schemas"].count(name) != 1:
            raise ValueError("schema must be registered exactly once: " + name)
    if (
        manifest["requires"]["semantic_catalogs"].count("strategic_value_model.yaml")
        != 1
    ):
        raise ValueError(
            "value model must be registered exactly once in semantic catalogs"
        )

    pro = yaml.safe_load(changed["semantics/" + SCHEMA_FILES[0]])
    com = yaml.safe_load(changed["semantics/" + SCHEMA_FILES[1]])
    if pro["artifact_id"] != PROJECTION_SCHEMA_ARTIFACT:
        raise ValueError("projection schema artifact_id mismatch")
    if (
        pro["properties"]["schema"]["const"] != profile["output"]["schema"]
        or profile["output"]["schema"] != PROJECTION_OUTPUT
    ):
        raise ValueError("projection schema const does not match profile")
    if com["properties"]["schema"]["const"] != selected[0]["output"]["schema"]:
        raise ValueError("composition schema const does not match composition profile")
    if pro["properties"]["artifact_id"]["const"] != MODEL_ARTIFACT_ID:
        raise ValueError("projection schema model identity mismatch")
    for label, descriptor in (
        ("projection", pro["properties"]["invariants"]),
        ("composition", com["properties"]["invariants"]["properties"]["invariants"]),
    ):
        enum = descriptor["items"]["properties"]["id"]["enum"]
        exact_selection(list(enum), f"{label} schema invariant enum")
        if descriptor["min_items"] != 12:
            raise ValueError(f"{label} schema invariant min_items must be 12")
    if (
        pro["properties"]["invariants"]
        != com["properties"]["invariants"]["properties"]["invariants"]
    ):
        raise ValueError("projection and composition invariant descriptors differ")
    lineage = "relocated_additional_candidate_semantics"
    for label, props in (
        ("projection", pro["properties"]),
        ("composition", com["properties"]["strategic_value_model"]["properties"]),
    ):
        exact_selection(
            list(props["governed_by"]["properties"]["invariants"]["items"]["enum"]),
            f"{label} schema governed_by enum",
        )
        for cid, entry in props[lineage]["properties"].items():
            exact_selection(
                list(entry["properties"]["governing_invariants"]["items"]["enum"]),
                f"{label} schema lineage {cid} enum",
            )
            if (
                entry["properties"]["meaning"].get("const")
                != model[lineage][cid]["meaning"]
            ):
                raise ValueError(
                    f"{label} schema lineage {cid} meaning not pinned to model"
                )
    check_removed_ids_are_lineage_only(
        "projection schema", pro, [("properties", lineage)]
    )
    check_removed_ids_are_lineage_only(
        "composition schema",
        com,
        [("properties", "strategic_value_model", "properties", lineage)],
    )
    return len(invariants)


def generate(checkout):
    changed = {}

    def current(path):
        return (checkout / path).read_text(encoding="utf-8")

    model_path = "semantics/strategic_value_model.yaml"
    if (checkout / model_path).exists():
        raise ValueError(
            "strategic_value_model already exists; re-resolve current authority"
        )
    changed[model_path] = raw("semantics/strategic_value_model.yaml")

    p = "semantics/invariants.yaml"
    old_inv_bytes = (checkout / p).read_bytes()
    old_count = len(
        unique_ids(
            yaml.safe_load(old_inv_bytes)["invariants"], "existing canonical invariants"
        )
    )
    inv = merge_list(
        old_inv_bytes.decode("utf-8"),
        raw("overlays/invariants_additions.yaml"),
        "invariants",
    )
    changed[p] = inv
    inv_count = len(yaml.safe_load(inv)["invariants"])
    if inv_count != old_count + len(NEW_INVARIANTS):
        raise ValueError(
            f"invariant count {inv_count} != {old_count} + {len(NEW_INVARIANTS)}"
        )

    p = "semantics/contracts.yaml"
    c = update_derivation(
        current(p), old_inv_bytes, inv.encode("utf-8"), old_count, inv_count
    )
    changed[p] = merge_list(c, raw("overlays/contracts_additions.yaml"), "contracts")
    old_contracts = len(yaml.safe_load(current(p))["contracts"])
    new_contracts = len(yaml.safe_load(changed[p])["contracts"])
    if new_contracts != old_contracts + 1:
        raise ValueError(f"contract count {new_contracts} != {old_contracts} + 1")

    p = "semantics/vocabulary.yaml"
    v = current(p)
    existing = set(yaml.safe_load(v)["terms"])
    items = yaml.safe_load(raw("overlays/vocabulary_additions.yaml"))["terms"]
    if existing.intersection(items):
        raise ValueError(
            "canonical vocabulary term collision: "
            + str(sorted(existing.intersection(items)))
        )
    terms_text = raw("overlays/vocabulary_additions.yaml").split("terms:\n", 1)[1]
    changed[p] = one(
        v, "\nrelationships:\n", "\n" + terms_text.rstrip() + "\nrelationships:\n", p
    )

    p = "semantics/canonical_sources.yaml"
    s = current(p)
    new_source = (
        f"- id: {SOURCE_ID}\n"
        "  path: semantics/strategic_value_model.yaml\n"
        "  format: yaml\n"
        "  canonical: true\n"
        "  projection_allowed: true\n"
        "  derivation_allowed: false\n"
    )
    if SOURCE_ID in s:
        raise ValueError("source already exists")
    changed[p] = one(s, "\nrules:\n", "\n" + new_source + "rules:\n", p)

    p = "semantics/generic_compiler_manifest.yaml"
    s = current(p)
    if "strategic_value_model.yaml" in s or any(name in s for name in SCHEMA_FILES):
        raise ValueError(
            "value model or schema already registered in compiler manifest"
        )
    s = one(
        s,
        "  - strategic_plan_model.yaml\n",
        "  - strategic_plan_model.yaml\n  - strategic_value_model.yaml\n",
        p,
    )
    s = one(
        s,
        "  - pr_audit_composition.schema.yaml\n",
        "  - pr_audit_composition.schema.yaml\n"
        + "".join(f"  - {name}\n" for name in SCHEMA_FILES),
        p,
    )
    changed[p] = s

    p = "semantics/projection_profiles.yaml"
    s = current(p)
    pr = yaml.safe_load(s)
    if "strategic_value_model" in pr["source_classes"] or any(
        x["id"] == PROFILE_ID for x in pr["projection_profiles"]
    ):
        raise ValueError("projection already exists")
    unique_ids(pr["projection_profiles"], "existing projection profiles")
    profile_file = raw("overlays/projection_profile_additions.yaml")
    source_part, profile_part = profile_file.split("projection_profiles:\n", 1)
    src_block = source_part.split("source_classes:\n", 1)[1]
    s = one(
        s, "\nprojection_profiles:\n", "\n" + src_block + "projection_profiles:\n", p
    )
    changed[p] = one(
        s,
        "\nprojection_engine_contract_ref:\n",
        "\n" + profile_part.rstrip() + "\nprojection_engine_contract_ref:\n",
        p,
    )
    # The composition profile belongs in the canonical compiler catalog, not
    # in the projection profile or a second runtime-owned registry.
    p = "semantics/composition_profiles.yaml"
    comp = yaml.safe_load(current(p))
    unique_ids(comp["profiles"], "existing composition profiles")
    addition = yaml.safe_load(raw("overlays/composition_profile_additions.yaml"))[
        "profiles"
    ]
    if len(addition) != 1 or any(
        x["id"] == addition[0]["id"] for x in comp["profiles"]
    ):
        raise ValueError("composition profile collision or invalid overlay")
    comp_block = (
        raw("overlays/composition_profile_additions.yaml")
        .split("profiles:\n", 1)[1]
        .rstrip()
    )
    new_comp = (
        current(p).rstrip()
        + "\n"
        + "\n".join("  " + line if line else line for line in comp_block.splitlines())
        + "\n"
    )
    changed[p] = new_comp

    for schema_name in SCHEMA_FILES:
        dest = "semantics/" + schema_name
        if (checkout / dest).exists():
            raise ValueError("schema collision: " + dest)
        changed[dest] = raw(dest)

    generate.rebound = rebind_derived_ledgers(checkout, changed)
    verify_assembled(changed)
    return changed, inv_count


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--checkout", required=True)
    a.add_argument("--apply", action="store_true")
    a.add_argument(
        "--disposable",
        action="store_true",
        help="acknowledge that --checkout is a throwaway clone/worktree, not a working checkout",
    )
    args = a.parse_args()
    checkout = Path(args.checkout).resolve()

    def git(*cmd):
        return subprocess.run(
            ["git", "-C", str(checkout), *cmd],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    try:
        actual = git("rev-parse", "HEAD")
        if actual != BASE_SHA:
            raise ValueError(f"wrong target HEAD: {actual}; expected {BASE_SHA}")
        if git("status", "--porcelain"):
            raise ValueError("working tree not clean")
        proposed, inv_count = generate(checkout)
        if args.apply:
            if not args.disposable:
                raise ValueError(
                    "--apply requires --disposable: target a throwaway clone or worktree at BASE_SHA"
                )
            target = Path(git("rev-parse", "--show-toplevel")).resolve()
            own = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            if own and target == Path(own).resolve():
                raise ValueError(
                    "refusing --apply into the checkout that carries this candidate pack"
                )
            # Stage every file first; only after all staged writes succeed is
            # each one moved into place with an atomic rename. A staging failure
            # removes the staged files and leaves the checkout untouched.
            staged = []
            try:
                for rel, content in proposed.items():
                    dst = checkout / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dst.with_name("." + dst.name + ".sv-staged")
                    tmp.write_text(content, encoding="utf-8")
                    staged.append((tmp, dst))
            except OSError:
                for tmp, _ in staged:
                    tmp.unlink(missing_ok=True)
                raise
            for tmp, dst in staged:
                os.replace(tmp, dst)
        print(
            "STATUS="
            + ("LOCAL_FILES_WRITTEN_NOT_ADMITTED" if args.apply else "DRY_RUN_ONLY")
        )
        print("BASE_SHA=" + actual)
        print("INVARIANT_COUNT=" + str(inv_count))
        print("SELECTED_GOVERNING_INVARIANTS=" + ",".join(sorted(SELECTED)))
        for path in sorted(proposed):
            print("PATH=" + path)
        for path, names in sorted(generate.rebound.items()):
            print(f"DERIVATION_REBOUND={path}:{','.join(names)}")
        print(
            "REQUIRES=canonical collision review, target native validation, release manifest, protected publication, admission"
        )
        return 0
    except (
        ValueError,
        OSError,
        KeyError,
        yaml.YAMLError,
        subprocess.CalledProcessError,
    ) as exc:
        print("BLOCKED=" + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
