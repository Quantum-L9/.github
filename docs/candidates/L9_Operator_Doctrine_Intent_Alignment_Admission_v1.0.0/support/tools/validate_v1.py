#!/usr/bin/env python3
"""Read-only, local operator v1 admission pack verifier; not a global semantic authority check."""

import copy
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo-overlay"
S = REPO / "strategy"
SUP = ROOT / "support"
Z = SUP / "evidence/L9_Operator_Doctrine_Intent_Alignment_Candidate_v0.6.1.zip"
errors = []
neg = {}


def check(ok, why):
    if not ok:
        errors.append(why)


def h(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def yamlfile(path):
    return read(S / path)


def pointer(obj, path):
    if not isinstance(path, str) or not path.startswith("/") or "//" in path:
        raise ValueError("invalid pointer")
    v = obj
    for key in path[1:].split("/"):
        key = key.replace("~1", "/").replace("~0", "~")
        if not isinstance(v, dict) or key not in v:
            raise ValueError("unresolved selector")
        v = v[key]
    return v


def guarded_select(allowed, source, paths):
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate selector")
    if not set(paths).issubset(set(allowed[source])):
        raise ValueError("not allowlisted")
    if any(
        p == "/core_values" or p.startswith("/additional_core_value_candidates")
        for p in paths
    ):
        raise ValueError("unadopted values")


def reject(name, call):
    try:
        call()
    except (ValueError, KeyError, TypeError):
        neg[name] = "PASS"
    else:
        neg[name] = "FAIL"
        errors.append("negative " + name)


D = yamlfile("OPERATOR_DOCTRINE.yaml")
I = yamlfile("operator_strategic_intent.yaml")
P = yamlfile("alignment/operator_alignment.profile.yaml")
V = yamlfile("alignment/agent_views.yaml")
B = yamlfile("alignment/consumer_bindings.yaml")
M = json.loads((S / "OPERATOR_RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
check(
    all(
        d == "1.0.0"
        for d in (
            D["revision"],
            I["revision"],
            P["pack_revision"],
            V["version"],
            B["revision"],
        )
    ),
    "v1 revisions",
)
check(
    D["document_kind"] == "operator_foundational_doctrine"
    and I["document_kind"] == "operator_owned_strategic_intent",
    "record kinds",
)
check(
    "authority_class" not in D and "authority_class" not in I,
    "operator content manufactured global class",
)
check(
    I["doctrine_binding"]["doctrine_ref"] == D["doctrine_ref"]
    and I["doctrine_binding"]["doctrine_revision"] == D["revision"],
    "intent doctrine pin",
)
check(
    D["intent_relationship"]["dependent_revision"] == I["revision"],
    "doctrine intent pin",
)
check(
    P["profile_ref"] == "qap.operator-alignment/profile@1"
    and V["profile_ref"] == P["profile_ref"],
    "profile ref",
)
check(
    set(V["views"]) == {"planner", "meta_planner", "cto", "architect", "coding_agent"},
    "five views",
)
check(set(B["bindings"]) == set(V["views"]), "bindings")
check(
    all(
        v["status"] == "proposed_not_operator_adopted"
        for v in D["additional_core_value_candidates"].values()
    ),
    "proposed values promoted",
)
check(
    D["approval"]["effective_as_repository_source_only_after_authorized_adoption"]
    is True
    and I["approval"]["effective_as_repository_source_only_after_authorized_adoption"]
    is True,
    "adoption boundary",
)
check(
    D["approval"]["does_not_admit_global_l9_semantics"]
    and I["approval"]["does_not_admit_global_l9_semantics"],
    "global admission overclaim",
)
check(
    D["approval"]["approved_predecessor_zip_sha256"]
    == I["approval"]["approved_predecessor_zip_sha256"],
    "approval identity",
)
expected = {
    "strategy/OPERATOR_DOCTRINE.yaml",
    "strategy/operator_strategic_intent.yaml",
    "strategy/alignment/operator_alignment.profile.yaml",
    "strategy/alignment/agent_views.yaml",
    "strategy/alignment/consumer_bindings.yaml",
}
check(set(M["files"]) == expected, "source manifest inventory")
check(
    set(str(p.relative_to(REPO)) for p in REPO.rglob("*") if p.is_file())
    == expected | {"strategy/ADMISSION.md", "strategy/OPERATOR_RELEASE_MANIFEST.json"},
    "repo overlay contains unexpected files",
)
for path, sig in M["files"].items():
    target = REPO / path
    check(target.is_file() and h(target.read_bytes()) == sig, "source digest " + path)
c = copy.deepcopy(M)
c.pop("subject_digest", None)
check(
    M["subject_digest"]
    == "sha256:"
    + h(
        json.dumps(
            c, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ),
    "subject digest",
)
check(M["runtime_activation"] == "NOT_PERFORMED", "runtime activation overclaim")
for name, spec in P["source_instances"].items():
    check(
        spec["revision"] == "1.0.0" and spec["sha256"] == M["files"][spec["path"]],
        "profile source pin " + name,
    )
check(
    P["source_instances"]["intent"]["must_reference_doctrine_revision"]
    == D["revision"],
    "profile closure",
)
check(
    P["selection_policy"]["do_not_treat_proposed_core_values_as_adopted"] is True,
    "unadopted values guard",
)
allow = P["selection_policy"]["privileged_selector_allowlist"]
for role, view in V["views"].items():
    check(view["view_ref"] == B["bindings"][role]["view_ref"], "binding ref " + role)
    check(
        view["view_ref"].endswith("@1") and not view["view_ref"].endswith("-candidate"),
        "view ref version " + role,
    )
    check(view["privileged"] is (role != "coding_agent"), "privilege " + role)
    if role != "coding_agent":
        for source, key in (("doctrine", "doctrine_paths"), ("intent", "intent_paths")):
            try:
                guarded_select(allow, source, view[key])
                for ptr in view[key]:
                    pointer(D if source == "doctrine" else I, ptr)
            except ValueError as ex:
                errors.append("invalid selector " + role + " " + str(ex))
CA = V["views"]["coding_agent"]
check(
    CA["doctrine_paths"] == []
    and CA["intent_paths"] == []
    and B["bindings"]["coding_agent"]["scope"] == "delegated_task_contract_only",
    "coding scope",
)
for obj in CA["delegated_obligations"]:
    try:
        value = pointer(D if obj["source"] == "doctrine" else I, obj["pointer"])
        check(
            isinstance(value, str)
            and obj["evidence_quote"] in value
            and h(value.encode()) == obj["source_value_sha256"],
            "coding source quotation " + obj["id"],
        )
        check(
            obj["summary_review_state"]
            == "candidate_requires_operator_review_before_delegation",
            "coding task summary prematurely activated",
        )
    except (TypeError, KeyError, ValueError) as ex:
        errors.append("coding obligation " + obj["id"] + " " + str(ex))

# The original zip itself is the user-approved exact predecessor; verify preserved meaning.
check(h(Z.read_bytes()) == M["predecessor_zip_sha256"], "predecessor exact archive")
with zipfile.ZipFile(Z) as z:

    def old(file):
        return yaml.safe_load(z.read(file).decode())

    d = old("strategy/OPERATOR_DOCTRINE.yaml")
    i = old("strategy/operator_strategic_intent.candidate.yaml")
    p = old("alignment/operator_alignment.profile.candidate.yaml")
    v = old("alignment/agent_views.candidate.yaml")
    b = old("alignment/consumer_bindings.candidate.yaml")
    for k in ("central_thesis", "progress_test", "flywheel"):
        check(
            D["foundational_ideology"][k] == d["foundational_ideology"][k],
            "ideology meaning " + k,
        )
    for k in ("statement", "guardrail"):
        check(
            D["core_values"]["compounding_leverage"][k]
            == d["core_values"]["compounding_leverage"][k],
            "Compounding Leverage meaning " + k,
        )
    for k in ("first_principles", "convictions"):
        a = copy.deepcopy(D[k])
        c = copy.deepcopy(d[k])
        a.pop("status")
        c.pop("status")
        check(a == c, "doctrine meaning " + k)
    check(
        D["additional_core_value_candidates"] == d["additional_core_value_candidates"],
        "additional core values semantic drift",
    )
    check(D["boundaries"] == d["boundaries"], "doctrine boundaries semantic drift")
    check(
        I["content"] == i["content"]
        and I["relationship_to_strategy"] == i["relationship_to_strategy"],
        "strategic intent meaning drift",
    )
    for k in (
        "selection_policy",
        "runtime_boundary",
        "visibility",
        "semantic_authority",
    ):
        check(P[k] == p[k], "selection model drift " + k)
    check(
        V["view_rules"] == v["view_rules"]
        and B["activation_contract"] == b["activation_contract"],
        "view/binding guard drift",
    )
    for role in V["views"]:
        aa = copy.deepcopy(V["views"][role])
        bb = copy.deepcopy(v["views"][role])
        aa["view_ref"] = bb["view_ref"]
        check(aa == bb, "role view semantic drift " + role)
        aa = copy.deepcopy(B["bindings"][role])
        bb = copy.deepcopy(b["bindings"][role])
        aa["view_ref"] = bb["view_ref"]
        check(aa == bb, "role binding semantic drift " + role)

reject(
    "unadopted-value",
    lambda: guarded_select(allow, "doctrine", ["/additional_core_value_candidates"]),
)
reject("broad-core-values", lambda: guarded_select(allow, "doctrine", ["/core_values"]))
reject(
    "not-allowlisted", lambda: guarded_select(allow, "intent", ["/content/not-allowed"])
)
reject(
    "duplicate-selection",
    lambda: guarded_select(allow, "doctrine", ["/boundaries", "/boundaries"]),
)
reject("missing-selector", lambda: pointer(D, "/foundational_ideology/missing"))
reject("invalid-pointer", lambda: pointer(D, "//foundational_ideology"))
for role in V["views"]:
    z = json.loads((SUP / "previews" / f"{role}.preview.json").read_text())
    check(
        z["can_activate"] is False and z["runtime_receipt"] is None,
        "preview activation overclaim " + role,
    )
    check(z["view_ref"] == V["views"][role]["view_ref"], "preview role ref " + role)
    if role == "coding_agent":
        check("selected_operator_sections" not in z, "coding agent raw source leak")
        check(
            "source_sha256" not in z and "source_revision_refs" not in z,
            "coding agent source pointer leak",
        )
        check(
            all(set(ob) == {"id", "summary"} for ob in z["delegated_obligations"]),
            "coding agent source leaf leak",
        )
        check(
            z.get("example_only_no_task_contract_attached") is True,
            "coding preview task binding overclaim",
        )
    else:
        check(
            "selected_operator_sections" in z,
            "missing privileged source sections " + role,
        )
scenarios = (
    read(SUP / "tests/acceptance_scenarios.yaml")["cases"]
    + read(SUP / "tests/alignment_acceptance_scenarios.yaml")["cases"]
)
check(
    len(scenarios) == 55 and len(set(x["id"] for x in scenarios)) == 55,
    "behavioral scenario inventory",
)
run = subprocess.run(
    [sys.executable, str(SUP / "tools/render_alignment_v1.py"), "--check"],
    capture_output=True,
    text=True,
)
check(run.returncode == 0, "generated preview bytes differ " + run.stderr.strip())
report = {
    "schema": "operator-v1-local-admission-validation",
    "status": "PASS_LOCAL_ADMISSION_PACKAGE" if not errors else "FAIL",
    "errors": errors,
    "negative_controls": neg,
    "source_records_verified": 5,
    "role_views": 5,
    "behavioral_scenarios_specified": 55,
    "behavioral_scenarios_executed": 0,
    "predecessor_semantic_preservation": "PASS"
    if not any("drift" in x or "meaning" in x for x in errors)
    else "FAIL",
    "operator_adoption_into_github": "NOT_PERFORMED",
    "global_semantics_admission": "NOT_REQUESTED",
    "live_derived_operator_projection": "NOT_PERFORMED",
    "host_acl_and_access_isolation": "NOT_VERIFIED",
    "historical_source_completeness": "PARTIAL",
    "admission_subject_digest": M["subject_digest"],
    "predecessor_zip_sha256": M["predecessor_zip_sha256"],
}
print(json.dumps(report, indent=2))
sys.exit(0 if not errors else 1)
