#!/usr/bin/env python3
"""Suite for ops/register-org-repository.py (ADR-040).

Drives the real tool against a copy of this `.github` tree. No network. Proves
the organization-admitted entry is the one the law fixes (folded id, the single
admitted class, lifecycle current, no ProductKind), that apply writes an entry
plus a release record the semantic validator accepts, that a re-run is a no-op,
and that every refusal fails closed without leaving a partial write.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "ops" / "register-org-repository.py"

spec = importlib.util.spec_from_file_location("register_org_repository", TOOL_PATH)
assert spec is not None and spec.loader is not None
ro = importlib.util.module_from_spec(spec)
sys.modules["register_org_repository"] = ro
spec.loader.exec_module(ro)

REPO = "New.Org_Repo-2"
FOLDED = "new-org-repo-2"
GITHUB_ID = 987654321
OBSERVED_AT = "2026-11-17T12:00:00Z"


def copy_dotgithub(base: Path) -> Path:
    target = base / "dotgithub"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "node_modules", ".cache", "__pycache__"
        ),
    )
    return target


class Args:
    def __init__(self, repository: str = REPO, **overrides) -> None:
        self.repository = repository
        self.github_id = GITHUB_ID
        self.observed_at = OBSERVED_AT
        self.archived = False
        for key, value in overrides.items():
            setattr(self, key, value)


def expected_entry(repository: str = REPO, rid: str = FOLDED) -> dict:
    return {
        "id": rid,
        "coordinate": {
            "provider": "github",
            "organization": "Quantum-L9",
            "repository": repository,
        },
        "lifecycle": "current",
        "class_ref": "l9.repository-class/l9@1",
        "organization_admission": {
            "basis": "organization_completeness",
            "decision_record": "ADR-040",
            "github_repository_id": GITHUB_ID,
            "observed_at": OBSERVED_AT,
        },
    }


class RegisterOrgRepositoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.checkout = copy_dotgithub(Path(cls._tmp.name))
        cls.birth = ro._birth_tool(cls.checkout)
        cls.validator = cls.birth._load_validator(cls.checkout)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self._case = tempfile.TemporaryDirectory()
        self.case = Path(self._case.name)

    def tearDown(self) -> None:
        self._case.cleanup()

    # ── rendering ────────────────────────────────────────────────────────

    def test_renders_the_entry_the_law_fixes(self) -> None:
        entry = ro.render(Args(), self.checkout)
        self.assertEqual(entry, expected_entry())
        self.assertNotIn("product_kind", entry)
        self.assertEqual(self.validator.rc023_org_entry_problems(entry), [])

    def test_rendered_yaml_round_trips_and_quotes_timestamps(self) -> None:
        entry = ro.render(Args(), self.checkout)
        text = ro.render_entry_yaml(self.birth, entry)
        self.assertIn(f'observed_at: "{OBSERVED_AT}"', text)
        self.assertIn(f"github_repository_id: {GITHUB_ID}\n", text)
        self.assertEqual(ro.yaml.safe_load("x:\n" + text)["x"][0], entry)

    def test_cli_reads_the_working_directory_and_writes_one_fixed_result(self) -> None:
        """The command line carries no path: cwd is the tree, the result file is fixed."""
        argv = [
            "render",
            "--repository",
            REPO,
            "--github-id",
            str(GITHUB_ID),
            "--observed-at",
            OBSERVED_AT,
            "--write-result",
        ]
        prev_cwd, prev_temp = os.getcwd(), os.environ.get("RUNNER_TEMP")
        os.chdir(self.checkout)
        os.environ["RUNNER_TEMP"] = str(self.case)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ro.main(argv), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                for flag, bad in (
                    ("--repository", "bad/name"),
                    ("--observed-at", "2026-11-17 12:00"),
                ):
                    bad_argv = list(argv)
                    bad_argv[bad_argv.index(flag) + 1] = bad
                    self.assertEqual(ro.main(bad_argv), 1, flag)
            with (
                self.assertRaises(SystemExit),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                ro.main([*argv, "--changes-out", str(self.case / "x.json")])
        finally:
            os.chdir(prev_cwd)
            if prev_temp is None:
                os.environ.pop("RUNNER_TEMP", None)
            else:
                os.environ["RUNNER_TEMP"] = prev_temp
        written = json.loads(
            (self.case / "org-admission" / "admission.json").read_text()
        )
        self.assertEqual(written, {"status": "rendered", "entry": expected_entry()})

    def test_registry_ids_follow_the_folding_rule(self) -> None:
        """Every registered id is fold(name) except the grandfathered ones."""
        registry = ro.yaml.safe_load((self.checkout / ro.REGISTRY_PATH).read_text())
        fold = self.validator.rc023_factory_repository_id
        grandfathered = self.validator.RC023_GRANDFATHERED_IDS
        for item in registry["repositories"]:
            name = item["coordinate"]["repository"]
            if item["id"] in grandfathered:
                self.assertEqual(grandfathered[item["id"]], name)
            else:
                self.assertEqual(item["id"], fold(name), name)

    # ── apply: validator passes, idempotent ──────────────────────────────

    def test_apply_writes_entry_and_release_that_pass_the_validator(self) -> None:
        checkout = copy_dotgithub(self.case)
        major, minor, patch = self.birth.release_versions(checkout)[-1]
        result = ro.apply(Args(), checkout)
        self.assertEqual(result["status"], "added")
        version = f"v{major}.{minor}.{patch + 1}"
        self.assertEqual(result["release"], version)
        self.assertEqual(
            result["changed_paths"],
            [
                ro.REGISTRY_PATH,
                f"{ro.RELEASES_PATH}/{version}/MANIFEST.md",
                f"{ro.RELEASES_PATH}/{version}/README.md",
                f"{ro.RELEASES_PATH}/{version}/RELEASE_VALIDATION.md",
                f"{ro.RELEASES_PATH}/{version}/HASHES.sha256",
            ],
        )
        registry = ro.yaml.safe_load((checkout / ro.REGISTRY_PATH).read_text())
        self.assertEqual(registry["repositories"][-1], expected_entry())
        # apply ran the full semantic validator on this tree and kept it only
        # because it passed; a failing tree would have been restored.
        again = ro.apply(Args(), checkout)
        self.assertEqual(again["status"], "present")
        self.assertEqual(again["changed_paths"], [])
        later = ro.apply(Args(observed_at="2026-11-18T00:00:00Z"), checkout)
        self.assertEqual(later["status"], "present")
        self.assertEqual(later["changed_paths"], [])
        kept = ro.yaml.safe_load((checkout / ro.REGISTRY_PATH).read_text())
        self.assertEqual(
            kept["repositories"][-1]["organization_admission"]["observed_at"],
            OBSERVED_AT,
        )
        self.assertEqual(
            self.birth.release_versions(checkout)[-1], (major, minor, patch + 1)
        )

    # ── refusals ─────────────────────────────────────────────────────────

    def assertRefusedWithoutWrite(self, args_overrides: dict, repository=REPO) -> None:
        # Every refusal here happens before a byte is written, so the shared
        # checkout is used and then proven unchanged.
        checkout = self.checkout
        registry_before = (checkout / ro.REGISTRY_PATH).read_bytes()
        releases_before = self.birth.release_versions(checkout)
        with self.assertRaises(ro.OrgAdmissionError):
            ro.apply(Args(repository, **args_overrides), checkout)
        self.assertEqual((checkout / ro.REGISTRY_PATH).read_bytes(), registry_before)
        self.assertEqual(self.birth.release_versions(checkout), releases_before)

    def test_archived_repository_is_refused(self) -> None:
        self.assertRefusedWithoutWrite({"archived": True})

    def test_invalid_name_is_refused(self) -> None:
        self.assertRefusedWithoutWrite({}, repository="bad/name")

    def test_grandfathered_id_is_refused(self) -> None:
        self.assertRefusedWithoutWrite({}, repository="dot-github")

    def test_non_positive_repository_id_is_refused(self) -> None:
        self.assertRefusedWithoutWrite({"github_id": 0})

    def test_registered_repository_is_left_as_recorded(self) -> None:
        """An already-pinned coordinate is not proposed again, and its evidence stays."""
        checkout = self.checkout
        registry_before = (checkout / ro.REGISTRY_PATH).read_bytes()
        releases_before = self.birth.release_versions(checkout)
        result = ro.apply(
            Args(
                repository="Gate_SDK",
                github_id=1,
                observed_at="2026-11-18T00:00:00Z",
            ),
            checkout,
        )
        self.assertEqual(result["status"], "present")
        self.assertEqual(result["changed_paths"], [])
        self.assertEqual((checkout / ro.REGISTRY_PATH).read_bytes(), registry_before)
        self.assertEqual(self.birth.release_versions(checkout), releases_before)

    def test_same_fold_with_a_different_coordinate_is_a_collision(self) -> None:
        self.assertRefusedWithoutWrite({}, repository="gate-sdk")

    def test_leading_mark_folds_and_dot_github_does_not(self) -> None:
        fold = self.validator.rc023_factory_repository_id
        self.assertEqual(fold(".tools"), "tools")
        self.assertEqual(fold("_shared"), "shared")
        self.assertIsNone(fold(".github"))

    def test_a_failed_release_cut_removes_the_new_directory(self) -> None:
        checkout = copy_dotgithub(self.case)
        before = self.birth.release_versions(checkout)
        registry_before = (self.checkout / ro.REGISTRY_PATH).read_bytes()
        real = ro.write_hashes

        def boom(root, target):
            raise ro.OrgAdmissionError("hash failed")

        ro.write_hashes = boom
        try:
            with self.assertRaises(ro.OrgAdmissionError):
                ro.apply(Args(), checkout)
        finally:
            ro.write_hashes = real
        self.assertEqual(self.birth.release_versions(checkout), before)
        self.assertEqual((checkout / ro.REGISTRY_PATH).read_bytes(), registry_before)
        self.assertFalse((checkout / ro.RELEASES_PATH / f"v{before[-1][0]}.{before[-1][1]}.{before[-1][2] + 1}").exists())

    def test_ambiguous_class_is_refused(self) -> None:
        checkout = copy_dotgithub(self.case)
        classes_path = checkout / ro.CLASSES_PATH
        classes = ro.yaml.safe_load(classes_path.read_text())
        classes["classes"]["other"] = dict(
            classes["classes"]["l9"], id="l9.repository-class/other@1"
        )
        classes["catalog_status"]["admitted_classes"].append(
            "l9.repository-class/other@1"
        )
        classes_path.write_text(ro.yaml.safe_dump(classes))
        with self.assertRaises(ro.OrgAdmissionError):
            ro.render(Args(), checkout)

    def test_validator_rejects_the_entry_without_its_marker(self) -> None:
        """Without organization_admission an extra entry still needs the census pin."""
        entry = expected_entry()
        del entry["organization_admission"]
        docs = {
            ro.REGISTRY_PATH: ro.yaml.safe_load(
                (self.checkout / ro.REGISTRY_PATH).read_text()
            ),
            ro.CLASSES_PATH: ro.yaml.safe_load(
                (self.checkout / ro.CLASSES_PATH).read_text()
            ),
        }
        docs[ro.REGISTRY_PATH]["repositories"].append(entry)
        report = self.validator.Report()
        self.validator._evaluate_rc023(docs, report)
        self.assertTrue(report.failures)


if __name__ == "__main__":
    unittest.main()
