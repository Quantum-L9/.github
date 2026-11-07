#!/usr/bin/env python3
"""GT-core candidate preparation at exact PR #212 head only; fail closed on drift.

This script edits ONLY a local, clean, pinned .github checkout when --apply is
explicit. The GT+SV dependent overlay is NOT applied: SV is staged in PR 212
as documentation, not admitted as canonical semantics. No commit, push, PR, or admission occurs here.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import textwrap
import yaml

BASE_SHA = '85531616cee2da94bbb7154418a78537549a4d76'
CANONICAL_MAIN_SHA = '020a94bea86e7c5c5e4107da7014ec259508f397'
SV_PR_NUMBER = 212
SV_REVIEW_BLOBS = {'docs/candidates/SV/README.md': '4b1aa9496b2490d591b40e508dc4243877efb65d', 'docs/candidates/SV/overlays/projection_profile_additions.yaml': '82e063cf2e1349fc03813a060b65fe6fc75fe30b', 'docs/candidates/SV/overlays/composition_profile_additions.yaml': 'c14c27b842ef02e0abe965d4d2bbf1095629e9f8', 'docs/candidates/SV/overlays/contracts_additions.yaml': 'dec12362ec14fd06de17791d759e227a3adfbf04', 'docs/candidates/SV/overlays/invariants_additions.yaml': 'c5bdd3418bb9cc993573a87eebf29e9c405ecfb1', 'docs/candidates/SV/overlays/vocabulary_additions.yaml': 'c5f19da2b80e9f4991a158b6f1171851192429fa', 'docs/candidates/SV/semantics/strategic_value_model.yaml': '5f4ffbc1b6e4add5881f76ae3b176d4a82bbbcf6', 'docs/candidates/SV/semantics/strategic_planner_value_projection.schema.yaml': 'e702ec7f3cb26322c986eb26e917564eba5048f8', 'docs/candidates/SV/semantics/strategic_planner_value_composition.schema.yaml': '4bb57229d3ba7719a057c635b9976f80e7c3513e'}
ROOT = Path(__file__).resolve().parent
SOURCE_BLOBS = {
    'semantics/invariants.yaml': 'e864570545765a29a0af5cfcca35d3ac64841f0a',
    'semantics/contracts.yaml': '8a0d0513fcb28036682041ca8e759e31d7620f48',
    'semantics/vocabulary.yaml': '8f5d25f45b13f6bd0d40d0984dc5b311e68d8b48',
    'semantics/projection_profiles.yaml': 'c05b57cb5c725484e2214ee4b2f9069225186b0c',
    'semantics/composition_profiles.yaml': '6ee238e33e82e84d7cd6bab9f623b7670d34bcad',
    'semantics/generic_compiler_manifest.yaml': '17e99242728b2591c1dd705107cdf25ceed8e8d7',
}


def data(rel):
    return yaml.safe_load((ROOT / rel).read_text(encoding='utf-8'))


def txt(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def one(s, old, new, path):
    if s.count(old) != 1:
        raise ValueError(f'{path}: expected one exact anchor {old!r}, found {s.count(old)}')
    return s.replace(old, new, 1)


def append_top_list(s, rel, key):
    obj = yaml.safe_load(s)
    rows = data(rel)[key]
    if not isinstance(obj, dict) or not isinstance(obj.get(key), list):
        raise ValueError('invalid canonical list: '+key)
    existing = {v['id'] for v in obj[key]}
    if any(v['id'] in existing for v in rows):
        raise ValueError('identity collision in '+key)
    new = txt(rel).split(key+':\n', 1)[1]
    # The pinned file stores this top-level list as its final section.
    return s.rstrip()+'\n'+new.lstrip('\n').rstrip()+'\n'


def prepare(checkout):
    def original(path):
        return (checkout/path).read_text(encoding='utf-8')

    changed = {}
    for p in ('semantics/strategic_interaction_projection.schema.yaml',
              'semantics/strategic_interaction_composition.schema.yaml'):
        if (checkout/p).exists():
            raise ValueError(p+' already exists: re-resolve owner and target')
        changed[p] = txt(p)

    p = 'semantics/invariants.yaml'
    inv = append_top_list(original(p), 'overlays/invariants_additions.yaml', 'invariants')
    changed[p] = inv
    inv_count = len(yaml.safe_load(inv)['invariants'])
    inv_sha = hashlib.sha256(inv.encode('utf-8')).hexdigest()

    p = 'semantics/contracts.yaml'
    c = original(p)
    if not re.search(r'^  source_digest_sha256: [a-f0-9]{64}$', c, flags=re.M):
        raise ValueError('missing canonical contract source digest contract')
    c = re.sub(r'(^  source_digest_sha256: )[a-f0-9]{64}$',
               lambda m:m.group(1)+inv_sha,c,count=1,flags=re.M)
    c = re.sub(r'(^  source_invariant_count: )\d+$',
               lambda m:m.group(1)+str(inv_count),c,count=1,flags=re.M)
    changed[p] = append_top_list(c, 'overlays/contracts_gt_core.yaml', 'contracts')

    p = 'semantics/vocabulary.yaml'
    v = original(p)
    existing = set(yaml.safe_load(v)['terms'])
    incoming = set(data('overlays/vocabulary_additions.yaml')['terms'])
    if incoming & existing:
        raise ValueError('term identity collision: '+str(sorted(incoming & existing)))
    ins = txt('overlays/vocabulary_additions.yaml').split('terms:\n',1)[1]
    changed[p] = one(v,'\nrelationships:\n','\n'+ins.rstrip()+'\nrelationships:\n',p)

    p = 'semantics/projection_profiles.yaml'
    pr = original(p)
    obj = yaml.safe_load(pr)
    extras = data('overlays/projection_profile_additions.yaml')['projection_profiles']
    for x in extras:
        if x['id'] in {z['id'] for z in obj['projection_profiles']}:
            raise ValueError('profile collision: '+x['id'])
        if any(s not in obj['source_classes'] for s in x['sources']):
            raise ValueError('undeclared source class')
    pr_lines = txt('overlays/projection_profile_additions.yaml').split('projection_profiles:\n',1)[1]
    changed[p] = one(pr, '\nprojection_engine_contract_ref:\n',
                     '\n'+pr_lines.rstrip()+'\nprojection_engine_contract_ref:\n',p)

    p = 'semantics/composition_profiles.yaml'
    cp = original(p)
    cp_rows = data('overlays/composition_profile_additions.yaml')['profiles']
    cp_obj = yaml.safe_load(cp)
    if any(x['id'] in {z['id'] for z in cp_obj['profiles']} for x in cp_rows):
        raise ValueError('composition profile collision')
    # Canonical composition_profiles.yaml ends in the `profiles` list.
    if 'profiles:\n' not in cp:
        raise ValueError('missing composition list')
    new_rows = textwrap.indent(txt('overlays/composition_profile_additions.yaml').split('profiles:\n',1)[1].rstrip(), '  ')
    changed[p] = cp.rstrip()+'\n'+new_rows+'\n'

    p = 'semantics/generic_compiler_manifest.yaml'
    manifest = original(p)
    anchor = '  - pr_audit_composition.schema.yaml\n'
    lines = ('  - strategic_interaction_projection.schema.yaml\n'
             '  - strategic_interaction_composition.schema.yaml\n')
    changed[p] = one(manifest, anchor, anchor+lines, p)

    for path, value in changed.items():
        doc = yaml.safe_load(value)
        if not isinstance(doc, dict):
            raise ValueError('invalid resulting YAML: '+path)
    final_inv = {v['id'] for v in yaml.safe_load(changed['semantics/invariants.yaml'])['invariants']}
    for cc in yaml.safe_load(changed['semantics/contracts.yaml'])['contracts']:
        if cc['id']=='l9.contract/strategic-interaction-assessment@1':
            if not set(cc['source_invariants']) <= final_inv:
                raise ValueError('GT core contract references absent invariants')
    pdoc = yaml.safe_load(changed['semantics/projection_profiles.yaml'])
    for profile in pdoc['projection_profiles']:
        if profile['id']=='l9.projection/strategic-planner-interaction@1':
            for key in profile['sources']:
                if key not in pdoc['source_classes']:
                    raise ValueError('undeclared source class '+key)
    return changed, inv_count


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--checkout',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    checkout=Path(args.checkout).resolve()
    def git(*sub):
        return subprocess.run(['git','-C',str(checkout),*sub],
                              check=True,capture_output=True,text=True).stdout.strip()
    try:
        if git('rev-parse','HEAD') != BASE_SHA:
            raise ValueError('checkout HEAD does not match pinned .github SHA '+BASE_SHA)
        if git('status','--porcelain'):
            raise ValueError('checkout not clean')
        for p, expected in {**SOURCE_BLOBS, **SV_REVIEW_BLOBS}.items():
            if git('hash-object',p) != expected:
                raise ValueError('source blob differs from pinned repository: '+p)
        changes, count = prepare(checkout)
        if args.apply:
            for p, content in changes.items():
                dst=checkout/p
                dst.parent.mkdir(parents=True,exist_ok=True)
                dst.write_text(content,encoding='utf-8')
        print('STATUS='+('LOCAL_GT_CORE_WRITTEN_NOT_ADMITTED' if args.apply else 'DRY_RUN_GT_CORE_ONLY'))
        print('REVIEW_PR212_SHA='+BASE_SHA)
        print('CANONICAL_MAIN_BASE_SHA='+CANONICAL_MAIN_SHA)
        print('INVARIANT_COUNT='+str(count))
        for p in sorted(changes): print('CANDIDATE_PATH='+p)
        print('DEPENDENT_GT_SV_CONTRACT=BLOCKED_PR212_SV_IS_DOCUMENTATION_ONLY_NOT_ADMITTED')
        print('NATIVE_COMPILER_RECEIPTS=NOT_RUN')
        return 0
    except (ValueError, OSError, KeyError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
        print('BLOCKED='+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
