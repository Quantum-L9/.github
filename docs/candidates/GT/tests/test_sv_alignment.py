"""Cross-pack alignment with the reduced SV candidate (PR #215 @ a64d05a) and its evidence."""

import sys
import tarfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import EVIDENCE, GOVERNING, ROOT, read


class ReducedSvBinding(unittest.TestCase):
    def setUp(self):
        self.b = read("evidence/sv_alignment_binding.json")

    def test_exact_successor_coordinates(self):
        self.assertEqual(self.b["sv_candidate"]["pr"], 215)
        self.assertEqual(
            self.b["sv_candidate"]["head"], "a64d05a152b5920dad577cead26618a6f05fef09"
        )
        self.assertEqual(self.b["sv_candidate"]["stacked_on_pr"], 212)
        self.assertEqual(
            self.b["sv_candidate"]["stacked_on_head"],
            "85531616cee2da94bbb7154418a78537549a4d76",
        )
        self.assertEqual(
            self.b["canonical_target"], "020a94bea86e7c5c5e4107da7014ec259508f397"
        )
        for value in (self.b["sv_candidate"]["head"], self.b["canonical_target"]):
            self.assertRegex(value, r"^[0-9a-f]{40}$")
        self.assertNotIn(
            "main", (self.b["sv_candidate"]["head"], self.b["canonical_target"])
        )

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

    def test_authority_status_is_candidate_and_stage_b_closed(self):
        self.assertEqual(self.b["sv_authority_status"], "candidate_not_admitted")
        self.assertEqual(self.b["gt_authority_status"], "candidate_not_admitted")
        self.assertIsNone(self.b["admitted_foundation_revision"])

    def test_pinned_sv_application_and_pack_identities(self):
        self.assertEqual(len(self.b["sv_candidate"]["pack_blobs"]), 10)
        self.assertTrue(
            all(
                p.startswith("docs/candidates/SV/")
                for p in self.b["sv_candidate"]["pack_blobs"]
            )
        )
        applied = self.b["sv_applied_target_sha256"]
        self.assertEqual(len(applied), 13)
        self.assertTrue(all(len(v) == 64 for v in applied.values()))

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
        self.summary = read("evidence/integration-v1/qualification-summary.json")
        self.rehearsal = read("evidence/integration-v1/rehearsal.json")
        self.binding = read("evidence/sv_alignment_binding.json")

    def test_rehearsal_reproduces_pinned_sv_application(self):
        self.assertEqual(
            self.rehearsal["sv_candidate_head"], self.binding["sv_candidate"]["head"]
        )
        self.assertEqual(
            self.rehearsal["canonical_target"], self.binding["canonical_target"]
        )
        self.assertFalse(self.rehearsal["rehearsal_commit_pushed"])
        changed = self.rehearsal["changed_canonical_paths_vs_target"]
        self.assertEqual(len(changed), 15)
        sv_only = set(self.binding["sv_applied_target_sha256"]) - {
            "semantics/" + n
            for n in (
                "invariants.yaml",
                "contracts.yaml",
                "vocabulary.yaml",
                "projection_profiles.yaml",
                "composition_profiles.yaml",
                "generic_compiler_manifest.yaml",
                "capabilities.yaml",
                "lifecycle.yaml",
                "receipt_catalog.yaml",
            )
        }
        for rel in sv_only:
            self.assertEqual(
                changed[rel], self.binding["sv_applied_target_sha256"][rel], rel
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
        for key in gt + [k for k in sv if k != "sv:compose"]:
            self.assertEqual(
                (run[key]["exit_code"], run[key]["result"]), (0, "pass"), key
            )
        self.assertEqual(run["sv:compose"]["result"], "unknown")
        self.assertEqual(
            sorted(run["sv:compose"]["artifacts"][0]["unresolved_criteria"]),
            sorted(
                "declared_constraint:required_provenance:" + x
                for x in (
                    "composition_profile_digest",
                    "composition_profile_ref",
                    "source_projection_digests",
                    "source_projection_refs",
                )
            ),
        )
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
        controls = read("evidence/integration-v1/producer-negative-controls.json")
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
        self.assertGreaterEqual(sum(line.startswith("PASS") for line in log), 54)

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


if __name__ == "__main__":
    unittest.main()
