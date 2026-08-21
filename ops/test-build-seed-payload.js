'use strict';

/**
 * Asserts the l9-ci-pack seed payload includes the locked Biome contract
 * and that the Node lint caller is the SDK Biome workflow, not ESLint.
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-build-seed-payload.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  buildSeedPayload,
  parseCategories,
  isStockEslintNodeWorkflow,
  selectSeedWrites,
  STOCK_ESLINT_NODE_DEST,
} = require('./build-seed-payload.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

try {
  const cats = parseCategories('l9-ci-pack');
  assert.deepStrictEqual(cats, ['l9-ci-pack']);

  const payload = buildSeedPayload({ fs, categories: cats });

  for (const dest of [
    'biome.json',
    '.biomeignore',
    '.editorconfig',
    '.vscode/extensions.json',
    '.github/workflows/l9-lint-test-node.yml',
    '.github/workflows/l9-analysis.yml',
    '.github/governance/execution-profiles.yaml',
  ]) {
    assert.ok(payload[dest], `missing seed dest ${dest}`);
  }

  const biome = JSON.parse(payload['biome.json']);
  assert.strictEqual(biome.$schema, 'https://biomejs.dev/schemas/2.5.8/schema.json');
  assert.strictEqual(biome.formatter.enabled, true);
  assert.strictEqual(biome.linter.enabled, true);

  const nodeWf = payload['.github/workflows/l9-lint-test-node.yml'];
  assert.match(nodeWf, /l9-biome-scan\.yml@[0-9a-f]{40}/);
  assert.doesNotMatch(nodeWf, /npx --no-install eslint/);
  assert.doesNotMatch(nodeWf, /name: ESLint/);

  const exts = JSON.parse(payload['.vscode/extensions.json']);
  assert.ok(exts.recommendations.includes('biomejs.biome'));

  const stockEslint = [
    'name: L9 Lint and Test (Node)',
    'jobs:',
    '  lint:',
    '    name: ESLint',
    '      - name: ESLint',
    '        run: npx --no-install eslint .',
  ].join('\n');
  assert.strictEqual(isStockEslintNodeWorkflow(stockEslint), true);
  assert.strictEqual(isStockEslintNodeWorkflow(nodeWf), false);
  assert.strictEqual(isStockEslintNodeWorkflow('name: ESLint\nrun: npx eslint .'), false);

  const dest = STOCK_ESLINT_NODE_DEST;
  let plan = selectSeedWrites({ [dest]: nodeWf, 'biome.json': '{}' }, {
    [dest]: stockEslint,
    'biome.json': true,
  });
  assert.deepStrictEqual(plan.replaced, [dest]);
  assert.ok(plan.writes.includes(dest));
  assert.ok(plan.kept.includes('biome.json'));

  plan = selectSeedWrites({ [dest]: nodeWf }, { [dest]: nodeWf });
  assert.deepStrictEqual(plan.replaced, []);
  assert.deepStrictEqual(plan.kept, [dest]);

  plan = selectSeedWrites({ [dest]: nodeWf }, { [dest]: null });
  assert.deepStrictEqual(plan.writes, [dest]);

  console.log('ok: l9-ci-pack payload includes locked Biome contract');
  console.log('ok: stock ESLint node caller is replaceable; Biome/custom are kept');
} finally {
  process.chdir(origCwd);
}
