#!/usr/bin/env python3
"""Suite for ops/register-birth.py (ADR-039).

Builds a factory-shaped newborn (receipt + root commit with trailers) and a
factory-shaped template repository in temporary git repositories, then drives
the real tool against a copy of this `.github` tree. No network.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "ops" / "register-birth.py"

spec = importlib.util.spec_from_file_location("register_birth", TOOL_PATH)
assert spec is not None and spec.loader is not None
rb = importlib.util.module_from_spec(spec)
sys.modules["register_birth"] = rb
spec.loader.exec_module(rb)

REPO = "l9-fixture-node"
POLICY_SHA = "d" * 40
BORN_AT = "2026-11-13T12:00:00Z"


def git(cwd: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout


PASSING_VERIFIER = """import json, sys
print(json.dumps({"schema": "l9.birth-integrity-report/v1", "result": "PASS",
  "checks": [{"key": "receipt.present", "status": "PASS"},
             {"key": "root.manifest", "status": "PASS"}]}))
"""
FAILING_VERIFIER = """import json, sys
print(json.dumps({"schema": "l9.birth-integrity-report/v1", "result": "FAIL",
  "checks": [{"key": "root.manifest", "status": "FAIL"}]}))
sys.exit(1)
"""


def make_template(base: Path, verifier: str) -> tuple[Path, str]:
    """A factory-shaped repository whose default branch carries a verifier."""
    tpl = base / "template"
    (tpl / "scripts" / "birth-runner").mkdir(parents=True)
    git(tpl, "init", "-q", "-b", "main")
    (tpl / ".l9-template-version").write_text("2.1.0\n")
    (tpl / rb.FACTORY_VERIFIER).write_text(verifier)
    git(tpl, "add", "-A")
    git(tpl, "commit", "-q", "-m", "factory")
    sha = git(tpl, "rev-parse", "HEAD").strip()
    git(tpl, "update-ref", "refs/remotes/origin/main", sha)
    return tpl, sha


def make_newborn(
    base: Path, template_sha: str, *, tamper=None, trailer_class=None
) -> Path:
    newborn = base / "newborn"
    (newborn / ".l9").mkdir(parents=True)
    git(newborn, "init", "-q", "-b", "main")
    (newborn / "README.md").write_text("# fixture\n")
    receipt = {
        "schema": rb.RECEIPT_SCHEMA,
        "repository": f"{rb.ORG}/{REPO}",
        "repo_class": "org_seeded_self_governed",
        "template": {"repository": rb.FACTORY, "sha": template_sha, "version": "2.1.0"},
        "org_policy": {"repository": "Quantum-L9/.github", "sha": POLICY_SHA},
        "payload_mode": "product",
        "manifest_sha256": "e" * 64,
        "born_at": BORN_AT,
    }
    receipt["digest"] = rb.receipt_digest(receipt)
    if tamper:
        tamper(receipt)
    (newborn / rb.RECEIPT_PATH).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    git(newborn, "add", "-A")
    message = (
        "chore: birth\n\n"
        f"L9-Birth-Receipt: sha256:{receipt['digest']}\n"
        f"L9-Template: {template_sha}\n"
        "L9-Template-Version: 2.1.0\n"
        f"L9-Policy: {POLICY_SHA}\n"
        f"L9-Class: {trailer_class or receipt['repo_class']}\n"
    )
    git(newborn, "commit", "-q", "-m", message)
    return newborn


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
    def __init__(self, newborn: Path, template: Path, checkout: Path, skip: bool):
        self.newborn = str(newborn)
        self.template = str(template)
        self.checkout = str(checkout)
        self.repository = REPO
        self.skip_factory_verifier = skip
        self.changes_out = None


class RegisterBirthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.base = Path(cls._tmp.name)
        cls.checkout = copy_dotgithub(cls.base)
        cls.validator = rb._load_validator(cls.checkout)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def setUp(self) -> None:
        self._case = tempfile.TemporaryDirectory()
        self.case = Path(self._case.name)

    def tearDown(self) -> None:
        self._case.cleanup()

    def birth(self, verifier: str = PASSING_VERIFIER, **kwargs) -> tuple[Path, Path]:
        template, sha = make_template(self.case, verifier)
        return make_newborn(self.case, sha, **kwargs), template

    def expected_entry(self, newborn: Path, template: Path) -> dict:
        receipt = json.loads((newborn / rb.RECEIPT_PATH).read_text())
        return {
            "id": REPO,
            "coordinate": {
                "provider": "github",
                "organization": "Quantum-L9",
                "repository": REPO,
            },
            "lifecycle": "current",
            "class_ref": "l9.repository-class/l9@1",
            "birth_provenance": {
                "factory": "Quantum-L9/l9-repo-template",
                "receipt_schema": "l9.birth-receipt/v1",
                "receipt_digest": f"sha256:{receipt['digest']}",
                "root_commit": git(newborn, "rev-parse", "HEAD").strip(),
                "template_sha": git(template, "rev-parse", "HEAD").strip(),
                "template_version": "2.1.0",
                "org_policy_sha": POLICY_SHA,
                "birth_profile": "org_seeded_self_governed",
                "born_at": BORN_AT,
            },
        }

    # ── rendering ────────────────────────────────────────────────────────

    def test_renders_entry_from_receipt_through_the_factory_verifier(self) -> None:
        newborn, template = self.birth()
        entry = rb.prove_and_render(
            Args(newborn, template, self.checkout, False), self.checkout
        )
        self.assertEqual(entry, self.expected_entry(newborn, template))
        self.assertEqual(self.validator.rc023_factory_entry_problems(entry), [])

    def test_rendered_yaml_round_trips_and_quotes_timestamps(self) -> None:
        newborn, template = self.birth()
        entry = rb.prove_and_render(
            Args(newborn, template, self.checkout, True), self.checkout
        )
        text = rb.render_entry_yaml(entry)
        self.assertIn(f'born_at: "{BORN_AT}"', text)
        self.assertEqual(rb.yaml.safe_load("x:\n" + text)["x"][0], entry)

    def test_id_rule(self) -> None:
        rid = self.validator.rc023_factory_repository_id
        self.assertEqual(rid("l9-state"), "l9-state")
        self.assertEqual(rid("L9_Original_Repo"), "l9-original-repo")
        self.assertEqual(rid("Foo..Bar__baz"), "foo-bar-baz")
        self.assertIsNone(rid(".github"))
        self.assertIsNone(rid("bad/name"))

    # ── apply: validator passes, idempotent, duplicates refused ──────────

    def test_apply_writes_entry_and_release_that_pass_the_validator(self) -> None:
        checkout = copy_dotgithub(self.case)
        newborn, template = self.birth()
        before = rb.release_versions(checkout)[-1]
        result = rb.apply(Args(newborn, template, checkout, False))
        self.assertEqual(result["status"], "added")
        major, minor, patch = before
        version = f"v{major}.{minor}.{patch + 1}"
        self.assertEqual(result["release"], version)
        self.assertIn(rb.REGISTRY_PATH, result["changed_paths"])
        self.assertIn(
            f"{rb.RELEASES_PATH}/{version}/HASHES.sha256", result["changed_paths"]
        )
        registry = rb.yaml.safe_load((checkout / rb.REGISTRY_PATH).read_text())
        self.assertEqual(
            registry["repositories"][-1], self.expected_entry(newborn, template)
        )
        # apply already ran the validator; run it once more from here as evidence
        rb.run_validator(checkout)
        # a re-run is a no-op
        again = rb.apply(Args(newborn, template, checkout, False))
        self.assertEqual(again["status"], "present")
        self.assertEqual(again["changed_paths"], [])
        self.assertEqual(rb.release_versions(checkout)[-1], (major, minor, patch + 1))

    def test_duplicate_with_different_content_is_refused(self) -> None:
        newborn, template = self.birth()
        entry = rb.prove_and_render(
            Args(newborn, template, self.checkout, True), self.checkout
        )
        text = (self.checkout / rb.REGISTRY_PATH).read_text()
        added, status = rb.add_entry(text, entry)
        self.assertEqual(status, "added")
        self.assertEqual(rb.add_entry(added, entry), (added, "present"))
        other = copy.deepcopy(entry)
        other["birth_provenance"]["root_commit"] = "f" * 40
        with self.assertRaisesRegex(rb.BirthRegistrationError, "different entry"):
            rb.add_entry(added, other)
        squat = copy.deepcopy(entry)
        squat["coordinate"]["repository"] = "l9-deploy"
        squat["id"] = "l9-deploy"
        with self.assertRaisesRegex(rb.BirthRegistrationError, "different entry"):
            rb.add_entry(text, squat)

    # ── unverifiable births are refused ──────────────────────────────────

    def assert_refused(
        self, newborn: Path, template: Path, pattern: str, skip: bool = True
    ) -> None:
        with self.assertRaisesRegex(rb.BirthRegistrationError, pattern):
            rb.prove_and_render(
                Args(newborn, template, self.checkout, skip), self.checkout
            )

    def test_tampered_receipt_is_refused(self) -> None:
        newborn, template = self.birth(tamper=lambda r: r.update(repo_class="default"))
        self.assert_refused(newborn, template, "digest")

    def test_trailer_disagreement_is_refused(self) -> None:
        newborn, template = self.birth(trailer_class="default")
        self.assert_refused(newborn, template, "trailers disagree")

    def test_receipt_modified_after_birth_is_refused(self) -> None:
        newborn, template = self.birth()
        path = newborn / rb.RECEIPT_PATH
        path.write_text(path.read_text().replace("  ", "   "))
        self.assert_refused(newborn, template, "modified after the root commit")

    def test_foreign_factory_is_refused(self) -> None:
        def fork(receipt: dict) -> None:
            receipt["template"]["repository"] = "someone/fork"
            receipt["digest"] = rb.receipt_digest(receipt)

        newborn, template = self.birth(tamper=fork)
        self.assert_refused(newborn, template, "not the factory")

    def test_wrong_repository_is_refused(self) -> None:
        newborn, _template = self.birth()
        with self.assertRaisesRegex(rb.BirthRegistrationError, "receipt names"):
            receipt = rb.load_receipt(newborn)
            rb.verify_receipt(newborn, "some-other-repo", receipt)

    def test_missing_receipt_is_refused(self) -> None:
        newborn, template = self.birth()
        (newborn / rb.RECEIPT_PATH).unlink()
        self.assert_refused(newborn, template, "not factory-born")

    def test_shallow_clone_is_refused(self) -> None:
        newborn, template = self.birth()
        (newborn / "NEXT.md").write_text("next\n")
        git(newborn, "add", "-A")
        git(newborn, "commit", "-q", "-m", "next")
        shallow = self.case / "shallow"
        git(self.case, "clone", "-q", "--depth", "1", f"file://{newborn}", str(shallow))
        self.assert_refused(shallow, template, "shallow")

    def test_failing_factory_verifier_is_refused(self) -> None:
        newborn, template = self.birth(verifier=FAILING_VERIFIER)
        self.assert_refused(newborn, template, "not PASS", skip=False)

    def test_template_commit_off_the_factory_branch_is_refused(self) -> None:
        _newborn, template = self.birth()
        git(template, "commit", "-q", "--allow-empty", "-m", "later")
        git(template, "update-ref", "refs/remotes/origin/main", "HEAD")
        git(template, "checkout", "-q", "--orphan", "fork")
        (template / rb.FACTORY_VERIFIER).write_text(PASSING_VERIFIER)
        git(template, "add", "-A")
        git(template, "commit", "-q", "-m", "fork verifier")
        fork_sha = git(template, "rev-parse", "HEAD").strip()
        with self.assertRaisesRegex(rb.BirthRegistrationError, "not on"):
            rb.verify_factory_revision(template, fork_sha)

    def test_ambiguous_class_is_refused(self) -> None:
        classes = rb.yaml.safe_load((self.checkout / rb.CLASSES_PATH).read_text())
        self.assertEqual(rb.admitted_class(classes), "l9.repository-class/l9@1")
        second = copy.deepcopy(classes)
        second["classes"]["aux"] = {
            "id": "l9.repository-class/aux@1",
            "status": "current",
        }
        second["catalog_status"]["admitted_classes"].append("l9.repository-class/aux@1")
        with self.assertRaisesRegex(rb.BirthRegistrationError, "ambiguous"):
            rb.admitted_class(second)

    def test_validator_rejects_an_untyped_registry_addition(self) -> None:
        """Without birth_provenance an extra entry still needs the census pin."""
        entry = {
            "id": REPO,
            "coordinate": {
                "provider": "github",
                "organization": "Quantum-L9",
                "repository": REPO,
            },
            "lifecycle": "current",
            "class_ref": "l9.repository-class/l9@1",
        }
        docs = {
            rb.REGISTRY_PATH: rb.yaml.safe_load(
                (self.checkout / rb.REGISTRY_PATH).read_text()
            ),
            rb.CLASSES_PATH: rb.yaml.safe_load(
                (self.checkout / rb.CLASSES_PATH).read_text()
            ),
        }
        docs[rb.REGISTRY_PATH]["repositories"].append(entry)
        report = self.validator.Report()
        self.validator._evaluate_rc023(docs, report)
        self.assertTrue(report.failures)


class ChangesOutConfinementTest(unittest.TestCase):
    """--changes-out may only write a .json file directly inside $RUNNER_TEMP/birth."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._saved = os.environ.get("RUNNER_TEMP")
        os.environ["RUNNER_TEMP"] = self._tmp.name

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("RUNNER_TEMP", None)
        else:
            os.environ["RUNNER_TEMP"] = self._saved
        self._tmp.cleanup()

    def test_scratch_path_is_accepted(self) -> None:
        target = Path(self._tmp.name) / "birth" / "registration.json"
        self.assertEqual(rb.confined_output(str(target)), target.resolve())

    def test_other_directory_is_refused(self) -> None:
        with self.assertRaises(rb.BirthRegistrationError):
            rb.confined_output(str(Path(self._tmp.name) / "registration.json"))

    def test_traversal_is_refused(self) -> None:
        raw = str(Path(self._tmp.name) / "birth" / ".." / ".." / "registration.json")
        with self.assertRaises(rb.BirthRegistrationError):
            rb.confined_output(raw)

    def test_other_file_name_is_refused(self) -> None:
        with self.assertRaises(rb.BirthRegistrationError):
            rb.confined_output(str(Path(self._tmp.name) / "birth" / "other.json"))

    def test_symlink_is_refused(self) -> None:
        birth = Path(self._tmp.name) / "birth"
        birth.mkdir()
        link = birth / "registration.json"
        link.symlink_to("/etc/passwd")
        with self.assertRaises(rb.BirthRegistrationError):
            rb.confined_output(str(link))


if __name__ == "__main__":
    unittest.main(verbosity=1)
