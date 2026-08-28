'use strict';

/**
 * Asserts the default seed payload is stack-aware and omits drop-ranked dests.
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
  isStockUnsafeNodeWorkflow,
  isReplaceableStockNodeWorkflow,
  preserveTunedNodeEnv,
  readTopLevelEnv,
  selectSeedWrites,
  biomeSchemaOf,
  DEFAULT_CATEGORIES,
  OPT_IN_CATEGORIES,
  STOCK_ESLINT_NODE_DEST,
  STOCK_BIOME_DEST,
  STOCK_BIOME_SCHEMA,
  PYTHON_LINT_DEST,
  RETIRED_CATEGORIES,
} = require('./build-seed-payload.js');

const root = path.resolve(__dirname, '..');

/** The frozen pack, in the destination shape the retired category used to emit. */
function readFrozenPack() {
  const out = {};
  for (const [srcDir, destPrefix] of [
    ['l9-ci-pack/workflows', '.github/workflows'],
    ['l9-ci-pack/governance', '.github/governance'],
  ]) {
    for (const name of fs.readdirSync(path.join(root, srcDir)).sort()) {
      out[`${destPrefix}/${name}`] = fs.readFileSync(path.join(root, srcDir, name), 'utf8');
    }
  }
  for (const [src, dest] of [
    ['l9-ci-pack/biome.json', 'biome.json'],
    ['l9-ci-pack/.biomeignore', '.biomeignore'],
    ['l9-ci-pack/.editorconfig', '.editorconfig'],
    ['l9-ci-pack/.vscode/extensions.json', '.vscode/extensions.json'],
  ]) {
    out[dest] = fs.readFileSync(path.join(root, src), 'utf8');
  }
  return out;
}
const origCwd = process.cwd();
process.chdir(root);

try {
  // RETIRED: still parses as a name, but building it fails closed and 'all'
  // never includes it. See RETIRED_CATEGORIES in build-seed-payload.js.
  assert.ok(RETIRED_CATEGORIES.includes('l9-ci-pack'));
  assert.ok(!DEFAULT_CATEGORIES.includes('l9-ci-pack'));
  assert.ok(!parseCategories('all').includes('l9-ci-pack'));
  assert.throws(
    () => buildSeedPayload({ fs, categories: ['l9-ci-pack'], hasPython: true }),
    /RETIRED/,
    'a retired category must fail closed, not seed an empty payload',
  );
  assert.deepStrictEqual(parseCategories('all'), [...DEFAULT_CATEGORIES]);
  assert.ok(!parseCategories('all').includes('labels'));
  assert.ok(!parseCategories('all').includes('on-org-update'));
  assert.ok(OPT_IN_CATEGORIES.includes('labels'));
  assert.ok(RETIRED_CATEGORIES.includes('on-org-update'));
  assert.throws(
    () => buildSeedPayload({ fs, categories: ['on-org-update'] }),
    /RETIRED/,
    'the receiver for the retired copier must fail closed too',
  );
  assert.deepStrictEqual(parseCategories('labels'), ['labels']);

  const defaultPayload = buildSeedPayload({ fs, categories: 'all' });
  for (const dest of [
    'LICENSE',
    '.github/FUNDING.yml',
    'SUPPORT.md',
    '.github/workflows/on-org-update.yml',
    '.github/labels.yml',
    '.github/ISSUE_TEMPLATE/bug_report.yml',
    '.github/ISSUE_TEMPLATE/feature_request.yml',
    PYTHON_LINT_DEST,
  ]) {
    assert.ok(!(dest in defaultPayload), `default payload must omit ${dest}`);
  }

  // `.github/workflows/l9-lint-test.yml` was the pack's Python lint caller. It
  // is FORBID in both governed repo classes and is no longer seeded by anything,
  // so the default payload must omit it at every hasPython setting.
  assert.ok(
    !(PYTHON_LINT_DEST in buildSeedPayload({ fs, categories: 'all', hasPython: true })),
    'the retired Python lint caller must not be seeded, even for a Python repo',
  );
  // Its content contract still holds for the frozen copy in l9-ci-pack/.
  const pythonPayload = readFrozenPack();
  assert.ok(pythonPayload[PYTHON_LINT_DEST], 'frozen pack still ships the Python lint caller');
  assert.match(pythonPayload[PYTHON_LINT_DEST], /name: Python Test Suite/);
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /^\s*name:\s*Test Suite\s*$/m);
  // Toolchain versions must not be pinned here (that is install-consumer-ci@v2's
  // job), but the consumer's own package still has to be installed — see the
  // "Install consumer package and dependencies" assertions below.
  // The rule is "never INSTALL an unpinned plugin", not "never look".
  // Forbidding the read too is what produced the live regression: the install
  // fallback was removed, the read was removed with it, and the four `--cov`
  // flags stayed — so pytest exited 4 with `unrecognized arguments` in every
  // consumer that does not ship pytest-cov (l9-ci-core PR #113).
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /pip install (ruff|mypy|pytest)\b/);
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /pip install pytest-cov/);
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /python -c "import xdist"/);
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /python -c "import pytest_timeout"/);

  // Coverage must be guarded by a probe, and the probe must not go through a
  // pipe: under `set -o pipefail`, `pytest --help | grep -q` reports 141 when
  // grep exits at the first match, so the probe answers "absent" on a repo
  // that ships the plugin.
  const pyBody = pythonPayload[PYTHON_LINT_DEST]
    .split('\n')
    .filter((l) => !/^\s*#/.test(l))
    .join('\n');
  assert.match(pyBody, /--cov=/, 'coverage is still offered when available');
  assert.match(pyBody, /python -c "import pytest_cov"/, 'coverage is guarded by an import probe');
  assert.doesNotMatch(pyBody, /pytest --help[^\n]*\|[^\n]*grep/, 'probe must not use a pipe');

  // Job names are language-qualified so a seeded job cannot take over a check
  // context the consumer already publishes.
  assert.match(pythonPayload[PYTHON_LINT_DEST], /name: Python Lint and Type Check/);
  assert.doesNotMatch(pythonPayload[PYTHON_LINT_DEST], /^\s*name:\s*Lint and Type Check\s*$/m);

  // mypy must not be pointed at the whole checkout in a flat-layout repo.
  assert.match(pyBody, /--exclude/, 'mypy scopes away tests/fixtures when SOURCE_DIR is the repo root');
  assert.match(pythonPayload[PYTHON_LINT_DEST], /name: Detect Python package/);

  // Dropping the unpinned pytest-plugin fallbacks must not also drop the
  // consumer's own dependencies: pytest fails on import without them.
  assert.match(
    pythonPayload[PYTHON_LINT_DEST],
    /name: Install consumer package and dependencies/,
  );
  assert.match(pythonPayload[PYTHON_LINT_DEST], /pip install -e "\.\[dev\]"/);
  assert.match(pythonPayload[PYTHON_LINT_DEST], /pip install -r requirements\.txt/);

  const contributing = defaultPayload['CONTRIBUTING.md'];
  assert.ok(contributing, 'CONTRIBUTING.md is default-seeded');
  assert.doesNotMatch(contributing, /\.cursor\/rules/);
  assert.doesNotMatch(contributing, /\.cursor\/skills/);
  assert.doesNotMatch(contributing, /\.cursor\/commands/);
  assert.match(contributing, /PR_REMEDIATE=0 make pr/);
  assert.match(contributing, /l9-governance/);

  const security = buildSeedPayload({
    fs,
    categories: ['community-health'],
    repository: 'Quantum-L9/example',
  })['SECURITY.md'];
  assert.match(security, /https:\/\/github\.com\/Quantum-L9\/example\/security\/advisories\/new/);
  assert.doesNotMatch(security, /Quantum-L9\/\.github\/security\/advisories\/new/);

  const cfg = buildSeedPayload({
    fs,
    categories: ['issue-templates'],
    repository: 'Quantum-L9/example',
  })['.github/ISSUE_TEMPLATE/config.yml'];
  assert.match(cfg, /https:\/\/github\.com\/Quantum-L9\/example\/security\/advisories\/new/);
  assert.ok(
    buildSeedPayload({ fs, categories: ['issue-templates'] })[
      '.github/ISSUE_TEMPLATE/seed-ci-failure.yml'
    ],
  );

  const dependabot = defaultPayload['.github/dependabot.yml'];
  assert.match(dependabot, /package-ecosystem: github-actions/);
  assert.match(dependabot, /open-pull-requests-limit: 2/);
  assert.doesNotMatch(dependabot, /package-ecosystem: pip/);
  assert.doesNotMatch(dependabot, /labels:/);

  const codeowners = defaultPayload['.github/CODEOWNERS'];
  assert.doesNotMatch(codeowners, /^\*\s+@Quantum-L9\/platform\s*$/m);
  assert.match(codeowners, /\/\.github\//);
  assert.match(codeowners, /SECURITY\.md/);

  const caller = defaultPayload['.github/workflows/governance.yml'];
  assert.match(caller, /permissions:\n\s+contents: read\n\s+pull-requests: write/);
  assert.match(caller, /permissions:\n\s+contents: read\n\s+issues: write/);
  assert.doesNotMatch(caller, /^\s+secrets:\s*inherit\s*$/m);

  assert.ok(defaultPayload['.github/PULL_REQUEST_TEMPLATE/agent.md']);
  assert.ok(defaultPayload['.github/pull_request_template.md']);
  assert.ok(defaultPayload['.github/ISSUE_TEMPLATE/1-bug.yml']);
  assert.ok(defaultPayload['.github/ISSUE_TEMPLATE/2-feature.yml']);

  // `l9-ci-pack/` is frozen reference material, not a seed source. Its content
  // contract (pinned callers, JSON-in-YAML governance, the locked Biome schema)
  // is still asserted below — read from disk, because the seed path that used to
  // produce it is now refused.
  const pack = readFrozenPack();
  for (const dest of [
    'biome.json',
    '.biomeignore',
    '.editorconfig',
    '.vscode/extensions.json',
    '.github/workflows/l9-lint-test-node.yml',
    '.github/workflows/l9-analysis.yml',
    '.github/governance/execution-profiles.yaml',
    '.github/governance/semgrep-identity-map.yaml',
    '.github/governance/semgrep-finding-policy.yaml',
    PYTHON_LINT_DEST,
  ]) {
    assert.ok(pack[dest], `missing seed dest ${dest}`);
  }

  for (const dest of Object.keys(pack).filter((d) => d.startsWith('.github/governance/') && d.endsWith('.yaml'))) {
    JSON.parse(pack[dest]);
  }

  const thresholds = JSON.parse(pack['.github/governance/quality-thresholds.yaml']);
  assert.ok(thresholds.profiles.pr_fast.sdk_policy);
  assert.notStrictEqual(thresholds.profiles.pr_fast.sdk_policy, '');
  const profiles = JSON.parse(pack['.github/governance/execution-profiles.yaml']);
  assert.ok(profiles.profiles.agent);
  assert.ok(profiles.profiles.l4_local);
  assert.ok(profiles.profiles.agent.allowed_events.includes('workflow_dispatch'));
  const promo = JSON.parse(pack['.github/governance/promotion-policy.yaml']);
  assert.strictEqual(promo.requirements.approval_team, '@Quantum-L9/platform');

  const biome = JSON.parse(pack['biome.json']);
  assert.strictEqual(biome.$schema, STOCK_BIOME_SCHEMA);
  assert.strictEqual(biome.formatter.enabled, true);
  assert.ok(biome.files.includes.includes('!**/.l9'));

  const nodeWf = pack['.github/workflows/l9-lint-test-node.yml'];
  assert.match(nodeWf, /l9-biome-scan\.yml@[0-9a-f]{40}/);
  assert.doesNotMatch(nodeWf, /npx --no-install eslint/);
  assert.doesNotMatch(nodeWf, /name: ESLint/);
  assert.match(nodeWf, /name: Detect Node package/);
  assert.match(nodeWf, /name: Node Test Suite/);
  assert.doesNotMatch(nodeWf, /^\s*name:\s*Test Suite\s*$/m);
  assert.doesNotMatch(nodeWf, /cache:\s*\$\{\{\s*env\.PACKAGE_MANAGER\s*\}\}/);
  assert.strictEqual(isStockUnsafeNodeWorkflow(nodeWf), false);

  const analysis = pack['.github/workflows/l9-analysis.yml'];
  // v2 central orchestrator: the SDK owns semgrep execution, stack routing,
  // and governance fallback (resolve-governance defaults/). The seeded caller
  // must be a thin stub — SHA-pinned kernel call, no tool installs of its own,
  // and literal `with:` inputs (the env context is unavailable in
  // jobs.<id>.with, so `${{ env.* }}` there silently evaluates empty).
  assert.match(analysis, /analyze-semgrep\.yml@[0-9a-f]{40}/);
  assert.doesNotMatch(analysis, /pip install/);
  assert.doesNotMatch(analysis, /l9-ci-core[^\n]*@main/);
  assert.match(analysis, /security-events: write/);
  assert.doesNotMatch(analysis, /\$\{\{ env\./);
  assert.match(analysis, /^ *language: "(python|typescript)" *$/m);
  assert.match(analysis, /^name: L9 Analysis *$/m);

  // The pack's static editor-recommendation contract. The per-repo GENERATOR
  // that used to vary this by language had exactly one caller — the retired
  // l9-ci-pack category — and went with it; only the frozen file remains.
  const exts = JSON.parse(pack['.vscode/extensions.json']);
  assert.ok(exts.recommendations.includes('biomejs.biome'));
  assert.ok(
    !('.vscode/extensions.json' in defaultPayload),
    'editor recommendations are no longer seeded into consumer repositories',
  );

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

  const stockUnsafe = [
    'name: L9 Lint and Test (Node)',
    'uses: Quantum-L9/l9-ci-sdk/.github/workflows/l9-biome-scan.yml@deadbeef',
    '    name: Test Suite',
    '          cache: ${{ env.PACKAGE_MANAGER }}',
  ].join('\n');
  assert.strictEqual(isStockUnsafeNodeWorkflow(stockUnsafe), true);
  assert.strictEqual(isReplaceableStockNodeWorkflow(stockUnsafe), true);
  plan = selectSeedWrites({ [dest]: nodeWf }, { [dest]: stockUnsafe });
  assert.deepStrictEqual(plan.replaced, [dest]);
  assert.ok(plan.writes.includes(dest));

  const customizedBiomeOnly = [
    'name: L9 Biome (JSON/JS/TS)',
    'uses: Quantum-L9/l9-ci-sdk/.github/workflows/l9-biome-scan.yml@deadbeef',
  ].join('\n');
  assert.strictEqual(isStockUnsafeNodeWorkflow(customizedBiomeOnly), false);
  plan = selectSeedWrites({ [dest]: nodeWf }, { [dest]: customizedBiomeOnly });
  assert.deepStrictEqual(plan.replaced, []);
  assert.deepStrictEqual(plan.kept, [dest]);

  const otherSchema = JSON.stringify({ $schema: 'https://biomejs.dev/schemas/1.0.0/schema.json' });
  plan = selectSeedWrites(
    { [STOCK_BIOME_DEST]: pack['biome.json'] },
    { [STOCK_BIOME_DEST]: otherSchema },
  );
  assert.deepStrictEqual(plan.writes, []);
  assert.deepStrictEqual(plan.kept, [STOCK_BIOME_DEST]);
  assert.strictEqual(biomeSchemaOf(otherSchema), 'https://biomejs.dev/schemas/1.0.0/schema.json');

  // A consumer that tuned only the env: block (l9-ci-pack/README.md §5.4) still
  // matches every stock marker, so the upgrade must carry those values over
  // instead of reverting them to the payload defaults.
  const shippedNode = pack[STOCK_ESLINT_NODE_DEST];
  const tunedStockNode = shippedNode
    .replace('name: Node Test Suite', 'name: Test Suite')
    .replace('NODE_VERSION: "20"', 'NODE_VERSION: "22"')
    .replace('PACKAGE_MANAGER: "npm"', 'PACKAGE_MANAGER: "pnpm"')
    .replace(
      'node-version: ${{ env.NODE_VERSION }}',
      'node-version: ${{ env.NODE_VERSION }}\n          cache: ${{ env.PACKAGE_MANAGER }}',
    );
  assert.strictEqual(isStockUnsafeNodeWorkflow(tunedStockNode), true);
  assert.deepStrictEqual(readTopLevelEnv(tunedStockNode).NODE_VERSION, '"22"');

  const upgradePayload = { [STOCK_ESLINT_NODE_DEST]: shippedNode };
  plan = selectSeedWrites(upgradePayload, { [STOCK_ESLINT_NODE_DEST]: tunedStockNode });
  assert.deepStrictEqual(plan.replaced, [STOCK_ESLINT_NODE_DEST]);
  const upgraded = upgradePayload[STOCK_ESLINT_NODE_DEST];
  assert.match(upgraded, /NODE_VERSION: "22"/);
  assert.match(upgraded, /PACKAGE_MANAGER: "pnpm"/);
  // the unsafe parts still get replaced by the shipped caller
  assert.match(upgraded, /name: Node Test Suite/);
  assert.doesNotMatch(upgraded, /cache: \$\{\{ env\.PACKAGE_MANAGER \}\}/);
  // an untuned consumer file is upgraded byte-for-byte to the payload
  const untunedPayload = { [STOCK_ESLINT_NODE_DEST]: shippedNode };
  selectSeedWrites(untunedPayload, {
    [STOCK_ESLINT_NODE_DEST]: shippedNode.replace('name: Node Test Suite', 'name: Test Suite')
      .replace(
        'node-version: ${{ env.NODE_VERSION }}',
        'node-version: ${{ env.NODE_VERSION }}\n          cache: ${{ env.PACKAGE_MANAGER }}',
      ),
  });
  assert.strictEqual(untunedPayload[STOCK_ESLINT_NODE_DEST], shippedNode);
  assert.strictEqual(preserveTunedNodeEnv(shippedNode, 'not a workflow'), shippedNode);

  const pin = fs.readFileSync('ops/governance-v1-pin.txt', 'utf8');
  assert.match(pin, /7ed3ab8650583f6659a6caf061eae77dbd3ed1be/);

  console.log('ok: default payload drops LICENSE/FUNDING/SUPPORT/labels/on-org-update/dup issues');
  console.log('ok: Python lint dest is stack-gated and skip-safe');
  console.log('ok: CONTRIBUTING has no v2 .cursor/rules|skills|commands ritual');
  console.log('ok: governance pack is JSON-in-YAML with sdk_policy + agent/l4 profiles');
  console.log('ok: stock ESLint and unsafe Node callers are replaceable; custom + other biome $schema kept');
  console.log('ok: Node caller upgrade preserves the consumer-tuned env: block');
  console.log('ok: Python test job installs the consumer package and dependencies');
} finally {
  process.chdir(origCwd);
}
