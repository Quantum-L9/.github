'use strict';

/**
 * Asserts the default seed payload MATERIALIZES exactly the repository-local
 * surfaces and omits every INHERIT, REMOTE APPLY, and FORBID dest
 * (docs/REPO_BIRTH_PROFILES.md).
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-build-seed-payload.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  buildSeedPayload,
  parseCategories,
  selectSeedWrites,
  DEFAULT_CATEGORIES,
  OPT_IN_CATEGORIES,
  PYTHON_LINT_DEST,
  RETIRED_CATEGORIES,
  ISSUE_TEMPLATES_MATERIALIZED,
} = require('./build-seed-payload.js');
const { loadRepoClasses, resolveProfile } = require('./repo-class-profile.js');

// Explicit comparator: a default `.sort()` compares by string conversion,
// which is an implicit ordering rule one refactor away from being wrong.
const byName = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

try {
  // RETIRED: still parses as a name, but building it fails closed and 'all'
  // never includes it. See RETIRED_CATEGORIES in build-seed-payload.js.
  assert.deepStrictEqual(parseCategories('all'), [...DEFAULT_CATEGORIES]);
  assert.ok(!parseCategories('all').includes('labels'));
  assert.ok(!parseCategories('all').includes('on-org-update'));
  assert.ok(OPT_IN_CATEGORIES.includes('labels'));
  assert.ok(RETIRED_CATEGORIES.includes('on-org-update'));
  assert.ok(RETIRED_CATEGORIES.includes('l9-ci-pack'));
  assert.throws(
    () => buildSeedPayload({ fs, categories: ['on-org-update'] }),
    /RETIRED/,
    'the receiver for the retired copier must fail closed too',
  );
  assert.throws(
    () => buildSeedPayload({ fs, categories: ['l9-ci-pack'] }),
    /RETIRED/,
    'the retired CI pack must fail closed too',
  );
  assert.deepStrictEqual(parseCategories('labels'), ['labels']);

  const defaultPayload = buildSeedPayload({ fs, categories: 'all' });

  // MATERIALIZE: every dest a default consumer must carry as local bytes.
  for (const dest of [
    'SECURITY.md',
    '.github/CODEOWNERS',
    '.github/dependabot.yml',
    '.github/workflows/governance.yml',
    '.github/ISSUE_TEMPLATE/1-bug.yml',
    '.github/ISSUE_TEMPLATE/2-feature.yml',
    '.github/pull_request_template.md',
    '.github/PULL_REQUEST_TEMPLATE/release.md',
  ]) {
    assert.ok(dest in defaultPayload, `default payload must materialize ${dest}`);
  }

  // Never in the payload: INHERIT surfaces GitHub serves org-wide, REMOTE APPLY
  // state, retired CI, the deleted infra template, and LICENSE.
  for (const dest of [
    'LICENSE',
    'CODE_OF_CONDUCT.md',
    'CONTRIBUTING.md',
    'SUPPORT.md',
    '.github/FUNDING.yml',
    '.github/VULNERABILITY_REPORT.yml',
    '.github/PULL_REQUEST_TEMPLATE/infra.md',
    '.github/labels.yml',
    '.github/workflows/on-org-update.yml',
    '.github/workflows/l9-lint-test.yml',
    '.github/ISSUE_TEMPLATE/bug_report.yml',
    '.github/ISSUE_TEMPLATE/feature_request.yml',
    '.github/ISSUE_TEMPLATE/seed-ci-failure.yml',
    PYTHON_LINT_DEST,
  ]) {
    assert.ok(!(dest in defaultPayload), `default payload must omit ${dest}`);
  }

  // community-health is SECURITY.md alone: the one file with consumer-specific
  // routing. The passive surfaces are INHERIT and never copied.
  const communityHealth = buildSeedPayload({ fs, categories: ['community-health'] });
  assert.deepStrictEqual(Object.keys(communityHealth), ['SECURITY.md']);

  // pr-templates materializes the human template and the release template,
  // by name. The deleted infra template must never reappear via a directory
  // copy.
  const prTemplates = buildSeedPayload({ fs, categories: ['pr-templates'] });
  assert.deepStrictEqual(Object.keys(prTemplates).sort(byName), [
    '.github/PULL_REQUEST_TEMPLATE/release.md',
    '.github/pull_request_template.md',
  ]);
  assert.match(prTemplates['.github/PULL_REQUEST_TEMPLATE/release.md'], /^## Release/);
  assert.ok(
    !fs.existsSync('.github/PULL_REQUEST_TEMPLATE/infra.md'),
    'the infra PR template is deleted, not merely unseeded',
  );

  // `.github/workflows/l9-lint-test.yml` was the pack's Python lint caller. It
  // is FORBID in both governed repo classes and is no longer seeded by anything,
  // so the default payload must omit it at every hasPython setting.
  assert.ok(
    !(PYTHON_LINT_DEST in buildSeedPayload({ fs, categories: 'all', hasPython: true })),
    'the retired Python lint caller must not be seeded, even for a Python repo',
  );
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

  assert.ok(!defaultPayload['.github/PULL_REQUEST_TEMPLATE/agent.md']);
  assert.ok(!defaultPayload['.github/ISSUE_TEMPLATE/EXAMPLE.md']);
  assert.ok(defaultPayload['.github/pull_request_template.md']);
  assert.ok(defaultPayload['.github/ISSUE_TEMPLATE/1-bug.yml']);
  assert.ok(defaultPayload['.github/ISSUE_TEMPLATE/2-feature.yml']);

  // An existing file is left alone. Canonical CI is l9-ci-core
  // `.github/workflows/org-ci.yml`, not a file this seeder writes.
  const ciCaller = '.github/workflows/l9-lint-test-node.yml';
  const keptPlan = selectSeedWrites(
    { [ciCaller]: 'name: copied caller\n', 'biome.json': '{"$schema":"pack"}\n' },
    { [ciCaller]: 'name: already there\n', 'biome.json': '{"$schema":"other"}' },
  );
  assert.deepStrictEqual(keptPlan.writes, []);
  assert.deepStrictEqual(keptPlan.replaced, []);
  assert.deepStrictEqual(keptPlan.kept, [ciCaller, 'biome.json']);
  const missingPlan = selectSeedWrites({ 'README.md': 'x' }, { 'README.md': null });
  assert.deepStrictEqual(missingPlan.writes, ['README.md']);
  assert.ok(
    !('.vscode/extensions.json' in defaultPayload),
    'editor recommendations are no longer seeded into consumer repositories',
  );

  // ── Required sources (G1): a named source that is gone fails the build ────
  // An fs view over this checkout that hides some paths and adds others, so
  // the real fixtures are never touched.
  const enoent = (p) => Object.assign(new Error(`ENOENT: no such file, open '${p}'`), { code: 'ENOENT' });
  const fsWith = ({ hide = [], add = {} } = {}) => ({
    ...fs,
    existsSync: (p) => (p in add) || (!hide.includes(p) && fs.existsSync(p)),
    statSync: (p) => ((p in add) ? { isFile: () => true } : fs.statSync(p)),
    readFileSync: (p, enc) => {
      if (p in add) return add[p];
      if (hide.includes(p)) throw enoent(p);
      return fs.readFileSync(p, enc);
    },
    readdirSync: (p) => {
      const extra = Object.keys(add).filter((a) => a.startsWith(`${p}/`)).map((a) => a.slice(p.length + 1));
      return [...fs.readdirSync(p).filter((n) => !hide.includes(`${p}/${n}`)), ...extra];
    },
  });

  // V01: the named release template is missing.
  assert.throws(
    () => buildSeedPayload({ fs: fsWith({ hide: ['.github/PULL_REQUEST_TEMPLATE/release.md'] }), categories: 'all' }),
    /seed source \.github\/PULL_REQUEST_TEMPLATE\/release\.md is missing/,
    'a missing named PR template must fail the build, not shrink the payload',
  );
  // Every activated category's sources are required, not only templates.
  for (const [cat, src] of [
    ['codeowners', 'policies/CODEOWNERS'],
    ['dependabot', '.github/dependabot.yml'],
    ['governance', 'policies/governance-caller.yml'],
    ['community-health', 'SECURITY.md'],
    ['labels', '.github/labels.yml'],
  ]) {
    assert.throws(
      () => buildSeedPayload({ fs: fsWith({ hide: [src] }), categories: [cat] }),
      (err) => err.message.includes(`seed source ${src} is missing`),
      `${cat}: a missing source must throw`,
    );
  }
  // A category not requested does not need its source.
  assert.doesNotThrow(() => buildSeedPayload({ fs: fsWith({ hide: ['.github/labels.yml'] }), categories: 'all' }));

  // V02: a required issue form is missing → throws; an unnamed new form is
  // never swept into the payload.
  assert.throws(
    () => buildSeedPayload({ fs: fsWith({ hide: ['.github/ISSUE_TEMPLATE/3-task.yml'] }), categories: ['issue-templates'] }),
    /seed source \.github\/ISSUE_TEMPLATE\/3-task\.yml is missing/,
  );
  const withNewForm = buildSeedPayload({
    fs: fsWith({ add: { '.github/ISSUE_TEMPLATE/9-new.yml': 'name: new\n' } }),
    categories: ['issue-templates'],
  });
  assert.ok(!('.github/ISSUE_TEMPLATE/9-new.yml' in withNewForm), 'an unnamed issue form must not be distributed');
  assert.deepStrictEqual(Object.keys(withNewForm).sort(byName), [...ISSUE_TEMPLATES_MATERIALIZED].sort(byName));
  assert.strictEqual(ISSUE_TEMPLATES_MATERIALIZED.length, 7);

  // Exact class payload sizes (13 / 4 / 0).
  const classes = loadRepoClasses(fs);
  const sizes = Object.fromEntries(['default', 'non_constellation_python', 'self_governed'].map((c) => [
    c, Object.keys(buildSeedPayload({ fs, profile: resolveProfile(classes, c) })).length,
  ]));
  assert.deepStrictEqual(sizes, { default: 13, non_constellation_python: 4, self_governed: 0 });

  // V21: every eligible file already present → nothing to write.
  const present = Object.fromEntries(Object.keys(defaultPayload).map((p) => [p, true]));
  assert.deepStrictEqual(selectSeedWrites(defaultPayload, present).writes, []);

  // V24: an explicit category the class forbids throws, naming class and path.
  assert.throws(
    () => buildSeedPayload({ fs, categories: ['governance'], profile: resolveProfile(classes, 'non_constellation_python') }),
    /violates repo class non_constellation_python: \.github\/workflows\/governance\.yml/,
  );


  console.log('ok: default payload materializes SECURITY.md, ownership, governance caller, issue + PR templates');
  console.log('ok: default payload omits INHERIT surfaces (CoC/CONTRIBUTING/SUPPORT/FUNDING/VULNERABILITY_REPORT), LICENSE, labels, retired CI, infra.md');
  console.log('ok: community-health is SECURITY.md alone; release.md is materialized by pr-templates');
  console.log('ok: Python lint dest is not seeded');
  console.log('ok: existing files are left untouched');
} finally {
  process.chdir(origCwd);
}
