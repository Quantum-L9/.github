#!/usr/bin/env python3
"""Regenerate (or ``--check``) MANIFEST.json, SHA256SUMS.txt and the candidate revision.

Inputs are the pack's own files; MANIFEST.json, SHA256SUMS.txt and
evidence/candidate_revision.json are derived and excluded from the inventory.
The candidate revision is sha256 over ``path NUL bytes NUL`` for the normative
candidate files in a fixed order. It is a local digest, not an admission or
compiler digest.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ("MANIFEST.json", "SHA256SUMS.txt", "evidence/candidate_revision.json")
NORMATIVE = (
    "overlays/vocabulary_additions.yaml",
    "overlays/invariants_additions.yaml",
    "overlays/contracts_gt_core.yaml",
    "overlays/contracts_sv_dependent.yaml",
    "overlays/projection_profile_additions.yaml",
    "overlays/projection_forbidden_constraint_additions.yaml",
    "overlays/composition_profile_additions.yaml",
    "semantics/strategic_interaction_projection.schema.yaml",
    "semantics/strategic_interaction_composition.schema.yaml",
    "schemas/gt_sv_consumer_assessment.candidate.schema.json",
)


def pack_files():
    return sorted(
        p.relative_to(ROOT).as_posix()
        for p in ROOT.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.relative_to(ROOT).as_posix() not in DERIVED
    )


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def candidate_revision():
    digest = hashlib.sha256()
    for rel in NORMATIVE:
        digest.update(rel.encode() + b"\0" + (ROOT / rel).read_bytes() + b"\0")
    return digest.hexdigest()


def render():
    binding = json.loads((ROOT / "evidence/sv_alignment_binding.json").read_text())
    summary = json.loads(
        (ROOT / "evidence/integration-v1/qualification-summary.json").read_text()
    )
    controls = json.loads(
        (ROOT / "evidence/integration-v1/producer-negative-controls.json").read_text()
    )
    files = pack_files()
    revision = candidate_revision()
    manifest = {
        "schema": "l9.gt.dotgithub-candidate-local/v3",
        "status": "CANDIDATE_ONLY_NOT_CANONICAL",
        "target": "Quantum-L9/.github",
        "canonical_target": binding["canonical_target"],
        "sv_candidate_pr": binding["sv_candidate"]["pr"],
        "sv_candidate_head": binding["sv_candidate"]["head"],
        "reviewed_gt_head": "d9292f2440808fecb71539ef0de6d8474dfe384b",
        "gt_core": "LOCAL_REHEARSAL_QUALIFIED_NOT_ADMITTED",
        "gt_sv_dependent": "BLOCKED_UNTIL_ADMITTED_FOUNDATION_RECORDED",
        "semantic_invariant_candidates": 1,
        "gt_governing_invariants": 6,
        "gt_vocabulary_terms": 12,
        "gt_source_projection_classes": 3,
        "sv_source_projection_classes": len(binding["sv_source_classes"]),
        "local_test_command": "python -m unittest discover -s tests",
        "native_validator": "54 PASS; SC-008/SC-010 release inventory FAIL",
        "producer": {
            "compiler_revision": summary["compiler_revision"],
            "rehearsal_revision": summary["authority_revision"],
            "gt_composition_result": summary["run1"]["gt:compose"]["result"],
            "sv_composition_result": summary["run1"]["sv:compose"]["result"],
            "byte_identical_repeat": summary["byte_identical_outputs"],
            "negative_controls_matched": f"{sum(c['mechanism_matched'] for c in controls['controls'])}/{controls['count']}",
        },
        "remote_mutation": False,
        "no_skills": True,
        "candidate_revision": "sha256:" + revision,
        "files": [
            {"path": rel, "bytes": (ROOT / rel).stat().st_size, "sha256": sha(rel)}
            for rel in files
        ],
    }
    sums = "".join(f"{sha(rel)}  {rel}\n" for rel in files)
    cand = {
        "sha256": revision,
        "paths": list(NORMATIVE),
        "notes": "locally computed digest over ordered path\\0bytes\\0; not canonical git/admission or compiler digest",
        "sv_candidate_head": binding["sv_candidate"]["head"],
        "canonical_target": binding["canonical_target"],
    }
    return {
        "MANIFEST.json": json.dumps(manifest, indent=1) + "\n",
        "SHA256SUMS.txt": sums,
        "evidence/candidate_revision.json": json.dumps(cand, indent=2) + "\n",
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = render()
    stale = [
        rel
        for rel, text in outputs.items()
        if not (ROOT / rel).exists() or (ROOT / rel).read_text() != text
    ]
    if args.check:
        for rel in stale:
            print("STALE=" + rel)
        return 1 if stale else 0
    for rel, text in outputs.items():
        (ROOT / rel).write_text(text, encoding="utf-8")
    print("WROTE=" + ",".join(outputs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
