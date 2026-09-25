'use strict';

/**
 * G2 adapter proofs: the three materialization paths execute the compiled
 * governance plan and nothing else.
 *
 * Runs the real `script:` bodies of auto-seed-new-repo.yml and
 * seed-governance.yml (ops/workflow-script-harness.js) and the shell path
 * (ops/sync-org-files.sh) against the same target, and asserts:
 *   - all three write exactly plan.materialize for the same facts (AC-INT-002,
 *     AC-INT-001 at the adapter boundary)
 *   - a class plan is honored: INHERIT not copied, FORBID not written
 *   - an operator filter can only narrow; an unauthorized category refuses
 *     the repository with zero writes (AC-ADV-003, GV-004)
 *   - an unknown or unreadable marker never falls back to default (AC-ADV-001,
 *     AC-ADV-009); a missing authority SHA writes nothing
 *   - the PR records the plan's authority SHA and digest (13-observability)
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-plan-adapters.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { notFound, makeScriptRunner, makeBranchStubs } = require('./workflow-script-harness.js');
const { compileGovernancePlan } = require('./compile-repo-governance.js');

const root = path.resolve(__dirname, '..');
const SHA = '77587b7421b2e7cfad391e5036f531d8b5833e2b';
const MARKER = '.l9/org-birth-profile.yaml';
const MUTATIONS = new Set(['git.createRef', 'git.createCommit', 'pulls.create', 'graphql.updateRefs', 'git.createBlob']);

/**
 * @param {string} branch
 * @param {object} o
 * @param {Record<string,string>} [o.files]  consumer files present on the remote
 * @param {string[]} [o.unreadable]  paths that exist but whose content read fails
 */
function makeGithub(branch, { files = {}, unreadable = [] } = {}) {
  const calls = [];
  const state = { sha: null };
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'git.createBlob') return { data: { sha: `blob-${calls.length}` } };
    if (name === 'git.createTree') return { data: { sha: 'tree-sha' } };
    if (name === 'git.createCommit') return { data: { sha: 'new-commit-sha' } };
    if (name === 'pulls.create') return { data: { number: 999 } };
    if (name === 'git.createRef') state.sha = args.sha;
    return { data: {} };
  };
  const shared = makeBranchStubs({ branch, state, calls, openPRs: [], record });
  const probes = {};
  const repoData = { name: 'consumer-repo', owner: { login: 'Quantum-L9' }, default_branch: 'main', archived: false, fork: false };
  const github = {
    paginate: async () => [repoData],
    request: async () => {
      throw new Error('compare must not be requested for an absent branch');
    },
    graphql: async () => {
      throw new Error('no graphql expected on a fresh repo');
    },
    rest: {
      users: { getAuthenticated: async () => ({ data: { login: 'seeder-bot' } }) },
      repos: {
        getContent: async ({ path: p }) => {
          if (unreadable.includes(p)) {
            // Existence probe succeeds; the content read fails.
            probes[p] = (probes[p] || 0) + 1;
            if (probes[p] > 1) throw new Error('500 transient read failure');
            return { data: [] };
          }
          if (Object.hasOwn(files, p)) {
            return { data: { content: Buffer.from(files[p]).toString('base64') } };
          }
          throw notFound('Not Found');
        },
        get: async () => ({ data: repoData }),
      },
      pulls: shared.pulls,
      git: {
        getRef: shared.getRef,
        getCommit: async () => ({ data: { tree: { sha: 'base-tree-sha' } } }),
        createBlob: record('git.createBlob'),
        createTree: record('git.createTree'),
        createCommit: record('git.createCommit'),
        createRef: record('git.createRef'),
      },
    },
  };
  return { github, calls, state };
}

const autoSeed = (env = {}) =>
  makeScriptRunner({
    file: path.join(root, '.github/workflows/auto-seed-new-repo.yml'),
    root,
    tmpTag: 'plan-auto-',
    envFor: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', TARGET_REPO: '', REPO_CLASS: '', GITHUB_SHA: SHA, ...env }),
    makeGithub: (o) => makeGithub('chore/auto-seed-governance', o),
    mutations: MUTATIONS,
  });

const seedGovernance = (env = {}) =>
  makeScriptRunner({
    file: path.join(root, '.github/workflows/seed-governance.yml'),
    root,
    tmpTag: 'plan-seed-',
    envFor: (dry) => ({ SEED_MODE: dry ? 'dry-run' : 'seed', SEED_REPO_FILTER: '', SEED_CATEGORIES: 'all', GITHUB_SHA: SHA, ...env }),
    makeGithub: (o) => makeGithub('chore/seed-governance', o),
    mutations: MUTATIONS,
  });

const treePaths = (r) => {
  const tree = r.calls.find((c) => c.name === 'git.createTree');
  return tree ? tree.args.tree.map((t) => t.path).sort() : [];
};

function planPaths(facts) {
  const cwd = process.cwd();
  process.chdir(root);
  try {
    const plan = compileGovernancePlan({ fs, authoritySha: SHA, repository: 'Quantum-L9/consumer-repo', facts });
    return plan.materialize.files.map((f) => f.path).sort();
  } finally {
    process.chdir(cwd);
  }
}

function shellSync(files, args = []) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'plan-shell-'));
  for (const [p, body] of Object.entries(files)) {
    fs.mkdirSync(path.dirname(path.join(dir, p)), { recursive: true });
    fs.writeFileSync(path.join(dir, p), body);
  }
  const bash = ['/usr/bin/bash', '/bin/bash'].find((b) => fs.existsSync(b));
  const out = spawnSync(bash, ['ops/sync-org-files.sh', dir, '--repo', 'Quantum-L9/consumer-repo', ...args], {
    cwd: root,
    encoding: 'utf8',
  });
  const written = [];
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      if (e.isDirectory()) walk(full);
      else written.push(path.relative(dir, full));
    }
  };
  walk(dir);
  fs.rmSync(dir, { recursive: true, force: true });
  return { status: out.status, written: written.filter((p) => !Object.hasOwn(files, p)).sort(), stderr: out.stderr };
}

(async () => {
  const ABSENT = { marker_state: 'absent', has_root_codeowners: false, has_python: false, has_package_json: false };

  // ── same facts → same writes, all three adapters (AC-INT-002) ───────────
  const expected = planPaths(ABSENT);
  assert.ok(expected.length > 0, 'default plan materializes files');
  const auto = await autoSeed()({});
  const seed = await seedGovernance()({});
  const shell = shellSync({});
  assert.deepStrictEqual(auto.failures, [], `auto-seed failed: ${auto.failures}`);
  assert.deepStrictEqual(seed.failures, [], `seed-governance failed: ${seed.failures}`);
  assert.strictEqual(shell.status, 0, `shell sync failed: ${shell.stderr}`);
  assert.deepStrictEqual(treePaths(auto), expected, 'auto-seed writes exactly the plan');
  assert.deepStrictEqual(treePaths(seed), expected, 'seed-governance writes exactly the plan');
  assert.deepStrictEqual(shell.written, expected, 'shell sync writes exactly the plan');
  console.log(`ok: auto-seed, seed-governance, and shell sync write the same ${expected.length} plan files`);

  // Plan identity reaches the PR (observability).
  const prBody = auto.calls.find((c) => c.name === 'pulls.create').args.body;
  assert.match(prBody, new RegExp(`authority \`${SHA}\``));
  assert.match(prBody, /digest `[0-9a-f]{64}`/);
  const seedBody = seed.calls.find((c) => c.name === 'pulls.create').args.body;
  assert.match(seedBody, /digest `[0-9a-f]{64}`/);
  console.log('ok: seed PRs record the plan authority SHA and digest');

  // ── a class plan is honored by every adapter ─────────────────────────────
  const ncpMarker = { [MARKER]: 'profile: non_constellation_python\n' };
  const ncpExpected = planPaths({ ...ABSENT, marker_state: 'present', marker_text: ncpMarker[MARKER] });
  assert.ok(ncpExpected.includes('.github/labels.yml') && !ncpExpected.includes('CODE_OF_CONDUCT.md'));
  const autoNcp = await autoSeed()({ files: ncpMarker });
  const seedNcp = await seedGovernance()({ files: ncpMarker });
  const shellNcp = shellSync(ncpMarker);
  assert.deepStrictEqual(treePaths(autoNcp), ncpExpected);
  assert.deepStrictEqual(treePaths(seedNcp), ncpExpected, 'seed-governance is class-aware (was class-blind: F-04)');
  assert.deepStrictEqual(shellNcp.written, ncpExpected, 'shell sync is class-aware');
  for (const p of [...treePaths(seedNcp), ...shellNcp.written]) {
    assert.ok(!/^\.github\/workflows\//.test(p), `${p}: FORBID path written`);
  }
  console.log('ok: a marker class governs all three adapters — INHERIT not copied, FORBID not written');

  // ── an operator filter only narrows (AC-ADV-003, GV-004) ─────────────────
  const narrowed = await seedGovernance({ SEED_CATEGORIES: 'codeowners' })({});
  assert.deepStrictEqual(treePaths(narrowed), ['.github/CODEOWNERS']);
  const widened = await seedGovernance({ SEED_CATEGORIES: 'governance' })({ files: ncpMarker });
  assert.strictEqual(widened.mutated, false, 'unauthorized category must write nothing');
  assert.ok(widened.failures.length === 1, 'an unauthorized category is a reported failure, not a skip');
  const retired = await seedGovernance({ SEED_CATEGORIES: 'l9-ci-pack' })({});
  assert.strictEqual(retired.mutated, false, 'retired CI category must write nothing');
  assert.strictEqual(shellSync(ncpMarker, ['--include', 'governance']).status, 2, 'shell refuses unauthorized category');
  console.log('ok: category filters narrow the plan; unauthorized and retired categories write nothing (GV-004)');

  // ── fail closed on explicit declarations (AC-ADV-001, AC-ADV-009) ────────
  const unknown = { [MARKER]: 'profile: totally_made_up\n' };
  for (const [label, run] of [['auto-seed', autoSeed()], ['seed-governance', seedGovernance()]]) {
    const r = await run({ files: unknown });
    assert.strictEqual(r.mutated, false, `${label}: unknown marker class must write nothing`);
    const unreadable = await run({ unreadable: [MARKER] });
    assert.strictEqual(unreadable.mutated, false, `${label}: an unreadable marker must not read as absent`);
  }
  // A forced operator class that does not exist stops auto-seed outright.
  const forced = await autoSeed({ REPO_CLASS: 'defualt' })({});
  assert.strictEqual(forced.mutated, false);
  assert.ok(forced.failures.some((f) => /operator requested unknown repo class defualt/.test(f)), `${forced.failures}`);
  console.log('ok: unknown, unreadable, or mistyped class declarations write nothing and never become default');

  // ── no authority revision, no plan, no writes (GOV-019) ──────────────────
  for (const [label, run] of [['auto-seed', autoSeed({ GITHUB_SHA: '' })], ['seed-governance', seedGovernance({ GITHUB_SHA: '' })]]) {
    const r = await run({});
    assert.strictEqual(r.mutated, false, `${label}: must not write without an authority SHA`);
    assert.ok(r.failures.length > 0, `${label}: a missing authority SHA must fail the run`);
  }
  console.log('ok: without an exact authority SHA neither seeder writes');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
