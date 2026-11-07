#!/usr/bin/env python3
"""Qualify real L9 compiler schema interpreter against exact candidate witnesses.

Run inside the actual pinned l9-semantic-compiler-engine environment, with its
Python package importable. Missing package is BLOCKED, never a silent skip/PASS.
Does not replace producer projection, receipts, source selection or admission.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def assert_check(violations, expected, label):
    if bool(violations) != expected:
        raise AssertionError(f'{label}: violations={violations!r}, expected_violation={expected}')


def main():
    try:
        from l9_semantic_compiler.passes.validate import schema_violations
    except ImportError as exc:
        print(json.dumps({'result':'BLOCKED','reason':'REAL_COMPILER_NOT_IMPORTABLE',
                          'detail':str(exc),'not_claimed':'native schema qualification'}))
        return 2
    pro = yaml.safe_load((ROOT/'semantics/strategic_planner_value_projection.schema.yaml').read_text())
    com = yaml.safe_load((ROOT/'semantics/strategic_planner_value_composition.schema.yaml').read_text())
    model = yaml.safe_load((ROOT/'semantics/strategic_value_model.yaml').read_text())
    profile = yaml.safe_load((ROOT/'overlays/projection_profile_additions.yaml').read_text())['projection_profiles'][0]
    selected = {selector[2:]: deepcopy(model[selector[2:]]) for selector in
                profile['sources']['strategic_value_model']['selectors']}
    assert_check(schema_violations(selected,pro), False, 'complete_model_selected_payload')
    for change in (False,1):
        altered = deepcopy(selected)
        altered['valuation']['accounting_partition_contract']['normative_partition']['mutually_exclusive_booking'] = change
        assert_check(schema_violations(altered,pro), True, 'normative_boolean_cannot_flip')
    no_ids=deepcopy(selected)
    no_ids['governed_by']['invariants']=[]
    assert_check(schema_violations(no_ids,pro),True,'empty_min_items_with_array')
    terms=yaml.safe_load((ROOT/'overlays/vocabulary_additions.yaml').read_text())['terms']
    vocab={'terms':terms}
    assert_check(schema_violations(vocab,pro),False,'nested_terms_positive')
    broken=deepcopy(vocab)
    broken['terms']['strategic_value']['definition']=9
    assert_check(schema_violations(broken,pro),True,'nested_terms_malformed_definition')
    assert_check(schema_violations({'strategic_value_model':selected},com),True,
                 'composition_missing_four_namespaces')
    print(json.dumps({'result':'NATIVE_SCHEMA_DIALECT_REGRESSIONS_PASS',
                      'checks':['positive_model','false_boolean','integer_boolean',
                                'empty_min_items','positive_nested_term',
                                'malformed_nested_definition','missing_namespaces'],
                      'scope':'schema_violations_only_not_real_projections_or_receipts'},indent=2))
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(json.dumps({'result':'FAIL','exception':type(exc).__name__,'detail':str(exc)},indent=2))
        sys.exit(1)
