"""Lossless candidate-ID reduction and claim-specific contract scope checks."""
from pathlib import Path
import unittest
import yaml
from reduction_closure import donor_statements, expected

ROOT=Path(__file__).resolve().parents[1]

def load(path):return yaml.safe_load((ROOT/path).read_text())

class IrreducibilityTests(unittest.TestCase):
    def setUp(self):
        self.inv=load('overlays/invariants_additions.yaml')['invariants']
        self.model=load('semantics/strategic_value_model.yaml')
        self.contract=load('overlays/contracts_additions.yaml')['contracts'][0]
        self.profile=load('overlays/projection_profile_additions.yaml')['projection_profiles'][0]

    def test_first_fourteen_are_exhaustively_dispositioned(self):
        kept={x['id'] for x in self.inv if x['id'] in ('L9-SV-001','L9-SV-002')}
        formerly=set(self.model['retained_former_candidate_semantics'])
        self.assertEqual(kept,{'L9-SV-001','L9-SV-002'})
        self.assertEqual(formerly,{f'L9-SV-{n:03d}' for n in range(3,15)})
        self.assertEqual(kept|formerly,{f'L9-SV-{n:03d}' for n in range(1,15)})
        self.assertFalse(kept&formerly)

    def test_every_former_statement_retains_exact_identity_and_executable_contract_obligation(self):
        former=self.model['retained_former_candidate_semantics']
        for ident,p in former.items():
            self.assertEqual(p['source_candidate_id'],ident)
            self.assertGreater(len(p['meaning'].strip()),55)
            self.assertEqual(p['governing_layer'],
                             'strategic_value_model_and_assessment_contract_not_independent_global_invariant')
            node=self.model
            for part in p['model_section'].split('.'):
                self.assertIn(part,node, f'{ident}: lost placement {part}')
                node=node[part]
            self.assertIn(p['contract_obligation'],
                          self.contract['requires']+self.contract['guarantees'],
                          f'{ident}: proposed destination obligation is not present')
            self.assertIn(ident,self.model['retained_former_candidate_semantics'])
            self.assertNotIn(ident,self.contract['source_invariants'])
            self.assertFalse(any(ident in selector for selector in
                                 self.profile['sources']['invariants']['selectors']))

    def test_six_additional_meanings_are_relocated_not_admitted(self):
        exp=expected()
        lineage=self.model['relocated_additional_candidate_semantics']
        self.assertEqual(set(lineage),{f'L9-SV-{n:03d}' for n in range(15,21)})
        self.assertFalse(set(lineage)&set(self.model['retained_former_candidate_semantics']))
        statements=donor_statements()
        for ident,p in lineage.items():
            row=exp['relocated'][ident]
            self.assertEqual(p['source_candidate_id'],ident)
            self.assertEqual(p['meaning'],statements[ident])
            self.assertEqual(p['disposition'],row['disposition'])
            self.assertEqual(p['authority_status'],'not_admitted_as_independent_invariant')
            self.assertEqual(p['when'],row['when'])
            node=self.model
            for part in p['model_section'].split('.'):
                self.assertIn(part,node,f'{ident}: lost placement {part}')
                node=node[part]
            self.assertTrue(node)
            self.assertIn(p['contract_obligation'],self.contract['requires'])
            self.assertTrue(set(p['governing_invariants'])<=set(self.contract['source_invariants']))
            self.assertNotIn(ident,self.contract['source_invariants'])
            self.assertNotIn(ident,self.model['governed_by']['invariants'])
            self.assertFalse(any(ident in selector for selector in
                                 self.profile['sources']['invariants']['selectors']))
            self.assertNotIn(ident,{r['id'] for r in self.inv})

    def test_twenty_candidate_meanings_are_all_preserved(self):
        kept={x['id'] for x in self.inv}
        former=set(self.model['retained_former_candidate_semantics'])
        relocated=set(self.model['relocated_additional_candidate_semantics'])
        self.assertEqual(len(kept),2)
        self.assertEqual(len(former)+len(relocated),18)
        self.assertEqual(kept|former|relocated,{f'L9-SV-{n:03d}' for n in range(1,21)})

    def test_assessment_contract_does_not_apply_to_unrelated_numerical_work(self):
        self.assertEqual(self.contract['applies_to'],
                         ['assessments_asserting_applicable_objective_relative_quantitative_strategic_value_claims'])
        applicability=self.contract['applicability']
        self.assertIn('generic_numerical_reasoning_without_strategic_value_claim',applicability['does_not_apply_to'])
        self.assertIn('unrelated_governed_decision_evaluation',applicability['does_not_apply_to'])
        self.assertIn('unrelated_strategic_planning_activity',applicability['does_not_apply_to'])
        self.assertIn('imposing_strategic_value_specific_math_on_unrelated_evaluations',
                      self.contract['forbidden'])
        self.assertEqual(self.model['assessment_applicability']['unsupported_claim'],
                         'conditional_or_unknown_not_imposed_method')

if __name__=='__main__':unittest.main()
