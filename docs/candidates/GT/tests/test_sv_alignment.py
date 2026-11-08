"""Cross-pack alignment with the admitted SV foundation (v3.32.0, ADR-029) and its evidence."""

import sys
import tarfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import EVIDENCE, GOVERNING, ROOT, read


class AdmittedSvBinding(unittest.TestCase):
    def setUp(self):
        self.b = read("evidence/sv_alignment_binding.json")

    def test_exact_admitted_coordinates(self):
        admitted = self.b["sv_admitted"]
        self.assertEqual(admitted["release"], "v3.32.0")
        self.assertEqual(admitted["admission_pr"], 222)
        self.assertEqual(
            admitted["admission_merge_commit"],
            "64d8b8598300f94c3201f26866f73be6895dab60",
        )
        self.assertTrue(admitted["adr"].startswith("docs/adr/ADR-029-"))
        self.assertEqual(
            self.b["canonical_target"], "c9bbfaf61bd0f7444b1a617876a031c2fba75406"
        )
        self.assertEqual(
            self.b["canonical_target_semantics_tree"],
            admitted["admitted_semantics_tree"],
        )
        for value in (
            self.b["canonical_target"],
            self.b["canonical_target_semantics_tree"],
            admitted["admission_merge_commit"],
            admitted["compiler_pinned_by_admission"],
        ):
            self.assertRegex(value, r"^[0-9a-f]{40}$")
        self.assertIn("D1", admitted["owner_decisions"])
        self.assertIn("verbatim", admitted["owner_decisions"]["D1"])

    def test_reduced_sv_law_and_terms(self):
        self.assertEqual(set(self.b["sv_new_invariants"]), {"L9-SV-001", "L9-SV-002"})
        self.assertEqual(
            self.b["sv_lineage_only_ids"], [f"L9-SV-{n:03d}" for n in range(15, 21)]
        )
        self.assertFalse(
            set(self.b["sv_lineage_only_ids"]) & set(self.b["sv_governing_invariants"])
        )
        self.assertEqual(len(self.b["sv_governing_invariants"]), 12)
        self.assertEqual(len(self.b["sv_vocabulary_terms"]), 11)
        self.assertEqual(
            self.b["sv_source_classes"],
            [
                "strategic_value_model",
                "vocabulary",
                "invariants",
                "contracts",
                "authority_model",
            ],
        )
        self.assertEqual(self.b["sv_model"], "l9.strategic.value@1")
        self.assertEqual(
            self.b["sv_contract"], "l9.contract/strategic-value-assessment@1"
        )
        self.assertEqual(
            self.b["sv_projection"], "l9.projection/strategic-planner-value@1"
        )
        self.assertEqual(
            self.b["sv_composition"], "l9.compose/strategic-planner-value@1"
        )

    def test_old_eight_invariant_binding_is_gone(self):
        self.assertFalse((ROOT / "evidence/pr212_alignment_binding.json").exists())
        self.assertNotIn("sv_invariants_proposed", self.b)

    def test_authority_status_and_stage_b_closed(self):
        self.assertEqual(self.b["sv_authority_status"], "admitted_v3.32.0")
        self.assertEqual(self.b["gt_authority_status"], "candidate_not_admitted")
        self.assertIsNone(self.b["admitted_foundation_revision"])

    def test_pinned_admitted_sv_files_and_superseded_candidate_record(self):
        owned = self.b["sv_admitted"]["sv_owned_files_sha256"]
        self.assertEqual(
            set(owned),
            {
                "semantics/strategic_value_model.yaml",
                "semantics/strategic_planner_value_projection.schema.yaml",
                "semantics/strategic_planner_value_composition.schema.yaml",
            },
        )
        self.assertTrue(all(len(v) == 64 for v in owned.values()))
        old = self.b["superseded_bindings"][0]
        self.assertEqual(old["sv_candidate"]["pr"], 215)
        self.assertEqual(len(old["sv_candidate"]["pack_blobs"]), 10)
        self.assertEqual(len(old["sv_applied_target_sha256"]), 13)
        # The admitted SV-owned files are byte-identical to the #215 candidate's.
        for rel, digest in owned.items():
            self.assertEqual(old["sv_applied_target_sha256"][rel], digest, rel)

    def test_gt_terms_and_invariants_disjoint_from_sv(self):
        gt_terms = read("overlays/vocabulary_additions.yaml")["terms"]
        self.assertFalse(set(gt_terms) & set(self.b["sv_vocabulary_terms"]))
        self.assertNotIn("strategic_commitment", gt_terms)
        self.assertIn("incentive_bearing_commitment", gt_terms)
        gt_inv = {
            x["id"] for x in read("overlays/invariants_additions.yaml")["invariants"]
        }
        self.assertEqual(gt_inv, {"L9-GT-001"})


class IntegratedQualificationEvidence(unittest.TestCase):
    def setUp(self):
        self.summary = read("evidence/integration-v2/qualification-summary.json")
        self.rehearsal = read("evidence/integration-v2/rehearsal.json")
        self.binding = read("evidence/sv_alignment_binding.json")

    def test_rehearsal_is_gt_core_on_the_admitted_foundation(self):
        self.assertEqual(
            self.rehearsal["canonical_target"], self.binding["canonical_target"]
        )
        self.assertEqual(
            self.rehearsal["canonical_target_semantics_tree"],
            self.binding["canonical_target_semantics_tree"],
        )
        self.assertEqual(
            self.rehearsal["sv_admitted"]["admission_merge_commit"],
            self.binding["sv_admitted"]["admission_merge_commit"],
        )
        self.assertFalse(self.rehearsal["rehearsal_commit_pushed"])
        changed = self.rehearsal["changed_canonical_paths_vs_target"]
        # GT core only: eleven files, and no admitted SV-owned file is touched.
        self.assertEqual(len(changed), 11)
        self.assertFalse(
            set(changed) & set(self.binding["sv_admitted"]["sv_owned_files_sha256"])
        )
        for name in (
            "strategic_interaction_projection",
            "strategic_interaction_composition",
        ):
            self.assertIn(f"semantics/{name}.schema.yaml", changed)

    def test_real_producer_three_plus_one_gt_and_five_plus_one_sv(self):
        run = self.summary["run1"]
        gt = [k for k in run if k.startswith("gt:")]
        sv = [k for k in run if k.startswith("sv:")]
        self.assertEqual(len(gt), 4)
        self.assertEqual(len(sv), 6)
        for key in gt + sv:
            self.assertEqual(
                (run[key]["exit_code"], run[key]["result"]), (0, "pass"), key
            )
            self.assertFalse(run[key]["artifacts"][0]["unresolved_criteria"], key)
        self.assertEqual(run["gt:compose"]["component_count"], 3)
        self.assertEqual(run["sv:compose"]["component_count"], 5)
        self.assertTrue(self.summary["run2_equal_results"])
        self.assertTrue(self.summary["byte_identical_outputs"])
        self.assertEqual(
            self.summary["authority_revision"], self.rehearsal["rehearsal_commit"]
        )
        self.assertEqual(
            self.summary["compiler_revision"], self.rehearsal["compiler_revision"]
        )

    def test_qualification_acceptance_policy(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import copy

        from run_integrated_qualification import acceptance

        run = self.summary["run1"]
        self.assertEqual(self.summary["acceptance_failures"], [])
        self.assertEqual(acceptance(run), [])
        broken = copy.deepcopy(run)
        broken["gt:invariants"].update(exit_code=2, status="failed", result=None)
        self.assertTrue(acceptance(broken))
        gt_unknown = copy.deepcopy(run)
        gt_unknown["gt:compose"].update(exit_code=3, result="unknown")
        self.assertTrue(acceptance(gt_unknown))
        sv_extra = copy.deepcopy(run)
        sv_extra["sv:compose"]["artifacts"][0]["unresolved_criteria"].append(
            "declared_constraint:other"
        )
        self.assertTrue(acceptance(sv_extra))
        # The pre-admission SV deviation (unknown on required_provenance) is gone.
        sv_unknown = copy.deepcopy(run)
        sv_unknown["sv:compose"].update(exit_code=3, result="unknown")
        self.assertTrue(acceptance(sv_unknown))
        missing = {k: v for k, v in run.items() if k != "gt:contracts"}
        self.assertTrue(acceptance(missing))

    def test_archived_outputs_match_recorded_digests(self):
        import hashlib

        for run in ("run1", "run2"):
            with tarfile.open(EVIDENCE / f"projection-{run}.tar") as tar:
                for rel, digest in self.summary["run1_output_digests"].items():
                    data = tar.extractfile("./" + rel).read()
                    self.assertEqual(
                        hashlib.sha256(data).hexdigest(), digest, f"{run}:{rel}"
                    )

    def test_producer_negative_controls_all_matched(self):
        controls = read("evidence/integration-v2/producer-negative-controls.json")
        self.assertTrue(controls["all_matched"])
        self.assertEqual(controls["count"], 19)
        self.assertEqual(
            controls["authority_revision"], self.rehearsal["rehearsal_commit"]
        )
        names = {c["control"] for c in controls["controls"]}
        for required in (
            "profile_selects_sv_invariant_with_schema_widened",
            "profile_selects_sv_contract_with_schema_widened",
            "profile_selects_sv_vocabulary_term",
            "profile_reverts_to_unregistered_forbidden_tokens",
            "profile_drops_one_governing_invariant",
            "projection_schema_discriminator_removed",
            "composition_missing_namespace",
            "composition_duplicate_source",
        ):
            self.assertIn(required, names)

    def test_native_validator_fails_only_release_inventory(self):
        log = (EVIDENCE / "native-semantic-validation.log").read_text().splitlines()
        fails = [line.split()[1] for line in log if line.startswith("FAIL")]
        self.assertEqual(set(fails), {"SC-008", "semantic-foundation"})
        self.assertIn(
            "SC-010", next(line for line in log if line.startswith("FAIL semantic"))
        )
        self.assertGreaterEqual(sum(line.startswith("PASS") for line in log), 56)

    def test_forbidden_criterion_evaluated_by_producer(self):
        import json

        with tarfile.open(EVIDENCE / "projection-run1.tar") as tar:
            receipts = [
                json.load(tar.extractfile(m))
                for m in tar.getmembers()
                if m.name.startswith("./receipts/") and m.isfile()
            ]
        key = "declared_constraint:forbidden:sv_semantic_records_excluded_from_gt_projection"
        seen = {}
        for receipt in receipts:
            if (
                receipt["operation"] != "projection"
                or "interaction" not in receipt["exact_subject_ref"]
            ):
                continue
            crit = receipt["verification_basis"]["criteria"][key]
            seen[receipt["exact_subject_ref"].split("#")[1]] = (
                crit["status"],
                crit["applicable_selections"],
            )
        self.assertEqual(
            seen,
            {
                "l9.source/vocabulary@1": ("pass", 11),
                "l9.source/invariants@1": ("pass", 2),
                "l9.source/contracts@1": ("pass", 1),
            },
        )

    def test_producer_invariant_selection_is_the_governing_six(self):
        from fixtures import gt_payload

        self.assertEqual(
            sorted(r["id"] for r in gt_payload("invariants")["invariants"]),
            sorted(GOVERNING),
        )


class PackInventory(unittest.TestCase):
    def test_manifest_checksums_and_revision_are_current(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import refresh_pack_inventory

        self.assertEqual(refresh_pack_inventory.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
