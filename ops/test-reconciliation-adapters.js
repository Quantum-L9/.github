'use strict';

/**
 * G4 adapter proofs: enforcement and drift reconciliation read the same
 * compiled plan as birth and seed.
 *
 * Runs the real `script:` bodies of enforce-policies.yml and
 * continuous-sync.yml (ops/workflow-script-harness.js) and asserts:
 *   - enforcement checks exactly plan.mandatory_files.effective and sync
 *     repairs exactly its `managed` subset — one waiver answer (AC-INT-003,
 *     GOV-015)
 *   - a file the class waives is never restored (GV-005, AC-ADV-004, GOV-016)
 *   - required managed drift still opens a remediation PR with the org
 *     template bytes (B-15)
 *   - settings enforcement patches exactly the plan drift, never
 *     default_branch (B-13, AC-INT-005 enforcement half)
 *   - an unresolvable class is not enforced or repaired as default
 *     (checkpoint marker_fetch_error_fail_closed, AC-ADV-009)
 *   - repository exceptions and both opt-out markers still hold
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-reconciliation-adapters.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { notFound, makeScriptRunner } = require('./workflow-script-harness.js');
const { compileGovernancePlan } = require('./compile-repo-governance.js');
const { managedRequirements, settingsDrift } = require('./plan-adapter.js');

const root = path.resolve(__dirname, '..');
const SHA = '77587b7421b2e7cfad391e5036f531d8b5833e2b';
const MARKER = '.l9/org-birth-profile.yaml';
const MUTATIONS = new Set([
  'repos.update',
  'git.createRef',
  'git.updateRef',
  'repos.createOrUpdateFileContents',
  'pulls.create',
]);

function planFor(repoName, files = {}) {
  const cwd = process.cwd();
  process.chdir(root);
  try {
    const facts = { marker_state: 'absent', has_root_codeowners: false, has_python: false, has_package_json: false };
    if (Object.hasOwn(files, MARKER)) Object.assign(facts, { marker_state: 'present', marker_text: files[MARKER] });
    return compileGovernancePlan({ fs, authoritySha: SHA, repository: `Quantum-L9/${repoName}`, facts });
  } finally {
    process.chdir(cwd);
  }
}

/**
 * @param {object} o
 * @param {string} [o.name]  repository name the org listing returns
 * @param {Record<string,string>} [o.files]
 * @param {string[]} [o.unreadable]
 * @param {object} [o.settings]
 * @param {Record<string, number|null>} [o.probeErrors]  paths whose every read
 *   fails with that HTTP status (null = network error with no status)
 */
function makeGithub({ name = 'target', files = {}, unreadable = [], settings = {}, probeErrors = {} } = {}) {
  const calls = [];
  const probes = {};
  const record = (callName, data = {}) => async (args) => {
    calls.push({ name: callName, args });
    return { data };
  };
  const repoData = { name, owner: { login: 'Quantum-L9' }, default_branch: 'main', archived: false, fork: false, ...settings };
  const github = {
    paginate: async () => [repoData],
    rest: {
      repos: {
        getContent: async ({ path: p, ref }) => {
          calls.push({ name: 'repos.getContent', args: { path: p, ref } });
          if (Object.hasOwn(probeErrors, p)) {
            const status = probeErrors[p];
            throw Object.assign(new Error(status ? `HTTP ${status}` : 'socket hang up'), status ? { status } : {});
          }
          if (unreadable.includes(p)) {
            probes[p] = (probes[p] || 0) + 1;
            if (probes[p] > 1) throw new Error('500 transient read failure');
            return { data: [] };
          }
          if (Object.hasOwn(files, p)) return { data: { content: Buffer.from(files[p]).toString('base64'), sha: `sha-${p}` } };
          throw notFound('Not Found');
        },
        get: async () => ({ data: repoData }),
        update: record('repos.update'),
        createOrUpdateFileContents: record('repos.createOrUpdateFileContents'),
      },
      pulls: {
        list: async () => ({ data: [] }),
        create: record('pulls.create', { number: 777 }),
      },
      git: {
        getRef: async () => ({ data: { object: { sha: 'base-sha' } } }),
        createRef: record('git.createRef'),
        updateRef: record('git.updateRef'),
      },
    },
  };
  return { github, calls, state: {} };
}

const runner = (file, envFor) =>
  makeScriptRunner({ file: path.join(root, file), root, tmpTag: 'reconcile-', envFor, makeGithub, mutations: MUTATIONS });
const enforce = (env = {}) =>
  runner('.github/workflows/enforce-policies.yml', (dry) => ({ DRY_RUN: dry ? 'true' : 'false', FILTER: '', GITHUB_SHA: SHA, ...env }));
const sync = (env = {}) =>
  runner('.github/workflows/continuous-sync.yml', (dry) => ({ DRY_RUN: dry ? 'true' : 'false', FILTER: '', GITHUB_SHA: SHA, ...env }));

const rowFor = (r, name) => {
  const table = r.tables[0];
  const row = table && table.slice(1).find((cells) => cells[0] === name);
  return row ? row[row.length - 1] : 'compliant';
};
// Explicit code-unit order (Sonar S2871); identical to a comparator-less sort.
const byCodeUnit = (a, b) => (a < b ? -1 : Number(a > b));
const missingFrom = (status) => [...status.matchAll(/missing: ([^;]+)/g)].map((m) => m[1]).sort(byCodeUnit);
const restored = (r) => r.calls.filter((c) => c.name === 'repos.createOrUpdateFileContents').map((c) => c.args.path).sort(byCodeUnit);

(async () => {
  // ── one waiver answer for enforcement and sync (AC-INT-003, GOV-015) ────
  const cases = [
    ['target', {}],
    ['target', { [MARKER]: 'profile: non_constellation_python\n' }],
    ['l9-ci-core', {}], // self_governed via org override
  ];
  for (const [name, files] of cases) {
    const plan = planFor(name, files);
    const e = await enforce()({ name, files, settings: plan.remote_apply.repo_settings.desired });
    const s = await sync()({ name, files });
    const expectMissing = plan.mandatory_files.effective.map((r) => r.path).sort(byCodeUnit);
    const expectRestored = managedRequirements(plan).map((r) => r.path).sort(byCodeUnit);
    assert.deepStrictEqual(missingFrom(rowFor(e, name)), expectMissing, `${name} ${plan.repo_class.name}: enforcement set`);
    assert.deepStrictEqual(restored(s), expectRestored, `${name} ${plan.repo_class.name}: sync repair set`);
    for (const waived of plan.mandatory_files.waived) {
      assert.ok(!missingFrom(rowFor(e, name)).includes(waived), `${waived} waived but enforced`);
      assert.ok(!restored(s).includes(waived), `${waived} waived but restored`);
    }
  }
  console.log('ok: enforcement and continuous-sync apply the same plan waivers for default, non_constellation_python, self_governed');

  // ── a waived managed file is never restored (GV-005, AC-ADV-004) ─────────
  const sg = await sync()({ name: 'l9-ci-core' });
  assert.strictEqual(sg.mutated, false, 'self_governed waives every managed file: no repair, no branch, no PR');
  console.log('ok: continuous-sync opens nothing for a class that waives its managed files (GV-005)');

  // ── required managed drift is restored with template bytes (B-15) ───────
  const drift = await sync()({ files: { '.github/dependabot.yml': 'drifted\n' } });
  const writes = drift.calls.filter((c) => c.name === 'repos.createOrUpdateFileContents');
  const dep = writes.find((w) => w.args.path === '.github/dependabot.yml');
  assert.ok(dep, 'drifted managed file restored');
  assert.strictEqual(Buffer.from(dep.args.content, 'base64').toString('utf8'), fs.readFileSync(path.join(root, 'templates/dependabot.yml'), 'utf8'));
  const pr = drift.calls.find((c) => c.name === 'pulls.create');
  assert.ok(pr && /digest `[0-9a-f]{64}`/.test(pr.args.body), 'remediation PR records the plan digest');
  const dry = await sync()({ dry: true, files: { '.github/dependabot.yml': 'drifted\n' } });
  assert.strictEqual(dry.mutated, false);
  console.log('ok: required managed drift is restored from the plan-named template; dry run writes nothing');

  // ── settings enforcement patches exactly the plan drift (B-13) ──────────
  const plan = planFor('target');
  const current = { ...plan.remote_apply.repo_settings.desired, has_wiki: true, default_branch: 'trunk' };
  const es = await enforce()({ settings: current });
  const update = es.calls.find((c) => c.name === 'repos.update');
  const { owner: _o, repo: _r, ...patch } = update.args;
  assert.deepStrictEqual(patch, Object.fromEntries(settingsDrift(plan, current).map((d) => [d.key, d.expected])));
  assert.deepStrictEqual(Object.keys(patch), ['has_wiki']);
  const esDry = await enforce()({ dry: true, settings: current });
  assert.strictEqual(esDry.mutated, false);
  console.log('ok: enforcement patches exactly the plan settings drift, never default_branch; dry run writes nothing');

  // ── unresolvable class: not enforced, not repaired (fail closed) ────────
  const unknownClass = { files: { [MARKER]: 'profile: totally_made_up\n' } };
  const eu = await enforce()({ ...unknownClass, settings: current });
  assert.strictEqual(eu.mutated, false, 'no settings patch for an unresolvable class');
  assert.match(rowFor(eu, 'target'), /unresolvable repo class: .* not enforced/);
  assert.ok(!/missing:/.test(rowFor(eu, 'target')), 'no file findings computed under a default fallback');
  assert.ok(eu.warnings.some((w) => /unresolvable class/.test(w)), 'an unresolvable class is warned, not silent');
  const su = await sync()(unknownClass);
  assert.strictEqual(su.mutated, false, 'no repair for an unresolvable class');
  assert.match(rowFor(su, 'target'), /skipped: unresolvable repo class/);
  console.log('ok: an unknown marker class is neither enforced nor repaired as default, and is warned');

  // ── a failed observation is never "absent" (AC-ADV-009) ──────────────────
  // The FIRST probe of each fact is attacked — the opt-out marker, the class
  // marker, a codeowners fact, a managed file — not only a later read. Each
  // must leave the repository untouched AND turn the run red.
  const attacks = [
    ['enforce', enforce, '.l9/no-policy-enforcement', 500],
    ['enforce', enforce, MARKER, 403],
    ['enforce', enforce, 'CODEOWNERS', null],
    ['enforce', enforce, 'README.md', 502],
    ['sync', sync, '.l9/no-sync', 403],
    ['sync', sync, MARKER, 500],
    ['sync', sync, 'package.json', 429],
    ['sync', sync, '.github/dependabot.yml', 502],
  ];
  for (const [label, make, probePath, status] of attacks) {
    const what = `${label}: ${status || 'network'} on ${probePath}`;
    const r = await make()({ probeErrors: { [probePath]: status }, settings: current });
    assert.strictEqual(r.mutated, false, `${what} must not mutate`);
    assert.ok(r.failures.some((f) => /could not be evaluated/.test(f)), `${what} must fail the run: ${JSON.stringify(r.failures)}`);
    assert.match(rowFor(r, 'target'), /FAILED — not evaluated/, `${what} is reported, not a quiet row`);
  }
  // The second-read variant still fails closed.
  const unreadMarker = await enforce()({ unreadable: [MARKER], settings: current });
  assert.strictEqual(unreadMarker.mutated, false);
  assert.ok(unreadMarker.failures.length > 0);
  console.log('ok: a 403/5xx/429/network failure on any first probe mutates nothing and fails the run');

  // ── exceptions and opt-outs still hold ───────────────────────────────────
  const exempt = await enforce()({ name: 'Cursor-Governance', settings: planFor('Cursor-Governance').remote_apply.repo_settings.desired });
  assert.strictEqual(rowFor(exempt, 'Cursor-Governance'), 'compliant', 'exception repo has no mandatory-file findings');
  const optEnforce = await enforce()({ files: { '.l9/no-policy-enforcement': '' }, settings: current });
  assert.strictEqual(optEnforce.mutated, false);
  assert.strictEqual(rowFor(optEnforce, 'target'), 'opted out');
  const optSync = await sync()({ files: { '.l9/no-sync': '' } });
  assert.strictEqual(optSync.mutated, false);
  console.log('ok: repository exceptions, .l9/no-policy-enforcement, and .l9/no-sync still hold');

  // ── a non-class plan failure is the run's failure, not a green row ──────
  // Missing authority SHA stands in for any template/authority defect: it
  // disables every repository's plan, and must never finish green (F04).
  for (const [label, make] of [['enforce', enforce], ['sync', sync]]) {
    const r = await make({ GITHUB_SHA: '' })({ settings: current });
    assert.strictEqual(r.mutated, false, `${label}: no authority SHA, no mutation`);
    assert.ok(r.failures.some((f) => /could not be evaluated/.test(f)), `${label}: a plan failure must fail the run`);
  }
  console.log('ok: without an exact authority SHA neither enforcement nor sync mutates, and both runs fail');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
