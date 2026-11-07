"""Pre-admission semantic-contract tests, not numerical-method implementation proof."""
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]


def load(path):
    return yaml.safe_load((ROOT/path).read_text())


class PartitionAndMethodAlignment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=load('semantics/strategic_value_model.yaml')
        cls.contract=load('overlays/contracts_additions.yaml')['contracts'][0]
        cls.invariants={x['id']:x['statement'] for x in load('overlays/invariants_additions.yaml')['invariants']}
        cls.profile=load('overlays/projection_profile_additions.yaml')['projection_profiles'][0]

    def test_accounting_partition_is_mandatory_complete_exclusive_and_projected(self):
        value=self.model['valuation']
        partition=value['accounting_partition_contract']
        self.assertEqual(partition['status'],'mandatory_precondition_for_complete_five_term_value_claim')
        self.assertEqual(partition['required_component_buckets'],
                         ['ImmediateExpectedValue','SystemicFutureValue','DirectCost',
                          'ExpectedRiskLoss','OpportunityCost'])
        norm=partition['normative_partition']
        self.assertIs(norm['mutually_exclusive_booking'],True)
        self.assertIs(norm['exhaustive_material_consequence_coverage'],True)
        self.assertIs(norm['losses_and_costs_already_reflected_in_utility_flows_cannot_be_subtracted_again'],True)
        self.assertIs(norm['unknown_effect_booking_never_defaults_to_zero'],True)
        self.assertIn('$.valuation', self.profile['sources']['strategic_value_model']['selectors'])
        self.assertIn('exhaustive, mutually exclusive accounting partition', self.invariants['L9-SV-002'])
        self.assertIn('exactly_one_accounting_home_per_material_effect_with_gross_net_reconciliation',
                      self.contract['requires'])

    def test_partition_negative_witnesses_refuse_net_flow_cost_double_count(self):
        part=self.model['valuation']['accounting_partition_contract']
        led=part['component_coverage_ledger']
        self.assertIn('accounting_bucket_or_embedded_component_reference',
                      led['required_per_material_effect'])
        self.assertIn('excluded from separate subtraction',led['embedded_cost_handling'])
        witnesses=part['negative_witnesses']
        for key in ('embedded_DC_subtracted_again', 'embedded_expected_risk_loss_subtracted_again',
                    'embedded_opportunity_cost_subtracted_again'):
            self.assertEqual(witnesses[key],'forbidden_double_booking')
        for key in ('unclassified_material_consequence','zero_subtraction_without_ledger_basis'):
            self.assertEqual(witnesses[key],'unknown_or_conditional')
        self.assertIn('separately_subtracting_direct_cost_or_risk_loss_already_embedded_in_utility_flows',
                      self.contract['forbidden'])
        self.assertIn('treating_unmapped_material_accounting_consequences_as_zero',
                      self.contract['forbidden'])
        self.assertEqual(100-20,80)  # gross representation witness
        self.assertEqual(80-0,80)    # net representation witness
        self.assertNotEqual(80-20,80)  # explicitly forbidden duplicate subtraction

    def test_qv_is_supported_optional_and_method_conditional(self):
        look=self.model['strategic_interaction_lookahead']
        self.assertEqual(look['method_policy'],
                         'supported_mathematical_formulation_not_universal_algorithm_requirement')
        self.assertTrue({'bounded_scenario_analysis','robust_optimization',
                         'bounded_QV_belief_state_lookahead',
                         'other_owner_admitted_question_appropriate_methods'} <=
                        set(look['supported_method_families']))
        self.assertIn('qv_only_required_model_coordinates',look)
        self.assertIn('qv_only_stopping_conditions',look)
        self.assertNotIn('required_model_coordinates',look)
        self.assertNotIn('stopping_conditions',look)
        self.assertIn('$.strategic_interaction_lookahead',
                      self.profile['sources']['strategic_value_model']['selectors'])
        self.assertIn('qv_belief_state_model_coordinates_only_when_qv_method_selected',
                      self.contract['requires'])
        self.assertIn('requiring_belief_state_QV_optimizer_for_every_legitimate_strategic_assessment',
                      self.contract['forbidden'])
        self.assertIn('not_universal_algorithm_requirement',look['method_policy'])
        self.assertIn('L9-SV-011',self.model['retained_former_candidate_semantics'])
        self.assertIn('conditional_or_unknown',look['selection_requirements'][-1])

    def test_model_validation_evidence_replaces_general_proof(self):
        for filename in ('overlays/contracts_additions.yaml','semantics/strategic_value_model.yaml',
                         'overlays/invariants_additions.yaml'):
            self.assertNotIn('model_adequacy_proof',(ROOT/filename).read_text())
        requires=self.contract['requires']
        self.assertIn('method_identity_input_lineage_executed_method_evidence_and_applicable_independently_reviewable_model_validation_evidence_for_strong_numerical_claims', requires)
        assurance=self.model['evaluation_integrity']['independent_method_assurance']
        self.assertIn('applicable_independently_reviewable_model_validation_evidence_distinct_from_arithmetic_correctness',assurance)
        self.assertIn('mathematical_proof_of_general_real_world_forecast_adequacy_not_presumed',assurance)
        self.assertIn('independently reviewable model-validation evidence',self.invariants['L9-SV-020'])
        self.assertIn('demanding_mathematical_proof_of_general_real_world_forecast_adequacy',
                      self.contract['forbidden'])

    def test_canonical_scope_and_version_do_not_drift(self):
        self.assertEqual(self.model['artifact_id'],'l9.strategic.value@1')
        self.assertEqual(self.contract['id'],'l9.contract/strategic-value-assessment@1')
        self.assertEqual(self.profile['id'],'l9.projection/strategic-planner-value@1')
        self.assertEqual(len(self.invariants),8)
        self.assertEqual(len(self.profile['sources']),5)
        self.assertEqual(len(load('overlays/vocabulary_additions.yaml')['terms']),11)


if __name__=='__main__':
    unittest.main()
