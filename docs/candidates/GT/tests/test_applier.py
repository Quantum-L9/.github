"""Applier behaviour on a synthetic SV-applied target (structure only, not the canonical repo)."""

import hashlib
import inspect
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import GOVERNING, ROOT, git, init_repo, synthetic_sv_applied

import apply_to_pinned_checkout as applier


class CoreStageOnSyntheticTarget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = synthetic_sv_applied(Path(self.tmp.name) / "repo")

    def tearDown(self):
        self.tmp.cleanup()

    def test_core_assembles_gt_on_top_of_sv(self):
        changed, count, rebound, resolved = applier.generate_core(self.root)
        self.assertEqual(count, 13)
        inv = yaml.safe_load(changed["semantics/invariants.yaml"])["invariants"]
        self.assertEqual([r["id"] for r in inv].count("L9-GT-001"), 1)
        contracts = yaml.safe_load(changed["semantics/contracts.yaml"])
        ids = [c["id"] for c in contracts["contracts"]]
        self.assertIn(applier.GT_CORE_CONTRACT_ID, ids)
        self.assertIn(applier.SV_CONTRACT_ID, ids)
        self.assertNotIn(applier.GT_DEPENDENT_CONTRACT_ID, ids)
        digest = hashlib.sha256(
            changed["semantics/invariants.yaml"].encode()
        ).hexdigest()
        self.assertEqual(contracts["derivation"]["source_digest_sha256"], digest)
        self.assertEqual(contracts["derivation"]["source_invariant_count"], 13)
        self.assertEqual(
            rebound, {"semantics/lifecycle.yaml": ["invariants.yaml", "contracts.yaml"]}
        )
        lifecycle = yaml.safe_load(changed["semantics/lifecycle.yaml"])["derivation"]
        by_name = {e["artifact"]: e for e in lifecycle["source_artifacts"]}
        self.assertEqual(by_name["invariants.yaml"]["sha256"], digest)
        self.assertEqual(by_name["contracts.yaml"]["item_count"], 3)
        self.assertEqual(
            resolved,
            {
                applier.GT_OUTPUT: "strategic_interaction_projection.schema.yaml",
                applier.GT_COMPOSED_OUTPUT: "strategic_interaction_composition.schema.yaml",
            },
        )
        pdoc = yaml.safe_load(changed["semantics/projection_profiles.yaml"])
        self.assertIn(
            applier.GT_FORBIDDEN, pdoc["forbidden_constraints"]["definitions"]
        )
        self.assertEqual(list(pdoc)[-1], "validation_rules")
        manifest = yaml.safe_load(changed["semantics/generic_compiler_manifest.yaml"])
        self.assertEqual(
            manifest["requires"]["artifact_schemas"][-3:],
            [
                "strategic_planner_value_composition.schema.yaml",
                "strategic_interaction_projection.schema.yaml",
                "strategic_interaction_composition.schema.yaml",
            ],
        )
        self.assertEqual(len(changed), 9)

    def test_old_eight_invariant_sv_assumption_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_sv_applied(
                Path(tmp) / "repo",
                sv_invariants=[
                    f"L9-SV-{n:03d}" for n in (1, 2, 15, 16, 17, 18, 19, 20)
                ],
            )
            with self.assertRaisesRegex(ValueError, "SV invariants must be exactly"):
                applier.generate_core(root)

    def test_missing_sv_application_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_sv_applied(Path(tmp) / "repo", sv_invariants=())
            with self.assertRaises(ValueError):
                applier.generate_core(root)

    def test_stale_contract_derivation_fails_closed(self):
        path = self.root / "semantics/contracts.yaml"
        text = path.read_text()
        path.write_text(
            text.replace("source_invariant_count: 12", "source_invariant_count: 11")
        )
        with self.assertRaisesRegex(ValueError, "contracts derivation count"):
            applier.generate_core(self.root)

    def test_stale_derived_ledger_fails_closed(self):
        path = self.root / "semantics/lifecycle.yaml"
        lines = path.read_text().split("\n")
        lines[4] = "    sha256: " + "0" * 64
        path.write_text("\n".join(lines))
        with self.assertRaisesRegex(ValueError, "stale derivation digest"):
            applier.generate_core(self.root)

    def test_canonical_collision_and_existing_schema_fail_closed(self):
        (
            self.root / "semantics/strategic_interaction_projection.schema.yaml"
        ).write_text("x: 1\n")
        with self.assertRaisesRegex(ValueError, "already exists"):
            applier.generate_core(self.root)

    def test_duplicate_ids_inside_overlay_are_rejected(self):
        base = "schema: s\ninvariants:\n- id: A\n"
        extra = "invariants:\n- id: B\n- id: B\n"
        with self.assertRaisesRegex(ValueError, "duplicate IDs"):
            applier.merge_list(base, extra, "invariants")

    def test_gt_term_colliding_with_canonical_is_rejected(self):
        path = self.root / "semantics/vocabulary.yaml"
        path.write_text(
            path.read_text().replace(
                "relationships:",
                "  deviation_gain:\n    semantic_class: x\n    definition: y\nrelationships:",
            )
        )
        with self.assertRaisesRegex(ValueError, "term collision"):
            applier.generate_core(self.root)

    def _verify_with(self, mutate):
        changed, *_ = applier.generate_core(self.root)
        before = dict(changed)
        mutate(changed)
        self.assertNotEqual(before, changed, "mutation did not apply")
        return applier.verify_assembled(self.root, changed)

    def test_assembled_rejects_missing_or_extra_governing_selection(self):
        sel = '$.invariants[?(@.id=="L9-ASSURANCE-001")]'

        def drop(changed):
            changed["semantics/projection_profiles.yaml"] = changed[
                "semantics/projection_profiles.yaml"
            ].replace(f"      - {sel}\n", "", 1)

        def dup(changed):
            changed["semantics/projection_profiles.yaml"] = changed[
                "semantics/projection_profiles.yaml"
            ].replace(f"      - {sel}\n", f"      - {sel}\n      - {sel}\n", 1)

        def extra(changed):
            changed["semantics/projection_profiles.yaml"] = changed[
                "semantics/projection_profiles.yaml"
            ].replace(
                f"      - {sel}\n",
                f'      - {sel}\n      - $.invariants[?(@.id=="L9-SV-001")]\n',
                1,
            )

        for mutate in (drop, dup, extra):
            with (
                self.subTest(mutate=mutate.__name__),
                self.assertRaisesRegex(
                    ValueError, "GT invariant selection must equal the core contract"
                ),
            ):
                self._verify_with(mutate)

    def test_assembled_rejects_unregistered_forbidden_token(self):
        def revert(changed):
            changed["semantics/projection_profiles.yaml"] = changed[
                "semantics/projection_profiles.yaml"
            ].replace(
                "  forbidden:\n  - " + applier.GT_FORBIDDEN + "\n",
                "  forbidden:\n  - projection_ranking_or_executing\n",
                1,
            )

        with self.assertRaisesRegex(ValueError, "forbidden token"):
            self._verify_with(revert)

    def test_assembled_rejects_missing_schema_discriminator(self):
        def strip(changed):
            key = "semantics/strategic_interaction_projection.schema.yaml"
            changed[key] = changed[key].replace(
                "  schema:\n    const: l9.projection.strategic-planner-interaction/v1\n",
                "",
            )

        with self.assertRaisesRegex(ValueError, "must resolve to exactly one schema"):
            self._verify_with(strip)

    def test_assembled_rejects_dependent_contract_in_core(self):
        def add(changed):
            changed["semantics/contracts.yaml"] += (
                f"- id: {applier.GT_DEPENDENT_CONTRACT_ID}\n  purpose: x\n"
            )

        with self.assertRaisesRegex(ValueError, "dependent contract"):
            self._verify_with(add)


class TargetPinning(unittest.TestCase):
    """verify_admitted_sv_target binds a clean HEAD on the admitted SV tree."""

    MODEL = "semantics/strategic_value_model.yaml"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "semantics").mkdir(parents=True)
        (self.root / "semantics/a.yaml").write_text("a: 1\n")
        (self.root / self.MODEL).write_text("artifact_id: l9.strategic.value@1\n")
        self.head = init_repo(self.root)
        self.tree = git(self.root, "rev-parse", "HEAD:semantics").strip()
        self.pins = {
            self.MODEL: hashlib.sha256(
                (self.root / self.MODEL).read_bytes()
            ).hexdigest()
        }

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, head=None, tree=None, pins=None):
        with (
            mock.patch.object(applier, "CANONICAL_TARGET", head or self.head),
            mock.patch.object(applier, "CANONICAL_TREE", tree or self.tree),
            mock.patch.object(applier, "SV_OWNED_SHA256", pins or self.pins),
        ):
            applier.verify_admitted_sv_target(self.root)

    def test_clean_admitted_target_passes(self):
        self.check()

    def test_wrong_head_fails(self):
        with self.assertRaisesRegex(ValueError, "wrong target HEAD"):
            self.check(head="0" * 40)

    def test_dirty_target_fails(self):
        (self.root / "semantics/extra.yaml").write_text("e: 1\n")
        with self.assertRaisesRegex(ValueError, "not clean"):
            self.check()

    def test_modified_tracked_file_fails(self):
        (self.root / "semantics/a.yaml").write_text("a: 2\n")
        with self.assertRaisesRegex(ValueError, "not clean"):
            self.check()

    def test_wrong_semantics_tree_fails(self):
        with self.assertRaisesRegex(ValueError, "admitted SV foundation tree"):
            self.check(tree="0" * 40)

    def test_sv_owned_digest_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "admitted SV pin"):
            self.check(pins={self.MODEL: "0" * 64})

    def test_binding_pins_the_admitted_sv_foundation(self):
        binding = applier.BINDING
        self.assertEqual(binding["schema"], "l9.gt.sv-alignment-binding/v3")
        self.assertEqual(
            applier.CANONICAL_TARGET, "c9bbfaf61bd0f7444b1a617876a031c2fba75406"
        )
        self.assertEqual(
            applier.CANONICAL_TREE, "251bb3d9238f93f0207b1f8443c80359e034595b"
        )
        admitted = binding["sv_admitted"]
        self.assertEqual(admitted["release"], "v3.32.0")
        self.assertEqual(admitted["admission_pr"], 222)
        self.assertEqual(
            admitted["admission_merge_commit"],
            "64d8b8598300f94c3201f26866f73be6895dab60",
        )
        self.assertEqual(admitted["admitted_semantics_tree"], applier.CANONICAL_TREE)
        self.assertEqual(len(applier.SV_OWNED_SHA256), 3)
        self.assertEqual(binding["sv_authority_status"], "admitted_v3.32.0")
        old = binding["superseded_bindings"][0]
        self.assertEqual(
            old["canonical_target"], "020a94bea86e7c5c5e4107da7014ec259508f397"
        )
        self.assertEqual(
            old["sv_candidate"]["head"], "a64d05a152b5920dad577cead26618a6f05fef09"
        )


class DependentStage(unittest.TestCase):
    def test_refuses_without_admitted_foundation(self):
        self.assertIsNone(applier.ADMITTED_FOUNDATION_REVISION)
        with tempfile.TemporaryDirectory() as tmp:
            rc = applier.main(["--checkout", tmp, "--stage", "dependent"])
        self.assertEqual(rc, 2)

    def test_no_flag_bypasses_the_admission_check(self):
        source = inspect.getsource(applier)
        self.assertNotIn("--include-dependent", source)
        self.assertNotIn("--admitted-revision", source)
        self.assertNotIn("--expected-sha", source)
        core = inspect.getsource(applier.generate_core)
        self.assertNotIn("contracts_sv_dependent", core)
        self.assertIn(
            "contracts_sv_dependent", inspect.getsource(applier.generate_dependent)
        )

    def _admitted_foundation(self, tmp):
        root = synthetic_sv_applied(Path(tmp) / "repo")
        changed, *_ = applier.generate_core(root)
        for rel, text in changed.items():
            (root / rel).write_text(text)
        return root, init_repo(root)

    def test_applies_against_recorded_admitted_foundation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, head = self._admitted_foundation(tmp)
            with mock.patch.object(applier, "ADMITTED_FOUNDATION_REVISION", head):
                changed, _, rebound, _ = applier.generate_dependent(root)
            ids = [
                c["id"]
                for c in yaml.safe_load(changed["semantics/contracts.yaml"])[
                    "contracts"
                ]
            ]
            self.assertEqual(ids.count(applier.GT_DEPENDENT_CONTRACT_ID), 1)
            self.assertIn("semantics/lifecycle.yaml", rebound)

    def test_refuses_other_revision_or_dirty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, head = self._admitted_foundation(tmp)
            with (
                mock.patch.object(applier, "ADMITTED_FOUNDATION_REVISION", "1" * 40),
                self.assertRaisesRegex(ValueError, "admitted foundation"),
            ):
                applier.generate_dependent(root)
            (root / "semantics/x.yaml").write_text("x: 1\n")
            with (
                mock.patch.object(applier, "ADMITTED_FOUNDATION_REVISION", head),
                self.assertRaisesRegex(ValueError, "not clean"),
            ):
                applier.generate_dependent(root)

    def test_refuses_incomplete_release_a_foundation(self):
        cases = {
            "composition profile missing": (
                "semantics/composition_profiles.yaml",
                "l9.compose/strategic-planner-interaction@1",
                "l9.compose/other@1",
            ),
            "forbidden criterion missing": (
                "semantics/projection_profiles.yaml",
                "    sv_semantic_records_excluded_from_gt_projection:\n",
                "    renamed_criterion:\n",
            ),
            "schema registration missing": (
                "semantics/generic_compiler_manifest.yaml",
                "  - strategic_interaction_composition.schema.yaml\n",
                "",
            ),
        }
        for label, (rel, old, new) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                root = synthetic_sv_applied(Path(tmp) / "repo")
                changed, *_ = applier.generate_core(root)
                self.assertEqual(changed[rel].count(old), 1)
                changed[rel] = changed[rel].replace(old, new)
                for path, text in changed.items():
                    (root / path).write_text(text)
                head = init_repo(root)
                with (
                    mock.patch.object(applier, "ADMITTED_FOUNDATION_REVISION", head),
                    self.assertRaisesRegex(ValueError, "not the complete release A"),
                ):
                    applier.generate_dependent(root)

    def test_refuses_foundation_without_gt_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_sv_applied(Path(tmp) / "repo")
            head = init_repo(root)
            with (
                mock.patch.object(applier, "ADMITTED_FOUNDATION_REVISION", head),
                self.assertRaisesRegex(ValueError, "GT core is not present"),
            ):
                applier.generate_dependent(root)


class ApplyGuards(unittest.TestCase):
    @staticmethod
    def _repo(tmp):
        root = Path(tmp) / "repo"
        (root / "semantics").mkdir(parents=True)
        (root / "semantics/a.yaml").write_text("a: 1\n")
        (root / "semantics/b.yaml").write_text("b: 1\n")
        init_repo(root)
        return root

    def _main_with(self, root, *flags):
        proposed = {"semantics/a.yaml": "a: 2\n", "semantics/b.yaml": "b: 2\n"}
        with (
            mock.patch.object(applier, "verify_admitted_sv_target", return_value=None),
            mock.patch.object(
                applier, "generate_core", return_value=(proposed, 0, {}, {})
            ),
        ):
            return applier.main(["--checkout", str(root), "--apply", *flags])

    def test_apply_requires_disposable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            # Verification is stubbed so the guard itself is what is exercised.
            self.assertEqual(self._main_with(root), 2)
            self.assertEqual((root / "semantics/a.yaml").read_text(), "a: 1\n")
            self.assertEqual(self._main_with(root, "--disposable"), 0)
            self.assertEqual((root / "semantics/a.yaml").read_text(), "a: 2\n")
            self.assertEqual(list(root.rglob("*.gt-staged")), [])

    def test_refuses_the_checkout_that_carries_the_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            pack = root / "docs" / "candidates" / "GT"
            pack.mkdir(parents=True)
            with (
                mock.patch.object(applier, "ROOT", pack),
                self.assertRaisesRegex(ValueError, "refusing --apply"),
            ):
                applier.write_staged(root, {"x": "y"})
            self.assertFalse((root / "x").exists())

    def test_failed_rename_rolls_back_every_replaced_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            real_replace = applier.os.replace
            calls = []

            def flaky(src, dst):
                calls.append(dst)
                if len(calls) == 2:
                    raise OSError("simulated rename failure")
                return real_replace(src, dst)

            proposed = {"semantics/a.yaml": "a: 2\n", "semantics/new.yaml": "n: 1\n"}
            with (
                mock.patch.object(applier.os, "replace", side_effect=flaky),
                self.assertRaisesRegex(OSError, "simulated rename failure"),
            ):
                applier.write_staged(root, proposed)
            self.assertEqual((root / "semantics/a.yaml").read_text(), "a: 1\n")
            self.assertFalse((root / "semantics/new.yaml").exists())
            self.assertEqual(list(root.rglob("*.gt-staged")), [])

    def test_script_never_publishes(self):
        text = (ROOT / "apply_to_pinned_checkout.py").read_text()
        for forbidden in ("git push", "gh pr create", "commit", "--force"):
            if forbidden == "commit":
                self.assertNotIn('"commit"', text)
                continue
            self.assertNotIn(forbidden, text)

    def test_governing_set_matches_core_contract(self):
        core = yaml.safe_load((ROOT / "overlays/contracts_gt_core.yaml").read_text())[
            "contracts"
        ][0]
        self.assertEqual(list(applier.GT_GOVERNING), core["source_invariants"])
        self.assertEqual(list(applier.GT_GOVERNING), GOVERNING)


if __name__ == "__main__":
    unittest.main()
