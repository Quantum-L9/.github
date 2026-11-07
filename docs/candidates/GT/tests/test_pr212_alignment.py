"""PR #212 cross-pack semantic alignment, using revision-pinned connector inventory.
These tests operate on candidate records, NOT independently retrieved current canonical
source bytes or the real Semantic Compiler selector/schema interpreter.
"""
import json
import sys
from pathlib import Path
import unittest
import yaml
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from apply_to_pinned_checkout import BASE_SHA, CANONICAL_MAIN_SHA, SV_REVIEW_BLOBS, SOURCE_BLOBS

def obj(p):
    v=(ROOT/p).read_text(encoding='utf-8')
    return json.loads(v) if p.endswith('.json') else yaml.safe_load(v)

class PR212CrossPackTests(unittest.TestCase):
    def setUp(self):
        self.sv=obj('evidence/pr212_alignment_binding.json')
        self.gt_terms=obj('overlays/vocabulary_additions.yaml')['terms']
        self.gt_profile=obj('overlays/projection_profile_additions.yaml')['projection_profiles'][0]
        self.gt_core=obj('overlays/contracts_gt_core.yaml')['contracts'][0]
        self.gt_dependent=obj('overlays/contracts_sv_dependent.yaml')['contracts'][0]
    def test_exact_pr212_identity_and_documentation_only(self):
        self.assertEqual(self.sv['pr_head'],BASE_SHA)
        self.assertEqual(self.sv['main_base'],CANONICAL_MAIN_SHA)
        self.assertEqual(self.sv['pr'],212)
        self.assertEqual(self.sv['pr_scope'],'docs/candidates/SV only; canonical semantics unchanged')
        self.assertEqual(SV_REVIEW_BLOBS,self.sv['source_blobs_observed_via_github_connector'])
        self.assertEqual(len(SV_REVIEW_BLOBS),9)
        self.assertEqual(len(SOURCE_BLOBS),6)
        self.assertTrue(all(x.startswith('docs/candidates/SV/') for x in SV_REVIEW_BLOBS))
    def test_canonical_plan_commitment_collision_repaired(self):
        self.assertNotIn('strategic_commitment',self.gt_terms)
        self.assertIn('incentive_bearing_commitment',self.gt_terms)
        self.assertIn('strategic_commitment',obj('evidence/sv_collision_report.json')['original_gt_vs_canonical_collision'])
        self.assertEqual(len(self.gt_terms),12)
        self.assertIn('$.terms.incentive_bearing_commitment',self.gt_profile['sources']['vocabulary']['selectors'])
        self.assertNotIn('$.terms.strategic_commitment',self.gt_profile['sources']['vocabulary']['selectors'])
    def test_sv_specific_terms_and_invariants_not_copied(self):
        self.assertFalse(set(self.gt_terms)&set(self.sv['sv_terms_proposed']))
        self.assertEqual(len(self.sv['sv_terms_proposed']),11)
        self.assertEqual(len(self.sv['sv_invariants_proposed']),8)
        self.assertFalse(set(self.sv['sv_invariants_proposed']) & {x['id'] for x in obj('overlays/invariants_additions.yaml')['invariants']})
        self.assertEqual(set(self.gt_profile['sources']),{'vocabulary','invariants','contracts'})
        self.assertEqual(self.sv['sv_source_classes'],['strategic_value_model','vocabulary','invariants','contracts','authority_model'])
        self.assertNotIn('strategic_value_model',self.gt_profile['sources'])
    def test_gt_profile_and_sv_profile_are_separate_named_views(self):
        cp=obj('overlays/composition_profile_additions.yaml')['profiles'][0]
        self.assertEqual(self.gt_profile['id'],'l9.projection/strategic-planner-interaction@1')
        self.assertEqual(cp['composes']['projection_profile'],self.gt_profile['id'])
        self.assertEqual(cp['merge_strategy']['placement'],'source_class_namespace')
        self.assertEqual(self.sv['sv_projection'],'l9.projection/strategic-planner-value@1')
        self.assertEqual(self.sv['sv_composition'],'l9.compose/strategic-planner-value@1')
        self.assertNotEqual(cp['id'],self.sv['sv_composition'])
    def test_gt_contract_independent_of_value_and_non_universal(self):
        self.assertEqual(self.gt_core['applicability']['sv_dependency'],'none_for_gt_only')
        self.assertIn('passive_world_assessment_without_strategic_interaction_claim',self.gt_core['applicability']['does_not_apply_to'])
        self.assertFalse(any(k.startswith('L9-SV-') for k in self.gt_core['source_invariants']))
        self.assertNotIn(self.sv['sv_contract'],json.dumps(self.gt_core))
    def test_sv_dependent_contract_reuses_pr212_exact_identities(self):
        s=' '.join(self.gt_dependent['requires'])
        for token in ['sv_source_l9_strategic_value_model','sv_projection_l9_projection_strategic_planner_value_at_1',
                      'composition_l9_compose_strategic_planner_value_at_1','three_source_gt_semantic_view',
                      'one_question_appropriate_numerical_owner_method','iev_sfv_dc_erl_oc',
                      'one_explicit_compatible_objective_focal_beneficiary_or_authorized_welfare_aggregation',
                      'nonanticipative']:
            self.assertIn(token,s)
        self.assertEqual(self.gt_dependent['applicability']['trigger'],'assessment_asserts_combined_gt_conditioned_quantitative_strategic_value')
        self.assertIn('gt_only_non_sv_assessment',self.gt_dependent['applicability']['does_not_apply_to'])
        self.assertIn('sv_only_assessment',self.gt_dependent['applicability']['does_not_apply_to'])
        self.assertIn('mandatory_qv_method_for_all_gt_sv_combined_evaluations',self.gt_dependent['forbidden'])
    def test_gt_schema_uses_pr212_typed_shape(self):
        proj=obj('semantics/strategic_interaction_projection.schema.yaml')
        comp=obj('semantics/strategic_interaction_composition.schema.yaml')
        self.assertEqual(set(proj['properties']),{'terms','invariants','contracts'})
        self.assertNotIn('required',proj)  # per-source heterogeneous union: source identity verified by compiler
        self.assertEqual(set(proj['properties']['terms']['required']),set(self.gt_terms))
        for kind in ['invariants','contracts']:
            array=proj['properties'][kind]
            self.assertEqual(array['type'],'array')
            self.assertGreaterEqual(array['min_items'],1)
            self.assertEqual(array['items']['type'],'object')
        self.assertEqual(proj['properties']['invariants']['items']['properties']['id']['const'],'L9-GT-001')
        self.assertEqual(proj['properties']['contracts']['items']['properties']['id']['const'],self.gt_core['id'])
        self.assertEqual(comp['required'],['vocabulary','invariants','contracts'])
        self.assertEqual(comp['properties']['vocabulary']['properties']['terms'],proj['properties']['terms'])
        self.assertEqual(comp['properties']['contracts']['properties']['contracts'],proj['properties']['contracts'])
        self.assertNotIn('strategic_value_model',comp['properties'])
    def test_composition_fails_closed_without_namespace(self):
        local=obj('schemas/strategic_interaction_composed_payload.candidate.schema.json')
        instance={'vocabulary':{'terms':self.gt_terms},'invariants':{'invariants':obj('overlays/invariants_additions.yaml')['invariants']},
                  'contracts':{'contracts':[self.gt_core]}}
        jsonschema.validate(instance,local)
        for key in ['vocabulary','invariants','contracts']:
            bad=dict(instance);bad.pop(key)
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(bad,local)
    def test_consumer_refs_compositions_not_single_per_source_projections(self):
        schema=obj('schemas/gt_sv_consumer_assessment.candidate.schema.json')
        gt='l9.compose/strategic-planner-interaction@1#l9.projection/strategic-planner-interaction@1'
        sv='l9.compose/strategic-planner-value@1#l9.projection/strategic-planner-value@1'
        self.assertEqual(schema['properties']['gt_semantic_view']['properties']['ref']['const'],gt)
        self.assertEqual(schema['properties']['sv_semantic_view']['properties']['ref']['const'],sv)
        self.assertNotIn('gt_projection',schema['properties'])
        self.assertNotIn('sv_projection',schema['properties'])
        self.assertIn('sv_accounting_receipt',schema['allOf'][0]['then']['required'])
    def test_evaluated_requires_accounting_and_compatible_refs(self):
        schema=obj('schemas/gt_sv_consumer_assessment.candidate.schema.json')
        d='sha256:'+'a'*64
        rr=lambda v:{'ref':v,'digest':d}
        x={'schema':'l9.assessment.gt-sv-composed/v1','status':'evaluated','authority_effect':'none',
           'gt_semantic_view':rr('l9.compose/strategic-planner-interaction@1#l9.projection/strategic-planner-interaction@1'),
           'sv_semantic_view':rr('l9.compose/strategic-planner-value@1#l9.projection/strategic-planner-value@1'),
           'gt_assessment':rr('gt'), 'sv_assessment':rr('sv'),'numerical_result':rr('num'),'sv_accounting_receipt':rr('acct'),
           'comparison':{'compatibility_status':'compatible','objective_ref':'obj','beneficiary_ref':'ben',
                         'baseline_ref':'base','state_revision_ref':'rev','time_basis_ref':'weekly','horizon_ref':'4','utility_unit':'USD'}}
        jsonschema.validate(x,schema)
        for bad in [dict(x,sv_accounting_receipt=None),{k:v for k,v in x.items() if k!='sv_accounting_receipt'},
                    dict(x,gt_semantic_view=rr('wrong')),dict(x,sv_semantic_view=rr('wrong')),dict(x,gt_uplift=50)]:
            with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(bad,schema)
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(dict(x,status='unresolved',material_unknowns=['SV not admitted']),schema)
    def test_unresolved_sv_does_not_fabricate_sourcerefs_or_numbers(self):
        schema=obj('schemas/gt_sv_consumer_assessment.candidate.schema.json')
        jsonschema.validate({'schema':'l9.assessment.gt-sv-composed/v1','status':'unresolved',
                             'material_unknowns':['SV PR212 not admitted'],'authority_effect':'none'},schema)
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate({'schema':'l9.assessment.gt-sv-composed/v1','status':'evaluated','authority_effect':'none'},schema)
    def test_no_skill_and_no_sv_source_artifact_in_candidate(self):
        self.assertFalse(any('/skills/' in p.as_posix() or p.name=='SKILL.md' or p.name=='skill.zip' for p in ROOT.rglob('*')))
        self.assertFalse((ROOT/'semantics/strategic_value_model.yaml').exists())
        self.assertFalse((ROOT/'semantics/strategic_planner_value_projection.schema.yaml').exists())
        self.assertTrue((ROOT/'PR212_ALIGNMENT.md').exists())

if __name__=='__main__':unittest.main()
