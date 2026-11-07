"""Local shape and ownership closure for proposed canonical schema definitions.

Not an independent Semantic Compiler qualification receipt.
"""
from pathlib import Path
from copy import deepcopy
import re
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]

def read(rel):
    return yaml.safe_load((ROOT/rel).read_text())

class SchemaCompositionClosure(unittest.TestCase):
    def setUp(self):
        self.pro=read('overlays/projection_profile_additions.yaml')['projection_profiles'][0]
        self.com=read('overlays/composition_profile_additions.yaml')['profiles'][0]
        self.ps=read('semantics/strategic_planner_value_projection.schema.yaml')
        self.cs=read('semantics/strategic_planner_value_composition.schema.yaml')
        self.model=read('semantics/strategic_value_model.yaml')
        self.value_terms=read('overlays/vocabulary_additions.yaml')['terms']
        self.inv=read('overlays/invariants_additions.yaml')['invariants']

    def test_profile_and_payload_schema_version_1_are_bound(self):
        self.assertEqual(self.pro['id'],'l9.projection/strategic-planner-value@1')
        self.assertEqual(self.pro['output']['schema'],'l9.projection.strategic-planner-value/v1')
        self.assertEqual(self.ps['properties']['schema']['const'],self.pro['output']['schema'])
        self.assertEqual(self.ps['governed_by']['projection_profile_ref'],self.pro['id'])
        self.assertEqual(self.ps['artifact_id'],'l9.schema/strategic-planner-value-projection@1')
        self.assertEqual(self.ps['canonical_source']['artifact'],'strategic_planner_value_projection.schema.yaml')
        self.assertNotIn('$.schema',self.pro['sources']['strategic_value_model']['selectors'],
                         'Source model version must not collide with derived payload schema const')
        self.assertEqual(self.ps['properties']['artifact_id']['const'],self.model['artifact_id'])

    def test_composition_is_exact_five_source_namespaces(self):
        required=['strategic_value_model','vocabulary','invariants','contracts','authority_model']
        self.assertEqual(list(self.pro['sources']),required)
        self.assertEqual(self.cs['required'],required)
        self.assertEqual(set(self.cs['properties'])-{'schema'},set(required))
        self.assertEqual(self.com['composes']['projection_profile'],self.pro['id'])
        self.assertEqual(self.com['merge_strategy'],{
            'placement':'source_class_namespace','source_coverage':'exact',
            'duplicate_source':'conflict','semantic_identity_collision':'require_equivalence'})
        self.assertEqual(self.com['output']['schema'],'l9.composed-projection.strategic-planner-value/v1')
        self.assertEqual(self.cs['properties']['schema']['const'],self.com['output']['schema'])
        self.assertEqual(self.cs['governed_by']['composition_profile_ref'],self.com['id'])
        self.assertEqual(self.cs['governed_by']['projection_profile_ref'],self.pro['id'])

    def test_model_selectors_are_structurally_resolved_and_required_in_composition(self):
        selects=[s[2:] for s in self.pro['sources']['strategic_value_model']['selectors']]
        self.assertEqual(set(selects),set(self.cs['properties']['strategic_value_model']['required']))
        self.assertTrue(set(selects) <= set(self.model))
        for k in selects:
            self.assertIn(k,self.ps['properties'])
            self.assertIn(k,self.cs['properties']['strategic_value_model']['properties'])
        self.assertEqual(set(self.model['retained_former_candidate_semantics']),
                         {f'L9-SV-{i:03d}' for i in range(3,15)})
        retained=self.cs['properties']['strategic_value_model']['properties']['retained_former_candidate_semantics']
        self.assertEqual(set(retained['required']),set(self.model['retained_former_candidate_semantics']))

    def test_value_and_global_invariant_coverage_matches_schema_exact_ids(self):
        new={r['id'] for r in self.inv}
        self.assertEqual(new,{'L9-SV-001','L9-SV-002'} | {f'L9-SV-{i:03d}' for i in range(15,21)})
        global_ids={r for r in self.model['governed_by']['invariants'] if not r.startswith('L9-SV-')}
        sel={s.split('"')[1] for s in self.pro['sources']['invariants']['selectors']}
        self.assertEqual(sel,new|global_ids)
        schema_set=set(self.ps['properties']['invariants']['items']['properties']['id']['enum'])
        self.assertEqual(sel,schema_set)
        self.assertEqual(self.ps['properties']['invariants']['min_items'],len(sel))
        self.assertEqual(self.cs['properties']['invariants']['properties']['invariants'],
                         self.ps['properties']['invariants'])
        self.assertEqual(set(self.ps['properties']['terms']['required']),set(self.value_terms))
        self.assertEqual(set(self.ps['properties']['terms']['fields']),set(self.value_terms))
        self.assertEqual(len(self.value_terms),11)

    def test_derived_composition_is_not_a_numerical_or_planning_authority(self):
        self.assertEqual(self.com['conflict_result'],'invalid')
        self.assertIn('non-authoritative consumer view',self.com['purpose'].lower())
        self.assertIn('non-authoritative',self.com['purpose'])
        self.assertEqual(self.ps['schema'],'l9.schema-definition/v1')
        self.assertEqual(self.cs['schema'],'l9.schema-definition/v1')
        self.assertEqual(self.ps['authority']['authority_class'],'canonical')
        self.assertFalse(any(v=='any' for v in self._all_type_values(self.ps)))
        self.assertFalse(any(v=='any' for v in self._all_type_values(self.cs)))

    @staticmethod
    def _all_type_values(obj):
        if isinstance(obj,dict):
            for k,v in obj.items():
                if k=='type':yield v
                yield from SchemaCompositionClosure._all_type_values(v)
        elif isinstance(obj,list):
            for i in obj: yield from SchemaCompositionClosure._all_type_values(i)

    def test_negative_mismatches_are_disprovable(self):
        broken=deepcopy(self.cs)
        broken['required'].remove('authority_model')
        self.assertNotEqual(set(broken['required']),set(self.pro['sources']))
        bad=deepcopy(self.ps)
        bad['properties']['schema']['const']='l9.projection.strategic-planner-value/v99'
        self.assertNotEqual(bad['properties']['schema']['const'],self.pro['output']['schema'])

    def test_profile_and_composition_artifact_references_have_canonical_mapping(self):
        # These exact source and file coordinates are checked again by the patch applier.
        self.assertEqual(self.pro['sources']['strategic_value_model']['selectors'][0],'$.artifact_id')
        self.assertEqual(self.pro['output']['schema'],self.ps['properties']['schema']['const'])
        self.assertEqual(self.com['output']['schema'],self.cs['properties']['schema']['const'])

if __name__=='__main__':unittest.main()
