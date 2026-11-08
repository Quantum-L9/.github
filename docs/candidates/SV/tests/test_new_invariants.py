"""Two proposed Strategic Value invariants; six former candidates relocated."""

import unittest
from pathlib import Path

import yaml
from reduction_closure import expected

BASE = Path(__file__).resolve().parents[1]
RELOCATED = {f"L9-SV-{i:03d}" for i in range(15, 21)}


class NewInvariantClosure(unittest.TestCase):
    def setUp(self):
        self.inv = yaml.safe_load(
            (BASE / "overlays/invariants_additions.yaml").read_text()
        )["invariants"]
        self.model = yaml.safe_load(
            (BASE / "semantics/strategic_value_model.yaml").read_text()
        )
        self.contract = yaml.safe_load(
            (BASE / "overlays/contracts_additions.yaml").read_text()
        )["contracts"][0]
        self.profile = yaml.safe_load(
            (BASE / "overlays/projection_profile_additions.yaml").read_text()
        )["projection_profiles"][0]

    def test_exactly_two_new_invariant_identities_are_unique_and_grounded(self):
        ids = [x["id"] for x in self.inv]
        self.assertEqual(ids, ["L9-SV-001", "L9-SV-002"])
        self.assertEqual(set(ids), expected()["new_ids"])
        self.assertTrue(
            all(
                x["owner"] == "Quantum-L9/.github" and x["scope"] == "global"
                for x in self.inv
            )
        )
        self.assertFalse(RELOCATED & set(ids))

    def test_new_laws_and_reused_global_laws_referenced_by_model_contract_and_profile(
        self,
    ):
        governing = expected()["selected_ids"]
        for i in governing:
            self.assertIn(i, self.model["governed_by"]["invariants"])
            self.assertIn(i, self.contract["source_invariants"])
            self.assertIn(
                f'$.invariants[?(@.id=="{i}")]',
                self.profile["sources"]["invariants"]["selectors"],
            )
        for i in RELOCATED:
            self.assertNotIn(i, self.model["governed_by"]["invariants"])
            self.assertNotIn(i, self.contract["source_invariants"])
            self.assertIn(i, self.model["relocated_additional_candidate_semantics"])
        self.assertIn(
            "$.evaluation_integrity",
            self.profile["sources"]["strategic_value_model"]["selectors"],
        )
        self.assertEqual(len(self.model["evaluation_integrity"]), 6)
        self.assertEqual(len(set(self.contract["source_invariants"])), 12)

    def test_activation_remains_unadmitted_and_reviewable(self):
        content = (BASE / "README.md").read_text().lower()
        self.assertIn("not canonically admitted", content)
        self.assertIn("native", content)
        self.assertNotIn("status: admitted", content)


if __name__ == "__main__":
    unittest.main()
