"""Independent direct execution of each adversarial witness + positive control."""

import copy
import json
import unittest
from pathlib import Path

from reduction_closure import expected, load_sources
from run_strategic_value_falsifiers import diagnose, run

R = Path(__file__).resolve().parent
CASE_SET = json.loads((R / "falsification_cases.json").read_text())
CASES = {x["case_id"]: x for x in CASE_SET["cases"]}


class IndependentlyExecutableFalsifiers(unittest.TestCase):
    def check(self, case):
        rec = CASES[case]
        self.assertEqual(
            diagnose(case, copy.deepcopy(rec["negative"])), rec["expected_failure"]
        )
        self.assertEqual(
            diagnose(case, copy.deepcopy(rec["positive"])), "DECLARATION_NOT_FALSIFIED"
        )
        self.assertEqual(run(CASE_SET, case)["result"], "PASS")

    def test_sv015_confounded_baseline(self):
        self.check("SV015")

    def test_sv016_cross_actor_double_credit(self):
        self.check("SV016")

    def test_sv017_hindsight_policy(self):
        self.check("SV017")

    def test_sv018_portfolio_cannibalization(self):
        self.check("SV018")

    def test_sv019_sensitivity_preference_flip(self):
        self.check("SV019")

    def test_sv020_false_numerical_assurance(self):
        self.check("SV020")

    def test_all_six_witnesses_have_distinct_rule_identity_and_positive_controls(self):
        self.assertEqual(set(CASES), {f"SV{x:03d}" for x in range(15, 21)})
        self.assertEqual(len({x["expected_failure"] for x in CASES.values()}), 6)
        self.assertEqual(run(CASE_SET)["result"], "PASS")

    def test_receipts_carry_lineage_not_canonical_invariant_claims(self):
        exp = expected()
        model = load_sources()["model"]["relocated_additional_candidate_semantics"]
        result = run(CASE_SET)
        self.assertEqual(
            result["assurance"],
            "LOCAL_CONTRACT_FALSIFICATION_ONLY_NOT_NUMERICAL_VALIDATION",
        )
        for receipt in result["cases"]:
            self.assertNotIn("source_invariant", receipt)
            origin = receipt["origin_candidate_id"]
            row = exp["relocated"][origin]
            self.assertEqual(row["falsifier_case_ref"], receipt["case_id"])
            self.assertEqual(receipt["disposition"], row["disposition"])
            self.assertEqual(
                receipt["governing_invariants"], model[origin]["governing_invariants"]
            )
            self.assertEqual(
                receipt["contract_obligation"], model[origin]["contract_obligation"]
            )
            self.assertEqual(
                receipt["negative_result"], row["expected_negative_result"]
            )
            self.assertLessEqual(
                set(receipt["governing_invariants"]), exp["selected_ids"]
            )
            self.assertNotIn(origin, exp["selected_ids"])

    def test_mutated_invalid_case_is_detectable(self):
        altered = copy.deepcopy(CASE_SET)
        altered["cases"][0]["negative"] = altered["cases"][0]["positive"]
        self.assertEqual(run(altered)["result"], "FAIL")


if __name__ == "__main__":
    unittest.main()
