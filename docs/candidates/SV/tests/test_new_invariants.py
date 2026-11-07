from pathlib import Path
import unittest
import yaml

BASE = Path(__file__).resolve().parents[1]
NEW = {f'L9-SV-{i:03d}' for i in range(15, 21)}


class NewInvariantClosure(unittest.TestCase):
    def test_six_new_invariant_identities_are_unique_and_grounded(self):
        inv = yaml.safe_load((BASE/'overlays/invariants_additions.yaml').read_text())['invariants']
        ids = [x['id'] for x in inv]
        self.assertEqual(len(ids), 8)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(NEW.issubset(set(ids)))
        self.assertTrue(all(x['owner'] == 'Quantum-L9/.github' for x in inv))

    def test_all_new_laws_referenced_by_model_contract_and_profile(self):
        model = yaml.safe_load((BASE/'semantics/strategic_value_model.yaml').read_text())
        contract = yaml.safe_load((BASE/'overlays/contracts_additions.yaml').read_text())['contracts'][0]
        profile = yaml.safe_load((BASE/'overlays/projection_profile_additions.yaml').read_text())['projection_profiles'][0]
        for i in NEW:
            self.assertIn(i, model['governed_by']['invariants'])
            self.assertIn(i, contract['source_invariants'])
            self.assertIn(f'$.invariants[?(@.id=="{i}")]',profile['sources']['invariants']['selectors'])
        self.assertIn('$.evaluation_integrity',profile['sources']['strategic_value_model']['selectors'])
        self.assertEqual(len(model['evaluation_integrity']),6)
        self.assertEqual(len(set(contract['source_invariants'])),8)

    def test_activation_remains_unadmitted_and_reviewable(self):
        content = (BASE/'README.md').read_text().lower()
        self.assertIn('not canonically admitted',content)
        self.assertIn('native',content)

if __name__ == '__main__':
    unittest.main()
