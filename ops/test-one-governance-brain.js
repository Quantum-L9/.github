'use strict';

/**
 * Cutover gate: organization governance policy is interpreted in exactly one
 * place (docs/adr/0001-one-governance-brain.md; GOV-001, GOV-002; AC-ARCH-001,
 * AC-ARCH-002).
 *
 * No workflow, shell script, or Makefile target may resolve repo classes, read
 * the policy files, compute waivers or managed sets, or parse the label
 * taxonomy itself. They reach policy only through the compiler
 * (ops/compile-repo-governance.js) and its adapter (ops/plan-adapter.js).
 *
 * Allowed: the compiler, its primitives (ops/*.js modules), tests, and docs.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-one-governance-brain.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

// Direct policy interpretation: class resolution, policy reads, waiver or
// managed-set logic, taxonomy parsing — the 15-verification search gate.
const SHADOW = [
  /\bclassForRepo\(/,
  /\bresolveProfile\(/,
  /\bapplyProfile\(/,
  /\bbuildSeedPayload\(/,
  /\bcollectSeedFiles\(/,
  /\bwaivesMandatoryFile\(/,
  /\bparseClassMarker\(/,
  /\bloadRepoClasses\(/,
  /\bparseLabels\(/,
  /mandatory_files_waive/,
  /MANAGED\s*=\s*\{/,
  /policies\/(repo-classes|repo-settings|mandatory-files)\.yml['"`]/,
  /\.github\/labels\.yml['"`]/,
  /repo-class-profile\.js/,
  /label-taxonomy\.js/,
];

function operationalFiles() {
  const out = [];
  const add = (dir, filter) => {
    const abs = path.join(root, dir);
    if (!fs.existsSync(abs)) return;
    for (const name of fs.readdirSync(abs)) {
      if (filter(name)) out.push(path.join(dir, name));
    }
  };
  add('.github/workflows', (n) => /\.ya?ml$/.test(n));
  add('scripts', (n) => /\.(sh|js)$/.test(n));
  // Shell entry points under ops/ are operational; ops/*.js are primitives
  // and adapters, and ops/test-* are tests.
  add('ops', (n) => n.endsWith('.sh') && !n.startsWith('test-') && n !== 'validate-starters.sh');
  out.push('Makefile');
  return out;
}

// Comment lines explain the contract and may name what they no longer do.
const code = (text) =>
  text
    .split('\n')
    .filter((l) => !/^\s*(#|\/\/|\*)/.test(l))
    .join('\n');

const hits = [];
for (const rel of operationalFiles()) {
  const text = code(fs.readFileSync(path.join(root, rel), 'utf8'));
  for (const re of SHADOW) {
    const m = text.match(re);
    if (m) hits.push(`${rel}: ${m[0]}`);
  }
}
assert.deepStrictEqual(hits, [], `shadow policy interpreters outside the compiler:\n  ${hits.join('\n  ')}`);
console.log(`ok: ${operationalFiles().length} workflows/scripts interpret no policy outside the compiler`);

// Every workflow that governs a repository reaches policy through the adapter.
for (const wf of [
  'auto-seed-new-repo.yml',
  'seed-governance.yml',
  'repo-birth-bootstrap.yml',
  'sync-labels-all.yml',
  'enforce-policies.yml',
  'continuous-sync.yml',
]) {
  const text = fs.readFileSync(path.join(root, '.github/workflows', wf), 'utf8');
  assert.match(text, /require\('\.\/ops\/plan-adapter\.js'\)/, `${wf} must consume the compiled plan`);
}
console.log('ok: every class-aware governance workflow consumes the compiled plan');

// One targeted front door (GOV-021, AC-ARCH-003): the Makefile exposes one
// targeted birth action and no direct targeted seed entry point.
const makefile = fs.readFileSync(path.join(root, 'Makefile'), 'utf8');
const targeted = [...makefile.matchAll(/^([a-z-]+):.*##.*REPO=/gm)].map((m) => m[1]);
assert.ok(targeted.includes('birth'), 'Makefile exposes `birth`');
assert.ok(!targeted.includes('birth-seed') && !targeted.includes('birth-bootstrap'), `legacy targeted entry points remain: ${targeted}`);
console.log('ok: the Makefile exposes one targeted governance front door (make birth)');
