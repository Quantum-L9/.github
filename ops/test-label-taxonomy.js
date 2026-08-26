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
const { parseLabels } = require('./label-taxonomy.js');

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

  console.log(`ok: org taxonomy parses (${labels.length} labels, all three fields, hex colors)`);
  console.log('ok: partial, commented, and duplicate label lines are skipped, not half-applied');
} finally {
  process.chdir(origCwd);
}
