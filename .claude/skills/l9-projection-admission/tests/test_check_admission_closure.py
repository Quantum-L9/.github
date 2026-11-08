"""Rung-by-rung tests for check_admission_closure.py on a synthetic semantics repository.

Each test builds a small git repository shaped like Quantum-L9/.github (ledgers, one
release record, one ADR, a stand-in validator whose exit code the test controls) and
moves exactly one fact to show which rung it decides.
"""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_admission_closure as cac

SUBJECT = {
    "schema": cac.SUBJECT_SCHEMA,
    "invariants": ["L9-X-001"],
    "vocabulary_terms": ["x_term"],
    "contracts": ["l9.contract/x@1"],
    "canonical_sources": ["l9.source/x-model@1"],
    "source_classes": ["x_model"],
    "projection_profiles": ["l9.projection/x@1"],
    "composition_profiles": ["l9.compose/x@1"],
    "schemas": ["x_projection.schema.yaml", "x_composition.schema.yaml"],
}

LEDGERS = {
    "invariants.yaml": "invariants:\n- id: L9-X-001\n  statement: x holds\n  scope: global\n",
    "vocabulary.yaml": "terms:\n  x_term:\n    definition: an x\n",
    "contracts.yaml": "contracts:\n- id: l9.contract/x@1\n  purpose: x\n",
    "canonical_sources.yaml": (
        "sources:\n- id: l9.source/x-model@1\n  path: semantics/x_model.yaml\n"
        "  projection_allowed: true\n"
    ),
    "x_model.yaml": "artifact_id: l9.x/global@1\nvalue: 1\n",
    "projection_profiles.yaml": (
        "source_classes:\n  x_model:\n    canonical_artifact: x_model.yaml\n"
        "projection_profiles:\n- id: l9.projection/x@1\n  purpose: project x\n"
        "  sources:\n    x_model:\n      selectors: [$.value]\n"
        "  output:\n    schema: l9.projection.x/v1\n"
    ),
    "composition_profiles.yaml": (
        "profiles:\n- id: l9.compose/x@1\n  composes:\n    projection_profile: l9.projection/x@1\n"
        "  output:\n    schema: l9.composed-projection.x/v1\n"
    ),
    "generic_compiler_manifest.yaml": (
        "requires:\n  semantic_catalogs: [x_model.yaml]\n"
        "  artifact_schemas: [x_projection.schema.yaml, x_composition.schema.yaml]\n"
    ),
    "x_projection.schema.yaml": "properties:\n  schema:\n    const: l9.projection.x/v1\n",
    "x_composition.schema.yaml": "properties:\n  schema:\n    const: l9.composed-projection.x/v1\n",
}

VALIDATOR = (
    "import pathlib, sys\n"
    "sys.exit(int(pathlib.Path(__file__).with_name('exit_code').read_text()))\n"
)


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root

    def git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def release(self, version: str, status: str) -> None:
        files = sorted(f"semantics/{n}" for n in LEDGERS)
        manifest = "# Manifest\n\n" + "".join(f"- `{f}`\n" for f in files)
        self.write(f"docs/semantic-foundation/{version}/MANIFEST.md", manifest)
        self.write(
            f"docs/semantic-foundation/{version}/README.md",
            f"# {version}\n\nStatus: {status}\n",
        )
        lines = []
        for rel in files:
            digest = hashlib.sha256((self.root / rel).read_bytes()).hexdigest()
            lines.append(f"{digest}  ./{rel}\n")
        self.write(f"docs/semantic-foundation/{version}/HASHES.sha256", "".join(lines))

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")


def build(
    root: Path,
    *,
    status="**ADMITTED ADDITIVE SUCCESSOR** (ADR-001)",
    adr_version="v1.0.0",
):
    repo = Repo(root)
    repo.git("init", "-q")
    repo.git("config", "user.email", "fixture@example.invalid")
    repo.git("config", "user.name", "fixture")
    for name, text in LEDGERS.items():
        repo.write(f"semantics/{name}", text)
    repo.write("scripts/validate-semantics.py", VALIDATOR)
    repo.write("scripts/exit_code", "0")
    repo.release("v1.0.0", status)
    repo.write(
        "docs/adr/ADR-001-admit.md",
        f"# ADR-001\n\n**Status:** Accepted for semantic-foundation {adr_version}.\n",
    )
    repo.commit("release v1.0.0")
    return repo


class _Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = build(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def verdict(self, subject=None):
        return cac.evaluate(
            self.repo.root, subject or cac.load_subject(self._subject()), "origin/main"
        )

    def _subject(self, body=None):
        path = self.tmp / "subject.json"
        path.write_text(json.dumps(body or SUBJECT), encoding="utf-8")
        return path


class Ladder(_Fixture):
    def test_admitted_and_current_reaches_admitted(self):
        report = self.verdict()
        self.assertEqual(report["verdict"], "ADMITTED", json.dumps(report, indent=1))
        self.assertEqual(report["admission"]["release"], "v1.0.0")
        self.assertEqual(report["admission"]["adr"], "ADR-001-admit.md")
        self.assertEqual(report["admission"]["changed_since_admission"], [])

    def test_unregistered_schema_is_incomplete(self):
        self.repo.write(
            "semantics/generic_compiler_manifest.yaml",
            "requires:\n  semantic_catalogs: [x_model.yaml]\n  artifact_schemas: [x_projection.schema.yaml]\n",
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        gaps = "\n".join(report["registration"]["gaps"])
        self.assertIn(
            "schema x_composition.schema.yaml: not in generic_compiler_manifest", gaps
        )
        self.assertIn(
            "composition profile l9.compose/x@1: no registered schema declares", gaps
        )

    def test_undeclared_source_class_is_incomplete(self):
        text = LEDGERS["projection_profiles.yaml"].replace(
            "x_model:\n    canonical_artifact", "y:\n    canonical_artifact"
        )
        self.repo.write("semantics/projection_profiles.yaml", text)
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn(
            "source class x_model: not declared",
            "\n".join(report["registration"]["gaps"]),
        )

    def test_source_missing_from_semantic_catalogs_is_incomplete(self):
        self.repo.write(
            "semantics/generic_compiler_manifest.yaml",
            LEDGERS["generic_compiler_manifest.yaml"].replace("[x_model.yaml]", "[]"),
        )
        self.assertEqual(self.verdict()["verdict"], "INCOMPLETE")

    def test_duplicate_invariant_is_incomplete(self):
        self.repo.write(
            "semantics/invariants.yaml",
            LEDGERS["invariants.yaml"] + "- id: L9-X-001\n  statement: again\n",
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "INCOMPLETE")
        self.assertIn(
            "invariant L9-X-001: defined 2 times", report["registration"]["gaps"]
        )

    def test_failing_validator_stops_at_registered(self):
        self.repo.write("scripts/exit_code", "1")
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertEqual(report["validator"]["status"], "fail")

    def test_bytes_drifting_from_release_stop_at_registered(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        report = self.verdict()
        self.assertEqual(report["verdict"], "REGISTERED")
        self.assertIn(
            "v1.0.0: semantics/x_model.yaml bytes differ from the release hash",
            report["release"]["gaps"],
        )

    def test_candidate_release_stops_at_released_candidate(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.repo = build(self.tmp, status="**ADDITIVE SUCCESSOR CANDIDATE**")
        report = self.verdict()
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertEqual(report["release"]["release_status"], "CANDIDATE")
        self.assertEqual(report["release"]["status"], "pass")

    def test_admitted_status_without_matching_adr_is_not_admitted(self):
        shutil.rmtree(self.tmp)
        self.tmp.mkdir()
        self.repo = build(self.tmp, adr_version="v9.9.9")
        report = self.verdict()
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertIsNone(report["admission"]["tried"][0]["adr"])

    def test_record_changed_after_admission_is_not_admitted(self):
        changed = LEDGERS["projection_profiles.yaml"].replace(
            "purpose: project x", "purpose: project x, revised"
        )
        self.repo.write("semantics/projection_profiles.yaml", changed)
        self.repo.release("v1.1.0", "**ADDITIVE SUCCESSOR CANDIDATE**")
        self.repo.commit("candidate v1.1.0 revises the profile")
        report = self.verdict()
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertEqual(report["release"]["version"], "v1.1.0")
        self.assertIn(
            "projection profile:l9.projection/x@1",
            report["admission"]["changed_since_admission"],
        )

    def test_later_admitted_release_takes_over(self):
        changed = LEDGERS["projection_profiles.yaml"].replace(
            "purpose: project x", "purpose: project x, revised"
        )
        self.repo.write("semantics/projection_profiles.yaml", changed)
        self.repo.release("v1.1.0", "**ADMITTED ADDITIVE SUCCESSOR** (ADR-002)")
        self.repo.write(
            "docs/adr/ADR-002-admit.md",
            "# ADR-002\n\n**Status:** Accepted for semantic-foundation v1.1.0.\n",
        )
        self.repo.commit("admit v1.1.0")
        report = self.verdict()
        self.assertEqual(report["verdict"], "ADMITTED")
        self.assertEqual(report["admission"]["release"], "v1.1.0")

    def test_uncommitted_registration_is_not_admitted_on_main(self):
        # A new invariant registered and released in the working tree only: main never saw it.
        self.repo.write(
            "semantics/invariants.yaml",
            LEDGERS["invariants.yaml"] + "- id: L9-X-002\n  statement: y\n",
        )
        self.repo.release("v1.1.0", "**ADMITTED ADDITIVE SUCCESSOR** (ADR-002)")
        subject = dict(SUBJECT, invariants=["L9-X-002"])
        report = self.verdict(cac.load_subject(self._subject(subject)))
        self.assertEqual(report["verdict"], "RELEASED_CANDIDATE")
        self.assertEqual(report["admission"]["status"], "fail")


class InputsAndExitCodes(_Fixture):
    def run_main(self, *extra, subject=None):
        return cac.main(
            [
                "--checkout",
                str(self.repo.root),
                "--subject",
                str(self._subject(subject)),
                *extra,
            ]
        )

    def test_exit_zero_when_required_rung_reached(self):
        self.assertEqual(self.run_main("--require", "registered"), 0)
        self.assertEqual(self.run_main("--require", "admitted"), 0)

    def test_exit_one_when_required_rung_not_reached(self):
        self.repo.write("scripts/exit_code", "1")
        self.assertEqual(self.run_main("--require", "released"), 1)

    def test_downstream_requirement_without_compiler_is_unresolved(self):
        self.assertEqual(self.run_main("--require", "downstream"), 2)

    def test_missing_main_ref_is_unresolved(self):
        self.assertEqual(self.run_main("--main-ref", "origin/nope"), 2)

    def test_missing_validator_is_unresolved(self):
        (self.repo.root / "scripts" / "validate-semantics.py").unlink()
        self.assertEqual(self.run_main(), 2)

    def test_malformed_subjects_are_unresolved(self):
        for body in (
            {"schema": "other"},
            {"schema": cac.SUBJECT_SCHEMA},
            {"schema": cac.SUBJECT_SCHEMA, "invariants": ["A", "A"]},
            {"schema": cac.SUBJECT_SCHEMA, "profiles": ["x"]},
            {"schema": cac.SUBJECT_SCHEMA, "invariants": "L9-X-001"},
        ):
            self.assertEqual(self.run_main(subject=body), 2, body)

    def test_downstream_refuses_a_dirty_checkout(self):
        self.repo.write(
            "semantics/x_model.yaml", LEDGERS["x_model.yaml"] + "value2: 2\n"
        )
        result = cac.downstream(
            self.repo.root,
            self.tmp / "no-compiler",
            self.tmp / "out",
            cac.load_subject(self._subject()),
        )
        self.assertEqual(result["status"], "fail")
        self.assertIn("tracked changes", result["reason"])


if __name__ == "__main__":
    unittest.main()
