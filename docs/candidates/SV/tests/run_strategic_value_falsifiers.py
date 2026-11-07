#!/usr/bin/env python3
"""Minimal executable falsification witnesses for the safeguards formerly
proposed as L9-SV-015..020 and now carried by the Strategic Value model and
assessment contract under the twelve selected governing invariants.

The case IDs keep the historical candidate lineage for traceability; they are
not canonical invariant references. Not a production evaluator, numerical
solver, causal model, or admission proof.
The positive result means only that THIS finite witness is not contradicted.
Run: python tests/run_strategic_value_falsifiers.py [--case SV015]
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _ref(value):
    return isinstance(value, str) and bool(value.strip())


def diagnose(case_id, input_data):
    """Return first discriminating violation code, or DECLARATION_NOT_FALSIFIED."""
    x=input_data
    if case_id == 'SV015':
        comparable=(x['intervention_initial']==x['baseline_initial'] and
                    x['intervention_context']==x['baseline_context'])
        if not comparable and not _ref(x.get('reviewed_adjustment_ref')):
            return 'UNIDENTIFIED_COUNTERFACTUAL'
    elif case_id == 'SV016':
        if x['objective_scope'].startswith('focal:') and not _ref(x.get('authorized_aggregation_ref')):
            if any(e['actor'] not in x['allowed_actor_refs'] for e in x['utility_entries']):
                return 'UNAUTHORIZED_ACTOR_AGGREGATION'
        if sum(e['delta'] for e in x['utility_entries'])!=x['reported_total']:
            return 'UNAUTHORIZED_ACTOR_AGGREGATION'
    elif case_id == 'SV017':
        if any(row['observation_available_time']>row['action_time'] for row in x['decisions']):
            return 'FUTURE_OBSERVATION_LEAK'
    elif case_id == 'SV018':
        if (sum(a['capacity_required'] for a in x['actions'])>x['joint_capacity'] or
            not _ref(x.get('independence_validation_ref'))):
            if x['reported_joint_value']==sum(a['standalone_value'] for a in x['actions']):
                return 'UNJUSTIFIED_JOINT_ADDITIVITY'
    elif case_id == 'SV019':
        if x['result_shape']=='unique_winner':
            chosen=x.get('preferred_action')
            if not _ref(chosen) or any(any(v>scenario[chosen] for k,v in scenario.items()
                if k!='scenario' and k!=chosen) for scenario in x['admissible_scenarios']):
                return 'UNSUPPORTED_PRECISE_WINNER'
    elif case_id == 'SV020':
        if x['assurance_level']=='independently_verified':
            if not all(_ref(x.get(k)) for k in
                ('executed_method_ref','model_validation_evidence_ref','independent_review_ref')):
                return 'UNSUPPORTED_VERIFIED_METHOD_CLAIM'
    else:
        raise ValueError(f'unknown falsification case {case_id}')
    return 'DECLARATION_NOT_FALSIFIED'


def run(fixtures, only_case=None):
    cases=fixtures['cases']
    if only_case:
        cases=[c for c in cases if c['case_id']==only_case]
    if not cases or len({c['case_id'] for c in cases})!=len(cases):
        raise ValueError('no unique, matching cases')
    receipts=[]
    for c in cases:
        negative=diagnose(c['case_id'], copy.deepcopy(c['negative']))
        control=diagnose(c['case_id'], copy.deepcopy(c['positive']))
        passed=(negative==c['expected_failure'] and control=='DECLARATION_NOT_FALSIFIED')
        # Lineage-safe descriptor: the origin is a historical candidate ID,
        # never a claim that a canonical invariant of that ID exists.
        receipts.append({'case_id':c['case_id'],'origin_candidate_id':c['origin_candidate_id'],
                         'disposition':c['disposition'],
                         'governing_invariants':list(c['governing_invariants']),
                         'contract_obligation':c['contract_obligation'],
                         'negative_result':negative,'expected_failure':c['expected_failure'],
                         'positive_control_result':control,'pass':passed})
    return {'schema':'l9.strategic-value-falsification-result/v1',
            'assurance':'LOCAL_CONTRACT_FALSIFICATION_ONLY_NOT_NUMERICAL_VALIDATION',
            'result':'PASS' if all(r['pass'] for r in receipts) else 'FAIL',
            'cases':receipts}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',choices=[f'SV{x:03d}' for x in range(15,21)])
    parser.add_argument('--fixture',default=str(ROOT/'falsification_cases.json'))
    args=parser.parse_args()
    cases=json.loads(Path(args.fixture).read_text(encoding='utf-8'))
    result=run(cases,args.case)
    print(json.dumps(result,indent=2))
    return 0 if result['result']=='PASS' else 2

if __name__=='__main__':
    raise SystemExit(main())
