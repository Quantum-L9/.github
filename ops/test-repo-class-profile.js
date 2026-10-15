'use strict';

/**
 * Asserts the organization birth profile contract.
 *
 * The load-bearing claim: seeding a `non_constellation_python` repository must
 * never write a path that Quantum-L9/l9-repo-template's
 * scripts/inventory_check.py DENY_CI_DISTRIBUTION fails closed on. Before this
 * contract existed, the default payload wrote 11 of them.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-repo-class-profile.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const {
  DEFAULT_CLASSES_PATH,
  parseJsonInYaml,
  loadRepoClasses,
  parseClassMarker,
  classForRepo,
  matchPattern,
  resolveProfile,
  applyProfile,
  waivesMandatoryFile,
} = require('./repo-class-profile.js');
const os = require('node:os');
// dependabot.yml is rendered per repository root (ADR 0019); these class
// assertions hold for any shape, so they use the github-actions-only one.
const { shapeFromRoot } = require('./render-dependabot.js');
const ACTIONS_ONLY = shapeFromRoot({ names: [] });
const {
  buildSeedPayload,
  DEFAULT_CATEGORIES,
  parseCategories,
  planConsumerSeed,
} = require('./build-seed-payload.js');

// `[].sort()` with no comparator sorts by string conversion. These lists are
// already strings, but an assertion whose outcome depends on an implicit
// ordering rule is one refactor away from being wrong, so the rule is stated.
const byName = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

// The template's own deny list, transcribed. If l9-repo-template adds an entry,
// this list and policies/repo-classes.yml must both grow — the whole point of
// the contract is that the two repos agree in one direction, upstream to down.
const TEMPLATE_DENY_CI_DISTRIBUTION = [
  '.l9/ci-pin',
  'scripts/sync_ci_from_pack.py',
  'requirements-consumer-ci.txt',
  '.github/workflows/l9-analysis.yml',
  '.github/workflows/l9-lint-test.yml',
  '.github/workflows/on-org-update.yml',
  '.github/workflows/governance.yml',
  '.github/governance',
];

try {
  // ── policy file shape ──────────────────────────────────────────────────
  const doc = loadRepoClasses(fs);
  assert.strictEqual(doc.schema, 'l9.org-birth-profile/v1');
  assert.strictEqual(doc.default_class, 'default');
  assert.strictEqual(doc.marker_path, '.l9/org-birth-profile.yaml');
  assert.ok(doc.classes.default, 'default class defined');
  assert.ok(doc.classes.non_constellation_python, 'non_constellation_python class defined');

  // Comment stripping must not eat JSON string content.
  assert.deepStrictEqual(parseJsonInYaml('# note\n{"a": "b#c"}\n'), { a: 'b#c' });
  assert.throws(() => parseJsonInYaml(''), /empty/);
  assert.throws(() => parseJsonInYaml('not json'), /not JSON-in-YAML/);

  // The policy file must stay parseable by PyYAML too — enforce-policies.yml
  // and the Python birth orchestrator both read it.
  assert.doesNotThrow(() => JSON.parse(
    fs.readFileSync(DEFAULT_CLASSES_PATH, 'utf8').replace(/^[ \t]*#.*$/gm, ''),
  ));

  // ── marker parsing ─────────────────────────────────────────────────────
  assert.strictEqual(parseClassMarker('profile: non_constellation_python\n'), 'non_constellation_python');
  assert.strictEqual(parseClassMarker('schema: x\nprofile: "default"\n'), 'default');
  assert.strictEqual(parseClassMarker("profile: 'default'\n"), 'default');
  assert.strictEqual(parseClassMarker(''), null);
  assert.strictEqual(parseClassMarker(null), null);
  assert.strictEqual(parseClassMarker('no profile key here'), null);
  // An indented `profile:` is a nested key, not the marker.
  assert.strictEqual(parseClassMarker('  profile: sneaky\n'), null);

  // ── pattern matching ───────────────────────────────────────────────────
  assert.strictEqual(matchPattern(['a/b'], 'a/b'), 'a/b');
  assert.strictEqual(matchPattern(['a/**'], 'a/b/c'), 'a/**');
  assert.strictEqual(matchPattern(['a/**'], 'ab/c'), null);
  assert.strictEqual(matchPattern(['a/**'], 'a/'), 'a/**');
  assert.strictEqual(matchPattern([], 'a'), null);
  assert.strictEqual(matchPattern(undefined, 'a'), null);

  // ── resolution ─────────────────────────────────────────────────────────
  const def = resolveProfile(doc, null);
  assert.strictEqual(def.name, 'default');
  assert.match(def.resolved_from, /no marker/);

  const unknown = resolveProfile(doc, 'does-not-exist');
  assert.strictEqual(unknown.name, 'default', 'unknown class falls back, never widens');
  assert.match(unknown.resolved_from, /unknown class does-not-exist/);
  assert.throws(() => resolveProfile(doc, 'does-not-exist', { strict: true }), /unknown repo class/);

  const ncp = resolveProfile(doc, 'non_constellation_python');
  assert.strictEqual(ncp.name, 'non_constellation_python');
  assert.ok(ncp.remote_apply.labels, 'labels are REMOTE APPLY for this class');
  assert.ok(ncp.remote_apply.repo_settings, 'repo settings are REMOTE APPLY for this class');

  // ── the default class is the frozen four-mode model ────────────────────
  // MATERIALIZE the repository-local surfaces; INHERIT the passive
  // community-health surfaces GitHub serves org-wide; FORBID nothing.
  assert.deepStrictEqual(
    [...def.seed_categories].sort(byName),
    [...DEFAULT_CATEGORIES].sort(byName),
    'default class must reproduce DEFAULT_CATEGORIES exactly',
  );
  const PASSIVE_COMMUNITY_HEALTH = [
    '.github/FUNDING.yml',
    '.github/VULNERABILITY_REPORT.yml',
    'CODE_OF_CONDUCT.md',
    'CONTRIBUTING.md',
    'SUPPORT.md',
  ];
  assert.deepStrictEqual(
    [...def.inherit].sort(byName),
    PASSIVE_COMMUNITY_HEALTH,
    'default inherits exactly the passive community-health surfaces',
  );
  assert.ok(!def.inherit.includes('SECURITY.md'), 'SECURITY.md is MATERIALIZE, never inherited by default');
  assert.deepStrictEqual(def.forbid, []);
  for (const hasPython of [true, false]) {
    const profiled = buildSeedPayload({ fs, repoShape: ACTIONS_ONLY, profile: def, hasPython, repository: 'Quantum-L9/x' });
    assert.deepStrictEqual(Object.keys(profiled).sort(byName), [
      '.github/CODEOWNERS',
      '.github/ISSUE_TEMPLATE/1-bug.yml',
      '.github/ISSUE_TEMPLATE/2-feature.yml',
      '.github/ISSUE_TEMPLATE/3-task.yml',
      '.github/ISSUE_TEMPLATE/4-incident.yml',
      '.github/ISSUE_TEMPLATE/ci-failure.yml',
      '.github/ISSUE_TEMPLATE/config.yml',
      '.github/ISSUE_TEMPLATE/gov-violation.yml',
      '.github/PULL_REQUEST_TEMPLATE/release.md',
      '.github/dependabot.yml',
      '.github/pull_request_template.md',
      '.github/workflows/governance.yml',
      'SECURITY.md',
    ], `default class materializes exactly the repository-local surfaces (hasPython=${hasPython})`);
    // The inherit list names surfaces the categories never produce, so the
    // profile drops nothing: the unprofiled payload and the profiled one agree.
    const legacy = buildSeedPayload({ fs, repoShape: ACTIONS_ONLY, hasPython, repository: 'Quantum-L9/x' });
    assert.deepStrictEqual(Object.keys(profiled).sort(byName), Object.keys(legacy).sort(byName));
    for (const dest of Object.keys(legacy)) {
      assert.strictEqual(profiled[dest], legacy[dest], `default class must not rewrite ${dest}`);
    }
  }
  // Every passive surface GitHub serves from this repository exists here, at
  // the path GitHub reads an org default from (FUNDING.yml and
  // VULNERABILITY_REPORT.yml only count inside .github/), so inheritance is
  // real and not a name for "nobody ships it".
  for (const inherited of def.inherit) {
    assert.ok(fs.existsSync(inherited), `${inherited} must exist in the org .github repo to be inherited`);
  }

  // ── the non-Constellation Python class ─────────────────────────────────
  const born = buildSeedPayload({
    fs,
    repoShape: ACTIONS_ONLY,
    profile: ncp,
    hasPython: true,
    repository: 'Quantum-L9/l9-observability-core',
  });
  const bornDests = Object.keys(born).sort(byName);
  assert.deepStrictEqual(bornDests, [
    '.github/CODEOWNERS',
    '.github/dependabot.yml',
    '.github/labels.yml',
    'SECURITY.md',
  ], 'class seeds exactly the non-inheritable, repo-local surfaces');
  // SECURITY.md is materialized BECAUSE it carries consumer-specific routing.
  assert.match(
    born['SECURITY.md'],
    /https:\/\/github\.com\/Quantum-L9\/l9-observability-core\/security\/advisories\/new/,
  );
  // The passive community-health surfaces and both template sets are INHERIT
  // for this class: asked for explicitly, they drop out of the payload and
  // only SECURITY.md remains.
  const ncpInheritProbe = buildSeedPayload({
    fs,
    repoShape: ACTIONS_ONLY,
    profile: ncp,
    categories: ['community-health', 'issue-templates', 'pr-templates'],
    repository: 'Quantum-L9/l9-observability-core',
  });
  assert.deepStrictEqual(Object.keys(ncpInheritProbe), ['SECURITY.md']);
  for (const passive of ['CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'SUPPORT.md', '.github/FUNDING.yml', '.github/VULNERABILITY_REPORT.yml']) {
    assert.ok(matchPattern(ncp.inherit, passive), `non_constellation_python inherits ${passive}`);
  }

  // The claim this whole contract exists to make.
  for (const denied of TEMPLATE_DENY_CI_DISTRIBUTION) {
    for (const dest of bornDests) {
      assert.ok(
        dest !== denied && !dest.startsWith(`${denied}/`),
        `payload must never write template-denied ${denied} (got ${dest})`,
      );
    }
  }

  // `labels` was opt-in and therefore absent from `all`, but the template
  // REQUIRES .github/labels.yml. A class, not a global default, is what makes
  // both true at once.
  assert.ok(born['.github/labels.yml'], 'labels.yml is MATERIALIZE for this class');
  const legacyAll = buildSeedPayload({ fs, repoShape: ACTIONS_ONLY, categories: 'all' });
  assert.ok(!('.github/labels.yml' in legacyAll), 'labels stays out of the global default');

  // Asking for the historic default categories under this class is a loud
  // configuration error, not a silent drop.
  assert.throws(
    () => buildSeedPayload({ fs, repoShape: ACTIONS_ONLY, profile: ncp, categories: 'all', hasPython: true }),
    (err) => {
      assert.match(err.message, /violates repo class non_constellation_python/);
      assert.match(err.message, /governance\.yml/);
      return true;
    },
    'a forbidden dest must throw',
  );

  assert.ok(
    !Object.keys(buildSeedPayload({ fs, repoShape: ACTIONS_ONLY, categories: 'all', hasPython: true })).some((p) =>
      p.endsWith('l9-analysis.yml'),
    ),
    'the default seed must not write a copied analysis workflow',
  );

  // ── INHERIT drops, never errors ────────────────────────────────────────
  const inheritOnly = { 'CODE_OF_CONDUCT.md': 'x', '.github/ISSUE_TEMPLATE/1-bug.yml': 'y', 'keep.md': 'z' };
  const { payload: kept, inherited } = applyProfile(inheritOnly, ncp);
  assert.deepStrictEqual(Object.keys(kept), ['keep.md']);
  assert.deepStrictEqual(inherited.sort(byName), [
    '.github/ISSUE_TEMPLATE/1-bug.yml',
    'CODE_OF_CONDUCT.md',
  ]);

  // ── mandatory-file waivers ─────────────────────────────────────────────
  assert.ok(waivesMandatoryFile(ncp, '.github/workflows/governance.yml'));
  assert.ok(!waivesMandatoryFile(ncp, '.github/CODEOWNERS'));
  assert.ok(!waivesMandatoryFile(def, '.github/workflows/governance.yml'));

  // Every waived path must correspond to a real mandatory-files entry —
  // a waiver for a file nobody mandates is dead policy.
  const mandatory = fs.readFileSync('policies/mandatory-files.yml', 'utf8');
  for (const waived of ncp.mandatory_files_waive) {
    assert.ok(
      mandatory.includes(waived),
      `waiver ${waived} does not name a path in policies/mandatory-files.yml`,
    );
  }

  // ── org overrides: classify a repo that has not declared a marker ──────
  // Every one of these was a live red seeder PR before the class existed.
  const OVERRIDE_EXPECTATIONS = {
    'l9-repo-template': 'non_constellation_python',
    'l9-ci-core': 'self_governed',
    'l9-meta-injector': 'self_governed',
  };
  for (const [repo, expected] of Object.entries(OVERRIDE_EXPECTATIONS)) {
    const decided = classForRepo(doc, repo, null);
    assert.strictEqual(decided.name, expected, `${repo} resolves to ${expected}`);
    assert.strictEqual(decided.source, 'org override');
  }

  // A repository's own declaration outranks the override — the org classifies
  // what has not declared, it does not overrule what has.
  const declared = classForRepo(doc, 'l9-ci-core', 'profile: non_constellation_python\n');
  assert.strictEqual(declared.name, 'non_constellation_python');
  assert.strictEqual(declared.source, 'marker');
  assert.strictEqual(declared.error, null);

  // ── an explicit declaration we cannot honor FAILS CLOSED ───────────────
  // `default` is the widest payload there is. Falling back to it on a typo
  // would turn `profile: non_constelation_python` into a broad-seeding
  // candidate — the exact class of pull request this contract exists to stop.
  for (const [label, markerText] of [
    ['a typo in the class name', 'profile: non_constelation_python\n'],
    ['an unknown class', 'profile: totally_made_up\n'],
    ['a marker with no profile key', 'schema: l9.org-birth-profile-marker/v1\n'],
    ['an empty marker file', ''],
    ['a marker that is only whitespace', '   \n'],
    ['an indented (nested) profile key', '  profile: sneaky\n'],
  ]) {
    const bad = classForRepo(doc, 'some-repo', markerText);
    assert.strictEqual(bad.name, null, `${label} must not resolve to a class`);
    assert.ok(bad.error, `${label} must report an error`);
    assert.strictEqual(bad.source, 'marker');
  }

  // The failure survives an override: a repo that declared something broken is
  // not quietly rescued by the org map either.
  const brokenOverridden = classForRepo(doc, 'l9-ci-core', 'profile: non_constelation_python\n');
  assert.ok(brokenOverridden.error, 'a malformed marker beats the override, and errors');

  // Absence is NOT malformation: a repo that never declared has made no
  // statement to contradict, so override-then-default still applies.
  assert.strictEqual(classForRepo(doc, 'l9-ci-core', null).name, 'self_governed');
  assert.strictEqual(classForRepo(doc, 'l9-ci-core', null).error, null);
  assert.strictEqual(classForRepo(doc, 'unlisted-repo', null).name, null);
  assert.strictEqual(classForRepo(doc, 'unlisted-repo', null).error, null);

  // An unlisted repo with no marker keeps the historic behavior exactly.
  const plain = classForRepo(doc, 'some-other-repo', null);
  assert.strictEqual(plain.name, null);
  assert.strictEqual(plain.error, null);
  assert.strictEqual(resolveProfile(doc, plain.name).name, 'default');

  // ── LICENSE is outside universal distribution ──────────────────────────
  // GitHub does not propagate it as a community-health default and no class
  // seeds it, so no class may list it as mandatory-seeded either.
  // Line-wise, whitespace-normalized match; no regex so there is nothing to
  // backtrack on.
  const mandatoryEntries = fs.readFileSync('policies/mandatory-files.yml', 'utf8')
    .split('\n')
    .map((line) => line.trim().split(/\s+/).join(' '));
  assert.ok(
    !mandatoryEntries.includes('- path: LICENSE'),
    'LICENSE is not a mandatory consumer file',
  );
  for (const name of Object.keys(doc.classes)) {
    const payloadKeys = Object.keys(buildSeedPayload({
      fs,
      repoShape: ACTIONS_ONLY, profile: resolveProfile(doc, name), repository: 'Quantum-L9/x',
    }));
    assert.ok(!payloadKeys.includes('LICENSE'), `${name} must not seed LICENSE`);
  }

  // An override naming an undefined class is a policy bug, caught at load.
  assert.throws(
    () => loadRepoClasses({
      existsSync: () => true,
      readFileSync: () => JSON.stringify({
        default_class: 'default',
        classes: { default: {} },
        overrides: { 'x': 'nope' },
      }),
    }),
    /override x names undefined class nope/,
  );

  // ── self_governed writes no files at all ───────────────────────────────
  const selfGoverned = resolveProfile(doc, 'self_governed');
  assert.deepStrictEqual(selfGoverned.seed_categories, [], 'self_governed materializes nothing');
  for (const hasPython of [true, false]) {
    const payload = buildSeedPayload({
      fs,
      repoShape: ACTIONS_ONLY, profile: selfGoverned, hasPython, repository: 'Quantum-L9/l9-ci-core',
    });
    assert.deepStrictEqual(
      Object.keys(payload), [],
      'a self-governed repo receives capabilities through the API, never files',
    );
  }
  assert.ok(selfGoverned.remote_apply.labels, 'labels still apply remotely');
  assert.ok(selfGoverned.remote_apply.repo_settings, 'settings still apply remotely');
  // Every community-health surface, SECURITY.md included, is INHERIT here.
  for (const inherited of [
    'CODE_OF_CONDUCT.md',
    'CONTRIBUTING.md',
    'SECURITY.md',
    'SUPPORT.md',
    '.github/FUNDING.yml',
    '.github/VULNERABILITY_REPORT.yml',
    '.github/ISSUE_TEMPLATE/config.yml',
    '.github/pull_request_template.md',
    '.github/PULL_REQUEST_TEMPLATE/release.md',
  ]) {
    assert.ok(matchPattern(selfGoverned.inherit, inherited), `self_governed inherits ${inherited}`);
  }
  // The paths that actually broke these repos must be forbidden outright.
  for (const denied of [
    '.github/workflows/governance.yml',
    '.github/workflows/l9-lint-test.yml',
    '.github/workflows/l9-lint-test-node.yml',
  ]) {
    assert.ok(
      matchPattern(selfGoverned.forbid, denied),
      `self_governed must forbid ${denied}`,
    );
  }
  // Mandatory-file reporting must not nag a repo for files it may not carry.
  assert.ok(waivesMandatoryFile(selfGoverned, '.github/workflows/governance.yml'));
  assert.ok(waivesMandatoryFile(selfGoverned, '.github/CODEOWNERS'));

  // ── planConsumerSeed: the manual (shell) path binds to the same class law ──
  // ops/sync-org-files.sh writes nothing itself; this is the whole decision.
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'plan-consumer-seed-'));
  try {
    const consumer = (name, marker, files = {}) => {
      const dir = path.join(work, name);
      fs.mkdirSync(dir, { recursive: true });
      if (marker != null) {
        fs.mkdirSync(path.join(dir, '.l9'), { recursive: true });
        fs.writeFileSync(path.join(dir, doc.marker_path), marker);
      }
      for (const [rel, body] of Object.entries(files)) {
        fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
        fs.writeFileSync(path.join(dir, rel), body);
      }
      return dir;
    };

    // default class: no marker, no override; the class payload, all missing.
    const plain = planConsumerSeed({ fs, path, consumerRoot: consumer('plain', null), repository: 'Quantum-L9/plain' });
    assert.strictEqual(plain.profile.name, 'default');
    assert.deepStrictEqual(plain.kept, []);
    assert.deepStrictEqual(plain.inherited, []);
    assert.ok(plain.writes.includes('.github/workflows/governance.yml'));
    assert.ok(plain.writes.includes('SECURITY.md'));
    assert.match(plain.payload['SECURITY.md'], /Quantum-L9\/plain\/security\/advisories\/new/);

    // marker beats override; the class payload and nothing forbidden.
    const ncpDir = consumer('ncp', 'profile: non_constellation_python\n');
    const ncpPlan = planConsumerSeed({ fs, path, consumerRoot: ncpDir, repository: 'Quantum-L9/ncp' });
    assert.strictEqual(ncpPlan.profile.name, 'non_constellation_python');
    assert.strictEqual(ncpPlan.profile.resolved_from, 'marker');
    assert.deepStrictEqual(ncpPlan.writes.sort(byName), [
      '.github/CODEOWNERS', '.github/dependabot.yml', '.github/labels.yml', 'SECURITY.md',
    ]);
    for (const denied of TEMPLATE_DENY_CI_DISTRIBUTION) {
      assert.ok(!ncpPlan.writes.some((w) => w === denied || w.startsWith(`${denied}/`)), `plan must never write ${denied}`);
    }
    // explicit FORBID request throws (the shell turns this into exit 2).
    assert.throws(
      () => planConsumerSeed({ fs, path, consumerRoot: ncpDir, repository: 'Quantum-L9/ncp', categories: 'governance' }),
      /violates repo class non_constellation_python.*governance\.yml/,
    );
    // explicit INHERIT request drops, reported, never written.
    const ncpInherit = planConsumerSeed({
      fs, path, consumerRoot: ncpDir, repository: 'Quantum-L9/ncp', categories: 'community-health,pr-templates',
    });
    assert.deepStrictEqual(ncpInherit.writes, ['SECURITY.md']);
    assert.deepStrictEqual(ncpInherit.inherited.sort(byName), [
      '.github/PULL_REQUEST_TEMPLATE/release.md', '.github/pull_request_template.md',
    ]);

    // missing-only: an existing consumer file is kept and the payload is not
    // what is on disk, so the caller can prove it never overwrote.
    const seeded = consumer('seeded', null, {
      'SECURITY.md': '# consumer-owned\n',
      '.github/pull_request_template.md': 'local template\n',
      'CODEOWNERS': '* @Quantum-L9/seeded-owners\n',
    });
    const seededPlan = planConsumerSeed({ fs, path, consumerRoot: seeded, repository: 'Quantum-L9/seeded' });
    assert.deepStrictEqual(seededPlan.kept.sort(byName), ['.github/pull_request_template.md', 'SECURITY.md']);
    assert.ok(!seededPlan.writes.includes('SECURITY.md'));
    assert.ok(!('.github/CODEOWNERS' in seededPlan.payload), 'root CODEOWNERS suppresses the path-scoped template');
    assert.ok(seededPlan.writes.includes('.github/PULL_REQUEST_TEMPLATE/release.md'));

    // self_governed: zero writes, everything inherited.
    const sgPlan = planConsumerSeed({ fs, path, consumerRoot: consumer('sg', 'profile: self_governed\n'), repository: 'Quantum-L9/sg' });
    assert.deepStrictEqual(sgPlan.writes, []);
    assert.deepStrictEqual(sgPlan.kept, []);
    assert.deepStrictEqual(Object.keys(sgPlan.payload), []);

    // org override classifies an unmarked repo by name.
    const ovrPlan = planConsumerSeed({ fs, path, consumerRoot: consumer('l9-ci-core', null), repository: 'Quantum-L9/l9-ci-core' });
    assert.strictEqual(ovrPlan.profile.name, 'self_governed');
    assert.strictEqual(ovrPlan.profile.resolved_from, 'org override');
    assert.deepStrictEqual(ovrPlan.writes, []);

    // a malformed or unknown explicit marker fails closed, never default.
    for (const [label, marker] of [
      ['typo', 'profile: non_constelation_python\n'],
      ['empty', ''],
      ['no key', 'schema: x\n'],
    ]) {
      assert.throws(
        () => planConsumerSeed({ fs, path, consumerRoot: consumer(`bad-${label.replace(' ', '-')}`, marker), repository: 'Quantum-L9/bad' }),
        /refusing to seed/,
        `${label} marker must refuse`,
      );
    }
    // no remote: no repo name, so overrides cannot apply; marker still rules.
    const noRemote = planConsumerSeed({ fs, path, consumerRoot: consumer('no-remote', null) });
    assert.strictEqual(noRemote.profile.name, 'default');
    assert.match(noRemote.payload['SECURITY.md'], /Quantum-L9\/\.github\/security\/advisories\/new/, 'verbatim without a repository');
  } finally {
    fs.rmSync(work, { recursive: true, force: true });
  }

  console.log('ok: repo-classes policy is JSON-in-YAML and PyYAML-readable');
  console.log('ok: planConsumerSeed (shell path) classifies, refuses FORBID, drops INHERIT, keeps existing files, fails closed on a bad marker');
  console.log('ok: org overrides classify undeclared repos; a marker still outranks them');
  console.log('ok: a malformed or unknown EXPLICIT class fails closed, never widens to default');
  console.log('ok: LICENSE is neither mandatory nor seeded by any class');
  console.log('ok: self_governed seeds zero files, inherits every community-health surface, applies labels + settings remotely');
  console.log('ok: resolveProfile is strict at birth and defensive on a null (absent) class');
  console.log('ok: default class materializes SECURITY.md + templates and inherits the passive community-health surfaces');
  console.log('ok: non_constellation_python materializes SECURITY.md and no template-denied CI distribution path');
  console.log('ok: labels.yml is MATERIALIZE per class while staying out of the global default');
  console.log('ok: a forbidden dest throws; an inherited dest drops');
} finally {
  process.chdir(origCwd);
}

// ── enforce-policies.yml: class reads fail closed (GAR G9, V18) ─────────────
// The real `script:` body runs against a stubbed API. A marker that cannot be
// read, or that declares an unknown class, must not be assessed as `default`
// (the widest mandatory set), and an unreadable mandatory file is not missing.
(async () => {
  const { loadScriptModule, makeCore, makeScopedRequire } = require('./workflow-script-harness.js');
  const root = path.resolve(__dirname, '..');
  const enforce = loadScriptModule(path.join(root, '.github/workflows/enforce-policies.yml'), 'enforce-policies-');
  const MARKER = '.l9/org-birth-profile.yaml';
  const policies = {
    'policies/repo-settings.yml': { defaults: {} },
    'policies/mandatory-files.yml': { files: [{ path: '.github/workflows/governance.yml' }, { path: 'README.md' }] },
  };
  // `dryRun` is the DRY_RUN env the step receives. A scheduled run has no
  // inputs, so it gets 'false' (`inputs.dry_run || 'false'`) and APPLIES
  // settings: that is the mode a fail-open probe would damage.
  const runEnforceFull = async ({ files = {}, errors = {}, dryRun = 'true', settings, current = {} }) => {
    const scoped = makeScopedRequire(root);
    const pol = settings ? { ...policies, 'policies/repo-settings.yml': settings } : policies;
    const req = (m) => (m === 'child_process'
      ? { execSync: (cmd) => JSON.stringify(pol[Object.keys(pol).find((p) => cmd.includes(p))]) }
      : scoped(m));
    const updates = [];
    const github = {
      paginate: async () => [{ name: 'consumer-repo', archived: false, fork: false }],
      rest: {
        repos: {
          listForOrg: () => {},
          get: async () => ({ data: current }),
          update: async (args) => {
            updates.push(args);
            return { data: {} };
          },
          getContent: async ({ path: p }) => {
            if (errors[p]) throw Object.assign(new Error(`HTTP ${errors[p]}`), { status: errors[p] });
            if (p in files) return { data: { type: 'file', content: Buffer.from(files[p]).toString('base64') } };
            throw Object.assign(new Error('Not Found'), { status: 404 });
          },
        },
      },
    };
    const core = makeCore();
    const prev = process.cwd();
    const prevEnv = { DRY_RUN: process.env.DRY_RUN, FILTER: process.env.FILTER };
    process.chdir(root);
    Object.assign(process.env, { DRY_RUN: dryRun, FILTER: '' });
    try {
      await enforce(github, core, {}, req);
    } finally {
      process.chdir(prev);
      for (const [k, v] of Object.entries(prevEnv)) {
        if (v === undefined) delete process.env[k];
        else process.env[k] = v;
      }
    }
    // The summary table lists only non-compliant repositories.
    const row = core.tables.at(-1).slice(1).find((r) => r[0] === 'consumer-repo');
    return { status: row ? row[1] : 'compliant', updates, failures: core.failures };
  };
  const runEnforce = async (opts) => (await runEnforceFull(opts)).status;

  // Marker 403: not absent, so no default-class assessment.
  let status = await runEnforce({ errors: { [MARKER]: 403 } });
  assert.match(status, /unresolved repo class: .*unreadable \(403\) — mandatory files not assessed/);
  assert.doesNotMatch(status, /missing:/, 'a 403 marker was assessed as the default class');
  // Malformed / unknown declared class: reported, not widened to default.
  for (const text of ['profile: no_such_class\n', 'garbage\n']) {
    status = await runEnforce({ files: { [MARKER]: text } });
    assert.match(status, /unresolved repo class: .*— mandatory files not assessed/);
    assert.doesNotMatch(status, /missing:/);
  }
  // Absent marker (404): default class, real absence is reported.
  status = await runEnforce({});
  assert.match(status, /missing: \.github\/workflows\/governance\.yml/);
  assert.match(status, /missing: README\.md/);
  // A declared class still waives what it must not carry.
  status = await runEnforce({ files: { [MARKER]: 'profile: non_constellation_python\n', 'README.md': '# x\n' } });
  assert.strictEqual(status, 'compliant');
  // An unreadable mandatory file is unverified, not missing.
  status = await runEnforce({ files: { '.github/workflows/governance.yml': 'x' }, errors: { 'README.md': 500 } });
  assert.match(status, /unverified: README\.md unreadable \(500\)/);
  assert.doesNotMatch(status, /missing: README\.md/);
  console.log('ok: enforce-policies — unreadable/malformed marker is unresolved, never assessed as default; unreadable files are unverified, not missing');

  // ── the opt-out probe fails closed (F1) ──────────────────────────────────
  // `.l9/no-policy-enforcement` gates a settings WRITE. Only a 404 means the
  // marker is absent; a 403/5xx is an unread opt-out, so the repository is
  // neither enforced nor reported compliant, and the run fails. Driven with
  // settings drift so a fail-open probe would be observable as repos.update.
  const OPT_OUT = '.l9/no-policy-enforcement';
  const drift = { settings: { defaults: { has_wiki: false } }, current: { has_wiki: true } };
  const healthy = { '.github/workflows/governance.yml': 'x', 'README.md': '# x\n' };
  for (const dryRun of ['false', 'true']) { // 'false' = scheduled run / Apply
    for (const code of [403, 500, 502]) {
      const r = await runEnforceFull({ ...drift, dryRun, files: healthy, errors: { [OPT_OUT]: code } });
      assert.deepStrictEqual(r.updates, [], `opt-out probe ${code} (DRY_RUN=${dryRun}) still called repos.update`);
      assert.ok(r.status.startsWith(`BLOCKED: ${OPT_OUT} unreadable (${code})`), `opt-out probe ${code}: status ${r.status}`);
      assert.doesNotMatch(r.status, /compliant|settings (fixed|drift)/);
      assert.strictEqual(r.failures.length, 1, `opt-out probe ${code} must fail the run`);
      assert.match(r.failures[0], /consumer-repo/);
    }
  }
  // 404 is a real absence: enforcement proceeds, a scheduled run applies.
  {
    const r = await runEnforceFull({ ...drift, dryRun: 'false', files: healthy });
    assert.deepStrictEqual(r.updates, [{ owner: 'Quantum-L9', repo: 'consumer-repo', has_wiki: false }]);
    assert.strictEqual(r.status, 'settings fixed: has_wiki');
    assert.deepStrictEqual(r.failures, []);
    const preview = await runEnforceFull({ ...drift, dryRun: 'true', files: healthy });
    assert.deepStrictEqual(preview.updates, []);
    assert.match(preview.status, /settings drift: has_wiki=true→false/);
  }
  // A present marker is an honoured opt-out: no write, no failure.
  for (const dryRun of ['false', 'true']) {
    const r = await runEnforceFull({ ...drift, dryRun, files: { ...healthy, [OPT_OUT]: '' } });
    assert.deepStrictEqual(r.updates, []);
    assert.strictEqual(r.status, 'opted out');
    assert.deepStrictEqual(r.failures, []);
  }
  console.log('ok: enforce-policies — opt-out probe 403/5xx blocks the repo (no repos.update, run fails); 404 enforces; a present marker opts out');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
