'use strict';

/**
 * Contract tests for the governance-plan compiler (ops/compile-repo-governance.js).
 *
 * Proves, against the real policy files and against in-memory fixtures:
 *   - every repo class compiles to a schema-valid plan (AC-CON-001)
 *   - class precedence marker > org override > default, operator request strict
 *     (AC-REG-001, AC-ADV-001; golden vectors GV-001, GV-002)
 *   - materialization equals buildSeedPayload() for every class — the default
 *     class byte-for-byte (AC-REG-002, AC-INT-001 at the compiler boundary)
 *   - INHERIT dropped, FORBID and retired categories rejected (AC-BEH-001,
 *     AC-ADV-002, AC-ADV-006)
 *   - determinism and digest semantics (AC-CON-003/004/006; GV-003)
 *   - path and content safety (AC-ADV-007) and schema rejection (AC-CON-002)
 *   - mandatory-file waivers, settings and labels desired state match the
 *     formulas the workflows use today (C-06, C-07)
 *   - verifyPlan and narrowMaterialization refuse tampering and widening
 *     (AC-ADV-003, AC-ADV-005 digest half, AC-ADV-008, AC-ADV-010; GV-004)
 *   - production provenance refuses a dirty or mismatched checkout (B-20)
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-compile-repo-governance.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const {
  canonicalJson,
  computePlanDigest,
  loadAuthority,
  compileGovernancePlan,
  verifyPlan,
  narrowMaterialization,
  assertCleanAuthority,
  GovernanceCompileError,
  NEVER_AUTO_APPLIED_SETTINGS,
} = require('./compile-repo-governance.js');
const { buildSeedPayload } = require('./build-seed-payload.js');
const { resolveProfile, parseJsonInYaml } = require('./repo-class-profile.js');
const { parseLabels } = require('./label-taxonomy.js');
const { compileSchema } = require('./json-schema-subset.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

const SHA = '77587b7421b2e7cfad391e5036f531d8b5833e2b';
const OTHER_SHA = 'a'.repeat(40);
const ABSENT = Object.freeze({
  marker_state: 'absent',
  has_root_codeowners: false,
  has_python: true,
  has_package_json: false,
});
const marker = (cls) => ({ ...ABSENT, marker_state: 'present', marker_text: `profile: ${cls}\n` });

// A copy of the real authority that a test can bend without touching disk.
const clone = (v) => JSON.parse(JSON.stringify(v));
const realAuthority = loadAuthority(fs);
const validate = compileSchema(realAuthority.schema);

const compile = (repository, facts = ABSENT, extra = {}) =>
  compileGovernancePlan({ fs, authoritySha: SHA, repository, facts, ...extra });

function throwsCode(fn, code, pattern) {
  assert.throws(fn, (err) => {
    assert.ok(err instanceof GovernanceCompileError, `expected GovernanceCompileError, got ${err}`);
    assert.strictEqual(err.code, code, `expected code ${code}, got ${err.code}: ${err.message}`);
    if (pattern) assert.match(err.message, pattern);
    return true;
  });
}

try {
  // ── every class compiles, schema-valid (AC-CON-001) ─────────────────────
  for (const cls of Object.keys(realAuthority.classes.classes)) {
    const plan = compile('Quantum-L9/example-repo', marker(cls));
    assert.deepStrictEqual(validate(plan), [], `class ${cls} plan must be schema-valid`);
    assert.strictEqual(plan.repo_class.name, cls);
    assert.strictEqual(plan.repo_class.resolved_from, 'marker');
    assert.strictEqual(plan.authority.sha, SHA);
    assert.strictEqual(plan.authority.repository, 'Quantum-L9/.github');
  }
  console.log('ok: every repo class compiles to a schema-valid l9.org-governance-plan/v1');

  // ── class precedence (GV-001, AC-REG-001) ───────────────────────────────
  assert.deepStrictEqual(compile('Quantum-L9/unlisted').repo_class, { name: 'default', resolved_from: 'default' });
  assert.deepStrictEqual(compile('Quantum-L9/l9-ci-core').repo_class, {
    name: 'self_governed',
    resolved_from: 'org_override',
  });
  // A repository's own declaration beats the org override.
  assert.deepStrictEqual(compile('Quantum-L9/l9-ci-core', marker('default')).repo_class, {
    name: 'default',
    resolved_from: 'marker',
  });
  assert.deepStrictEqual(compile('Quantum-L9/unlisted', ABSENT, { requestedClass: 'self_governed' }).repo_class, {
    name: 'self_governed',
    resolved_from: 'operator_request',
  });
  console.log('ok: precedence marker > org override > default; operator request recorded (GV-001)');

  // ── fail closed on explicit declarations (GV-002, AC-ADV-001) ───────────
  // The pack's GV-002 vector carries a literal backslash-n; a real newline is
  // what a marker file contains, and both must fail closed.
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_state: 'present', marker_text: 'profile: totally_made_up\n' }), 'class_resolution', /unknown class totally_made_up/);
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_state: 'present', marker_text: 'profile: totally_made_up\\n' }), 'class_resolution');
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_state: 'present', marker_text: 'not a marker' }), 'class_resolution', /no parseable profile/);
  // Present-but-empty is a malformed declaration, not absence (AC-ADV-009).
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_state: 'present', marker_text: '' }), 'class_resolution');
  throwsCode(() => compile('Quantum-L9/x', ABSENT, { requestedClass: 'defualt' }), 'class_resolution', /operator requested unknown/);
  console.log('ok: malformed, empty, or unknown marker and unknown operator class fail closed (GV-002)');

  // ── missing / malformed facts ───────────────────────────────────────────
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_state: 'unknown' }), 'missing_fact');
  throwsCode(() => compile('Quantum-L9/x', { marker_state: 'present', has_root_codeowners: false, has_python: false, has_package_json: false }), 'missing_fact');
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, has_python: 'yes' }), 'missing_fact');
  throwsCode(() => compile('Quantum-L9/x', { ...ABSENT, marker_text: 'profile: default\n' }), 'contract');
  throwsCode(() => compile('not-a-slug'), 'contract');
  console.log('ok: missing or contradictory target facts are refused');

  // ── authority SHA (AC-CON-005) ──────────────────────────────────────────
  for (const bad of ['HEAD', SHA.slice(0, 7), SHA.toUpperCase(), `${SHA}0`, '', null]) {
    throwsCode(() => compileGovernancePlan({ fs, authoritySha: bad, repository: 'Quantum-L9/x', facts: ABSENT }), 'authority_identity');
  }
  console.log('ok: authority SHA must be exactly 40 lowercase hex characters');

  // ── materialization parity with the existing seeder (AC-REG-002) ────────
  const factVariants = [
    { ...ABSENT },
    { ...ABSENT, has_root_codeowners: true },
    { ...ABSENT, has_python: false, has_package_json: true },
  ];
  for (const cls of Object.keys(realAuthority.classes.classes)) {
    for (const facts of factVariants) {
      const repository = 'Quantum-L9/parity-target';
      const plan = compile(repository, marker(cls));
      const withFacts = compile(repository, { ...marker(cls), ...facts, marker_state: 'present', marker_text: `profile: ${cls}\n` });
      const expected = buildSeedPayload({
        fs,
        profile: resolveProfile(realAuthority.classes, cls, { strict: true }),
        hasRootCodeowners: facts.has_root_codeowners,
        hasPython: facts.has_python,
        hasPackageJson: facts.has_package_json,
        repository,
      });
      const actual = Object.fromEntries(withFacts.materialize.files.map((f) => [f.path, f.content_utf8]));
      assert.deepStrictEqual(
        Object.keys(actual).sort(),
        Object.keys(expected).sort(),
        `class ${cls} ${JSON.stringify(facts)}: write set differs from buildSeedPayload`,
      );
      for (const dest of Object.keys(expected)) {
        assert.strictEqual(actual[dest], expected[dest], `class ${cls}: ${dest} content differs from buildSeedPayload`);
      }
      assert.ok(plan.materialize.files.every((f) => f.write_mode === 'missing_only'), 'no current dest is stock-replaceable');
    }
  }
  // Root CODEOWNERS is preserved as the ownership authority (B-08).
  assert.ok(!compile('Quantum-L9/x', { ...ABSENT, has_root_codeowners: true }).materialize.files.some((f) => f.path === '.github/CODEOWNERS'));
  assert.ok(compile('Quantum-L9/x').materialize.files.some((f) => f.path === '.github/CODEOWNERS'));
  console.log('ok: materialization equals buildSeedPayload for every class and fact variant (default byte-compatible)');

  // Provenance per entry: capability is a plan capability, source is a real template.
  for (const file of compile('Quantum-L9/x').materialize.files) {
    assert.ok(compile('Quantum-L9/x').capabilities.includes(file.capability), `${file.path} capability ${file.capability}`);
    assert.ok(fs.existsSync(file.source), `${file.path} source ${file.source} exists`);
  }
  console.log('ok: every materialized file names its capability and its template source');

  // self_governed seeds nothing but still inherits and forbids.
  const selfGoverned = compile('Quantum-L9/l9-ci-core');
  assert.strictEqual(selfGoverned.materialize.files.length, 0);
  assert.ok(selfGoverned.inherit.paths.includes('SECURITY.md'));
  assert.deepStrictEqual(selfGoverned.attestation.required_absent, selfGoverned.forbid.paths);

  // ── INHERIT / FORBID / retired (AC-BEH-001, AC-ADV-002, AC-ADV-006) ─────
  const bent = clone(realAuthority);
  bent.classes.classes.fixture_inherit = {
    description: 'test fixture',
    seed_categories: ['community-health', 'codeowners'],
    inherit: ['CODE_OF_CONDUCT.md'],
    forbid: [],
    remote_apply: { labels: false, repo_settings: false },
    mandatory_files_waive: [],
  };
  const inheritPlan = compileGovernancePlan({ fs, authority: bent, authoritySha: SHA, repository: 'Quantum-L9/x', facts: marker('fixture_inherit') });
  assert.ok(!inheritPlan.materialize.files.some((f) => f.path === 'CODE_OF_CONDUCT.md'), 'inherited path not materialized');
  assert.ok(inheritPlan.materialize.files.some((f) => f.path === 'CONTRIBUTING.md'), 'non-inherited sibling still materialized');
  assert.deepStrictEqual(inheritPlan.inherit.paths, ['CODE_OF_CONDUCT.md']);
  // Labels disabled: no desired labels, no remote verification (B-12).
  assert.deepStrictEqual(inheritPlan.remote_apply.labels, { enabled: false, items: [] });
  assert.strictEqual(inheritPlan.attestation.verify_remote_apply, false);
  console.log('ok: INHERIT paths are dropped from materialize and listed under inherit');

  bent.classes.classes.fixture_forbid = {
    description: 'test fixture',
    seed_categories: ['governance'],
    inherit: [],
    forbid: ['.github/workflows/**'],
    remote_apply: {},
    mandatory_files_waive: [],
  };
  throwsCode(
    () => compileGovernancePlan({ fs, authority: bent, authoritySha: SHA, repository: 'Quantum-L9/x', facts: marker('fixture_forbid') }),
    'policy_contradiction',
    /forbidden paths: \.github\/workflows\/governance\.yml \(forbid \.github\/workflows\/\*\*\)/,
  );
  for (const retired of ['l9-ci-pack', 'on-org-update']) {
    bent.classes.classes.fixture_retired = { ...bent.classes.classes.fixture_forbid, seed_categories: [retired], forbid: [] };
    throwsCode(
      () => compileGovernancePlan({ fs, authority: bent, authoritySha: SHA, repository: 'Quantum-L9/x', facts: marker('fixture_retired') }),
      'policy_contradiction',
      /retired seed category/,
    );
  }
  console.log('ok: a FORBID path in materialize and a retired CI category both refuse the plan');

  // ── determinism and digest (GV-003, AC-CON-003/004/006) ─────────────────
  const digests = new Set();
  const bytes = new Set();
  for (let i = 0; i < 100; i++) {
    const plan = compile('Quantum-L9/determinism');
    digests.add(plan.digest.value);
    bytes.add(canonicalJson(plan));
  }
  assert.strictEqual(digests.size, 1, '100 identical compiles give one digest');
  assert.strictEqual(bytes.size, 1, '100 identical compiles give one canonical byte string');

  const base = compile('Quantum-L9/determinism');
  assert.strictEqual(base.digest.value, computePlanDigest(base));
  assert.strictEqual(base.digest.algorithm, 'sha256');
  assert.strictEqual(base.digest.canonicalization, 'l9.canonical-json/v1');
  // Key order never matters; the digest field itself never participates.
  const shuffled = Object.fromEntries(Object.entries(base).reverse());
  assert.strictEqual(computePlanDigest(shuffled), base.digest.value);
  assert.strictEqual(computePlanDigest({ ...base, digest: { value: 'x' } }), base.digest.value);
  // No volatile metadata exists in the plan to leak into the digest.
  assert.ok(!/"(timestamp|generated_at|run_id|created_at)"/.test(canonicalJson(base)), 'no run metadata in plan');
  // Every authoritative input moves the digest.
  assert.notStrictEqual(compile('Quantum-L9/other-name').digest.value, base.digest.value, 'target identity');
  assert.notStrictEqual(compile('Quantum-L9/determinism', { ...ABSENT, has_python: false }).digest.value, base.digest.value, 'target fact');
  assert.notStrictEqual(
    compileGovernancePlan({ fs, authoritySha: OTHER_SHA, repository: 'Quantum-L9/determinism', facts: ABSENT }).digest.value,
    base.digest.value,
    'authority SHA',
  );
  const bytePatched = clone(base);
  bytePatched.materialize.files[0].content_utf8 += ' ';
  assert.notStrictEqual(computePlanDigest(bytePatched), base.digest.value, 'one content byte');
  const settingsBent = clone(realAuthority);
  settingsBent.settings.defaults.has_wiki = true;
  assert.notStrictEqual(
    compileGovernancePlan({ fs, authority: settingsBent, authoritySha: SHA, repository: 'Quantum-L9/determinism', facts: ABSENT }).digest.value,
    base.digest.value,
    'policy byte',
  );
  // Canonicalization refuses values JSON cannot represent exactly.
  throwsCode(() => canonicalJson({ a: undefined }), 'digest');
  throwsCode(() => canonicalJson({ a: Number.NaN }), 'digest');
  assert.strictEqual(canonicalJson({ b: [2, 1], a: { d: 1, c: 'é' } }), '{"a":{"c":"é","d":1},"b":[2,1]}');
  console.log('ok: 100 compiles → 1 digest; key order and digest field excluded; every input moves it (GV-003)');

  // ── schema rejection (AC-CON-002, AC-ADV-007) ───────────────────────────
  for (const key of ['authority', 'target', 'repo_class', 'digest']) {
    const broken = clone(base);
    delete broken[key];
    assert.ok(validate(broken).length > 0, `schema rejects a plan missing ${key}`);
  }
  for (const bad of ['/etc/passwd', '../escape', 'a/../../b', 'a\\..\\b', 'C:\\x', 'nul\u0000byte']) {
    const broken = clone(base);
    broken.materialize.files[0].path = bad;
    assert.ok(validate(broken).length > 0, `schema rejects materialize path ${JSON.stringify(bad)}`);
  }
  const extraKey = clone(base);
  extraKey.surprise = true;
  assert.ok(validate(extraKey).length > 0, 'schema rejects unknown top-level keys');
  // The dev pack's "invalid-unknown-class" example is schema-VALID: class names
  // are policy, not shape, so only the compiler can reject them (errata #4).
  const unknownClassShape = clone(base);
  unknownClassShape.repo_class.name = 'totally_made_up';
  assert.deepStrictEqual(validate(unknownClassShape), [], 'an unknown class name is a compiler decision, not a schema one');
  console.log('ok: schema rejects missing sections, unsafe paths, and unknown keys');

  // ── mandatory files (C-07) ──────────────────────────────────────────────
  const ncp = compile('Quantum-L9/l9-repo-template');
  assert.deepStrictEqual(ncp.mandatory_files.waived, ['.github/workflows/governance.yml']);
  assert.ok(!ncp.mandatory_files.effective.some((r) => r.path === '.github/workflows/governance.yml'));
  assert.deepStrictEqual(
    compile('Quantum-L9/l9-ci-core').mandatory_files.waived,
    ['.github/CODEOWNERS', '.github/dependabot.yml', '.github/workflows/governance.yml'],
  );
  const dflt = compile('Quantum-L9/unlisted');
  assert.deepStrictEqual(dflt.mandatory_files.waived, []);
  assert.deepStrictEqual(
    dflt.mandatory_files.effective.find((r) => r.path === '.github/CODEOWNERS'),
    { path: '.github/CODEOWNERS', mode: 'managed', source: 'templates/CODEOWNERS.repo' },
  );
  assert.deepStrictEqual(dflt.mandatory_files.effective.find((r) => r.path === 'README.md'), { path: 'README.md', mode: 'present' });
  // Repo-level exceptions exempt every mandatory file, as enforce-policies does.
  const exempt = compile('Quantum-L9/.github');
  assert.deepStrictEqual(exempt.mandatory_files.effective, []);
  assert.strictEqual(exempt.mandatory_files.waived.length, realAuthority.mandatory.files.length);
  console.log('ok: effective mandatory files honor class waivers and repo exceptions');

  // ── repository settings (C-06) ──────────────────────────────────────────
  // The formula enforce-policies.yml and repo-birth-bootstrap.yml run inline.
  const workflowFormula = (repoName) => {
    const settings = parseJsonInYaml(fs.readFileSync('policies/repo-settings.yml', 'utf8'));
    const defaults = settings.defaults || {};
    const overrides = (settings.overrides || [])
      .filter((o) => o.repos && o.repos.includes(repoName))
      .reduce((acc, o) => ({ ...acc, ...o, repos: undefined }), {});
    const expected = { ...defaults, ...overrides };
    delete expected.repos;
    delete expected.default_branch;
    return expected;
  };
  for (const repoName of ['unlisted', 'l9-assurance', 'quantum-dashboard', 'Quantum-Website-Cursor', 'l9-ci-core']) {
    const desired = compile(`Quantum-L9/${repoName}`).remote_apply.repo_settings.desired;
    assert.deepStrictEqual(desired, workflowFormula(repoName), `settings for ${repoName}`);
    assert.deepStrictEqual(Object.keys(desired), Object.keys(workflowFormula(repoName)), `settings key order for ${repoName}`);
    for (const never of NEVER_AUTO_APPLIED_SETTINGS) assert.ok(!(never in desired), `${never} is never auto-applied`);
  }
  const assurance = compile('Quantum-L9/l9-assurance').remote_apply.repo_settings;
  assert.strictEqual(assurance.enabled, true);
  assert.strictEqual(assurance.desired.has_projects, true);
  assert.strictEqual(assurance.desired.allow_merge_commit, true);
  console.log('ok: desired settings equal the workflows\' defaults+overrides formula, default_branch excluded');

  // ── labels (C-06) ───────────────────────────────────────────────────────
  const labels = compile('Quantum-L9/unlisted').remote_apply.labels;
  assert.strictEqual(labels.enabled, true);
  assert.deepStrictEqual(labels.items, parseLabels(fs.readFileSync('.github/labels.yml', 'utf8')));
  const noLabels = clone(realAuthority);
  noLabels.labels = [];
  throwsCode(
    () => compileGovernancePlan({ fs, authority: noLabels, authoritySha: SHA, repository: 'Quantum-L9/x', facts: ABSENT }),
    'policy_contradiction',
    /parses to no labels/,
  );
  console.log('ok: desired labels are the exact parsed taxonomy; an empty taxonomy refuses the plan');

  // ── verifyPlan (AC-ADV-005 digest half, AC-ADV-008, AC-ADV-010) ─────────
  const expect = { schema: realAuthority.schema, authoritySha: SHA, repository: 'Quantum-L9/determinism' };
  assert.strictEqual(verifyPlan(base, { ...expect, digest: base.digest.value }), base);
  const tampered = clone(base);
  tampered.materialize.files[0].content_utf8 = 'rewritten';
  throwsCode(() => verifyPlan(tampered, expect), 'digest');
  throwsCode(() => verifyPlan(base, { ...expect, digest: 'f'.repeat(64) }), 'digest', /not the expected/);
  throwsCode(() => verifyPlan(base, { ...expect, authoritySha: OTHER_SHA }), 'authority_identity');
  throwsCode(() => verifyPlan(base, { ...expect, repository: 'Quantum-L9/someone-else' }), 'authority_identity');
  const schemaInvalid = clone(base);
  delete schemaInvalid.attestation;
  throwsCode(() => verifyPlan(schemaInvalid, expect), 'contract', /not schema-valid/);
  // A re-digested plan that sneaks a forbidden path in is still refused.
  const smuggled = clone(selfGoverned);
  smuggled.materialize.files.push({
    path: '.github/workflows/governance.yml',
    capability: 'governance',
    source: 'templates/governance-caller.yml',
    write_mode: 'missing_only',
    content_utf8: 'x',
    content_sha256: require('node:crypto').createHash('sha256').update('x').digest('hex'),
  });
  smuggled.digest.value = computePlanDigest(smuggled);
  throwsCode(() => verifyPlan(smuggled, { ...expect, repository: 'Quantum-L9/l9-ci-core' }), 'policy_contradiction');
  console.log('ok: verifyPlan refuses tampered content, stale digest, wrong authority, wrong target, invalid schema');

  // ── operator filters only narrow (GV-004, AC-ADV-003, AC-BEH-005) ───────
  const all = narrowMaterialization(dflt, null);
  assert.strictEqual(all.length, dflt.materialize.files.length);
  const narrowed = narrowMaterialization(dflt, ['codeowners', 'dependabot']);
  assert.deepStrictEqual(narrowed.map((f) => f.path).sort(), ['.github/CODEOWNERS', '.github/dependabot.yml']);
  throwsCode(() => narrowMaterialization(ncp, ['governance']), 'policy_contradiction', /not authorized/);
  throwsCode(() => narrowMaterialization(dflt, ['l9-ci-pack']), 'policy_contradiction', /not authorized/);
  console.log('ok: an operator filter narrows the plan and refuses any capability it does not authorize (GV-004)');

  // ── production provenance (B-20) ────────────────────────────────────────
  assert.doesNotThrow(() => assertCleanAuthority({ headSha: SHA, authoritySha: SHA, gitStatus: '' }));
  throwsCode(() => assertCleanAuthority({ headSha: SHA, authoritySha: OTHER_SHA, gitStatus: '' }), 'authority_identity', /not the asserted/);
  throwsCode(() => assertCleanAuthority({ headSha: SHA, authoritySha: SHA, gitStatus: ' M policies/repo-settings.yml\n' }), 'authority_identity', /differ/);
  throwsCode(() => assertCleanAuthority({ headSha: 'garbage', authoritySha: SHA, gitStatus: '' }), 'authority_identity');
  console.log('ok: a production compile refuses a dirty or mismatched authority checkout');

  // ── purity (AC-ARCH-005) ────────────────────────────────────────────────
  const source = fs.readFileSync('ops/compile-repo-governance.js', 'utf8');
  const libraryPart = source.slice(0, source.indexOf('// ── CLI'));
  assert.ok(!/github\.rest|octokit|@actions|https?\.request|fetch\(/.test(libraryPart), 'compiler library performs no GitHub or network I/O');
  assert.ok(!/child_process/.test(libraryPart), 'only the CLI shells out (to git, for provenance)');
  console.log('ok: the compiler library is pure — GitHub I/O stays in adapters');
} finally {
  process.chdir(origCwd);
}
