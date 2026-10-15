'use strict';

/**
 * ops/render-dependabot.js renders a consumer's .github/dependabot.yml from
 * the fragments in policies/dependabot/, the consumer's root shape, and the
 * vendored Core list of Core-owned tools (ADR
 * docs/adr/0019-dependabot-managed-rendered.md).
 *
 * Every fixture under ops/fixtures/dependabot/ is rendered twice and compared
 * byte for byte with its golden. The ecosystem set, the Core-owned ignores,
 * the Core / SDK / .github action ignores and the absence of labels are
 * asserted on top of the bytes, so a regenerated golden cannot quietly drop
 * one. A tampered vendored list and a missing shape both throw.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-render-dependabot.js
 */
const assert = require('node:assert');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const {
  SOURCE_RECORD,
  shapeFromRoot,
  shapeOfDirectory,
  probeRepoShape,
  loadCoreOwnedNames,
  renderDependabot,
  renderedEcosystems,
} = require('./render-dependabot.js');
const { buildSeedPayload, renderDependabot: reexported } = require('./build-seed-payload.js');

const root = path.resolve(__dirname, '..');
const FIXTURES = 'ops/fixtures/dependabot';
const ACTION_IGNORES = ['Quantum-L9/.github*', 'Quantum-L9/l9-ci-core*', 'Quantum-L9/l9-ci-sdk*'];
const PYTHON_ECOSYSTEMS = ['uv', 'pip', 'pre-commit'];

// What each fixture must render, independently of its golden bytes.
const EXPECTED_ECOSYSTEMS = {
  'actions-only': ['github-actions'],
  uv: ['github-actions', 'uv'],
  'pip-only': ['github-actions', 'pip'],
  // gate_sdk's shape: a PEP 621 pyproject.toml with no lock or requirements
  // still gets pip, or a restore would delete its pip entry.
  'pep621-only': ['github-actions', 'pip'],
  'uv-pre-commit': ['github-actions', 'uv', 'pre-commit'],
};

/** Split a render into its `updates:` entries, keyed by package-ecosystem. */
function entries(yml) {
  const blocks = yml.split(/\n(?= {2}- package-ecosystem: )/).slice(1);
  return Object.fromEntries(blocks.map((b) => {
    const ecosystem = b.match(/^ {2}- package-ecosystem: (\S+)/)[1];
    const ignores = [...b.matchAll(/^ {6}- dependency-name: "([^"]+)"$/gm)].map((m) => m[1]);
    return [ecosystem, { text: b, ignores }];
  }));
}

/** A read-only fs view of this checkout with some files replaced. */
const fsWith = (replace) => ({
  ...fs,
  readFileSync: (p, enc) => (p in replace ? (enc ? replace[p] : Buffer.from(replace[p])) : fs.readFileSync(p, enc)),
});

const origCwd = process.cwd();
process.chdir(root);

(async () => {
  const owned = loadCoreOwnedNames(fs);
  const fixtures = fs.readdirSync(FIXTURES, { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name).sort();
  assert.deepStrictEqual(fixtures, Object.keys(EXPECTED_ECOSYSTEMS).sort(), 'every fixture is asserted, and every asserted fixture exists');

  for (const name of fixtures) {
    const spec = JSON.parse(fs.readFileSync(`${FIXTURES}/${name}/root.json`, 'utf8'));
    const shape = shapeFromRoot({ names: spec.names, pyprojectText: spec.pyproject ?? null });
    const first = renderDependabot({ fs, shape });
    const second = renderDependabot({ fs, shape });
    assert.strictEqual(first, second, `${name}: two renders differ`);
    assert.strictEqual(first, fs.readFileSync(`${FIXTURES}/${name}/expected.yml`, 'utf8'), `${name}: render differs from its golden`);
    assert.ok(first.endsWith('\n') && !first.endsWith('\n\n'), `${name}: exactly one trailing newline`);
    assert.ok(!first.includes('\r'), `${name}: LF only`);
    assert.doesNotMatch(first, /labels:/, `${name}: no labels (issue #132: missing labels fail PR creation)`);
    assert.doesNotMatch(first, /\d{4}-\d{2}-\d{2}|[0-9a-f]{40}/, `${name}: no timestamp or sha in the render`);

    const byEcosystem = entries(first);
    assert.deepStrictEqual(Object.keys(byEcosystem), EXPECTED_ECOSYSTEMS[name], `${name}: ecosystem set`);
    assert.deepStrictEqual(renderedEcosystems(shape), EXPECTED_ECOSYSTEMS[name]);
    assert.deepStrictEqual(byEcosystem['github-actions'].ignores, ACTION_IGNORES, `${name}: Core/SDK/.github action pins are not Dependabot's`);
    for (const ecosystem of PYTHON_ECOSYSTEMS) {
      if (!byEcosystem[ecosystem]) continue;
      const want = owned[ecosystem];
      assert.ok(want && want.length, `${ecosystem}: Core lists no owned names`);
      assert.deepStrictEqual(byEcosystem[ecosystem].ignores, want, `${name}: ${ecosystem} ignores every Core-owned name, sorted`);
    }
    for (const entry of Object.values(byEcosystem)) {
      assert.match(entry.text, /open-pull-requests-limit: 2\n/);
      assert.match(entry.text, /prefix: "chore\(deps\)"\n/);
      assert.match(entry.text, /cooldown:\n {6}default-days: 7\n/);
      assert.match(entry.text, /interval: weekly\n {6}day: monday\n/);
    }
    console.log(`ok: ${name} — golden bytes, idempotent, ecosystems ${EXPECTED_ECOSYSTEMS[name].join('+')}`);
  }

  // The Core-owned names come straight from the vendored list: every name in
  // every rendered ecosystem, and nothing a non-dependency lock key names.
  const vendored = JSON.parse(fs.readFileSync('policies/vendor/l9-ci-core/core-owned-tools.json', 'utf8'));
  for (const ecosystem of PYTHON_ECOSYSTEMS) {
    const fromCore = [...new Set(vendored.tools.flatMap((t) => (t.ecosystems || {})[ecosystem] || []))].sort();
    assert.deepStrictEqual(owned[ecosystem], fromCore, `${ecosystem}: derived names drift from the vendored list`);
  }
  for (const key of Object.keys(vendored.non_dependency_lock_keys)) {
    for (const ecosystem of PYTHON_ECOSYSTEMS) {
      assert.ok(!owned[ecosystem].includes(key), `${key} is a lock key, not a ${ecosystem} dependency`);
    }
  }

  // The vendored bytes are pinned: a tampered list throws, it never renders.
  const record = JSON.parse(fs.readFileSync(SOURCE_RECORD, 'utf8'));
  assert.strictEqual(
    crypto.createHash('sha256').update(fs.readFileSync(record.vendored_at)).digest('hex'),
    record.sha256,
  );
  assert.match(record.commit, /^[0-9a-f]{40}$/);
  const tampered = fs.readFileSync(record.vendored_at, 'utf8').replace('"ruff"', '"ruff-renamed"');
  assert.throws(
    () => renderDependabot({ fs: fsWith({ [record.vendored_at]: tampered }), shape: shapeFromRoot({ names: ['uv.lock'] }) }),
    /sha256 [0-9a-f]{64} does not match/,
  );
  console.log('ok: sha-mismatch-throws — a vendored list that does not match its recorded digest is refused');

  // No shape, no render; a malformed shape is not a shape.
  for (const shape of [undefined, null, {}, { uvLock: 'yes', requirements: [], pep621: false, preCommit: false }, { uvLock: false, requirements: 'requirements.txt', pep621: false, preCommit: false }]) {
    assert.throws(() => renderDependabot({ fs, shape }), /shape/, `rendered for shape ${JSON.stringify(shape)}`);
  }
  assert.throws(() => shapeFromRoot({ names: ['pyproject.toml'] }), /pyproject\.toml is listed/);
  assert.throws(() => shapeFromRoot({}), /names/);
  console.log('ok: no-shape-throws — a missing or malformed shape is refused, never defaulted to github-actions only');

  // Shape rules beyond the fixtures.
  assert.strictEqual(shapeFromRoot({ names: ['pyproject.toml'], pyprojectText: '[tool.poetry]\nname = "x"\n' }).pep621, false,
    'a pyproject.toml without a [project] table is not PEP 621');
  assert.deepStrictEqual(renderedEcosystems(shapeFromRoot({ names: ['pyproject.toml'], pyprojectText: '[tool.poetry]\n' })), ['github-actions']);
  assert.deepStrictEqual(shapeFromRoot({ names: ['requirements.in', 'requirements-dev.txt', 'requirements.txt', 'dev-requirements.txt'] }).requirements,
    ['requirements-dev.txt', 'requirements.txt']);
  // uv wins over pip: a uv repo's requirements.txt pins are updated by the uv ecosystem.
  assert.deepStrictEqual(renderedEcosystems(shapeFromRoot({ names: ['uv.lock', 'requirements.txt'] })), ['github-actions', 'uv']);
  console.log('ok: shape rules — [project] table, root requirements*.txt, uv over pip');

  // The remote probe: directories are not files, pyproject.toml is read only
  // when listed, and a listed but unreadable pyproject.toml throws.
  const reads = [];
  const probed = await probeRepoShape({
    listRoot: async () => [
      { name: 'uv.lock', type: 'dir' },
      { name: 'pyproject.toml', type: 'file' },
      { name: '.pre-commit-config.yaml', type: 'file' },
    ],
    readText: async (p) => { reads.push(p); return '[project]\nname = "x"\n'; },
  });
  assert.deepStrictEqual(reads, ['pyproject.toml']);
  assert.deepStrictEqual(renderedEcosystems(probed), ['github-actions', 'pip', 'pre-commit']);
  await assert.rejects(
    probeRepoShape({ listRoot: async () => [{ name: 'pyproject.toml', type: 'file' }], readText: async () => null }),
    /could not be read/,
  );
  await assert.rejects(probeRepoShape({ listRoot: async () => ({ type: 'file' }), readText: async () => null }), /not a directory listing/);
  const listingError = Object.assign(new Error('forbidden'), { status: 403 });
  await assert.rejects(probeRepoShape({ listRoot: async () => { throw listingError; }, readText: async () => null }), (e) => e === listingError);
  console.log('ok: probeRepoShape — files only, pyproject.toml read when listed, unreadable root or pyproject throws');

  // This repository runs its own rendering: .github/dependabot.yml is the
  // render for this checkout's root, byte for byte.
  assert.strictEqual(
    fs.readFileSync('.github/dependabot.yml', 'utf8'),
    renderDependabot({ fs, shape: shapeOfDirectory({ fs, path, dir: root }) }),
    '.github/dependabot.yml is not the render for this repository; run `node ops/render-dependabot.js > .github/dependabot.yml`',
  );
  // The seed payload carries exactly the renderer's bytes for the shape it is given.
  const uv = shapeFromRoot({ names: ['uv.lock'] });
  assert.strictEqual(reexported, renderDependabot);
  assert.strictEqual(buildSeedPayload({ fs, categories: ['dependabot'], repoShape: uv })['.github/dependabot.yml'], renderDependabot({ fs, shape: uv }));
  console.log('ok: self-config — .github/dependabot.yml is this repository\'s own render; the seed payload carries the render');

  console.log('\nall dependabot render scenarios passed');
})()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => process.chdir(origCwd));
