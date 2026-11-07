"""Local, synthetic checks for an unadmitted candidate; NOT compiler conformance."""
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

import jsonschema
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apply_to_pinned_checkout import prepare, BASE_SHA, SOURCE_BLOBS, SV_REVIEW_BLOBS, CANONICAL_MAIN_SHA


def read_y(rel):
    return yaml.safe_load((ROOT/rel).read_text(encoding='utf-8'))


def read_j(rel):
    return json.loads((ROOT/rel).read_text(encoding='utf-8'))


class CanonicalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.t=read_y('overlays/vocabulary_additions.yaml')['terms']
        self.i=read_y('overlays/invariants_additions.yaml')['invariants']
        self.c=read_y('overlays/contracts_gt_core.yaml')['contracts'][0]
        self.sv=read_y('overlays/contracts_sv_dependent.yaml')['contracts'][0]
        self.p=read_y('overlays/projection_profile_additions.yaml')['projection_profiles'][0]
        self.cp=read_y('overlays/composition_profile_additions.yaml')['profiles'][0]

    def test_minimal_nonduplicate_semantics(self):
        self.assertEqual(len(self.i),1)
        self.assertEqual(self.i[0]['id'],'L9-GT-001')
        self.assertEqual(len(self.t),12)
        self.assertFalse(set(self.t)&{'strategic_value','systemic_future_value','future_effect_identity','strategic_value_assessment','decision_relevant_information_value','counterfactual_baseline'})
        self.assertEqual(set(self.c['source_invariants'])&{'L9-GT-001'},{'L9-GT-001'})
        self.assertFalse(any(x.startswith('L9-SV-') for x in self.c['source_invariants']+self.sv['source_invariants']))
        self.assertNotIn('five_bucket',str(self.t))

    def test_gt_only_independent_of_sv(self):
        self.assertEqual(self.c['id'],'l9.contract/strategic-interaction-assessment@1')
        self.assertNotIn('strategic-value-assessment@1',json.dumps(self.c))
        self.assertIn('strategic-value-assessment@1',self.sv['purpose'])
        self.assertIn('sv_source_l9_strategic_value_model_and_contract_are_separately_admitted_not_merely_staged_in_pr_212',self.sv['requires'])

    def test_projection_is_gt_only_and_selector_closed(self):
        self.assertEqual(self.p['id'],'l9.projection/strategic-planner-interaction@1')
        self.assertEqual(self.p['consumer'],'strategic-planner')
        self.assertEqual(set(self.p['sources']),{'vocabulary','invariants','contracts'})
        self.assertEqual(set(self.p['sources']['vocabulary']['selectors']),{'$.terms.'+x for x in self.t})
        self.assertEqual(self.p['sources']['invariants']['selectors'],['$.invariants[?(@.id=="L9-GT-001")]'])
        self.assertEqual(self.p['sources']['contracts']['selectors'],['$.contracts[?(@.id=="'+self.c['id']+'")]'])
        self.assertNotIn('strategic-planner-value@1',json.dumps(self.p))
        self.assertEqual(self.cp['composes']['projection_profile'],self.p['id'])
        self.assertEqual(self.cp['merge_strategy']['placement'],'source_class_namespace')

    def test_no_new_valuer_or_permission(self):
        self.assertIn('consumer_keeps_strategy_policy_permission_and_execution_authority',self.c['requires'])
        self.assertIn('one_question_appropriate_numerical_owner_method_for_canonical_sv_valuation_not_mandatory_qv',self.sv['requires'])
        self.assertIn('semantic_projection_composition_does_not_execute_numerical_valuation',self.sv['guarantees'])
        self.assertIn('adding_independent_gt_uplift_to_already_counted_sv_effect',self.sv['forbidden'])
        self.assertIn('automatic_plan_revision_or_action_from_combined_assessment',self.sv['forbidden'])

    def test_official_schema_candidates_have_existing_shape(self):
        for name in ['strategic_interaction_projection','strategic_interaction_composition']:
            x=read_y('semantics/'+name+'.schema.yaml')
            self.assertEqual(x['schema'],'l9.schema-definition/v1')
            self.assertTrue(x['canonical'])
            self.assertEqual(x['authority']['owner'],'Quantum-L9/.github')
            self.assertEqual(x['type'],'object')
        self.assertEqual(read_y('semantics/strategic_interaction_composition.schema.yaml')['required'],['vocabulary','invariants','contracts'])

    def test_strict_local_schema_accepts_exact_projected_records(self):
        schema=read_j('schemas/strategic_interaction_selected_payload.candidate.schema.json')
        jsonschema.Draft202012Validator.check_schema(schema)
        for payload in [{'terms':self.t},{'invariants':self.i},{'contracts':[self.c]}]:
            jsonschema.validate(payload,schema)
        comp={'vocabulary':{'terms':self.t},'invariants':{'invariants':self.i},'contracts':{'contracts':[self.c]}}
        jsonschema.validate(comp,read_j('schemas/strategic_interaction_composed_payload.candidate.schema.json'))

    def test_strict_schema_rejects_swapped_sv_and_extra_semantics(self):
        schema=read_j('schemas/strategic_interaction_selected_payload.candidate.schema.json')
        bad=[{'terms':dict(self.t,strategic_value={'semantic_class':'value','definition':'copy'})},
             {'invariants':self.i,'sv':{'value':500}},
             {'contracts':[self.sv]},
             {'terms':self.t,'invariants':self.i}]
        for payload in bad:
            with self.subTest(payload=list(payload)):
                with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(payload,schema)

    def test_gt_sv_consumer_envelope_is_by_reference_only(self):
        schema=read_j('schemas/gt_sv_consumer_assessment.candidate.schema.json')
        jsonschema.Draft202012Validator.check_schema(schema)
        digest='sha256:'+'c'*64
        ref=lambda name:{'ref':name,'digest':digest}
        comparison=dict(objective_ref='objective',beneficiary_ref='beneficiary',baseline_ref='baseline',state_revision_ref='rev0',time_basis_ref='week',horizon_ref='4_weeks',utility_unit='USD',compatibility_status='compatible')
        x={'schema':'l9.assessment.gt-sv-composed/v1','status':'evaluated','gt_semantic_view':ref('l9.compose/strategic-planner-interaction@1#l9.projection/strategic-planner-interaction@1'), 'sv_semantic_view':ref('l9.compose/strategic-planner-value@1#l9.projection/strategic-planner-value@1'),'gt_assessment':ref('gt_result'),'sv_assessment':ref('sv_result'),'comparison':comparison,'numerical_result':ref('numerical_result'),'sv_accounting_receipt':ref('sv_accounting_ledger'),'authority_effect':'none'}
        jsonschema.validate(x,schema)
        for delta in ({'gt_uplift_usd':100},{'five_bucket_sv':{'immediate':100}}):
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(dict(x,**delta),schema)
        for altered in [dict(x,status='evaluated',comparison=dict(comparison,compatibility_status='unresolved')),{k:v for k,v in x.items() if k!='numerical_result'}]:
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(altered,schema)
        jsonschema.validate({'schema':x['schema'],'status':'unresolved','gt_semantic_view':ref('l9.compose/strategic-planner-interaction@1#l9.projection/strategic-planner-interaction@1'),'gt_assessment':ref('gt_result'),'material_unknowns':['SV not admitted'],'authority_effect':'none'},schema)
        jsonschema.validate({'schema':x['schema'],'status':'unresolved','material_unknowns':['GT model and SV not admitted'],'authority_effect':'none'},schema)
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(dict(x,status='unresolved',material_unknowns=['Missing evidence']),schema)

    def test_source_local_selector_replay_exact_records_only(self):
        # Only the pinned l9.selector syntax variants actually used here.
        # This is NOT native l9-semantic-compiler-engine replay.
        import re
        sources={
            'vocabulary':{'terms':self.t},
            'invariants':{'invariants':self.i},
            'contracts':{'contracts':[self.c]},
        }
        result={}
        for source_class,config in self.p['sources'].items():
            source=sources[source_class]
            selected={}
            for selector in config['selectors']:
                term=re.fullmatch(r'\$\.terms\.([a-z_]+)',selector)
                target=re.fullmatch(r'\$\.(invariants|contracts)\[\?\(@\.id=="([^"]+)"\)\]',selector)
                if term:
                    name=term.group(1)
                    if name not in source['terms']:
                        raise ValueError('missing term '+name)
                    selected.setdefault('terms',{})[name]=source['terms'][name]
                elif target:
                    family,ref=target.groups()
                    matches=[row for row in source[family] if row['id']==ref]
                    if len(matches)!=1:
                        raise ValueError('missing or duplicate canonical record '+ref)
                    selected.setdefault(family,[]).extend(matches)
                else:
                    raise ValueError('unsupported selector '+selector)
            result[source_class]=selected
        self.assertEqual(result,{'vocabulary':{'terms':self.t},'invariants':{'invariants':self.i},'contracts':{'contracts':[self.c]}})
        self.assertNotIn('strategic_value',result['vocabulary']['terms'])

    def test_native_manifest_names_not_synthetic_sv_schema(self):
        manifest=('semantics/strategic_interaction_projection.schema.yaml',
                  'semantics/strategic_interaction_composition.schema.yaml')
        for name in manifest:self.assertTrue((ROOT/name).exists())
        self.assertFalse((ROOT/'semantics/strategic_value_model.yaml').exists())
        self.assertFalse((ROOT/'semantics/strategic_value_interaction_assessment.schema.yaml').exists())

    def test_pinned_authority_evidence_is_partial_not_receipt(self):
        evidence=read_j('evidence/authority_binding.json')
        self.assertEqual(evidence['revision'],CANONICAL_MAIN_SHA)
        self.assertEqual(evidence['review_pr212_revision'],BASE_SHA)
        self.assertEqual(evidence['sv_review_blob_shas'],SV_REVIEW_BLOBS)
        for rel,blob in SOURCE_BLOBS.items():
            self.assertEqual(evidence['source_blob_shas'][rel],blob)
        self.assertEqual(evidence['sv_dependency']['status_at_pinned_main'],'not_admitted')
        self.assertIn('PARTIAL',evidence['authority_assessment'])


class SyntheticMathCounterexamples(unittest.TestCase):
    """Illustrations: NOT production GT/SV evaluator implementation or receipt."""

    def test_passive_world_matches_sv_only(self):
        self.assertEqual(sum(p*v for p,v in [(1.,1000.)]),1000.)

    def test_gt_response_can_reverse_plan_ranking(self):
        adjusted_a=sum(p*v for p,v in [(0.60,1000.),(0.40,400.)])
        original_a=1000.
        option_b=800.
        self.assertEqual(adjusted_a,760.)
        self.assertGreater(original_a,option_b)
        self.assertLess(adjusted_a,option_b)
        self.assertNotEqual(adjusted_a,original_a+adjusted_a)

    def test_one_future_effect_must_not_be_added_twice(self):
        booked_value=500.  # already includes reputation effect of 200
        reputation_effect=200.
        self.assertEqual(booked_value,500.)
        self.assertNotEqual(booked_value+reputation_effect,booked_value)
        forbidden=['adding_independent_gt_uplift_to_already_counted_sv_effect']
        self.assertIn('adding_independent_gt_uplift_to_already_counted_sv_effect',forbidden)

    def test_softmax_fixed_point_is_not_nash_proof(self):
        p=math.exp(2.)/(math.exp(2.)+math.exp(0.))
        gap=2.-(p*2.+(1.-p)*0.)
        self.assertGreater(gap,0.2)
        self.assertLess(gap,0.25)
        self.assertNotAlmostEqual(gap,0.,delta=1e-6)

    def test_missing_probability_mass_cannot_be_renormalized_silently(self):
        observed_mass=sum([.6,.2])
        self.assertNotAlmostEqual(observed_mass,1.)
        self.assertGreater(1.-observed_mass,0.)

    def test_joint_correlation_is_not_independent_product_without_evidence(self):
        p_a=.5;p_b=.5;reported_joint=.45
        self.assertNotAlmostEqual(p_a*p_b,reported_joint)

    def test_no_value_ranking_trumps_hard_infeasibility(self):
        actions={'illegal':{'feasible':False,'value':9999},'legal':{'feasible':True,'value':10}}
        result=max(((x,y['value']) for x,y in actions.items() if y['feasible']),key=lambda z:z[1])[0]
        self.assertEqual(result,'legal')


class SyntheticApplicationTests(unittest.TestCase):
    def test_prepare_synthetic_canonical_shape_without_sv(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'repo';(root/'semantics').mkdir(parents=True)
            entries={
                'invariants.yaml':"schema: l9.invariants/v1\ninvariants:\n"+''.join('- id: '+iid+'\n  statement: existing\n  scope: global\n  owner: Quantum-L9/.github\n' for iid in ['L9-AUTH-002','L9-HARD-001','L9-UNKNOWN-001','L9-EVIDENCE-001','L9-ASSURANCE-001']),
                'contracts.yaml':"schema: l9.contracts/v1\nderivation:\n  source_digest_sha256: "+'a'*64+"\n  source_invariant_count: 5\ncontracts:\n- id: l9.contract/old@1\n  purpose: old\n",
                'vocabulary.yaml':"schema: l9.vocabulary/v1\nterms:\n  authority:\n    semantic_class: governance\n    definition: old\nrelationships:\n  owns: {}\n",
                'projection_profiles.yaml':"schema: l9.projection-profile-catalog/v1\nsource_classes:\n  vocabulary:\n    canonical_artifact: vocabulary.yaml\n  invariants:\n    canonical_artifact: invariants.yaml\n  contracts:\n    canonical_artifact: contracts.yaml\nprojection_profiles:\n- id: l9.projection/old@1\n  class: consumer\n  consumer: old\n  sources: {}\nprojection_engine_contract_ref:\n  ref: old\n",
                'composition_profiles.yaml':"schema: l9.composition-profiles/v1\nprofiles:\n  - id: l9.compose/old@1\n    purpose: old\n",
                'generic_compiler_manifest.yaml':"schema: l9.generic-compiler-manifest/v1\nrequires:\n  artifact_schemas:\n  - pr_audit_composition.schema.yaml\n",
            }
            for name,body in entries.items():
                (root/'semantics'/name).write_text(body,encoding='utf-8')
            proposed,count=prepare(root)
            self.assertEqual(count,6)
            self.assertEqual(len(proposed),8)
            inv_text=proposed['semantics/invariants.yaml']
            ct=yaml.safe_load(proposed['semantics/contracts.yaml'])
            self.assertEqual(ct['derivation']['source_invariant_count'],6)
            self.assertEqual(ct['derivation']['source_digest_sha256'],hashlib.sha256(inv_text.encode()).hexdigest())
            ids={x['id'] for x in ct['contracts']}
            self.assertIn('l9.contract/strategic-interaction-assessment@1',ids)
            self.assertNotIn('l9.contract/strategic-value-interaction-composition@1',ids)
            prof=yaml.safe_load(proposed['semantics/projection_profiles.yaml'])
            cp=yaml.safe_load(proposed['semantics/composition_profiles.yaml'])
            self.assertIn('l9.projection/strategic-planner-interaction@1',{x['id'] for x in prof['projection_profiles']})
            self.assertIn('l9.compose/strategic-planner-interaction@1',{x['id'] for x in cp['profiles']})
            self.assertIn('strategic_interaction_composition.schema.yaml',proposed['semantics/generic_compiler_manifest.yaml'])

    def test_core_script_does_not_hide_override_or_publish(self):
        script=(ROOT/'apply_to_pinned_checkout.py').read_text(encoding='utf-8')
        self.assertIn("BASE_SHA = '85531616cee2da94bbb7154418a78537549a4d76'",script)
        self.assertNotIn('--expected-sha',script)
        self.assertNotIn('git push',script)
        self.assertNotIn('gh pr create',script)
        self.assertNotIn('contracts_sv_dependent',script)

if __name__=='__main__':unittest.main()
