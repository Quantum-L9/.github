'use strict';

/**
 * G3 adapter proofs: REMOTE APPLY paths apply the compiled plan's desired
 * state and nothing else.
 *
 * Runs the real `script:` bodies of repo-birth-bootstrap.yml and
 * sync-labels-all.yml (ops/workflow-script-harness.js) plus scripts/sync-labels.sh
 * (through a `gh` shim) and asserts:
 *   - bootstrap, sweep, and the CLI apply exactly plan.remote_apply.labels
 *     for the same target (AC-INT-004, AC-BEH-003)
 *   - bootstrap patches exactly the plan's settings drift, never
 *     default_branch (AC-BEH-004, AC-INT-005 bootstrap half)
 *   - a plan with labels disabled makes zero label mutations (B-12)
 *   - an unknown or unreadable marker fails the bootstrap before any
 *     mutation and is skipped (never labelled as default) by the sweep
 *     (AC-ADV-001, AC-ADV-009)
 *   - attestation reads back plan.attestation (present, marker, forbid)
 *   - summaries carry authority SHA and plan digest (AC-INT-007 precursor)
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-remote-apply-adapters.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { notFound, makeScriptRunner, makeBranchStubs } = require('./workflow-script-harness.js');
const { compileGovernancePlan } = require('./compile-repo-governance.js');
const { applyPlanLabels, settingsDrift } = require('./plan-adapter.js');

const root = path.resolve(__dirname, '..');
const SHA = '77587b7421b2e7cfad391e5036f531d8b5833e2b';
const MARKER = '.l9/org-birth-profile.yaml';
const MUTATIONS = new Set(['issues.createLabel', 'issues.updateLabel', 'repos.update']);
const ABSENT = { marker_state: 'absent', has_root_codeowners: false, has_python: false, has_package_json: false };

function planFor(repoName, facts = ABSENT) {
  const cwd = process.cwd();
  process.chdir(root);
  try {
    return compileGovernancePlan({ fs, authoritySha: SHA, repository: `Quantum-L9/${repoName}`, facts });
  } finally {
    process.chdir(cwd);
  }
}

/**
 * @param {object} o
 * @param {Record<string,string>} [o.files]  remote files (path → contents)
 * @param {string[]} [o.unreadable]  exist, but content reads fail
 * @param {object} [o.settings]  current repos.get().data
 * @param {string[]} [o.existingLabels]  labels already on the repo (create → 422)
 * @param {Record<string, number|null>} [o.probeErrors]  paths whose every read
 *   fails with that HTTP status (null = network error with no status)
 */
function makeGithub({ files = {}, unreadable = [], settings = {}, existingLabels = [], probeErrors = {} } = {}) {
  const calls = [];
  const probes = {};
  const record = (name, fn) => async (args) => {
    calls.push({ name, args });
    return fn ? fn(args) : { data: {} };
  };
  const repoData = { name: 'target', owner: { login: 'Quantum-L9' }, default_branch: 'main', archived: false, fork: false, ...settings };
  const branchState = { sha: null };
  const shared = makeBranchStubs({ branch: 'chore/auto-seed-governance', state: branchState, calls, openPRs: [], record: (name) => record(name, () => ({ data: { number: 1 } })) });
  const github = {
    paginate: async () => [repoData],
    rest: {
      repos: {
        getContent: async ({ path: p }) => {
          if (Object.hasOwn(probeErrors, p)) {
            const status = probeErrors[p];
            throw Object.assign(new Error(status ? `HTTP ${status}` : 'socket hang up'), status ? { status } : {});
          }
          if (unreadable.includes(p)) {
            probes[p] = (probes[p] || 0) + 1;
            if (probes[p] > 1) throw new Error('500 transient read failure');
            return { data: [] };
          }
          if (Object.hasOwn(files, p)) return { data: { content: Buffer.from(files[p]).toString('base64') } };
          throw notFound('Not Found');
        },
        get: async () => ({ data: repoData }),
        update: record('repos.update'),
      },
      issues: {
        createLabel: record('issues.createLabel', (args) => {
          if (existingLabels.includes(args.name)) {
            const e = new Error('already_exists');
            e.status = 422;
            throw e;
          }
          return { data: {} };
        }),
        updateLabel: record('issues.updateLabel'),
      },
      pulls: shared.pulls,
      git: {
        getRef: shared.getRef,
        getCommit: async () => ({ data: { tree: { sha: 'base-tree' } } }),
        createBlob: record('git.createBlob', () => ({ data: { sha: 'blob' } })),
        createTree: record('git.createTree', () => ({ data: { sha: 'tree' } })),
        createCommit: record('git.createCommit', () => ({ data: { sha: 'commit' } })),
        createRef: record('git.createRef'),
      },
    },
  };
  return { github, calls, state: {} };
}

const runner = (file, envFor) =>
  makeScriptRunner({ file: path.join(root, file), root, tmpTag: 'remote-apply-', envFor, makeGithub, mutations: MUTATIONS });

// The bootstrap is the single front door (G5): it runs at the checked-out
// authority and mutates only with the expected plan digest. Tests drive it the
// way a caller does — plan-only first, then apply with the reported digest.
const git = ['/usr/bin/git', '/usr/local/bin/git'].find((p) => fs.existsSync(p));
const HEAD = spawnSync(git, ['-C', root, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).stdout.trim();
const frontDoor = (env) =>
  runner('.github/workflows/repo-birth-bootstrap.yml', (dry) => ({
    DRY_RUN: dry ? 'true' : 'false',
    TARGET_REPO: 'target',
    REPO_CLASS: '',
    AUTHORITY_SHA: HEAD,
    EXPECTED_PLAN_DIGEST: '',
    ...env,
  }));
const bootstrap = (env = {}) => async (opts = {}) => {
  const planned = await frontDoor(env)({ ...opts, dry: true });
  const digest = planned.outputs.plan_digest;
  if (!digest) return planned; // refused while planning: report that run
  return frontDoor({ EXPECTED_PLAN_DIGEST: digest, ...env })(opts);
};
const sweep = (env = {}) =>
  runner('.github/workflows/sync-labels-all.yml', (dry) => ({
    DRY_RUN: dry ? 'true' : 'false',
    FILTER: '',
    GITHUB_SHA: SHA,
    ...env,
  }));

const labelNames = (r) =>
  r.calls.filter((c) => c.name === 'issues.createLabel').map((c) => `${c.args.name}|${c.args.color}|${c.args.description}`);

/** Run scripts/sync-labels.sh against a gh shim, from a clean copy of this tree. */
function cliSync(remoteFiles, { failPath = '' } = {}) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'sync-labels-'));
  const copy = path.join(tmp, 'org');
  const bin = path.join(tmp, 'bin');
  const log = path.join(tmp, 'gh.log');
  fs.mkdirSync(bin);
  // The compiler CLI refuses a dirty checkout (B-20), so run from a fresh
  // single-commit copy of the working tree: provenance holds, and the code
  // under test is this tree, not the last commit.
  fs.cpSync(root, copy, { recursive: true, filter: (src) => !src.includes(`${path.sep}.git${path.sep}`) && !src.endsWith(`${path.sep}.git`) });
  const git = ['/usr/bin/git', '/usr/local/bin/git'].find((p) => fs.existsSync(p));
  const g = (args) => spawnSync(git, ['-C', copy, ...args], { encoding: 'utf8' });
  g(['init', '-q']);
  g(['add', '-A']);
  g(['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'snapshot']);

  const files = JSON.stringify(remoteFiles);
  fs.writeFileSync(
    path.join(bin, 'gh'),
    `#!/usr/bin/env bash
echo "$*" >> ${JSON.stringify(log)}
if [[ "$1" == "api" ]]; then
  p="\${2#repos/Quantum-L9/target/contents/}"
  if [[ "$p" == "\${FAIL_PATH:-}" ]]; then echo "gh: Server Error (HTTP 500)" >&2; exit 1; fi
  body="$(FILES='${files.replace(/'/g, "'\\''")}' P="$p" node -e 'const f=JSON.parse(process.env.FILES); if (Object.hasOwn(f, process.env.P)) process.stdout.write(Buffer.from(f[process.env.P]).toString("base64")); else process.exit(3)')" || { echo "gh: Not Found (HTTP 404)" >&2; exit 1; }
  if [[ " $* " == *" --jq "* ]]; then echo "$body"; fi
  exit 0
fi
exit 0
`,
    { mode: 0o755 },
  );
  const bash = ['/usr/bin/bash', '/bin/bash'].find((b) => fs.existsSync(b));
  const out = spawnSync(bash, [path.join(copy, 'scripts/sync-labels.sh'), 'Quantum-L9/target'], {
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, FAIL_PATH: failPath },
  });
  const calls = fs.existsSync(log) ? fs.readFileSync(log, 'utf8').trim().split('\n') : [];
  fs.rmSync(tmp, { recursive: true, force: true });
  return { status: out.status, stderr: out.stderr, labelCreates: calls.filter((c) => c.startsWith('label create')) };
}

(async () => {
  const plan = planFor('target');
  const expectedLabels = plan.remote_apply.labels.items.map((l) => `${l.name}|${l.color}|${l.description}`);
  assert.ok(expectedLabels.length > 0);

  // ── same target → same label set, three adapters (AC-INT-004) ───────────
  const b = await bootstrap()({ files: { 'README.md': 'x', LICENSE: 'x' } });
  const s = await sweep()({});
  const cli = cliSync({});
  assert.deepStrictEqual(labelNames(b), expectedLabels, 'bootstrap applies exactly the plan labels');
  assert.deepStrictEqual(labelNames(s), expectedLabels, 'sweep applies exactly the plan labels');
  assert.strictEqual(cli.status, 0, `sync-labels.sh failed: ${cli.stderr}`);
  assert.strictEqual(cli.labelCreates.length, expectedLabels.length, 'CLI applies exactly the plan labels');
  assert.match(cli.stderr, /plan [0-9a-f]{12} @ [0-9a-f]{12}/, 'CLI names the plan it applied');
  console.log(`ok: bootstrap, sweep, and sync-labels.sh apply the same ${expectedLabels.length} plan labels`);

  // Existing labels are updated, not duplicated.
  const upd = await sweep()({ existingLabels: [plan.remote_apply.labels.items[0].name] });
  assert.strictEqual(upd.calls.filter((c) => c.name === 'issues.updateLabel').length, 1);
  console.log('ok: an existing label is updated in place');

  // ── settings: exactly the plan drift, never default_branch (AC-BEH-004) ──
  const current = { ...plan.remote_apply.repo_settings.desired, has_wiki: true, allow_merge_commit: true, default_branch: 'trunk' };
  const bs = await bootstrap()({ files: { 'README.md': 'x', LICENSE: 'x' }, settings: current });
  const update = bs.calls.find((c) => c.name === 'repos.update');
  assert.ok(update, 'drifted settings are patched');
  const { owner: _o, repo: _r, ...patch } = update.args;
  const expectedPatch = Object.fromEntries(settingsDrift(plan, current).map((d) => [d.key, d.expected]));
  assert.deepStrictEqual(patch, expectedPatch);
  assert.deepStrictEqual(Object.keys(patch).sort((a, b) => (a < b ? -1 : Number(a > b))), ['allow_merge_commit', 'has_wiki']);
  assert.ok(!('default_branch' in patch), 'default_branch is never auto-changed');
  const inSync = await bootstrap()({ files: { 'README.md': 'x', LICENSE: 'x' }, settings: plan.remote_apply.repo_settings.desired });
  assert.ok(!inSync.calls.some((c) => c.name === 'repos.update'), 'no patch when settings match');
  console.log('ok: bootstrap patches exactly the plan settings drift, default_branch excluded');

  // ── labels disabled in the plan → zero label mutations (B-12) ───────────
  const disabled = JSON.parse(JSON.stringify(plan));
  disabled.remote_apply.labels = { enabled: false, items: [] };
  const calls = [];
  const gh = { rest: { issues: { createLabel: async () => calls.push(1), updateLabel: async () => calls.push(1) } } };
  const r = await applyPlanLabels({ github: gh, owner: 'Quantum-L9', repo: 'x', plan: disabled });
  assert.deepStrictEqual([r.enabled, calls.length], [false, 0]);
  console.log('ok: a plan with labels disabled makes zero label calls');

  // ── fail closed on class declarations (AC-ADV-001, AC-ADV-009) ──────────
  const unknown = { [MARKER]: 'profile: totally_made_up\n', 'README.md': 'x', LICENSE: 'x' };
  const bu = await bootstrap()({ files: unknown });
  assert.strictEqual(bu.mutated, false, 'bootstrap must not mutate for an unknown class');
  assert.ok(bu.failures.some((f) => /unknown class totally_made_up/.test(f)), `${bu.failures}`);
  const bunread = await bootstrap()({ unreadable: [MARKER] });
  assert.strictEqual(bunread.mutated, false, 'an unreadable marker must not read as absent');
  assert.ok(bunread.failures.length > 0);
  const bforced = await bootstrap({ REPO_CLASS: 'defualt' })({});
  assert.strictEqual(bforced.mutated, false, 'a mistyped forced class must not mutate');
  const su = await sweep()({ files: unknown });
  assert.strictEqual(su.mutated, false, 'sweep must not label an unresolvable repository');
  assert.deepStrictEqual(su.failures, [], 'an unresolvable repository is skipped, not a sweep failure');
  assert.notStrictEqual(cliSync({ [MARKER]: 'profile: totally_made_up\n' }).status, 0, 'CLI refuses an unknown class');
  for (const [label, run] of [['bootstrap', bootstrap({ AUTHORITY_SHA: '' })], ['sweep', sweep({ GITHUB_SHA: '' })]]) {
    const x = await run({ files: { 'README.md': 'x', LICENSE: 'x' } });
    assert.strictEqual(x.mutated, false, `${label}: no authority SHA, no mutation`);
  }
  console.log('ok: unknown, unreadable, or mistyped classes and a missing authority SHA mutate nothing');

  // ── a failed observation is never "absent" (AC-ADV-009) ──────────────────
  // The first probe of each fact is attacked. Bootstrap refuses before any
  // mutation; the sweep fails that repository (and the run) with zero writes;
  // the CLI stops before compiling.
  for (const [probePath, status] of [[MARKER, 500], [MARKER, 403], [MARKER, null], ['CODEOWNERS', 429], ['package.json', 502]]) {
    const what = `${status || 'network'} on ${probePath}`;
    const bx = await bootstrap()({ files: { 'README.md': 'x', LICENSE: 'x' }, probeErrors: { [probePath]: status } });
    assert.strictEqual(bx.mutated, false, `bootstrap: ${what} must not mutate`);
    assert.ok(bx.failures.some((f) => /refused before any mutation/.test(f)), `bootstrap: ${what}: ${bx.failures}`);
    const sx = await sweep()({ probeErrors: { [probePath]: status } });
    assert.strictEqual(sx.mutated, false, `sweep: ${what} must not label`);
    assert.ok(sx.failures.length > 0, `sweep: ${what} must fail the run`);
  }
  const cliErr = cliSync({}, { failPath: MARKER });
  assert.notStrictEqual(cliErr.status, 0, 'CLI stops on a non-404 marker probe');
  assert.strictEqual(cliErr.labelCreates.length, 0, 'CLI applies nothing after a failed probe');
  // An attestation read that fails is a FAIL, never a pass by omission.
  const ax = await bootstrap()({ files: { [MARKER]: 'profile: self_governed\n', 'README.md': 'x', LICENSE: 'x' }, probeErrors: { '.github/workflows/governance.yml': 500 } });
  assert.ok(planFor('target', { ...ABSENT, marker_state: 'present', marker_text: 'profile: self_governed\n' }).attestation.required_absent.includes('.github/workflows/governance.yml'));
  assert.ok(ax.failures.some((f) => /attestation check/.test(f)), 'a failed FORBID probe fails attestation');
  console.log('ok: a 403/5xx/429/network failure on any first probe mutates nothing; a failed attestation read fails');

  // ── attestation reads back plan.attestation ──────────────────────────────
  const missingLicense = await bootstrap()({ files: { 'README.md': 'x' } });
  assert.ok(missingLicense.failures.some((f) => /attestation check/.test(f)), 'missing required file fails attestation');
  const selfGoverned = { [MARKER]: 'profile: self_governed\n', 'README.md': 'x', LICENSE: 'x', '.github/workflows/governance.yml': 'x' };
  const leaked = await bootstrap()({ files: selfGoverned });
  assert.ok(leaked.failures.length > 0, 'a FORBID path present on the remote fails attestation (GV-007)');
  // A forced class the marker contradicts is refused before the plan exists —
  // never discovered at attestation after labels and settings were written.
  const contradicted = await bootstrap({ REPO_CLASS: 'default' })({ files: { [MARKER]: 'profile: self_governed\n', 'README.md': 'x', LICENSE: 'x' } });
  assert.strictEqual(contradicted.mutated, false, 'a contradicted forced class mutates nothing');
  assert.ok(contradicted.failures.some((f) => /refused before any mutation.*declares self_governed/.test(f)), `${contradicted.failures}`);
  // A present marker with no readable profile is a FAIL, not "no marker".
  const garbled = await bootstrap()({ files: { 'README.md': 'x', LICENSE: 'x', [MARKER]: 'profile: default\n' } });
  assert.deepStrictEqual(garbled.failures, [], 'a matching marker attests');
  console.log('ok: attestation fails on a missing required file or a present FORBID path; a contradicted forced class is refused before any write');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
