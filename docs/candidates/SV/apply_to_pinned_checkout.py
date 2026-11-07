#!/usr/bin/env python3
"""Prepare the proposed Strategic Value canonical files in a CLEAN pinned local checkout.

This edits local files only under explicit --apply. It NEVER commits, pushes,
opens PRs, runs release gates, or admits semantics.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import yaml

BASE_SHA = '020a94bea86e7c5c5e4107da7014ec259508f397'
ROOT = Path(__file__).resolve().parent


def one(text, anchor, replacement, path):
    if text.count(anchor) != 1:
        raise ValueError(f'{path}: expected one anchor {anchor!r}, found {text.count(anchor)}')
    return text.replace(anchor, replacement, 1)


def raw(name):
    return (ROOT / name).read_text(encoding='utf-8')


def merge_list(base, extra, list_name):
    old = yaml.safe_load(base)
    new = yaml.safe_load(extra)
    seen = {x['id'] for x in old[list_name]}
    inc = new[list_name]
    if any(x['id'] in seen for x in inc):
        raise ValueError(f'duplicate {list_name} identity')
    return base.rstrip() + '\n' + extra.split(list_name + ':', 1)[1].lstrip('\n').rstrip() + '\n'


def generate(checkout):
    changed = {}
    def current(path):
        return (checkout / path).read_text(encoding='utf-8')

    model_path = 'semantics/strategic_value_model.yaml'
    if (checkout / model_path).exists():
        raise ValueError('strategic_value_model already exists; re-resolve current authority')
    changed[model_path] = raw('semantics/strategic_value_model.yaml')

    p = 'semantics/invariants.yaml'
    inv = merge_list(current(p), raw('overlays/invariants_additions.yaml'), 'invariants')
    changed[p] = inv
    inv_count = len(yaml.safe_load(inv)['invariants'])
    inv_digest = hashlib.sha256(inv.encode('utf-8')).hexdigest()

    p = 'semantics/contracts.yaml'
    c = current(p)
    c = re.sub(r'(source_digest_sha256: )([a-f0-9]{64})', r'\g<1>' + inv_digest, c, count=1)
    c = re.sub(r'(source_invariant_count: )([0-9]+)', r'\g<1>' + str(inv_count), c, count=1)
    changed[p] = merge_list(c, raw('overlays/contracts_additions.yaml'), 'contracts')

    p = 'semantics/vocabulary.yaml'
    v = current(p)
    existing = set(yaml.safe_load(v)['terms'])
    items = yaml.safe_load(raw('overlays/vocabulary_additions.yaml'))['terms']
    if existing.intersection(items):
        raise ValueError('canonical vocabulary term collision: ' + str(sorted(existing.intersection(items))))
    terms_text = raw('overlays/vocabulary_additions.yaml').split('terms:\n', 1)[1]
    changed[p] = one(v, '\nrelationships:\n', '\n' + terms_text.rstrip() + '\nrelationships:\n', p)

    p = 'semantics/canonical_sources.yaml'
    s = current(p)
    new_source = ('- id: l9.source/strategic-value-model@1\n'
                  '  path: semantics/strategic_value_model.yaml\n'
                  '  format: yaml\n'
                  '  canonical: true\n'
                  '  projection_allowed: true\n'
                  '  derivation_allowed: false\n')
    if 'l9.source/strategic-value-model@1' in s:
        raise ValueError('source already exists')
    changed[p] = one(s, '\nrules:\n', '\n' + new_source + 'rules:\n', p)

    p = 'semantics/generic_compiler_manifest.yaml'
    s = current(p)
    s = one(s, '  - strategic_plan_model.yaml\n',
            '  - strategic_plan_model.yaml\n  - strategic_value_model.yaml\n', p)
    s = one(s, '  - pr_audit_composition.schema.yaml\n',
            '  - pr_audit_composition.schema.yaml\n'
            '  - strategic_planner_value_projection.schema.yaml\n'
            '  - strategic_planner_value_composition.schema.yaml\n', p)
    changed[p] = s

    p = 'semantics/projection_profiles.yaml'
    s = current(p)
    pr = yaml.safe_load(s)
    if 'strategic_value_model' in pr['source_classes'] or any(x['id'] == 'l9.projection/strategic-planner-value@1' for x in pr['projection_profiles']):
        raise ValueError('projection already exists')
    profile_file = raw('overlays/projection_profile_additions.yaml')
    source_part, profile_part = profile_file.split('projection_profiles:\n', 1)
    src_block = source_part.split('source_classes:\n', 1)[1]
    s = one(s, '\nprojection_profiles:\n', '\n' + src_block + 'projection_profiles:\n', p)
    changed[p] = one(s, '\nprojection_engine_contract_ref:\n',
                     '\n' + profile_part.rstrip() + '\nprojection_engine_contract_ref:\n', p)
    # The composition profile belongs in the canonical compiler catalog, not
    # in the projection profile or a second runtime-owned registry.
    p = 'semantics/composition_profiles.yaml'
    comp = yaml.safe_load(current(p))
    addition = yaml.safe_load(raw('overlays/composition_profile_additions.yaml'))['profiles']
    if len(addition) != 1 or any(x['id'] == addition[0]['id'] for x in comp['profiles']):
        raise ValueError('composition profile collision or invalid overlay')
    comp_block = raw('overlays/composition_profile_additions.yaml').split('profiles:\n', 1)[1].rstrip()
    new_comp = current(p).rstrip() + '\n' + '\n'.join('  ' + line if line else line for line in comp_block.splitlines()) + '\n'
    changed[p] = new_comp

    for schema_name in ('strategic_planner_value_projection.schema.yaml',
                        'strategic_planner_value_composition.schema.yaml'):
        dest = 'semantics/' + schema_name
        if (checkout / dest).exists():
            raise ValueError('schema collision: ' + dest)
        changed[dest] = raw(dest)

    for path, content in changed.items():
        obj = yaml.safe_load(content)
        if obj is None or not isinstance(obj, dict):
            raise ValueError(f'bad YAML: {path}')
    profiles = yaml.safe_load(changed['semantics/projection_profiles.yaml'])
    candidates = [x for x in profiles['projection_profiles'] if x['id'] == 'l9.projection/strategic-planner-value@1']
    if len(candidates) != 1:
        raise ValueError('profile generation failed')
    for source_class in candidates[0]['sources']:
        if source_class not in profiles['source_classes']:
            raise ValueError('unregistered projection source class ' + source_class)
    composer = yaml.safe_load(changed['semantics/composition_profiles.yaml'])
    selected = [x for x in composer['profiles'] if x['id'] == 'l9.compose/strategic-planner-value@1']
    if len(selected) != 1 or selected[0]['composes']['projection_profile'] != candidates[0]['id']:
        raise ValueError('composition profile missing or not bound to projection profile')
    if selected[0]['output']['schema'] != 'l9.composed-projection.strategic-planner-value/v1':
        raise ValueError('composition output schema mismatch')
    manifest = yaml.safe_load(changed['semantics/generic_compiler_manifest.yaml'])
    for name in ('strategic_planner_value_projection.schema.yaml',
                 'strategic_planner_value_composition.schema.yaml'):
        if name not in manifest['requires']['artifact_schemas']:
            raise ValueError('schema missing from canonical compiler schema inventory: ' + name)
    schema = yaml.safe_load(changed['semantics/strategic_planner_value_projection.schema.yaml'])
    if schema['properties']['schema']['const'] != candidates[0]['output']['schema']:
        raise ValueError('projection schema const does not match profile')
    return changed, inv_count


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--checkout', required=True)
    a.add_argument('--apply', action='store_true')
    args = a.parse_args()
    checkout = Path(args.checkout).resolve()
    def git(*cmd):
        return subprocess.run(['git', '-C', str(checkout), *cmd], capture_output=True, text=True, check=True).stdout.strip()
    try:
        actual = git('rev-parse', 'HEAD')
        if actual != BASE_SHA:
            raise ValueError(f'wrong target HEAD: {actual}; expected {BASE_SHA}')
        if git('status', '--porcelain'):
            raise ValueError('working tree not clean')
        proposed, inv_count = generate(checkout)
        if args.apply:
            for rel, content in proposed.items():
                dst = checkout / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(content, encoding='utf-8')
        print('STATUS=' + ('LOCAL_FILES_WRITTEN_NOT_ADMITTED' if args.apply else 'DRY_RUN_ONLY'))
        print('BASE_SHA=' + actual)
        print('INVARIANT_COUNT=' + str(inv_count))
        for path in sorted(proposed):
            print('PATH=' + path)
        print('REQUIRES=canonical collision review, target native validation, release manifest, protected publication, admission')
        return 0
    except (ValueError, OSError, KeyError, yaml.YAMLError, subprocess.CalledProcessError) as exc:
        print('BLOCKED=' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
