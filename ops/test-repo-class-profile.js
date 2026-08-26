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
const { buildSeedPayload, DEFAULT_CATEGORIES } = require('./build-seed-payload.js');

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

  // ── the default class is a behavioral no-op ────────────────────────────
  // Every org sweep that ran before profiles existed must keep its payload.
  assert.deepStrictEqual(
    [...def.seed_categories].sort(),
    [...DEFAULT_CATEGORIES].sort(),
    'default class must reproduce DEFAULT_CATEGORIES exactly',
  );
  assert.deepStrictEqual(def.inherit, []);
  assert.deepStrictEqual(def.forbid, []);
  for (const hasPython of [true, false]) {
    const legacy = buildSeedPayload({ fs, hasPython, repository: 'Quantum-L9/x' });
    const profiled = buildSeedPayload({ fs, profile: def, hasPython, repository: 'Quantum-L9/x' });
    assert.deepStrictEqual(
      Object.keys(profiled).sort(),
      Object.keys(legacy).sort(),
      `default class must not change the payload (hasPython=${hasPython})`,
    );
    for (const dest of Object.keys(legacy)) {
      assert.strictEqual(profiled[dest], legacy[dest], `default class must not rewrite ${dest}`);
    }
  }

  // ── the non-Constellation Python class ─────────────────────────────────
  const born = buildSeedPayload({
    fs,
    profile: ncp,
    hasPython: true,
    repository: 'Quantum-L9/l9-observability-core',
  });
  const bornDests = Object.keys(born).sort();
  assert.deepStrictEqual(bornDests, [
    '.github/CODEOWNERS',
    '.github/dependabot.yml',
    '.github/labels.yml',
  ], 'class seeds exactly the non-inheritable, repo-local surfaces');

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
  const legacyAll = buildSeedPayload({ fs, categories: 'all' });
  assert.ok(!('.github/labels.yml' in legacyAll), 'labels stays out of the global default');

  // Asking for the historic default categories under this class is a loud
  // configuration error, not a silent drop.
  assert.throws(
    () => buildSeedPayload({ fs, profile: ncp, categories: 'all', hasPython: true }),
    (err) => {
      assert.match(err.message, /violates repo class non_constellation_python/);
      assert.match(err.message, /governance\.yml/);
      assert.match(err.message, /l9-analysis\.yml/);
      return true;
    },
    'a forbidden dest must throw',
  );

  // ── INHERIT drops, never errors ────────────────────────────────────────
  const inheritOnly = { 'CODE_OF_CONDUCT.md': 'x', '.github/ISSUE_TEMPLATE/1-bug.yml': 'y', 'keep.md': 'z' };
  const { payload: kept, inherited } = applyProfile(inheritOnly, ncp);
  assert.deepStrictEqual(Object.keys(kept), ['keep.md']);
  assert.deepStrictEqual(inherited.sort(), ['.github/ISSUE_TEMPLATE/1-bug.yml', 'CODE_OF_CONDUCT.md']);

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

  // ── the consumer LICENSE must never carry the .github-specific notice ──
  // The birth engine copies templates/community-health/LICENSE into every
  // newborn as canonical, so a repository-specific footer here is a licence
  // that lies about which repository it governs, reproduced automatically.
  const consumerLicense = fs.readFileSync('templates/community-health/LICENSE', 'utf8');
  assert.doesNotMatch(
    consumerLicense,
    /applies only to the Quantum-L9\/\.github repository/,
    'the consumer LICENSE template must not claim to govern only the .github repo',
  );
  assert.match(consumerLicense, /QUANTUM AI PARTNERS/, 'still the L9 proprietary licence');
  assert.match(consumerLicense, /GOVERNING LAW/, 'licence body intact');

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
      fs, profile: selfGoverned, hasPython, repository: 'Quantum-L9/l9-ci-core',
    });
    assert.deepStrictEqual(
      Object.keys(payload), [],
      'a self-governed repo receives capabilities through the API, never files',
    );
  }
  assert.ok(selfGoverned.remote_apply.labels, 'labels still apply remotely');
  assert.ok(selfGoverned.remote_apply.repo_settings, 'settings still apply remotely');
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

  console.log('ok: repo-classes policy is JSON-in-YAML and PyYAML-readable');
  console.log('ok: org overrides classify undeclared repos; a marker still outranks them');
  console.log('ok: a malformed or unknown EXPLICIT class fails closed, never widens to default');
  console.log('ok: consumer LICENSE template is generic, not .github-specific');
  console.log('ok: self_governed seeds zero files and still applies labels + settings remotely');
  console.log('ok: resolveProfile is strict at birth and defensive on a null (absent) class');
  console.log('ok: default class reproduces pre-profile seeding byte-for-byte');
  console.log('ok: non_constellation_python seeds no template-denied CI distribution path');
  console.log('ok: labels.yml is MATERIALIZE per class while staying out of the global default');
  console.log('ok: a forbidden dest throws; an inherited dest drops');
} finally {
  process.chdir(origCwd);
}
