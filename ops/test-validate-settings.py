#!/usr/bin/env python3
"""Suite for ops/validate-settings.py (GitHub settings as code).

Runs the real validator against this tree, then against copies with one defect
each. No network. Proves the populated declaration is valid, that every
refusal is fatal, that UNKNOWN is accepted wherever a value is, that a policy
disagreement is reported but not fatal unless --strict-policy, and that the
validator never writes.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT / "ops" / "validate-settings.py"

spec = importlib.util.spec_from_file_location("validate_settings", TOOL_PATH)
assert spec is not None and spec.loader is not None
vs = importlib.util.module_from_spec(spec)
sys.modules["validate_settings"] = vs
spec.loader.exec_module(vs)


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in (root / "settings").rglob("*") if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "dotgithub"
        for rel in (
            "settings",
            "semantics/repository_registry.yaml",
            "policies/repo-settings.yml",
        ):
            source = ROOT / rel
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def repo_path(self, name: str) -> Path:
        return self.root / "settings" / "repos" / f"{name}.yml"

    def edit(self, name: str, mutate) -> None:
        path = self.repo_path(name)
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        mutate(doc)
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    def errors(self, strict: bool = False) -> list[str]:
        return vs.validate(self.root, strict_policy=strict)[0]

    def assert_refused(self, fragment: str, strict: bool = False) -> None:
        errors = self.errors(strict)
        self.assertTrue(
            any(fragment in e for e in errors), f"{fragment!r} not in {errors}"
        )


class LiveTree(unittest.TestCase):
    def test_populated_declaration_is_valid(self) -> None:
        errors, _ = vs.validate(ROOT)
        self.assertEqual(errors, [])

    def test_dotgithub_is_declared_with_campaign_target(self) -> None:
        doc = yaml.safe_load(
            (ROOT / "settings/repos/.github.yml").read_text(encoding="utf-8")
        )
        self.assertEqual(doc["actions"]["access_level"], "organization")
        self.assertEqual(doc["visibility"], "public")
        self.assertIn("actions.access_level", doc["observed"]["decided"])

    def test_dotfile_declaration_is_discovered(self) -> None:
        names = [p.name for p in vs.repository_files(ROOT / "settings")]
        self.assertIn(".github.yml", names)

    def test_main_exit_code_and_summary(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(vs.main(["--root", str(ROOT)]), 0)
        self.assertIn("error(s)", out.getvalue())


class Refusals(Fixture):
    def test_valid_copy_passes_and_is_not_written(self) -> None:
        before = tree_digest(self.root)
        self.assertEqual(self.errors(), [])
        self.assertEqual(tree_digest(self.root), before)

    def test_filename_must_match_repository(self) -> None:
        self.repo_path("l9-ci-core").rename(self.repo_path("l9-ci-core-renamed"))
        self.assert_refused("file must be named l9-ci-core.yml")

    def test_one_repository_declared_twice(self) -> None:
        shutil.copy2(
            self.repo_path("l9-ci-core"),
            self.root / "settings" / "repos" / "l9-ci-core.yaml",
        )
        self.assert_refused("l9-ci-core is already declared by settings/repos/")

    def test_unregistered_repository(self) -> None:
        self.edit("l9-ci-core", lambda d: d.update(repository="not-a-registered-repo"))
        self.repo_path("l9-ci-core").rename(self.repo_path("not-a-registered-repo"))
        self.assert_refused("not registered in semantics/repository_registry.yaml")

    def test_secret_value_cannot_be_declared(self) -> None:
        def mutate(d):
            d["environments"][0]["secrets"] = {"BIRTH_APP_PRIVATE_KEY": "-----BEGIN"}

        self.edit("l9-repo-template", mutate)
        self.assert_refused("Additional properties are not allowed")

    def test_secret_names_must_be_names(self) -> None:
        self.edit(
            "l9-repo-template",
            lambda d: d["environments"][0].update(required_secrets=["ghp_abc123"]),
        )
        self.assert_refused("required_secrets")

    def test_bad_enum(self) -> None:
        self.edit("l9-ci-core", lambda d: d.update(visibility="secret"))
        self.assert_refused("visibility")

    def test_unknown_top_level_key(self) -> None:
        self.edit("l9-ci-core", lambda d: d.update(branch_protection={"main": True}))
        self.assert_refused("Additional properties are not allowed")

    def test_duplicate_ruleset_name(self) -> None:
        self.edit(
            "Cursor-Governance", lambda d: d["rulesets"].append(dict(d["rulesets"][0]))
        )
        self.assert_refused("duplicate rulesets name(s)")

    def test_unreadable_section_must_stay_unknown(self) -> None:
        self.edit(
            "l9-ci-core",
            lambda d: d["actions"].update(default_workflow_permissions="read"),
        )
        self.assert_refused(
            "actions.default_workflow_permissions is declared but actions/permissions was unreadable"
        )

    def test_unreadable_environment_field_must_stay_unknown(self) -> None:
        self.edit(
            "l9-repo-template", lambda d: d["environments"][0].update(wait_timer=0)
        )
        self.assert_refused(
            "environments[repo-birth].wait_timer is declared but environments was unreadable"
        )

    def test_decided_field_is_exempt_only_when_listed(self) -> None:
        self.edit(".github", lambda d: d["observed"].pop("decided"))
        self.assert_refused(
            "actions.access_level is declared but actions/permissions was unreadable"
        )

    def test_decided_environment_field_is_exempt(self) -> None:
        def mutate(d):
            d["environments"][0]["wait_timer"] = 0
            d["observed"].setdefault("decided", []).append("environments.wait_timer")

        self.edit("l9-repo-template", mutate)
        self.assertEqual(self.errors(), [])

    def test_sole_yaml_declaration_is_misnamed(self) -> None:
        self.repo_path("l9-ci-core").rename(
            self.root / "settings" / "repos" / "l9-ci-core.yaml"
        )
        self.assert_refused("file must be named l9-ci-core.yml")

    def test_every_merge_setting_is_required(self) -> None:
        self.edit("l9-ci-core", lambda d: d["merge"].pop("allow_merge_commit"))
        self.assert_refused("'allow_merge_commit' is a required property")

    def test_duplicate_yaml_key_is_refused(self) -> None:
        # Raw text: the dict-based editor cannot keep a duplicate key.
        path = self.repo_path("l9-ci-core")
        path.write_text(
            path.read_text(encoding="utf-8") + "visibility: private\n",
            encoding="utf-8",
        )
        self.assert_refused("found duplicate key 'visibility'")

    def test_yaml_merge_key_is_accepted(self) -> None:
        # `<<` is valid YAML that SafeLoader flattens; the duplicate scan must not refuse it.
        merged = self.root / "merged.yml"
        merged.write_text(
            "base: &b\n  a: 1\nchild:\n  <<: *b\n  c: 2\n", encoding="utf-8"
        )
        self.assertEqual(vs._load_yaml(merged)["child"], {"a": 1, "c": 2})

    def test_duplicate_key_inside_a_merge_source_is_refused(self) -> None:
        inline = self.root / "inline.yml"
        inline.write_text(
            "defaults:\n  <<: {allow_merge_commit: false, allow_merge_commit: true}\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(vs.DuplicateKeyError, "allow_merge_commit"):
            vs._load_yaml(inline)
        listed = self.root / "listed.yml"
        listed.write_text(
            "x:\n  <<: [{a: 1}, {b: 2, b: 3}]\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(vs.DuplicateKeyError, "'b'"):
            vs._load_yaml(listed)

    def test_reused_merged_mapping_is_not_a_false_duplicate(self) -> None:
        reused = self.root / "reused.yml"
        reused.write_text(
            "defaults: &base\n"
            "  allow_merge_commit: true\n"
            "overrides:\n"
            "  - <<: &override\n"
            "      <<: *base\n"
            "      allow_merge_commit: false\n"
            "      repos: [l9-ci-core]\n"
            "  - *override\n",
            encoding="utf-8",
        )
        doc = vs._load_yaml(reused)
        self.assertEqual(
            [o["allow_merge_commit"] for o in doc["overrides"]], [False, False]
        )

    def test_unhashable_key_is_one_error_and_validation_continues(self) -> None:
        # Files are checked in sorted order: the broken file must come BEFORE the
        # file whose error proves the run continued.
        names = [p.stem for p in vs.repository_files(self.root / "settings")]
        self.assertLess(names.index("Cursor-Governance"), names.index("l9-ci-core"))
        path = self.repo_path("Cursor-Governance")
        path.write_text(
            path.read_text(encoding="utf-8") + "? [a, b]\n: value\n", encoding="utf-8"
        )
        self.edit("l9-ci-core", lambda d: d.update(visibility="secret"))
        errors = self.errors()
        self.assertTrue(
            any(
                "Cursor-Governance.yml: invalid YAML" in e and "unhashable" in e
                for e in errors
            ),
            errors,
        )
        self.assertTrue(
            any(e.startswith("settings/repos/l9-ci-core.yml") for e in errors),
            errors,
        )

    def test_broken_registry_is_one_error_not_a_crash(self) -> None:
        path = self.root / "semantics" / "repository_registry.yaml"
        path.write_text("repositories: [unclosed\n", encoding="utf-8")
        errors = self.errors()
        self.assertTrue(
            any(
                e.startswith("semantics/repository_registry.yaml: invalid YAML")
                for e in errors
            ),
            errors,
        )
        self.assertFalse(any("not registered" in e for e in errors), errors)

    def test_broken_policy_is_one_error_not_a_crash(self) -> None:
        path = self.root / "policies" / "repo-settings.yml"
        path.write_text(
            path.read_text(encoding="utf-8") + "defaults: {}\n", encoding="utf-8"
        )
        self.assert_refused("policies/repo-settings.yml: invalid YAML")

    def test_missing_org(self) -> None:
        (self.root / "settings" / "org.yml").unlink()
        self.assert_refused("settings/org.yml: missing")

    def test_org_rulesets_are_not_redeclared(self) -> None:
        path = self.root / "settings" / "org.yml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        doc["org_rulesets"] = {"owner": "settings/"}
        path.write_text(yaml.safe_dump(doc), encoding="utf-8")
        self.assert_refused("settings/org.yml")


class UnknownAndPolicy(Fixture):
    def test_unknown_accepted_everywhere_a_value_is(self) -> None:
        def mutate(d):
            d["observed"]["unreadable"] = []
            d["visibility"] = "UNKNOWN"
            d["merge"] = "UNKNOWN"
            d["actions"] = "UNKNOWN"
            d["environments"] = "UNKNOWN"
            d["rulesets"] = "UNKNOWN"

        self.edit("l9-ci-core", mutate)
        self.assertEqual(self.errors(), [])

    def test_conflict_reported_not_fatal(self) -> None:
        self.edit("l9-ci-core", lambda d: d["merge"].update(allow_merge_commit=True))
        errors, conflicts = vs.validate(self.root)
        self.assertEqual(errors, [])
        self.assertTrue(
            any("l9-ci-core.yml: merge.allow_merge_commit=true" in c for c in conflicts)
        )

    def test_conflict_fatal_when_strict(self) -> None:
        self.edit("l9-ci-core", lambda d: d["merge"].update(allow_merge_commit=True))
        self.assert_refused("policies/repo-settings.yml says false", strict=True)

    def test_unknown_merge_value_is_not_a_conflict(self) -> None:
        self.edit(
            "l9-ci-core",
            lambda d: d["merge"].update(
                allow_merge_commit="UNKNOWN", allow_rebase_merge="UNKNOWN"
            ),
        )
        _, conflicts = vs.validate(self.root)
        self.assertFalse(any("l9-ci-core.yml" in c for c in conflicts))


if __name__ == "__main__":
    unittest.main()
