#!/usr/bin/env python3
"""Standalone structural and predecessor-preservation checks for a candidate ZIP.

No access to GitHub/semantic compiler is implied. This never proves admission,
source selector equivalence, producer receipts, or live consumer behavior.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, re, sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
 'gar':('gar_architecture_observer_v2','l9.projection/gar-architecture-observer@1','l9.projection/gar-architecture-observer@2','l9-global-architect','l9.projection.gar-architecture-observer/v2'),
 'planner':('strategic_planner_value_v2','l9.projection/strategic-planner-value@1','l9.projection/strategic-planner-value@2','strategic-planner','l9.projection.strategic-planner-value/v2'),
 'cursor':('cursor_governance_operating_plane_v3','l9.projection/cursor-governance-operating-plane@2','l9.projection/cursor-governance-operating-plane@3','Cursor-Governance','l9.projection.cursor-governance-operating-plane/v3')}
NEW_TERMS={'qualitative_strategic_value_screen','realized_strategic_compounding','signal','signal_propagation','signal_feedback_episode','signal_consumption'}
NEW_IDS={'L9-SVQ-001','L9-SVQ-002','L9-SIGNAL-001','L9-SIGNAL-002','L9-SIGNAL-003','L9-SIGNAL-004'}
REFS={'vocabulary':'l9.source/vocabulary@1','invariants':'l9.source/invariants@1','contracts':'l9.source/contracts@1','authority_model':'l9.source/authority-model@1','strategic_value_model':'l9.source/strategic-value-model@1','capabilities':'l9.source/capabilities@1','architecture_patterns':'l9.source/architecture-patterns@1','lifecycle':'l9.source/lifecycle@1','error_taxonomy':'l9.source/error-taxonomy@1','receipt_catalog':'l9.source/receipt-catalog@1'}
PROTO='l9.payload-validation/source-class-dispatch@1'
DIALECT='l9.schema-dialect/candidate-v2@1'
OPERATORS={'type','fields','required','additional_properties','items','min_items','const','enum'}
TYPES={'object','array','string_list','string','boolean','integer','number','null'}
FILTER_ID=re.compile(r'^\$\.(?:invariants|contracts)\[\?\(@\.id=="([^"\\]+)"\)\]$')
SELECTOR=re.compile(r'^\$\.[a-z_][a-z_0-9]*(?:\.[a-z_0-9]+|\[\*\](?:\.[a-z_0-9]+)?|\[\?\(@\.(?:id|scope)=="[a-zA-Z0-9_./@-]+"\)\])*$')

class Rejected(ValueError):pass

def req(test,why):
 if not test:raise Rejected(why)

def load(p):return yaml.safe_load(p.read_text(encoding='utf-8'))

def hash_selectors(selectors):
 return hashlib.sha256(json.dumps(selectors,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def fnv_selectors(selections):
 value=2166136261
 for s in selections:
  for char in s:
   value=((value^ord(char))*16777619)&0xffffffff
  value=(value*16777619)&0xffffffff
 return f'{value:08x}'

def descriptor(d,where):
 req(isinstance(d,dict),where+': descriptor not an object')
 req(set(d)<=OPERATORS,where+': unsupported descriptor keywords '+str(set(d)-OPERATORS))
 typ=d.get('type');req(typ in TYPES,where+': unsupported type '+str(typ))
 if typ=='object':
  req(isinstance(d.get('additional_properties'),bool),where+': implicit object openness')
  fields=d.get('fields',{});req(isinstance(fields,dict),where+': malformed fields')
  required=d.get('required',[])
  req(isinstance(required,list) and len(set(required))==len(required) and set(required)<=set(fields),where+': invalid required list')
  for k,v in fields.items():descriptor(v,where+'.'+k)
  req(set(d)<={'type','additional_properties','fields','required'},where+': stray object fields')
 elif typ=='array':
  req('items' in d,where+': item type absent')
  descriptor(d['items'],where+'[]')
  req('min_items' not in d or (isinstance(d['min_items'],int) and d['min_items']>0),where+': min_items invalid')
  req(set(d)<={'type','items','min_items'},where+': stray array fields')
 elif typ=='string_list':
  req(set(d)=={'type'},where+': string_list has unsupported keywords')
 else:
  req(set(d)<={'type','const','enum'},where+': scalar fields invalid')
  if 'enum' in d:req(isinstance(d['enum'],list) and len(d['enum'])==len(set(d['enum'])) and bool(d['enum']),where+': invalid enum')

def follow_path(des,parts,where):
 d=des
 for i,part in enumerate(parts):
  req(d.get('type')=='object',where+': parent is not object at '+'.'.join(parts[:i]))
  req(part in d.get('required',[]),where+': selected path is not required '+'.'.join(parts[:i+1]))
  req(part in d.get('fields',{}),where+': selected field untyped '+part)
  d=d['fields'][part]
 return d

def verify(root=ROOT):
 req(root.is_dir(),'Missing pack root')
 req(not (root/'patches').exists(),'Patch directory is forbidden in self-contained successor pack')
 req(not (root/'overlays').exists(),'Overlay directory is forbidden in self-contained successor pack')
 for f in ['MASTER_STRATEGIC_VALUE_INVARIANTS.md','MASTER_SIGNAL_INVARIANTS.md','SIGNAL_VOCABULARY_CANDIDATES.yaml','STRATEGIC_VALUE_VOCABULARY_CANDIDATES.yaml']:
  req(not any(p.name==f for p in root.rglob('*')),'Forbidden PR234 source copy: '+f)
 golden=load(root/'compatibility/predecessor_selection_contract.yaml')
 req(set(golden['predecessors'])==set(EXPECTED),'Three exact predecessor cases required')
 expected_files=set()
 records={}
 for mode,(name,old_id,new_id,consumer,output) in EXPECTED.items():
  f=root/'profiles'/f'{name}.profile.yaml';expected_files.add(f.relative_to(root).as_posix())
  p=load(f);records[mode]=p
  req(p.get('id')==new_id,mode+': wrong versioned identity')
  req(p.get('successor_of')==old_id,mode+': wrong predecessor')
  req(p.get('class')=='consumer' and p.get('consumer')==consumer,mode+': wrong consumer')
  req(p.get('output',{}).get('schema')==output,mode+': wrong output version')
  req(p.get('payload_validation')=={'protocol':PROTO},mode+': missing dispatch')
  req(p.get('breaking_changes',{}).get('consumer_migration')=='explicit',mode+': silent migration')
  sources=p.get('sources');req(isinstance(sources,dict) and sources,mode+': no sources')
  preserved=golden['predecessors'][mode]['source_selectors']
  req(set(preserved)<=set(sources),mode+': predecessor source class removed')
  if mode=='gar':req(set(sources)==set(preserved)|{'strategic_value_model'},'GAR exact eight source classes')
  if mode=='planner':req(set(sources)==set(preserved),'Planner exact five source classes')
  if mode=='cursor':req(set(sources)==set(preserved),'Cursor exact eight source classes')
  for cls,old in preserved.items():
   arr=sources[cls]['selectors']
   req(isinstance(arr,list) and arr,mode+'/'+cls+': empty selectors')
   req(all(isinstance(s,str) and SELECTOR.fullmatch(s) for s in arr),mode+'/'+cls+': unsupported selector expression')
   req(len(set(arr))==len(arr),mode+'/'+cls+': duplicate selector')
   n=old['count']
   req(hash_selectors(arr[:n])==old['selector_sha256'],mode+'/'+cls+': predecessor selector order/meaning changed')
   req(fnv_selectors(arr[:n])==old['remote_fingerprint_fnv1a32'],mode+'/'+cls+': independently observed remote fingerprint mismatch')
  for cls,doc in sources.items():
   req(cls in REFS,mode+': unknown source class '+cls)
   arr=doc.get('selectors',[])
   req(isinstance(arr,list) and len(arr)==len(set(arr)) and all(SELECTOR.fullmatch(s) for s in arr),mode+': selector invalid '+cls)
  selected_terms={s[8:] for s in sources['vocabulary']['selectors'] if s.startswith('$.terms.')}
  selected_ids={m.group(1) for s in sources['invariants']['selectors'] if (m:=FILTER_ID.fullmatch(s))}
  req(NEW_TERMS<=selected_terms and NEW_IDS<=selected_ids,mode+': incomplete six+six candidate selection')
  if mode=='cursor':
   req('$.invariants[?(@.scope=="global")]' in sources['invariants']['selectors'],mode+': original global invariant filter missing')
   req('$.contracts[*]' in sources['contracts']['selectors'],mode+': original complete contract selection missing')
   req('skill_command_or_routing_semantics' in p['forbidden'],mode+': skill routing grant guard absent')
  if mode=='planner':
   req('$.counterfactual_mathematics' in sources['strategic_value_model']['selectors'],mode+': predecessor math erased')
   req('$.valuation' in sources['strategic_value_model']['selectors'],mode+': original valuation erased')
   req(any('strategic-value-assessment@1' in x for x in sources['contracts']['selectors']),mode+': numerical contract absent')
  req('execution_publication_or_merge_authority_grant' in p['forbidden'],mode+': action/merge authority fence absent')
  contract_file=root/'consumer-contracts'/f'{name}.consumer.contract.yaml';expected_files.add(contract_file.relative_to(root).as_posix())
  contract=load(contract_file)
  req(contract.get('subject_profile')==new_id and contract.get('status')=='proposed_non_authoritative',mode+': consumer contract not bound')
  req(contract.get('verification_status')=='consumer_replay_not_executed',mode+': invented live consumer proof')
  kinds=['projection'] if mode=='cursor' else ['projection','composition']
  for kind in kinds:
   sf=root/'schemas'/f'{name}.{kind}.schema.yaml';expected_files.add(sf.relative_to(root).as_posix())
   schema=load(sf)
   req(schema.get('schema')=='l9.source-class-payload-schema/v1',sf.name+': not modern source-class schema')
   req(schema.get('document_kind')==kind+'_payload_schema',sf.name+': wrong kind')
   req(schema.get('payload_validation')=={'protocol':PROTO} and schema.get('descriptor_dialect')==DIALECT,sf.name+': dispatch/dialect missing')
   req(schema.get('canonical') is True and schema.get('authority',{}).get('owner')=='Quantum-L9/.github',sf.name+': desired target ownership incorrect')
   req(schema.get('governed_by',{}).get('projection_profile_ref')==new_id,sf.name+': wrong profile reference')
   expected_out=output if kind=='projection' else ('l9.composed-projection.gar-architecture-observer/v1' if mode=='gar' else 'l9.composed-projection.strategic-planner-value/v2')
   req(schema.get('schema_id')==expected_out,sf.name+': output schema ID misbound')
   req('properties' not in schema and 'type' not in schema,sf.name+': legacy global union schema not allowed')
   shapes=schema.get('source_shapes',[])
   req([s['source_class'] for s in shapes]==list(sources),sf.name+': missing/extra/reordered source shapes')
   for shape in shapes:
    cls=shape['source_class'];req(shape.get('source_ref')==REFS[cls],sf.name+': wrong registered source class')
    d=shape['descriptor'];descriptor(d,sf.name+'/'+cls)
    sels=sources[cls]['selectors']
    if cls=='vocabulary':
     terms=follow_path(d,['terms'],sf.name)
     names={s[8:] for s in sels}
     req(set(terms['required'])==names and set(terms['fields'])==names,sf.name+': selected terms lost or fabricated')
     for key in names:
      t=terms['fields'][key]
      req({'semantic_class','definition'}<=set(t.get('required',[])),sf.name+': basic vocab definition absent '+key)
      if key in NEW_TERMS:req('question' in t.get('required',[]),sf.name+': new term question missing '+key)
    elif cls in ('invariants','contracts'):
     lst=follow_path(d,[cls],sf.name)
     req(lst.get('type')=='array' and lst['items'].get('type')=='object',sf.name+': no structured records')
     req('id' in lst['items'].get('required',[]),sf.name+': record identity absent')
     is_bulk=any('[*]' in s or '@.scope==' in s for s in sels)
     if not is_bulk:
      wanted={m.group(1) for s in sels if (m:=FILTER_ID.fullmatch(s))}
      req(set(lst['items']['fields']['id'].get('enum',[]))==wanted,sf.name+': ID selection mismatch')
     req('min_items' in lst,sf.name+': no nonempty record guard')
    else:
     for selector in sels:
      x=selector[2:]
      if '[*]' in x:x=x.split('[*]',1)[0]
      if '[?' in x:x=x.split('[?',1)[0]
      follow_path(d,x.split('.'),sf.name)
  if mode!='cursor':
   cf=root/'compositions'/f'{name}.composition.yaml';expected_files.add(cf.relative_to(root).as_posix())
   c=load(cf)
   correct='l9.compose/gar-architecture-observer@1' if mode=='gar' else 'l9.compose/strategic-planner-value@2'
   req(c['id']==correct and c['composes']['projection_profile']==new_id,mode+': wrong full composer')
   if mode=='planner':req(c.get('successor_of')=='l9.compose/strategic-planner-value@1',mode+': composition predecessor absent')
   req(c.get('payload_validation')=={'protocol':PROTO},mode+': compose dispatch absent')
   req(c.get('merge_strategy')=={'placement':'source_class_namespace','source_coverage':'exact','duplicate_source':'conflict','semantic_identity_collision':'require_equivalence'},mode+': unsafe composition')
   req(c.get('conflict_result')=='invalid',mode+': unknown conflict fail-state')
   req(c.get('required_provenance')==['source_projection_refs','source_projection_digests','composition_profile_ref','composition_profile_digest'],mode+': incomplete provenance')
   req(c['output']['schema']==('l9.composed-projection.gar-architecture-observer/v1' if mode=='gar' else 'l9.composed-projection.strategic-planner-value/v2'),mode+': wrong compose schema')
 req(not list((root/'compositions').glob('*cursor*')),'Cursor was not given an unsolicited composed profile')
 binding=load(root/'SOURCE_BINDING.yaml')
 req(binding['canonical_comparison']['revision']=='dc96a8ae9f31e359bb0e52a0b1d778fc8f265d99','binding baseline changed')
 req(binding['pr234']['head_revision']=='28304c31bae83a1bfc450993029d5d07e180560b','PR234 donor identity changed')
 req(set(binding['pr234']['candidate_invariants'])==NEW_IDS and set(binding['pr234']['candidate_terms'])==NEW_TERMS,'donor semantic identity changed')
 req(binding['admission_status']=='PENDING' and binding['compiler_status']=='NOT_EXECUTED','fabricated authority or compile')
 manifests=[p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()]
 req(set(manifests)>=expected_files,'standalone files missing')
 return {'status':'LOCAL_STRUCTURAL_CHECK_PASS','profiles':{k:records[k]['id'] for k in EXPECTED},'composer_count':2,
         'profile_count':3,'source_class_schema_count':5,'consumer_contract_count':3,'predecessor_sel_counts':{mode:sum(rec['count'] for rec in golden['predecessors'][mode]['source_selectors'].values()) for mode in EXPECTED},
         'invariant_candidates':len(NEW_IDS),'vocabulary_candidates':len(NEW_TERMS),'canonical_compiler':'NOT_EXECUTED',
         'admission':'PENDING','consumer_replay':'NOT_EXECUTED'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);args=p.parse_args()
 try:print(json.dumps(verify(args.root),indent=2,sort_keys=True))
 except Exception as e:print('REJECTED:',str(e),file=sys.stderr);sys.exit(2)
