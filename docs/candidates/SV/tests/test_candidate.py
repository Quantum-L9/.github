import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('candidate_apply', ROOT / 'apply_to_pinned_checkout.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CandidateTests(unittest.TestCase):
    def fixture(self, root):
        sem = root / 'semantics'; sem.mkdir(parents=True)
        originals = {
            'invariants.yaml': 'schema: l9.invariants/v1\ninvariants:\n- id: L9-STRATEGY-001\n  statement: strategy owner\n',
            'contracts.yaml': 'schema: l9.contracts/v1\nderivation:\n  source_digest_sha256: ' + '0'*64 + '\n  source_invariant_count: 1\ncontracts:\n- id: l9.contract/projection@1\n  purpose: projection\n',
            'vocabulary.yaml': 'schema: l9.vocabulary/v1\nterms:\n  strategy:\n    definition: Strategy\nrelationships:\n  depends_on: {}\n',
            'canonical_sources.yaml': 'sources:\n- id: l9.source/authority-model@1\n  path: semantics/authority_model.yaml\nrules:\n  canonical_sources_must_be_registered: true\n',
            'projection_profiles.yaml': 'source_classes:\n  vocabulary:\n    canonical_artifact: vocabulary.yaml\n  invariants:\n    canonical_artifact: invariants.yaml\n  contracts:\n    canonical_artifact: contracts.yaml\n  authority_model:\n    canonical_artifact: authority_model.yaml\nprojection_profiles:\n- id: l9.projection/example@1\n  class: consumer\n  consumer: example\nprojection_engine_contract_ref:\n  artifact: projection_engine_contract.yaml\n',
            'generic_compiler_manifest.yaml': 'requires:\n  semantic_catalogs:\n  - strategic_plan_model.yaml\n  - vocabulary.yaml\n  artifact_schemas:\n  - pr_audit_composition.schema.yaml\n',
            'composition_profiles.yaml': 'schema: l9.composition-profiles/v1\nprofiles:\n  - id: l9.compose/example@1\n    purpose: fixture\n',
        }
        for name, content in originals.items():
            (sem/name).write_text(content)

    def test_generates_10_local_changes(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t); self.fixture(p)
            changes, count = mod.generate(p)
            self.assertEqual(count, 9)
            self.assertEqual(len(changes), 10)
            for path, content in changes.items():
                self.assertIsInstance(yaml.safe_load(content), dict)
            self.assertIn('l9.strategic.value@1', changes['semantics/strategic_value_model.yaml'])
            self.assertIn('l9.projection/strategic-planner-value@1', changes['semantics/projection_profiles.yaml'])
            self.assertIn('l9.contract/strategic-value-assessment@1', changes['semantics/contracts.yaml'])
            self.assertIn('l9.compose/strategic-planner-value@1', changes['semantics/composition_profiles.yaml'])
            self.assertIn('strategic_planner_value_projection.schema.yaml', changes['semantics/generic_compiler_manifest.yaml'])
            self.assertIn('strategic_planner_value_composition.schema.yaml', changes['semantics/generic_compiler_manifest.yaml'])

    def test_pr6_math_and_profile_are_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t); self.fixture(p)
            changes, count = mod.generate(p)
            model = yaml.safe_load(changes['semantics/strategic_value_model.yaml'])
            self.assertEqual(count, 9)
            self.assertEqual(model['artifact_id'], 'l9.strategic.value@1')
            self.assertEqual(model['source_lineage']['donor_commit'],
                             'fb0ae95620cea0dc3f48aa009056ddb755d69640')
            self.assertIn('bounded_expression', model['counterfactual_mathematics'])
            self.assertIn('bounded_recurrence', model['strategic_interaction_lookahead'])
            self.assertIn('nonanticipativity', model['evaluation_integrity'])
            profile = yaml.safe_load(changes['semantics/projection_profiles.yaml'])
            current = [x for x in profile['projection_profiles']
                       if x['id'] == 'l9.projection/strategic-planner-value@1'][0]
            selectors = current['sources']['strategic_value_model']['selectors']
            self.assertIn('$.counterfactual_mathematics', selectors)
            self.assertIn('$.strategic_interaction_lookahead', selectors)
            contract = yaml.safe_load(changes['semantics/contracts.yaml'])
            value_contract = [x for x in contract['contracts']
                              if x['id'] == 'l9.contract/strategic-value-assessment@1'][0]
            self.assertIn('complete_probability_mass_when_probabilistic_method_applies_or_explicit_unresolved_missing_mass',
                          value_contract['requires'])

    def test_retired_generic_leverage_machine_term_not_reintroduced(self):
        value_terms = yaml.safe_load(mod.raw('overlays/vocabulary_additions.yaml'))['terms']
        self.assertEqual(len(value_terms), 11)
        self.assertNotIn('leverage_mesh_loop', value_terms)
        self.assertNotIn('leverage_score', value_terms)
        self.assertIn('value_propagation_mesh', value_terms)
        invariants = yaml.safe_load(mod.raw('overlays/invariants_additions.yaml'))['invariants']
        self.assertEqual(len(invariants), 8)
        self.assertEqual(len({row['id'] for row in invariants}), 8)

    def test_collision_fail_closed(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t); self.fixture(p)
            f = p/'semantics/vocabulary.yaml'
            f.write_text(f.read_text().replace('relationships:', '  strategic_value:\n    definition: earlier\nrelationships:'))
            with self.assertRaisesRegex(ValueError, 'collision'):
                mod.generate(p)


if __name__ == '__main__':
    unittest.main()
