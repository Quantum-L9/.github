"""Shared fixtures: pack readers, producer evidence, and a synthetic SV-applied target.

The synthetic target is NOT the canonical repository. It carries only the
structure the GT applier reads (ledgers, profile catalogs, manifest, one derived
ledger) so the applier's checks can be exercised without network or the real
SV pack. Real-target behaviour is evidenced separately in
``evidence/integration-v1`` (native validator + real compiler).
"""

import json
import subprocess
import tarfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "integration-v1"

GOVERNING = [
    "L9-GT-001",
    "L9-AUTH-002",
    "L9-HARD-001",
    "L9-UNKNOWN-001",
    "L9-EVIDENCE-001",
    "L9-ASSURANCE-001",
]


def read(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    return json.loads(text) if rel.endswith(".json") else yaml.safe_load(text)


def producer_artifact(member, run="run1"):
    """One JSON file from the archived real-compiler output."""
    with tarfile.open(EVIDENCE / f"projection-{run}.tar") as tar:
        return json.load(tar.extractfile("./" + member))


GT_DIR = "l9.projection_strategic-planner-interaction_1/"


def gt_payload(source):
    return producer_artifact(GT_DIR + f"l9.source_{source}_1.projection.json")[
        "payload"
    ]


def _inv(iid):
    return (
        f"- id: {iid}\n  statement: existing {iid}\n  scope: global\n"
        "  owner: Quantum-L9/.github\n"
    )


def synthetic_sv_applied(root, *, sv_invariants=("L9-SV-001", "L9-SV-002")):
    """Write a minimal SV-applied semantics tree under ``root`` and return it."""
    binding = read("evidence/sv_alignment_binding.json")
    sem = root / "semantics"
    sem.mkdir(parents=True)
    existing = [g for g in GOVERNING if g != "L9-GT-001"] + [
        "L9-AUTH-001",
        "L9-STRATEGY-001",
        "L9-PROJECTION-001",
        "L9-PROV-001",
        "L9-COORD-001",
    ]
    inv = "schema: l9.invariants/v1\ninvariants:\n" + "".join(
        _inv(i) for i in existing + list(sv_invariants)
    )
    (sem / "invariants.yaml").write_text(inv, encoding="utf-8")
    import hashlib

    inv_digest = hashlib.sha256(inv.encode()).hexdigest()
    count = len(existing) + len(sv_invariants)
    contracts = (
        "schema: l9.contracts/v1\nderivation:\n"
        "  source_artifact: invariants.yaml\n"
        f"  source_digest_sha256: {inv_digest}\n"
        f"  source_invariant_count: {count}\n"
        "contracts:\n- id: l9.contract/old@1\n  purpose: old\n"
        f"- id: {binding['sv_contract']}\n  purpose: sv\n"
    )
    (sem / "contracts.yaml").write_text(contracts, encoding="utf-8")
    terms = "".join(
        f"  {t}:\n    semantic_class: value\n    definition: sv {t}\n"
        for t in binding["sv_vocabulary_terms"]
    )
    (sem / "vocabulary.yaml").write_text(
        "schema: l9.vocabulary/v1\nterms:\n"
        "  authority:\n    semantic_class: governance\n    definition: old\n"
        + terms
        + "relationships:\n  owns: {}\n",
        encoding="utf-8",
    )
    sv_sources = "".join(
        f"    {c}:\n      selectors:\n      - $.x\n"
        for c in binding["sv_source_classes"]
    )
    (sem / "projection_profiles.yaml").write_text(
        "schema: l9.projection-profile-catalog/v1\nsource_classes:\n"
        + "".join(
            f"  {c}:\n    canonical_artifact: {c}.yaml\n"
            for c in binding["sv_source_classes"]
        )
        + "projection_profiles:\n"
        f"- id: {binding['sv_projection']}\n  class: consumer\n  consumer: strategic-planner\n"
        "  sources:\n" + sv_sources + "projection_engine_contract_ref:\n  ref: old\n"
        "forbidden_constraints:\n  criterion_language:\n    name: l9.forbidden-constraint\n"
        "    version: 1\n  definitions:\n    unrelated_domain_payloads:\n"
        "      criterion: source_authority\n"
        "validation_rules:\n- id: PROJECTION-016\n  rule: declared\n",
        encoding="utf-8",
    )
    (sem / "composition_profiles.yaml").write_text(
        "schema: l9.composition-profiles/v1\nprofiles:\n"
        f"  - id: {binding['sv_composition']}\n    purpose: sv\n",
        encoding="utf-8",
    )
    (sem / "generic_compiler_manifest.yaml").write_text(
        "schema: l9.generic-compiler-manifest/v1\nrequires:\n  artifact_schemas:\n"
        "  - pr_audit_composition.schema.yaml\n"
        "  - strategic_planner_value_projection.schema.yaml\n"
        "  - strategic_planner_value_composition.schema.yaml\n",
        encoding="utf-8",
    )
    for name, out in (
        ("projection", "l9.projection.strategic-planner-value/v1"),
        ("composition", "l9.composed-projection.strategic-planner-value/v1"),
    ):
        (sem / f"strategic_planner_value_{name}.schema.yaml").write_text(
            f"schema: l9.schema-definition/v1\nproperties:\n  schema:\n    const: {out}\n",
            encoding="utf-8",
        )
    (sem / "pr_audit_composition.schema.yaml").write_text(
        "schema: l9.schema-definition/v1\nproperties:\n  schema:\n"
        "    const: l9.composed-projection.pr-audit/v1\n",
        encoding="utf-8",
    )
    (sem / "strategic_value_model.yaml").write_text(
        f"artifact_id: {binding['sv_model']}\n", encoding="utf-8"
    )
    con = (sem / "contracts.yaml").read_text()
    (sem / "lifecycle.yaml").write_text(
        "schema: l9.lifecycle/v1\nderivation:\n  source_artifacts:\n"
        "  - artifact: invariants.yaml\n"
        f"    sha256: {inv_digest}\n    item_count: {count}\n"
        "  - artifact: contracts.yaml\n"
        f"    sha256: {hashlib.sha256(con.encode()).hexdigest()}\n    item_count: 2\n",
        encoding="utf-8",
    )
    return root


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
        env={
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@localhost",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@localhost",
            "HOME": str(root),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        },
    ).stdout.strip()


def init_repo(root):
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    return git(root, "rev-parse", "HEAD")
