"""Admission-candidate schema closure checks, not genuine compiler receipts."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return yaml.safe_load((ROOT / name).read_text())


class SchemaHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load('semantics/strategic_value_model.yaml')
        cls.pro = load('semantics/strategic_planner_value_projection.schema.yaml')
        cls.com = load('semantics/strategic_planner_value_composition.schema.yaml')

    def walk(self, obj, path=()):
        if isinstance(obj, dict):
            yield path, obj
            for k, v in obj.items():
                yield from self.walk(v, path + (str(k),))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from self.walk(v, path + (str(i),))

    def test_all_normative_boolean_values_are_exact_source_consts(self):
        for schema in (self.pro, self.com):
            found = 0
            for path, node in self.walk(schema):
                if node.get('type') != 'boolean':
                    continue
                modelpath = path
                if modelpath[:2] == ('properties', 'strategic_value_model'):
                    modelpath = modelpath[2:]
                if modelpath[:1] == ('properties',):
                    modelpath = modelpath[1:]
                value = self.model
                for key in modelpath:
                    if key != 'properties':
                        value = value[key]
                self.assertIs(type(value), bool)
                self.assertIs(node.get('const'), value)
                found += 1
            self.assertEqual(found, 21)

    def test_minimum_string_lists_use_dialect_enforced_array_shape(self):
        for schema in (self.pro, self.com):
            converted = 0
            for _, node in self.walk(schema):
                if 'min_items' in node:
                    self.assertEqual(node.get('type'), 'array')
                    self.assertIn('items', node)
                    self.assertEqual(node['items'].get('type'), 'string') if node['items'].get('type') == 'string' else None
                    converted += node['items'].get('type') == 'string'
            self.assertGreaterEqual(converted, 31)

    def test_nested_vocabulary_definitions_are_typed_and_required(self):
        vocab = self.pro['properties']['terms']
        self.assertEqual(vocab['type'], 'object')
        self.assertEqual(len(vocab['required']), 11)
        for name in vocab['required']:
            term = vocab['fields'][name]
            self.assertEqual(term['type'], 'object')
            self.assertIn('definition', term['required'])
            self.assertEqual(term['properties']['definition']['type'], 'string')
        composed = self.com['properties']['vocabulary']['properties']['terms']
        self.assertEqual(set(composed['required']), set(vocab['required']))

    def test_derived_profile_and_composition_version_unmodified(self):
        profile = load('overlays/projection_profile_additions.yaml')['projection_profiles'][0]
        composition = load('overlays/composition_profile_additions.yaml')['profiles'][0]
        self.assertEqual(self.pro['properties']['schema']['const'], profile['output']['schema'])
        self.assertEqual(self.com['properties']['schema']['const'], composition['output']['schema'])
        self.assertEqual(composition['merge_strategy']['source_coverage'], 'exact')

    def test_projection_stays_source_class_polymorphic(self):
        self.assertNotIn('required', self.pro,
                         'per-source schema is heterogeneous; coverage is a separate producer obligation')
        self.assertEqual(set(self.com['required']),
                         set(load('overlays/projection_profile_additions.yaml')['projection_profiles'][0]['sources']))


if __name__ == '__main__':
    unittest.main()
