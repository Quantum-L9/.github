"""GT <-> SV boundary tests (remediation spec section 7).

The numerical cases are SYNTHETIC reference checks of the candidate contract's
claims, not a GT solver, a Numerical Reasoning implementation, or a receipt.
The consumer-envelope cases run the candidate verifier against the REAL producer
receipts archived in evidence/integration-v1.
"""

import copy
import itertools
import json
import math
import sys
import tarfile
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from fixtures import EVIDENCE, read
from verify_consumer_envelope import verify

BUCKETS = ("IEV", "SFV", "DC", "ERL", "OC")
GT_VIEW = "l9.compose/strategic-planner-interaction@1#l9.projection/strategic-planner-interaction@1"
SV_VIEW = "l9.compose/strategic-planner-value@1#l9.projection/strategic-planner-value@1"


def sv_from_ledger(ledger):
    """SV = IEV + SFV - DC - ERL - OC over exactly the five SV buckets."""
    if set(ledger) != set(BUCKETS):
        raise ValueError(
            f"ledger must use exactly the five SV buckets, got {sorted(ledger)}"
        )
    return ledger["IEV"] + ledger["SFV"] - ledger["DC"] - ledger["ERL"] - ledger["OC"]


def gt_conditioned_sv(paths):
    """One canonical SV over focal-action-conditioned joint response paths."""
    mass = sum(p for p, _ in paths)
    if not math.isclose(mass, 1.0):
        raise ValueError("response probability mass incomplete; remains Unknown")
    return sum(p * sv_from_ledger(ledger) for p, ledger in paths)


def nonanticipative(policy):
    """Each decision may use only observations available at or before its time."""
    return all(
        obs_time <= decision_time for decision_time, uses in policy for obs_time in uses
    )


def max_deviation_gain(payoffs, profile):
    """max_i sup_{a_i'} u_i(a_i', a_-i) - u_i(profile) for mixed 2-player profiles."""
    rows, cols = len(payoffs), len(payoffs[0])
    p, q = profile

    def u(i, pi, qi):
        return sum(
            pi[r] * qi[c] * payoffs[r][c][i] for r in range(rows) for c in range(cols)
        )

    base0, base1 = u(0, p, q), u(1, p, q)
    pure = lambda n, k: [1.0 if j == k else 0.0 for j in range(n)]
    g0 = max(u(0, pure(rows, r), q) for r in range(rows)) - base0
    g1 = max(u(1, p, pure(cols, c)) for c in range(cols)) - base1
    return max(g0, g1)


def certify_epsilon_nash(payoffs, profile, epsilon, *, iterate_converged):
    """Certification rests on the deviation condition, never on convergence alone."""
    del iterate_converged
    return max_deviation_gain(payoffs, profile) <= epsilon


class NoAdditiveGtUplift(unittest.TestCase):
    def setUp(self):
        self.good = {"IEV": 1000.0, "SFV": 300.0, "DC": 200.0, "ERL": 50.0, "OC": 100.0}
        self.bad = {"IEV": 200.0, "SFV": 0.0, "DC": 200.0, "ERL": 150.0, "OC": 100.0}

    def test_response_conditioned_value_is_not_a_sixth_bucket(self):
        with self.assertRaisesRegex(ValueError, "five SV buckets"):
            sv_from_ledger(dict(self.good, GT_UPLIFT=150.0))

    def test_gt_conditioning_reweights_one_canonical_sv(self):
        passive = gt_conditioned_sv([(1.0, self.good)])
        adaptive = gt_conditioned_sv([(0.6, self.good), (0.4, self.bad)])
        self.assertEqual(passive, 950.0)
        self.assertAlmostEqual(adaptive, 0.6 * 950.0 + 0.4 * -250.0)
        self.assertLess(adaptive, passive)
        self.assertNotAlmostEqual(adaptive, passive + adaptive)

    def test_gt_conditioning_may_raise_lower_or_leave_value(self):
        deterred = dict(self.good, ERL=0.0)
        self.assertGreater(
            gt_conditioned_sv([(1.0, deterred)]), gt_conditioned_sv([(1.0, self.good)])
        )
        self.assertEqual(gt_conditioned_sv([(0.5, self.good), (0.5, self.good)]), 950.0)

    def test_incomplete_response_mass_stays_unknown(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            gt_conditioned_sv([(0.6, self.good), (0.2, self.bad)])

    def test_contract_forbids_uplift_and_summing(self):
        forbidden = read("overlays/contracts_sv_dependent.yaml")["contracts"][0][
            "forbidden"
        ]
        self.assertIn(
            "adding_independent_gt_uplift_to_already_counted_sv_effect", forbidden
        )
        self.assertIn(
            "constructing_gt_plus_sv_value_by_summing_standalone_sv_and_gt_uplift",
            forbidden,
        )


class InformationTimingAndDependence(unittest.TestCase):
    def test_earlier_action_conditioned_on_later_observation_is_rejected(self):
        self.assertTrue(nonanticipative([(1, [0]), (2, [0, 1, 2])]))
        self.assertFalse(nonanticipative([(1, [0, 2]), (2, [1])]))

    def test_correlated_responses_are_not_silently_multiplied(self):
        # Two rivals each enter with marginal 0.5; joint entry observed at 0.45.
        joint = {(1, 1): 0.45, (1, 0): 0.05, (0, 1): 0.05, (0, 0): 0.45}
        independent = {k: 0.5 * 0.5 for k in itertools.product((0, 1), repeat=2)}
        loss = {(1, 1): -900.0, (1, 0): -100.0, (0, 1): -100.0, (0, 0): 0.0}
        ev = lambda dist: sum(dist[k] * loss[k] for k in loss)
        self.assertAlmostEqual(sum(joint.values()), 1.0)
        self.assertAlmostEqual(ev(joint), -415.0)
        self.assertAlmostEqual(ev(independent), -275.0)
        self.assertNotAlmostEqual(ev(joint), ev(independent))
        core = read("overlays/contracts_gt_core.yaml")["contracts"][0]
        self.assertIn(
            "focal_action_conditional_response_model_with_joint_dependence_or_explicit_unknown",
            core["requires"],
        )


class EquilibriumAssurance(unittest.TestCase):
    # Prisoner's-dilemma-like 2x2: (row payoff, column payoff)
    PAYOFFS = (((3.0, 3.0), (0.0, 5.0)), ((5.0, 0.0), (1.0, 1.0)))

    def test_stable_iterate_with_profitable_deviation_is_not_certified(self):
        # A damped/logit fixed point that has stopped moving but is not a best response.
        stable = ([0.7, 0.3], [0.7, 0.3])
        gain = max_deviation_gain(self.PAYOFFS, stable)
        self.assertGreater(gain, 0.5)
        self.assertFalse(
            certify_epsilon_nash(self.PAYOFFS, stable, 0.01, iterate_converged=True)
        )

    def test_true_equilibrium_certifies_by_deviation_condition(self):
        nash = ([0.0, 1.0], [0.0, 1.0])
        self.assertEqual(max_deviation_gain(self.PAYOFFS, nash), 0.0)
        self.assertTrue(
            certify_epsilon_nash(self.PAYOFFS, nash, 0.0, iterate_converged=False)
        )

    def test_contract_distinguishes_stability_from_solution_validity(self):
        core = read("overlays/contracts_gt_core.yaml")["contracts"][0]
        self.assertIn(
            "iterative_stability_alone_claimed_as_nash_equilibrium_proof",
            core["forbidden"],
        )
        self.assertIn(
            "claim_specific_diagnostics_must_distinguish_numerical_stability_from_deviation_gain_and_solution_validity",
            core["requires"],
        )


def producer_receipts():
    out = {}
    with tarfile.open(EVIDENCE / "projection-run1.tar") as tar:
        for member in tar.getmembers():
            if member.name.startswith("./receipts/") and member.isfile():
                receipt = json.load(tar.extractfile(member))
                out[receipt["output"]["digest"]] = receipt
    return out


class ConsumerEnvelopeAgainstRealReceipts(unittest.TestCase):
    def setUp(self):
        self.receipts = producer_receipts()
        by_ref = {r["exact_subject_ref"]: d for d, r in self.receipts.items()}
        self.gt = by_ref[GT_VIEW]
        self.sv = by_ref[SV_VIEW]
        self.projection = next(
            d for d, r in self.receipts.items() if r["operation"] == "projection"
        )
        rev = self.receipts[self.gt]["governing_coordinates"]
        self.num = "sha256:" + "e" * 64
        self.acct = "sha256:" + "f" * 64
        self.numerical = {
            "operation": "numerical_evaluation",
            "governing_coordinates": {
                "repository": rev["repository"],
                "revision": rev["revision"],
            },
            "inputs": [{"digest": self.gt}, {"digest": self.sv}],
            "output": {"digest": self.num},
        }
        comparison = {
            "objective_ref": "o",
            "beneficiary_ref": "b",
            "baseline_ref": "base",
            "state_revision_ref": "r",
            "time_basis_ref": "week",
            "horizon_ref": "4w",
            "utility_unit": "USD",
            "compatibility_status": "compatible",
        }
        ref = lambda r, d: {"ref": r, "digest": d}
        self.envelope = {
            "schema": "l9.assessment.gt-sv-composed/v1",
            "status": "evaluated",
            "gt_semantic_view": ref(GT_VIEW, self.gt),
            "sv_semantic_view": ref(SV_VIEW, self.sv),
            "gt_assessment": ref("gt", "sha256:" + "a" * 64),
            "sv_assessment": ref("sv", "sha256:" + "b" * 64),
            "comparison": comparison,
            "numerical_result": ref("num", self.num),
            "sv_accounting_receipt": ref("acct", self.acct),
            "authority_effect": "none",
        }

    def test_real_gt_composition_passes_and_sv_composition_is_unknown(self):
        self.assertEqual(self.receipts[self.gt]["result"], "pass")
        self.assertEqual(self.receipts[self.sv]["result"], "unknown")

    def test_evaluated_envelope_is_refused_while_sv_composition_is_unknown(self):
        receipts = dict(
            self.receipts,
            **{self.num: self.numerical, self.acct: {"output": {"digest": self.acct}}},
        )
        verdict, failures = verify(self.envelope, receipts)
        self.assertEqual(verdict, "refused")
        self.assertEqual(
            failures, ["sv_semantic_view: composition result is 'unknown'"]
        )

    def test_verified_when_both_views_pass_and_numeric_evidence_binds_them(self):
        receipts = copy.deepcopy(self.receipts)
        receipts[self.sv]["result"] = (
            "pass"  # counterfactual: owner resolves required_provenance
        )
        receipts[self.num] = self.numerical
        receipts[self.acct] = {"output": {"digest": self.acct}}
        self.assertEqual(verify(self.envelope, receipts), ("verified", []))

    def test_projection_receipt_cannot_certify_numerical_or_solver_execution(self):
        receipts = dict(self.receipts, **{self.acct: {}})
        env = dict(
            self.envelope, numerical_result={"ref": "num", "digest": self.projection}
        )
        verdict, failures = verify(env, receipts)
        self.assertEqual(verdict, "refused")
        self.assertTrue(
            any("does not evidence an executed valuation" in f for f in failures)
        )

    def test_syntactically_valid_but_unbacked_digest_is_refused(self):
        env = dict(
            self.envelope,
            gt_semantic_view={"ref": GT_VIEW, "digest": "sha256:" + "9" * 64},
        )
        verdict, failures = verify(env, self.receipts)
        self.assertEqual(verdict, "refused")
        self.assertIn("gt_semantic_view: no producer receipt", failures[0])

    def test_views_at_different_revisions_are_refused(self):
        receipts = copy.deepcopy(self.receipts)
        receipts[self.sv]["result"] = "pass"
        receipts[self.sv]["governing_coordinates"]["revision"] = "1" * 40
        receipts[self.num] = self.numerical
        receipts[self.acct] = {}
        verdict, failures = verify(self.envelope, receipts)
        self.assertEqual(verdict, "refused")
        self.assertTrue(any("different coordinates" in f for f in failures))

    def test_stale_numerical_coordinates_are_refused(self):
        receipts = copy.deepcopy(self.receipts)
        receipts[self.sv]["result"] = "pass"
        stale = copy.deepcopy(self.numerical)
        stale["governing_coordinates"]["revision"] = "2" * 40
        receipts[self.num] = stale
        receipts[self.acct] = {}
        verdict, failures = verify(self.envelope, receipts)
        self.assertEqual(
            failures, ["numerical_result: coordinates differ from semantic views"]
        )
        self.assertEqual(verdict, "refused")

    def test_no_authority_escape(self):
        schema = read("schemas/gt_sv_consumer_assessment.candidate.schema.json")
        for effect in ("plan_revision", "action_authorized", "candidate_selected"):
            with (
                self.subTest(effect=effect),
                self.assertRaises(jsonschema.ValidationError),
            ):
                jsonschema.validate(
                    dict(self.envelope, authority_effect=effect), schema
                )
        for extra in ({"gt_uplift": 100}, {"five_bucket_sv": {"IEV": 1}}):
            with self.assertRaises(jsonschema.ValidationError):
                jsonschema.validate(dict(self.envelope, **extra), schema)
        core = read("overlays/contracts_gt_core.yaml")["contracts"][0]
        dependent = read("overlays/contracts_sv_dependent.yaml")["contracts"][0]
        self.assertIn(
            "analysis_or_projection_result_promoted_to_action_permission",
            core["forbidden"],
        )
        self.assertIn(
            "automatic_plan_revision_or_action_from_combined_assessment",
            dependent["forbidden"],
        )

    def test_unresolved_envelope_carries_no_number(self):
        schema = read("schemas/gt_sv_consumer_assessment.candidate.schema.json")
        unresolved = {
            "schema": "l9.assessment.gt-sv-composed/v1",
            "status": "unresolved",
            "material_unknowns": ["SV not admitted"],
            "authority_effect": "none",
        }
        jsonschema.validate(unresolved, schema)
        self.assertEqual(verify(unresolved, {})[0], "not_evaluated")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(
                dict(unresolved, numerical_result={"ref": "n", "digest": self.num}),
                schema,
            )


class StaleCoordinatesInProducerEvidence(unittest.TestCase):
    def test_changed_source_or_profile_digest_invalidates_projection(self):
        controls = {
            c["control"]: c
            for c in read("evidence/integration-v1/producer-negative-controls.json")[
                "controls"
            ]
        }
        for name in (
            "source_digest_mutated",
            "profile_digest_mutated",
            "composition_profile_digest_mutated",
        ):
            self.assertTrue(controls[name]["mechanism_matched"], name)
            self.assertTrue(
                controls[name]["summary"]["typed_failure"].endswith("REVISION_MISMATCH")
            )


if __name__ == "__main__":
    unittest.main()
