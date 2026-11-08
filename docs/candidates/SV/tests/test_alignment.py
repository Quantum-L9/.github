"""Cross-source closure checks for the *candidate*, not canonical admission."""

import unittest
from pathlib import Path

import yaml
from reduction_closure import expected

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8"))


class AlignmentClosure(unittest.TestCase):
    def setUp(self):
        self.model = read("semantics/strategic_value_model.yaml")
        self.inv = read("overlays/invariants_additions.yaml")["invariants"]
        self.contract = read("overlays/contracts_additions.yaml")["contracts"][0]
        self.vocab = read("overlays/vocabulary_additions.yaml")["terms"]
        self.catalog = read("overlays/projection_profile_additions.yaml")
        self.profile = self.catalog["projection_profiles"][0]

    def test_two_new_invariants_and_twelve_governing_ids_close_over_model_contract_and_profile(
        self,
    ):
        exp = expected()
        ids = {row["id"] for row in self.inv}
        self.assertEqual(ids, exp["new_ids"])
        self.assertEqual(len(ids), 2)
        governing = exp["selected_ids"]
        self.assertEqual(len(governing), 12)
        self.assertEqual(set(self.contract["source_invariants"]), governing)
        self.assertEqual(set(self.model["governed_by"]["invariants"]), governing)
        selects = self.profile["sources"]["invariants"]["selectors"]
        self.assertEqual(len(selects), 12)
        self.assertEqual(
            set(selects), {f'$.invariants[?(@.id=="{i}")]' for i in governing}
        )

    def test_all_11_new_vocabulary_terms_are_projected(self):
        self.assertEqual(len(self.vocab), 11)
        selects = set(self.profile["sources"]["vocabulary"]["selectors"])
        self.assertEqual({f"$.terms.{term}" for term in self.vocab}, selects)

    def test_model_semantics_and_profile_are_complete(self):
        self.assertEqual(self.model["artifact_id"], "l9.strategic.value@1")
        self.assertEqual(
            self.model["identity"]["assessment_contract_ref"], self.contract["id"]
        )
        self.assertEqual(self.profile["id"], "l9.projection/strategic-planner-value@1")
        self.assertEqual(self.profile["consumer"], "strategic-planner")
        self.assertEqual(
            set(self.profile["sources"]),
            {
                "strategic_value_model",
                "vocabulary",
                "invariants",
                "contracts",
                "authority_model",
            },
        )
        self.assertEqual(
            self.catalog["source_classes"]["strategic_value_model"][
                "canonical_artifact"
            ],
            "strategic_value_model.yaml",
        )
        selectors = set(self.profile["sources"]["strategic_value_model"]["selectors"])
        self.assertLessEqual(
            {
                "$.authority",
                "$.canonical_source",
                "$.governed_by",
                "$.valuation",
                "$.counterfactual_mathematics",
                "$.strategic_interaction_lookahead",
                "$.evaluation_integrity",
                "$.assessment_claim_levels",
                "$.assessment_applicability",
                "$.retained_former_candidate_semantics",
                "$.relocated_additional_candidate_semantics",
            },
            selectors,
        )
        declared_global = {
            ref
            for ref in self.model["governed_by"]["invariants"]
            if not ref.startswith("L9-SV-")
        }
        self.assertLessEqual(
            {f'$.invariants[?(@.id=="{ref}")]' for ref in declared_global},
            set(self.profile["sources"]["invariants"]["selectors"]),
        )
        for ref in self.model["governed_by"]["contracts"]:
            self.assertIn(
                f'$.contracts[?(@.id=="{ref}")]',
                self.profile["sources"]["contracts"]["selectors"],
            )
        self.assertEqual(
            self.model["counterfactual_mathematics"]["numerical_owner"],
            "Numerical Reasoning",
        )
        self.assertTrue(self.model["comparisons"]["output_is_not_strategic_commitment"])

    def test_no_undeclared_mutation_or_bypass(self):
        script = (ROOT / "apply_to_pinned_checkout.py").read_text()
        self.assertRegex(
            script,
            r"(?m)^BASE_SHA = ['\"]a960d98ac2719fc912f959c1495d33dce068b140['\"]$",
        )
        self.assertNotIn("--expected-sha", script)
        self.assertIn("if actual != BASE_SHA:", script)
        self.assertNotIn("git push", script)
        self.assertRegex(script, r"['\"]--disposable['\"]")


if __name__ == "__main__":
    unittest.main()
