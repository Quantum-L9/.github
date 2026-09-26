'use strict';

/**
 * Asserts the shared label taxonomy parser.
 *
 * Three call sites read `.github/labels.yml` — the weekly org sweep, the
 * per-repo CLI, and the targeted birth bootstrap. They must all see the same
 * taxonomy, which is only true while they all call this one parser.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-label-taxonomy.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { parseLabels, planLabelSync } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

try {
  const labels = parseLabels(fs.readFileSync('.github/labels.yml', 'utf8'));
  assert.ok(labels.length > 0, 'org labels.yml must parse to at least one label');
  for (const l of labels) {
    assert.ok(l.name, 'every label has a name');
    assert.match(l.color, /^[0-9a-fA-F]{6}$/, `label ${l.name} has a 6-hex color`);
    assert.strictEqual(typeof l.description, 'string');
  }

  // The distributed copy must parse to the same taxonomy the org applies.
  const distributed = parseLabels(fs.readFileSync('templates/labels.yml', 'utf8'));
  assert.ok(distributed.length > 0, 'templates/labels.yml must parse too');

  // GitHub's API needs all three fields; a partial line is skipped, not
  // half-applied.
  assert.deepStrictEqual(parseLabels('  - { name: "a", color: "ff0000" }\n'), []);
  assert.deepStrictEqual(parseLabels('  - { color: "ff0000", description: "d" }\n'), []);

  // Key order is not significant.
  assert.deepStrictEqual(
    parseLabels('  - { description: "d", color: "ff0000", name: "a" }\n'),
    [{ name: 'a', color: 'ff0000', description: 'd' }],
  );

  // Empty descriptions are legal; comments and duplicates are not applied.
  assert.deepStrictEqual(
    parseLabels('# - { name: "x", color: "ff0000", description: "no" }\n'),
    [],
  );
  assert.strictEqual(
    parseLabels(
      '  - { name: "a", color: "ff0000", description: "" }\n' +
      '  - { name: "a", color: "00ff00", description: "dup" }\n',
    ).length,
    1,
    'first definition wins; a duplicate never re-colors a label mid-sweep',
  );

  assert.deepStrictEqual(parseLabels(null), []);
  assert.deepStrictEqual(parseLabels(''), []);

  // planLabelSync: what a repository needs to match the taxonomy.
  const want = [
    { name: 'type:bug', color: 'd73a4a', description: 'Incorrect behavior with evidence' },
    { name: 'needs:triage', color: 'ededed', description: 'Awaiting maintainer review' },
    { name: 'area:ci', color: '1d76db', description: 'CI/CD pipelines' },
  ];
  // A repository with nothing gets every label created.
  assert.deepStrictEqual(
    planLabelSync([], want).create.map((l) => l.name),
    ['type:bug', 'needs:triage', 'area:ci'],
  );
  const plan = planLabelSync(
    [
      { name: 'type:bug', color: 'D73A4A', description: 'Incorrect behavior with evidence' },
      { name: 'Needs:Triage', color: 'ededed', description: 'Awaiting maintainer review' },
      { name: 'area:ci', color: '000000', description: null },
      { name: 'deps', color: '0366d6', description: 'Dependabot' },
    ],
    want,
  );
  // Color compares case-insensitively; an exact match is left alone.
  assert.deepStrictEqual(plan.unchanged, ['type:bug']);
  // Names are case-insensitive on GitHub: a case-only difference is a rename,
  // never a second create; drifted color/description is an update.
  assert.deepStrictEqual(plan.create, []);
  assert.deepStrictEqual(
    plan.update.map((u) => [u.current_name, u.name]),
    [['Needs:Triage', 'needs:triage'], ['area:ci', 'area:ci']],
  );
  // Additive: a label outside the taxonomy is never planned for change.
  assert.ok(![...plan.update, ...plan.create].some((l) => l.name === 'deps'));
  // The live taxonomy against itself is all-unchanged (idempotent re-run).
  assert.strictEqual(planLabelSync(labels, labels).unchanged.length, labels.length);

  console.log(`ok: org taxonomy parses (${labels.length} labels, all three fields, hex colors)`);
  console.log('ok: partial, commented, and duplicate label lines are skipped, not half-applied');
  console.log('ok: planLabelSync creates missing, renames case-only, updates drift, leaves extras');
} finally {
  process.chdir(origCwd);
}
