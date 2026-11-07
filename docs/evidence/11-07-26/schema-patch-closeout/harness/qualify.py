#!/usr/bin/env python3
"""Qualify the ten candidate projection/composition profile pairs against the real compiler.

Read-only with respect to the authority: every input is read from git objects at
--revision. No schema is generated or derived. The compiler is invoked as a separate
process for project / compose / verify-projection, and imported (same pinned source)
for the composed verifier, the receipt validator and the v1 schema interpreter.

Usage: qualify.py --authority-root R --revision SHA --compiler-src DIR --out DIR
       [--pre-patch-revision SHA]   # PATCH-01 behavior-equivalence check
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path

import yaml

REPO = "Quantum-L9/.github"
PRE211 = "020a94bea86e7c5c5e4107da7014ec259508f397"
PROFILES = [
    "authority-resolution", "evidence-assessment", "semantic-change-context",
    "architecture-break-test", "globalization-assessment", "work-state-continuity",
    "hard-constraint-context", "identity-assurance", "strategic-metacognition",
    "strategic-planning-context",
]

ap = argparse.ArgumentParser()
ap.add_argument("--authority-root", required=True)
ap.add_argument("--revision", required=True)
ap.add_argument("--compiler-src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--pre-patch-revision")
ap.add_argument("--positive-only", action="store_true")
args = ap.parse_args()
sys.path.insert(0, args.compiler_src)

from l9_semantic_compiler.engine.canonical import digest  # noqa: E402
from l9_semantic_compiler.engine.errors import SemanticCompilerError  # noqa: E402
from l9_semantic_compiler.engine.receipts import validate_receipt_document  # noqa: E402
from l9_semantic_compiler.engine.registry import CanonicalAuthority  # noqa: E402
from l9_semantic_compiler.passes import projection as P  # noqa: E402
from l9_semantic_compiler.passes.validate import schema_violations  # noqa: E402

ROOT = Path(args.authority_root)
REV = args.revision
OUT = Path(args.out)
OUT.mkdir(parents=True, exist_ok=False)
ENV = {**os.environ, "PYTHONPATH": args.compiler_src}
CLI = [sys.executable, "-m", "l9_semantic_compiler"]
AUTH = CanonicalAuthority(ROOT, REV, repository=REPO)
AUTHSPEC = {"repository": REPO, "root": str(ROOT), "revision": REV}


def sh(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, env=ENV, check=False)
    try:
        doc = yaml.safe_load(p.stdout) if p.stdout.strip() else None
    except yaml.YAMLError:
        doc = {"unparsed_stdout": p.stdout[-2000:]}
    return p.returncode, doc, p.stderr[-2000:]


def sha(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_yaml(rev, path):
    return yaml.safe_load(subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{path}"],
                                         capture_output=True, text=True, check=True).stdout)


def failure_view(doc):
    """Reduce a compiler failure document to its typed identity."""
    if not isinstance(doc, dict):
        return {"raw": doc}
    diag = doc.get("diagnostic_coordinates") or {}
    return {"status": doc.get("status"), "typed_failure": doc.get("typed_failure"),
            "error_code": diag.get("error_code"), "criterion": diag.get("criterion"),
            "message": diag.get("message"), "failing_pass_ref": doc.get("failing_pass_ref")}


def exc_view(exc):
    d = getattr(exc, "diagnostics", None) or {}
    return {"error_class": type(exc).__name__, "code": getattr(exc, "code", None),
            "criterion": d.get("criterion") if isinstance(d, dict) else None, "message": str(exc)}


profile_catalog = git_yaml(REV, "semantics/projection_profiles.yaml")
composition_catalog = git_yaml(REV, "semantics/composition_profiles.yaml")


def profile_record(name):
    ref = f"l9.projection/{name}@1"
    [rec] = [p for p in profile_catalog["projection_profiles"] if p.get("id") == ref]
    return ref, rec


def composition_pin(name):
    ref = f"l9.compose/{name}@1"
    [rec] = [p for p in composition_catalog["profiles"] if p.get("id") == ref]
    return {"ref": ref, "digest": digest(rec)}, rec


def run_positive(name, root_dir):
    """project + compose + independent re-verification. Returns a structured record."""
    ref, rec = profile_record(name)
    rc, coords, err = sh([*CLI, "projection-coordinates", "--authority-root", str(ROOT),
                          "--revision", REV, "--repository", REPO, "--profile", ref])
    assert rc == 0, (name, rc, err)
    root_dir.mkdir(parents=True)
    req = {"schema": "l9.semantic-projection-request/v1", "authority": AUTHSPEC,
           "projection_profile": coords["projection_profile"], "sources": coords["sources"],
           "output_root": str(root_dir / "out")}
    (root_dir / "project.yaml").write_text(yaml.safe_dump(req))
    rc, proj, err = sh([*CLI, "project", str(root_dir / "project.yaml")])
    rec_out = {"profile": ref, "coordinates": coords, "project_exit": rc,
               "project_result": (proj or {}).get("result")}
    if rc != 0:
        rec_out["project_failure"] = failure_view(proj)
        rec_out["stderr"] = err
        return rec_out, None
    cpin, crec = composition_pin(name)
    creq = {"schema": "l9.semantic-composition-request/v1", "authority": AUTHSPEC,
            "composition_profile": cpin, "components": [a["path"] for a in proj["artifacts"]],
            "output_root": str(root_dir / "out")}
    (root_dir / "compose.yaml").write_text(yaml.safe_dump(creq))
    rc, comp, err = sh([*CLI, "compose", str(root_dir / "compose.yaml")])
    rec_out.update({"compose_exit": rc, "compose_result": (comp or {}).get("result"),
                    "composition_profile": cpin})
    if rc != 0:
        rec_out["compose_failure"] = failure_view(comp)
        return rec_out, None
    checks = {}
    declared_classes = list(rec["sources"])
    emitted = []
    for a in proj["artifacts"]:
        doc = json.loads(Path(a["path"]).read_text())
        receipt = json.loads(Path(a["receipt_path"]).read_text())
        rc_v, ver, _ = sh([*CLI, "verify-projection", "--authority-root", str(ROOT),
                           "--revision", REV, "--repository", REPO, "--artifact", a["path"]])
        try:
            validate_receipt_document(receipt)
            receipt_ok = True
        except SemanticCompilerError as exc:
            receipt_ok = exc_view(exc)
        pin = {s["ref"]: s["digest"] for s in coords["sources"]}
        emitted.append(doc["source_ref"])
        crit = (ver or {}).get("criteria") or {}
        inputs = receipt.get("inputs") or []
        checks[doc["source_ref"]] = {
            "artifact_result": a["result"], "unresolved": a["unresolved_criteria"],
            "verify_exit": rc_v, "verify_result": (ver or {}).get("result"),
            "verify_unresolved": (ver or {}).get("unresolved_criteria"),
            "payload_schema": crit.get("payload_schema", {}).get("status"),
            "payload_schema_artifact": crit.get("payload_schema", {}).get("schema_artifact"),
            # exact selector membership is the verifier's recomputation from the profile
            "selection_equivalence": crit.get("selection_equivalence", {}).get("status"),
            "receipt_valid": receipt_ok,
            "receipt_result": receipt.get("result"),
            "receipt_coverage": (receipt.get("verification_basis") or {}).get("coverage"),
            "profile_identity": doc.get("projection_profile_ref") == coords["projection_profile"]["ref"]
            and doc.get("projection_profile_digest") == coords["projection_profile"]["digest"]
            and receipt.get("profile") == coords["projection_profile"],
            "source_digest_matches_pin": doc.get("source_digest") == pin.get(doc["source_ref"]),
            "receipt_input_coordinates": len(inputs) == 1 and inputs[0].get("revision") == REV
            and inputs[0].get("ref") == doc["source_ref"] and inputs[0].get("digest") == doc["source_digest"],
            "receipt_output_binds_artifact": (receipt.get("output") or {}).get("digest") == doc["projection_digest"],
            "receipt_binds_output": receipt.get("receipt_digest") == a["receipt_digest"],
        }
    checks["_source_coverage"] = sorted(emitted) == sorted(s["ref"] for s in coords["sources"]) \
        and len(emitted) == len(declared_classes)
    ca = comp["artifacts"][0]
    composed = json.loads(Path(ca["path"]).read_text())
    components = [json.loads(Path(a["path"]).read_text()) for a in proj["artifacts"]]
    try:
        report = P.verify_composed_projection(AUTH, composed, components)
        crit = report["criteria"]
        cres, cunres = P.result_from_criteria(crit)
        composed_ok = {"result": cres, "unresolved": cunres,
                       "payload_schema": crit["payload_schema"]["status"]}
    except SemanticCompilerError as exc:
        composed_ok = exc_view(exc)
    creceipt = json.loads(Path(ca["receipt_path"]).read_text())
    try:
        validate_receipt_document(creceipt)
        creceipt_ok = True
    except SemanticCompilerError as exc:
        creceipt_ok = exc_view(exc)
    ns = sorted((composed.get("payload") or {}).keys() - {"schema"})
    checks["_composition"] = {
        "artifact_result": ca["result"], "unresolved": ca["unresolved_criteria"],
        "reverify": composed_ok, "receipt_valid": creceipt_ok,
        "namespace_coverage": ns == sorted(declared_classes),
        "component_order": [c["source_class"] for c in composed["components"]] == declared_classes,
        "composition_profile_identity": composed.get("composition_profile") == cpin,
        "receipt_result": creceipt.get("result"),
        "receipt_coverage": (creceipt.get("verification_basis") or {}).get("coverage"),
    }
    rec_out["checks"] = checks
    files = {}
    for a in [*proj["artifacts"], ca]:
        for k in ("path", "receipt_path"):
            files[str(Path(a[k]).relative_to(root_dir))] = sha(a[k])
    rec_out["files"] = files
    return rec_out, {"proj": proj, "comp": comp, "coords": coords, "cpin": cpin, "rec": rec,
                     "crec": crec, "dir": root_dir}


def all_pass(r):
    if r.get("project_result") != "pass" or r.get("compose_result") != "pass":
        return False
    for k, v in r["checks"].items():
        if k == "_source_coverage":
            if v is not True:
                return False
        elif k == "_composition":
            if not (v["artifact_result"] == "pass" and not v["unresolved"]
                    and isinstance(v["reverify"], dict) and v["reverify"].get("result") == "pass"
                    and v["reverify"].get("payload_schema") == "pass"
                    and v["receipt_valid"] is True and v["namespace_coverage"]
                    and v["receipt_result"] == "pass" and v["receipt_coverage"] == "complete"
                    and v["component_order"] and v["composition_profile_identity"]):
                return False
        else:
            if not (v["artifact_result"] == "pass" and not v["unresolved"] and v["verify_exit"] == 0
                    and v["verify_result"] == "pass" and not v["verify_unresolved"]
                    and v["payload_schema"] == "pass" and v["selection_equivalence"] == "pass"
                    and v["receipt_valid"] is True and v["receipt_result"] == "pass"
                    and v["receipt_coverage"] == "complete" and v["profile_identity"]
                    and v["source_digest_matches_pin"] and v["receipt_input_coordinates"]
                    and v["receipt_output_binds_artifact"] and v["receipt_binds_output"]):
                return False
    return True


# ---------------------------------------------------------------- schema negatives
def find(desc, payload, want, path=()):
    """Depth-first: first (path, descriptor, value) where want(descriptor, value) holds."""
    if isinstance(desc, dict) and want(desc, payload):
        return path, desc, payload
    if not isinstance(desc, dict):
        return None
    t = desc.get("type")
    if (t == "object" or "properties" in desc) and isinstance(payload, dict):
        for k, child in (desc.get("properties") or {}).items():
            if k in payload:
                hit = find(child, payload[k], want, (*path, k))
                if hit:
                    return hit
    if t == "array" and isinstance(payload, list) and isinstance(desc.get("items"), dict):
        for i, item in enumerate(payload):
            hit = find(desc["items"], item, want, (*path, i))
            if hit:
                return hit
    return None


def setp(obj, path, fn):
    for p in path[:-1]:
        obj = obj[p]
    fn(obj, path[-1])


def schema_negatives(schema_doc, payload):
    cases = {}
    top_props = schema_doc.get("properties") or {}
    # required field missing (deepest structural required: first object with a required key present)
    hit = find(schema_doc, payload, lambda d, v: d.get("type") == "object" and d.get("required")
               and isinstance(v, dict) and d is not schema_doc)
    if hit is None and schema_doc.get("required"):
        hit = ((), schema_doc, payload)
    if hit is None:
        hit = find(schema_doc, payload, lambda d, v: isinstance(d.get("items"), dict)
                   and d["items"].get("required") and isinstance(v, list) and v
                   and isinstance(v[0], dict))
        if hit:
            hit = ((*hit[0], 0), hit[1]["items"], hit[2][0])
    if hit:
        path, d, _ = hit
        key = d["required"][0]
        bad = copy.deepcopy(payload)
        if path:
            setp(bad, (*path, key), lambda o, k: o.pop(k))
        else:
            bad.pop(key)
        cases["missing_required_field"] = {"path": list(path) + [key], "violations": schema_violations(bad, schema_doc)}
    hit = find(schema_doc, payload, lambda d, v: d.get("type") == "array" and isinstance(v, list))
    if hit:
        path, _, _ = hit
        bad = copy.deepcopy(payload)
        setp(bad, path, lambda o, k: o.__setitem__(k, "not-a-list"))
        cases["wrong_type"] = {"path": list(path), "violations": schema_violations(bad, schema_doc)}
    bad = copy.deepcopy(payload)
    bad["schema"] = "l9.projection.wrong/v1"
    cases["wrong_top_const"] = {"path": ["schema"], "violations": schema_violations(bad, schema_doc)}
    hit = find(schema_doc, payload, lambda d, v: "const" in d and v == d["const"] and d is not top_props.get("schema"))
    if hit:
        path, _, _ = hit
        bad = copy.deepcopy(payload)
        setp(bad, path, lambda o, k: o.__setitem__(k, "__wrong_const__"))
        cases["wrong_nested_const"] = {"path": list(path), "violations": schema_violations(bad, schema_doc)}
    hit = find(schema_doc, payload, lambda d, v: "enum" in d and v in (d["enum"] or []))
    if hit:
        path, _, _ = hit
        bad = copy.deepcopy(payload)
        setp(bad, path, lambda o, k: o.__setitem__(k, "__not_in_enum__"))
        cases["wrong_enum"] = {"path": list(path), "violations": schema_violations(bad, schema_doc)}
    hit = find(schema_doc, payload, lambda d, v: d.get("type") == "array"
               and isinstance(d.get("min_items"), int) and d["min_items"] > 0 and isinstance(v, list))
    if hit:
        path, d, _ = hit
        bad = copy.deepcopy(payload)
        setp(bad, path, lambda o, k: o.__setitem__(k, o[k][: d["min_items"] - 1]))
        cases["array_below_min_items"] = {"path": list(path), "min_items": d["min_items"],
                                          "violations": schema_violations(bad, schema_doc)}
    cases["intact"] = {"violations": schema_violations(payload, schema_doc)}
    return cases


# ---------------------------------------------------------------- producer negatives
def producer_negatives(ctx, work):
    out = {}
    proj, coords, cpin = ctx["proj"], ctx["coords"], ctx["cpin"]
    work.mkdir(parents=True)

    def project_with(label, req_mut):
        req = {"schema": "l9.semantic-projection-request/v1", "authority": AUTHSPEC,
               "projection_profile": copy.deepcopy(coords["projection_profile"]),
               "sources": copy.deepcopy(coords["sources"]), "output_root": str(work / label)}
        req_mut(req)
        f = work / f"{label}.yaml"
        f.write_text(yaml.safe_dump(req))
        rc, doc, _ = sh([*CLI, "project", str(f)])
        return {"exit": rc, "result": (doc or {}).get("result"), **failure_view(doc)}

    def compose_with(label, components, pin=None):
        req = {"schema": "l9.semantic-composition-request/v1", "authority": AUTHSPEC,
               "composition_profile": pin or cpin, "components": components,
               "output_root": str(work / label)}
        f = work / f"{label}.yaml"
        f.write_text(yaml.safe_dump(req))
        rc, doc, _ = sh([*CLI, "compose", str(f)])
        return {"exit": rc, "result": (doc or {}).get("result"), **failure_view(doc)}

    out["missing_source_pin"] = project_with("missing-pin", lambda r: r["sources"].pop(0))
    out["wrong_profile_digest"] = project_with(
        "bad-profile-digest", lambda r: r["projection_profile"].__setitem__("digest", "sha256:" + "0" * 64))
    out["wrong_source_digest"] = project_with(
        "bad-source-digest", lambda r: r["sources"][0].__setitem__("digest", "sha256:" + "1" * 64))
    paths = [a["path"] for a in proj["artifacts"]]
    out["missing_component"] = compose_with("missing-component", paths[1:])
    out["duplicate_component"] = compose_with("duplicate-component", [*paths, paths[0]])
    out["wrong_composition_pin"] = compose_with(
        "bad-composition-pin", paths, {"ref": cpin["ref"], "digest": "sha256:" + "2" * 64})
    first = json.loads(Path(paths[0]).read_text())
    key = next(k for k in first["payload"] if k != "schema")
    altered = copy.deepcopy(first)
    altered["payload"][key] = "__altered__"
    f = work / "altered-no-redigest.json"
    f.write_text(json.dumps(altered))
    rc, doc, _ = sh([*CLI, "verify-projection", "--authority-root", str(ROOT), "--revision", REV,
                     "--repository", REPO, "--artifact", str(f)])
    out["altered_payload_no_redigest"] = {"exit": rc, "result": (doc or {}).get("result"), **failure_view(doc)}
    altered["projection_digest"] = P.envelope_digest(altered, "projection_digest")
    f = work / "altered-redigest.json"
    f.write_text(json.dumps(altered))
    rc, doc, _ = sh([*CLI, "verify-projection", "--authority-root", str(ROOT), "--revision", REV,
                     "--repository", REPO, "--artifact", str(f)])
    out["altered_payload_redigested"] = {"exit": rc, "result": (doc or {}).get("result"), **failure_view(doc)}
    receipt = json.loads(Path(proj["artifacts"][0]["receipt_path"]).read_text())
    tampered = copy.deepcopy(receipt)
    tampered["exact_subject_ref"] = "l9.projection/forged@1"
    try:
        validate_receipt_document(tampered)
        out["receipt_tamper"] = {"rejected": False}
    except SemanticCompilerError as exc:
        out["receipt_tamper"] = {"rejected": True, **exc_view(exc)}
    composed = json.loads(Path(ctx["comp"]["artifacts"][0]["path"]).read_text())
    components = [json.loads(Path(p).read_text()) for p in paths]
    bad = copy.deepcopy(composed)
    ns = next(k for k in bad["payload"] if k != "schema")
    bad["payload"].pop(ns)
    bad["composition_digest"] = P.envelope_digest(bad, "composition_digest")
    try:
        P.verify_composed_projection(AUTH, bad, components)
        out["composed_namespace_dropped_redigested"] = {"rejected": False}
    except SemanticCompilerError as exc:
        out["composed_namespace_dropped_redigested"] = {"rejected": True, **exc_view(exc)}
    # an authority revision that does not declare the profile (origin/main before #211)
    rc, doc, _ = sh([*CLI, "verify-projection", "--authority-root", str(ROOT), "--revision", PRE211,
                     "--repository", REPO, "--artifact", paths[0]])
    out["authority_revision_without_profile"] = {"exit": rc, "result": (doc or {}).get("result"),
                                                 "revision": PRE211, **failure_view(doc)}
    return out


def rejected(case):
    if "rejected" in case:
        return case["rejected"] is True
    if "violations" in case:
        return bool(case["violations"])
    return case.get("exit") not in (0, None) and case.get("result") != "pass"


# ---------------------------------------------------------------- PATCH-01 equivalence
def patch01_equivalence(pre_rev):
    """For each string_list descriptor whose min_items was removed, show the pinned
    interpreter accepts [] under both the original and the patched descriptor."""
    rows = []
    for name in PROFILES:
        stem = name.replace("-", "_")
        for kind in ("projection", "composition"):
            path = f"semantics/{stem}_{kind}.schema.yaml"
            before = git_yaml(pre_rev, path)
            after = git_yaml(REV, path)

            def walk(b, a, p):
                if isinstance(b, dict):
                    if b.get("type") == "string_list" and "min_items" in b:
                        rows.append({"file": path, "path": p, "min_items_removed": b["min_items"],
                                     "patched_has_min_items": "min_items" in a,
                                     "original_accepts_empty": schema_violations([], b) == [],
                                     "patched_accepts_empty": schema_violations([], a) == [],
                                     "original_rejects_non_list": bool(schema_violations("x", b)),
                                     "patched_rejects_non_list": bool(schema_violations("x", a))})
                    for k in ("properties", "fields"):
                        for kk, vv in (b.get(k) or {}).items():
                            walk(vv, (a.get(k) or {}).get(kk, {}), f"{p}.{kk}")
                    if isinstance(b.get("items"), dict):
                        walk(b["items"], a.get("items") or {}, f"{p}[*]")
            walk({"type": "object", "properties": before.get("properties")},
                 {"type": "object", "properties": after.get("properties")}, "$")
    return rows


summary = {"authority_repository": REPO, "authority_revision": REV,
           "semantics_tree": subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{REV}:semantics"],
                                            capture_output=True, text=True, check=True).stdout.strip(),
           "compiler_src": args.compiler_src, "profiles": {}}
for name in PROFILES:
    entry = {}
    try:
        r1, ctx = run_positive(name, OUT / "run-a" / name)
        entry["positive"] = r1
        entry["positive_pass"] = ctx is not None and all_pass(r1)
        if args.positive_only or ctx is None:
            summary["profiles"][name] = entry
            continue
        payload_cases = {}
        for a in ctx["proj"]["artifacts"]:
            doc = json.loads(Path(a["path"]).read_text())
            sid = (ctx["rec"].get("output") or {}).get("schema")
            sdoc = AUTH.schema_defining(sid).document
            payload_cases[doc["source_ref"]] = schema_negatives(sdoc, doc["payload"])
        composed = json.loads(Path(ctx["comp"]["artifacts"][0]["path"]).read_text())
        csid = (ctx["crec"].get("output") or {}).get("schema")
        payload_cases["_composition"] = schema_negatives(AUTH.schema_defining(csid).document,
                                                         composed["payload"])
        entry["schema_negatives"] = payload_cases
        entry["producer_negatives"] = producer_negatives(ctx, OUT / "neg" / name)
        neg_all = []
        for src, cases in payload_cases.items():
            for cname, c in cases.items():
                if cname == "intact":
                    neg_all.append(("schema", src, cname, c["violations"] == []))
                else:
                    neg_all.append(("schema", src, cname, rejected(c)))
        for cname, c in entry["producer_negatives"].items():
            neg_all.append(("producer", "-", cname, rejected(c)))
        entry["negative_tally"] = {"cases": len(neg_all), "as_expected": sum(1 for x in neg_all if x[3]),
                                   "unexpected": [x[:3] for x in neg_all if not x[3]]}
    except Exception:  # recorded, never swallowed into a pass
        entry["harness_error"] = traceback.format_exc()
        entry["positive_pass"] = False
    summary["profiles"][name] = entry

if args.pre_patch_revision:
    rows = patch01_equivalence(args.pre_patch_revision)
    summary["patch01_equivalence"] = {
        "pre_patch_revision": args.pre_patch_revision, "descriptors": len(rows),
        "all_equivalent": all(r["original_accepts_empty"] and r["patched_accepts_empty"]
                              and not r["patched_has_min_items"] and r["original_rejects_non_list"]
                              and r["patched_rejects_non_list"] for r in rows),
        "rows": rows}

(OUT / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=str) + "\n")
ok = all(e.get("positive_pass") for e in summary["profiles"].values())
print(json.dumps({n: {"positive_pass": e.get("positive_pass"), "negatives": e.get("negative_tally"),
                      "error": bool(e.get("harness_error"))} for n, e in summary["profiles"].items()},
                 indent=1))
if "patch01_equivalence" in summary:
    print("patch01:", summary["patch01_equivalence"]["descriptors"], summary["patch01_equivalence"]["all_equivalent"])
sys.exit(0 if ok else 1)
