"""Producer negative controls against the REAL compiler (scratch only)."""

import copy
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

SP = Path("/tmp/claude-0/-home-user/a2b6f907-ae31-5599-8c24-cf3342c0b873/scratchpad")
AUTH = SP / "dotgithub-base"
RUN1 = SP / "sv-projection-run1"
ENV = dict(os.environ, PYTHONPATH="/home/user/l9-semantic-compiler-engine/src")
REV = subprocess.run(
    ["git", "-C", str(AUTH), "rev-parse", "HEAD"], capture_output=True, text=True
).stdout.strip()


def cli(*args):
    p = subprocess.run(
        [sys.executable, "-m", "l9_semantic_compiler", *args],
        capture_output=True,
        text=True,
        env=ENV,
    )
    return p.returncode, p.stdout, p.stderr


def summarize(out):
    try:
        d = yaml.safe_load(out)
    except Exception:
        return {"raw": out[-300:]}
    if not isinstance(d, dict):
        return {"raw": str(d)[-300:]}
    arts = d.get("artifacts") or []
    diag = d.get("diagnostic_coordinates") or {}
    return {
        "status": d.get("status"),
        "result": d.get("result"),
        "typed_failure": d.get("typed_failure"),
        "criterion": diag.get("criterion"),
        "error_code": diag.get("error_code"),
        "message": diag.get("message"),
        "failing_pass_ref": d.get("failing_pass_ref"),
        "unresolved": sorted(
            {c for a in arts for c in (a.get("unresolved_criteria") or [])}
        )[:8],
        "failed": sorted({c for a in arts for c in (a.get("failed_criteria") or [])})[
            :8
        ],
        "error": d.get("error") or d.get("reason") or d.get("diagnostics"),
    }


def project(req, tag):
    with tempfile.TemporaryDirectory() as t:
        req = copy.deepcopy(req)
        req["output_root"] = t
        f = Path(t) / "req.yaml"
        f.write_text(yaml.safe_dump(req))
        rc, out, err = cli("project", str(f))
        return rc, summarize(out), err.strip()[-400:]


def compose(req):
    with tempfile.TemporaryDirectory() as t:
        req = copy.deepcopy(req)
        req["output_root"] = t
        f = Path(t) / "req.yaml"
        f.write_text(yaml.safe_dump(req))
        rc, out, err = cli("compose", str(f))
        return rc, summarize(out), err.strip()[-400:]


results = []


def record(name, mechanism, rc, summary, err, expect_nonpass=True):
    ok = rc != 0 if expect_nonpass else rc == 0
    results.append(
        {
            "control": name,
            "intended_mechanism": mechanism,
            "exit_code": rc,
            "summary": summary,
            "stderr_tail": err,
            "expected": "non-pass" if expect_nonpass else "pass",
            "detected": ok,
        }
    )


base = {
    c: yaml.safe_load((RUN1 / "requests" / f"{c}.request.yaml").read_text())
    for c in (
        "strategic_value_model",
        "vocabulary",
        "invariants",
        "contracts",
        "authority_model",
    )
}

rc, s, e = project(base["invariants"], "positive")
record("positive_control_invariants_projection", "none", rc, s, e, False)

r = copy.deepcopy(base["invariants"])
r["projection_profile"]["digest"] = "sha256:" + "0" * 64
record("profile_digest_mutated", "profile_currentness", *project(r, "x"))
r = copy.deepcopy(base["invariants"])
r["sources"][0]["digest"] = "sha256:" + "1" * 64
record("source_digest_mutated", "source_currentness", *project(r, "x"))
r = copy.deepcopy(base["invariants"])
r["sources"][0]["ref"] = "l9.source/contracts@1"
record("source_identity_swapped", "source_identity", *project(r, "x"))
r = copy.deepcopy(base["invariants"])
r["authority"]["revision"] = "020a94bea86e7c5c5e4107da7014ec259508f397"
record("revision_without_candidate_profile", "profile_resolution", *project(r, "x"))


# Mutated canonical source in a throwaway commit (plumbing only; HEAD untouched).
def commit_with(path, transform, msg):
    blob_src = subprocess.run(
        ["git", "-C", str(AUTH), "show", f"{REV}:{path}"],
        capture_output=True,
        text=True,
    ).stdout
    new = transform(blob_src)
    idx = Path(tempfile.mkdtemp()) / "index"
    env = dict(os.environ, GIT_INDEX_FILE=str(idx))
    subprocess.run(["git", "-C", str(AUTH), "read-tree", REV], env=env, check=True)
    blob = subprocess.run(
        ["git", "-C", str(AUTH), "hash-object", "-w", "--stdin"],
        input=new,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    subprocess.run(
        [
            "git",
            "-C",
            str(AUTH),
            "update-index",
            "--cacheinfo",
            f"100644,{blob},{path}",
        ],
        env=env,
        check=True,
    )
    tree = subprocess.run(
        ["git", "-C", str(AUTH), "write-tree"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    cenv = dict(
        os.environ,
        GIT_AUTHOR_NAME="neg",
        GIT_AUTHOR_EMAIL="neg@localhost",
        GIT_COMMITTER_NAME="neg",
        GIT_COMMITTER_EMAIL="neg@localhost",
    )
    return subprocess.run(
        ["git", "-C", str(AUTH), "commit-tree", tree, "-p", REV, "-m", msg],
        env=cenv,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def coords(rev, cls):
    rc, out, err = cli(
        "projection-coordinates",
        "--authority-root",
        str(AUTH),
        "--revision",
        rev,
        "--repository",
        "Quantum-L9/.github",
        "--profile",
        "l9.projection/strategic-planner-value@1",
        "--source-class",
        cls,
    )
    if rc != 0:
        return None, err
    d = yaml.safe_load(out)
    d["schema"] = "l9.semantic-projection-request/v1"
    d["authority"]["root"] = str(AUTH)
    return d, ""


def model_mutation(name, mech, transform):
    rev = commit_with("semantics/strategic_value_model.yaml", transform, "NEG " + name)
    req, err = coords(rev, "strategic_value_model")
    if req is None:
        record(name, mech, 99, {"coordinates_error": err[-300:]}, err[-300:])
        return
    record(name, mech, *project(req, "x"))


model_mutation(
    "model_normative_boolean_false",
    "payload_schema",
    lambda t: t.replace(
        "mutually_exclusive_booking: true", "mutually_exclusive_booking: false", 1
    ),
)
model_mutation(
    "model_required_array_emptied",
    "payload_schema",
    lambda t: t.replace(
        "    governing_invariants:\n    - L9-SV-001\n    model_section: evaluation_integrity.counterfactual_identification",
        "    governing_invariants: []\n    model_section: evaluation_integrity.counterfactual_identification",
        1,
    ),
)
model_mutation(
    "model_lineage_reintroduces_removed_id",
    "payload_schema",
    lambda t: t.replace(
        "    governing_invariants:\n    - L9-SV-001\n    model_section: evaluation_integrity.counterfactual_identification",
        "    governing_invariants:\n    - L9-SV-015\n    model_section: evaluation_integrity.counterfactual_identification",
        1,
    ),
)


def vocab_mut(t):
    return t.replace(
        "  decision_boundary:\n    semantic_class: decision_analysis\n    definition:",
        "  decision_boundary:\n    semantic_class: decision_analysis\n    definition_removed:",
        1,
    )


rev = commit_with("semantics/vocabulary.yaml", vocab_mut, "NEG vocab")
req, err = coords(rev, "vocabulary")
record(
    "vocabulary_definition_removed",
    "payload_schema",
    *(project(req, "x") if req else (99, {}, err)),
)

inv_mut = lambda t: t.replace("- id: L9-COORD-001", "- id: L9-COORD-001-RENAMED", 1)
rev = commit_with("semantics/invariants.yaml", inv_mut, "NEG invariant id")
req, err = coords(rev, "invariants")
record(
    "selected_invariant_id_renamed",
    "selection_equivalence",
    *(project(req, "x") if req else (99, {}, err)),
)

con_mut = lambda t: t.replace(
    "- id: l9.contract/hard-constraint@1", "- id: l9.contract/hard-constraint@9", 1
)
rev = commit_with("semantics/contracts.yaml", con_mut, "NEG contract id")
req, err = coords(rev, "contracts")
record(
    "selected_contract_id_renamed",
    "selection_equivalence",
    *(project(req, "x") if req else (99, {}, err)),
)

comp = yaml.safe_load((RUN1 / "requests" / "compose.request.yaml").read_text())
c = copy.deepcopy(comp)
c["components"] = [x for x in c["components"] if "authority-model" not in x]
record(
    "composition_missing_namespace", "composition source_coverage exact", *compose(c)
)
c = copy.deepcopy(comp)
c["components"] = c["components"] + [c["components"][0]]
record("composition_duplicate_source", "duplicate_source conflict", *compose(c))
c = copy.deepcopy(comp)
c["composition_profile"]["digest"] = "sha256:" + "2" * 64
record(
    "composition_profile_digest_mutated", "composition_profile_currentness", *compose(c)
)
c = copy.deepcopy(comp)
c["components"] = list(reversed(c["components"]))
rc, s, e = compose(c)
results.append(
    {
        "control": "composition_component_order_reversed",
        "intended_mechanism": "order independence",
        "exit_code": rc,
        "summary": s,
        "stderr_tail": e,
        "expected": "same result as canonical order (3/unknown)",
        "detected": rc == 3,
    }
)

# Tampered artifact bytes: verify-projection must fail.
art = sorted(
    glob.glob(
        str(
            RUN1
            / "l9.projection_strategic-planner-value_1"
            / "l9.source_invariants_1.projection.json"
        )
    )
)[0]
d = json.loads(Path(art).read_text())
d["payload"]["invariants"] = d["payload"]["invariants"][:-1]
with tempfile.TemporaryDirectory() as t:
    f = Path(t) / "tampered.projection.json"
    f.write_text(json.dumps(d, indent=2))
    rc, out, err = cli(
        "verify-projection",
        "--authority-root",
        str(AUTH),
        "--revision",
        REV,
        "--repository",
        "Quantum-L9/.github",
        "--artifact",
        str(f),
    )
    record(
        "artifact_payload_tampered",
        "projection_digest / delivered bytes",
        rc,
        summarize(out),
        err[-300:],
    )
    d2 = json.loads(Path(art).read_text())
    d2["source_digest"] = "sha256:" + "3" * 64
    f.write_text(json.dumps(d2, indent=2))
    rc, out, err = cli(
        "verify-projection",
        "--authority-root",
        str(AUTH),
        "--revision",
        REV,
        "--repository",
        "Quantum-L9/.github",
        "--artifact",
        str(f),
    )
    record(
        "artifact_receipt_binding_wrong_source_coordinate",
        "envelope digest / source coordinate",
        rc,
        summarize(out),
        err[-300:],
    )
rc, out, err = cli(
    "verify-projection",
    "--authority-root",
    str(AUTH),
    "--revision",
    REV,
    "--repository",
    "Quantum-L9/.github",
    "--artifact",
    art,
)
record(
    "positive_control_verify_untampered_artifact",
    "none",
    rc,
    summarize(out),
    err[-300:],
    False,
)

print(
    json.dumps(
        {
            "schema": "l9.sv-reduction-producer-negative-controls/v1",
            "rehearsal_authority_revision": REV,
            "compiler_revision": subprocess.run(
                [
                    "git",
                    "-C",
                    "/home/user/l9-semantic-compiler-engine",
                    "rev-parse",
                    "HEAD",
                ],
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "all_detected": all(r["detected"] for r in results),
            "controls": results,
        },
        indent=2,
    )
)
