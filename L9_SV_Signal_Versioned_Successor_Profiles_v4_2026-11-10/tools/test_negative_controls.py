#!/usr/bin/env python3
"""Negative structural probes. Does not simulate a semantic compiler or consumer."""
from __future__ import annotations
import tempfile, shutil, sys
from pathlib import Path
import yaml
from validate_successors import ROOT,verify,Rejected

GAR='profiles/gar_architecture_observer_v2.profile.yaml'
PLANNER='profiles/strategic_planner_value_v2.profile.yaml'
CURSOR='profiles/cursor_governance_operating_plane_v3.profile.yaml'
GSC='schemas/gar_architecture_observer_v2.projection.schema.yaml'
PSC='schemas/strategic_planner_value_v2.projection.schema.yaml'
CSC='schemas/cursor_governance_operating_plane_v3.projection.schema.yaml'
GC='compositions/gar_architecture_observer_v2.composition.yaml'
PC='compositions/strategic_planner_value_v2.composition.yaml'
BIN='SOURCE_BINDING.yaml'
CON='consumer-contracts/strategic_planner_value_v2.consumer.contract.yaml'
SEL='compatibility/predecessor_selection_contract.yaml'

def edit(root,path,mutator):
 p=root/path;v=yaml.safe_load(p.read_text(encoding='utf-8'));mutator(v)
 p.write_text(yaml.safe_dump(v,sort_keys=False),encoding='utf-8')

def del_first(d,cls):d['sources'][cls]['selectors'].pop(0)

def del_new_term(d):d['sources']['vocabulary']['selectors'].remove('$.terms.signal_consumption')

def del_new_id(d):d['sources']['invariants']['selectors'].remove('$.invariants[?(@.id=="L9-SIGNAL-004")]')

def altered_source_ref(d):d['source_shapes'][0]['source_ref']='l9.source/invariants@1'

def remove_shape(d):d['source_shapes'].pop()

def drop_question(d):
 term=d['source_shapes'][0]['descriptor']['fields']['terms']['fields']['signal_consumption'];term['required'].remove('question')

def drop_id(d):
 for s in d['source_shapes']:
  if s['source_class']=='invariants':
   s['descriptor']['fields']['invariants']['items']['required'].remove('id');break

def duplicate_selector(d):d['sources']['vocabulary']['selectors'].append(d['sources']['vocabulary']['selectors'][-1])

def bad_composition(d):d['merge_strategy']['duplicate_source']='keep_last'

def bad_protocol(d):d['payload_validation']['protocol']='unknown_protocol'

def do_one(label,path,fn):
 with tempfile.TemporaryDirectory(prefix='sv-signal-neg-') as temp:
  root=Path(temp)/'pack'
  shutil.copytree(ROOT,root)
  if path is None:fn(root)
  else:edit(root,path,fn)
  try:verify(root)
  except (Rejected, KeyError, ValueError, TypeError, FileNotFoundError, yaml.YAMLError) as e:
   print('REJECTED',label,':',str(e)[:125]);return
  raise AssertionError('FAILED TO REJECT negative control: '+label)

tests=[
 ('dropped predecessor GAR term',GAR,lambda d:del_first(d,'vocabulary')),
 ('dropped predecessor GAR invariant wildcard',GAR,lambda d:del_first(d,'invariants')),
 ('dropped predecessor Planner numeric model field',PLANNER,lambda d:del_first(d,'strategic_value_model')),
 ('dropped predecessor Cursor complete contract field',CURSOR,lambda d:d['sources']['contracts']['selectors'].remove('$.contracts[*]')),
 ('lost candidate signal term',GAR,del_new_term),
 ('lost candidate invariant',PLANNER,del_new_id),
 ('swapped successor consumer',GAR,lambda d:d.__setitem__('consumer','other-agent')),
 ('old projection identity',PLANNER,lambda d:d.__setitem__('id','l9.projection/strategic-planner-value@1')),
 ('wrong predecessor reference',CURSOR,lambda d:d.__setitem__('successor_of','l9.projection/cursor-governance-operating-plane@1')),
 ('wrong output version',GAR,lambda d:d['output'].__setitem__('schema','l9.projection.gar-architecture-observer/v1')),
 ('missing producer dispatch',PLANNER,lambda d:d.pop('payload_validation')),
 ('duplicate source selector',CURSOR,duplicate_selector),
 ('wrong source class owner',GSC,altered_source_ref),
 ('missing source descriptor',PSC,remove_shape),
 ('missing question on new term',CSC,drop_question),
 ('invariant records without ID',GSC,drop_id),
 ('legacy union schema',GSC,lambda d:d.__setitem__('type','object')),
 ('wrong schema identity',PSC,lambda d:d.__setitem__('schema_id','l9.projection.strategic-planner-value/v1')),
 ('wrong schema protocol',CSC,bad_protocol),
 ('unsafe duplicate precedence',GC,bad_composition),
 ('missing composition provenance',PC,lambda d:d['required_provenance'].pop()),
 ('missing composition dispatch',PC,lambda d:d.pop('payload_validation')),
 ('changed donor PR identity',BIN,lambda d:d['pr234'].__setitem__('head_revision','bad')),
 ('fake admission assertion',BIN,lambda d:d.__setitem__('admission_status','ADMITTED')),
 ('fake compiler run',BIN,lambda d:d.__setitem__('compiler_status','PASS')),
 ('false consumer replay proof',CON,lambda d:d.__setitem__('verification_status','consumer_replay_pass')),
 ('tampered remote comparator',SEL,lambda d:d['predecessors']['gar']['source_selectors']['vocabulary'].__setitem__('remote_fingerprint_fnv1a32','deadbeef')),
 ('new patch folder',None,lambda root:(root/'patches').mkdir()),
 ('injected copy of immutable invariant source',None,lambda root:(root/'MASTER_SIGNAL_INVARIANTS.md').write_text('invented')),
]

def run():
 verify(ROOT)
 for label,path,fn in tests:do_one(label,path,fn)
 print(f'PASS {len(tests)}/{len(tests)} structural negative controls; no real compiler or runtime claims')

if __name__=='__main__':
 try:run()
 except Exception as e:print('FAIL',e,file=sys.stderr);sys.exit(1)
