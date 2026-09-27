'use strict';

/**
 * Dogfood guard: every label this repository's own configuration applies or
 * depends on must be declared in `.github/labels.yml`.
 *
 * GitHub drops, without an error, an issue-form or Dependabot label that does
 * not exist in the repository, so a reference to an undeclared name is a label
 * that silently never lands — in this repo, and in every repo that inherits or
 * is seeded with these files. Before this test the org's own forms applied
 * `bug`, `triage`, `ci-failure`, `enhancement`, `governance` and `violation`,
 * none of them in the taxonomy (issue #132).
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-label-references.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { parseLabels } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const exists = (rel) => fs.existsSync(path.join(root, rel));
const declared = new Set(parseLabels(read('.github/labels.yml')).map((l) => l.name));

/** @type {Array<[string, string]>} [label, where] */
const refs = [];
const add = (label, where) => refs.push([label.trim(), where]);
/** Strip one pair of surrounding quotes (YAML scalar) — no regex backtracking. */
const unquote = (v) => {
  const t = v.trim();
  return /^(["']).*\1$/.test(t) ? t.slice(1, -1) : t;
};

// Issue forms: this repo's, the root copy, and the copies seeded to consumers.
for (const dir of ['.github/ISSUE_TEMPLATE', 'ISSUE_TEMPLATE', 'templates/issue-templates']) {
  if (!exists(dir)) continue;
  for (const f of fs.readdirSync(path.join(root, dir)).filter((n) => /\.ya?ml$/.test(n))) {
    const m = read(`${dir}/${f}`).match(/^labels:\s*\[([^\]]*)\]/m);
    if (!m) continue;
    for (const q of m[1].matchAll(/"([^"]+)"|'([^']+)'/g)) add(q[1] || q[2], `${dir}/${f}`);
  }
}

// Dependabot: list items under any `labels:` key.
for (const f of ['.github/dependabot.yml', 'templates/dependabot.yml']) {
  if (!exists(f)) continue;
  const lines = read(f).split('\n');
  for (let i = 0; i < lines.length; i++) {
    const key = lines[i].match(/^(\s*)labels:\s*$/);
    if (!key) continue;
    for (let j = i + 1; j < lines.length; j++) {
      const text = lines[j].trim();
      if (!text.startsWith('-') || lines[j].search(/\S/) <= key[1].length) break;
      add(unquote(text.slice(1)), f);
    }
  }
}

// Stale: the labels it filters on, exempts, and applies.
const stale = read('.github/workflows/stale.yml');
for (const key of [
  'only-labels',
  'exempt-issue-labels',
  'exempt-pr-labels',
  'stale-issue-label',
  'stale-pr-label',
]) {
  const line = stale
    .split('\n')
    .map((l) => l.trim())
    .find((l) => l.startsWith(`${key}:`));
  if (line)
    for (const l of unquote(line.slice(key.length + 1)).split(',')) add(l, `stale.yml ${key}`);
}

// PR labeler: every top-level key is a label it applies.
for (const m of read('.github/labeler.yml').matchAll(/^["']?([^\s#"'][^:"']*)["']?:\s*$/gm)) {
  add(m[1], '.github/labeler.yml');
}

// Workflows: literal labels passed to the issues API. Interpolated names
// (`sev:${key}`) are checked as families below.
const wfDir = '.github/workflows';
for (const f of fs.readdirSync(path.join(root, wfDir)).filter((n) => n.endsWith('.yml'))) {
  const text = read(`${wfDir}/${f}`);
  for (const m of text.matchAll(/\blabels:\s*(?:\[\s*)?'([^'$`]+)'/g)) add(m[1], `${wfDir}/${f}`);
  for (const m of text.matchAll(/\badd\.add\('([^'$`]+)'\)/g)) add(m[1], `${wfDir}/${f}`);
}
// issue-triage.yml / governance-issue.yml build `sev:S<n>` and
// `priority:P<n>` from the form's severity; both families must be whole.
for (const l of [
  'sev:S1',
  'sev:S2',
  'sev:S3',
  'sev:S4',
  'priority:P0',
  'priority:P1',
  'priority:P2',
  'priority:P3',
]) {
  add(l, 'issue-triage.yml / governance-issue.yml (derived)');
}

assert.ok(refs.length > 20, `expected to find label references, found ${refs.length}`);
const missing = refs.filter(([l]) => !declared.has(l));
assert.deepStrictEqual(
  missing.map(([l, where]) => `${l}  (${where})`),
  [],
  'every label this repo applies or depends on must be declared in .github/labels.yml',
);

// The seeded copy of the taxonomy is the org copy — consumers must not get a
// different label set than the one this repo carries.
assert.strictEqual(read('templates/labels.yml'), read('.github/labels.yml'));

console.log(
  `ok: all ${refs.length} label references in this repo's own config are declared (${declared.size} labels)`,
);
console.log('ok: templates/labels.yml is byte-identical to .github/labels.yml');
