'use strict';

/**
 * Runs the real `script:` body of the continuous-sync workflow against a
 * stubbed GitHub API and asserts it never rewrites the sync branch while a PR
 * is open on it.
 *
 * Why this is separate from test-seed-workflow-branch-guard.js: the two seed
 * workflows build a commit and move the ref with a GraphQL compare-and-swap,
 * so their proof is shaped around `git.createCommit` / `graphql.updateRefs`.
 * continuous-sync instead resets the ref with REST `git.updateRef({force})`
 * and writes files with `repos.createOrUpdateFileContents`. Same hazard,
 * different call surface — so it gets its own harness rather than distorting
 * the seed one.
 *
 * The defect (issue #60): the open-PR check ran AFTER the ref reset, so the
 * branch was already clobbered by the time the workflow reported
 * "PR already open". Scenario 1 fails against the pre-fix workflow.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-continuous-sync-branch-guard.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const WORKFLOW = '.github/workflows/continuous-sync.yml';
const BRANCH = 'chore/governance-sync';
const ORG = 'Quantum-L9';

/** Any successful write to the consumer repo. A read is not a mutation. */
const MUTATIONS = new Set([
  'git.createRef',
  'git.updateRef',
  'repos.createOrUpdateFileContents',
  'pulls.create',
]);

/** Extract the github-script `script: |` block without a YAML dependency. */
function extractScript(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const start = lines.findIndex((l) => /^\s*script:\s*\|\s*$/.test(l));
  assert.ok(start !== -1, `no "script: |" block in ${file}`);
  const indent = lines[start].match(/^\s*/)[0].length + 2;
  const body = [];
  for (const line of lines.slice(start + 1)) {
    if (line.trim() !== '' && line.match(/^\s*/)[0].length < indent) break;
    body.push(line.slice(indent));
  }
  return body.join('\n');
}

/** Load the extracted body as a real module — no eval, real stack traces. */
function loadScriptModule(file) {
  const body = extractScript(file);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sync-guard-'));
  const mod = path.join(dir, 'continuous-sync.script.js');
  fs.writeFileSync(
    mod,
    `'use strict';\nmodule.exports = async (github, core, context, require) => {\n${body}\n};\n`,
  );
  try {
    return require(mod);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

const notFound = (msg) => Object.assign(new Error(msg), { status: 404 });

/**
 * @param {null|{sha:string}} branch  stubbed sync-branch state (null = absent)
 * @param {number[]} openPRs         open PR numbers with head BRANCH
 */
function makeGithub({ branch, openPRs }) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'pulls.create') return { data: { number: 999 } };
    if (name === 'git.createRef') state.sha = args.sha;
    if (name === 'git.updateRef') state.sha = args.sha;
    return { data: {} };
  };

  return {
    github: {
      paginate: async () => [
        {
          name: 'consumer-repo',
          owner: { login: ORG },
          default_branch: 'main',
          archived: false,
          fork: false,
        },
      ],
      rest: {
        repos: {
          listForOrg: () => {},
          // Every managed path missing => maximal drift, so the workflow always
          // reaches the branch-write path this test is about.
          getContent: async (args) => {
            calls.push({ name: 'repos.getContent', args });
            throw notFound('Not Found');
          },
          createOrUpdateFileContents: record('repos.createOrUpdateFileContents'),
        },
        pulls: {
          list: async (args) => {
            calls.push({ name: 'pulls.list', args });
            return { data: openPRs.map((number) => ({ number })) };
          },
          create: record('pulls.create'),
        },
        git: {
          getRef: async (args) => {
            calls.push({ name: 'git.getRef', args });
            if (args.ref === `heads/${BRANCH}`) {
              if (state.sha === null) throw notFound('Branch not found');
              return { data: { object: { sha: state.sha } } };
            }
            return { data: { object: { sha: 'base-sha' } } };
          },
          createRef: async (args) => {
            calls.push({ name: 'git.createRef', args });
            if (state.sha !== null) throw Object.assign(new Error('exists'), { status: 422 });
            state.sha = args.sha;
            return { data: {} };
          },
          updateRef: record('git.updateRef'),
        },
      },
    },
    calls,
    state,
  };
}

function makeCore() {
  const failures = [];
  const summary = {
    addHeading: () => summary,
    addRaw: () => summary,
    addTable: () => summary,
    write: async () => summary,
  };
  return { info() {}, error() {}, setFailed: (m) => failures.push(m), failures, summary };
}

const scopedRequire = (m) => require(m.startsWith('.') ? path.resolve(root, m) : m);

const fn = loadScriptModule(path.join(root, WORKFLOW));

async function run({ branch, openPRs = [], dry = false } = {}) {
  const prevCwd = process.cwd();
  const env = { DRY_RUN: dry ? 'true' : 'false', FILTER: '' };
  const prevEnv = Object.fromEntries(Object.keys(env).map((k) => [k, process.env[k]]));
  process.chdir(root);
  Object.assign(process.env, env);
  const { github, calls, state } = makeGithub({ branch, openPRs });
  const core = makeCore();
  try {
    await fn(github, core, {}, scopedRequire);
  } finally {
    process.chdir(prevCwd);
    for (const [k, v] of Object.entries(prevEnv)) {
      if (v === undefined) delete process.env[k];
      else process.env[k] = v;
    }
  }
  const names = calls.map((c) => c.name);
  return { calls, names, state, failures: core.failures, mutated: names.some((n) => MUTATIONS.has(n)) };
}

(async () => {
  const label = path.basename(WORKFLOW);

  // 1. The defect: a PR is open on the sync branch, which carries review fixes.
  //    Nothing may be written, and the branch must still point where it did.
  let r = await run({ branch: { sha: 'branch-with-review-fixes' }, openPRs: [42] });
  assert.strictEqual(r.mutated, false, `${label}: wrote to a repo with an open sync PR`);
  assert.strictEqual(
    r.state.sha,
    'branch-with-review-fixes',
    `${label}: sync branch was moved despite an open PR`,
  );
  assert.deepStrictEqual(r.failures, [], `${label}: leaving a branch alone is not a failure`);
  console.log(`ok: ${label} — open sync PR leaves the branch untouched`);

  // 2. The guard must precede the ref write, not merely report after it.
  const firstWriteIdx = r.names.findIndex((n) => MUTATIONS.has(n));
  assert.strictEqual(firstWriteIdx, -1, `${label}: a write slipped past the open-PR guard`);
  assert.ok(
    r.names.includes('pulls.list'),
    `${label}: the open-PR probe must actually run`,
  );
  const probeIdx = r.names.indexOf('pulls.list');
  const refReadIdx = r.names.indexOf('git.getRef');
  assert.ok(
    refReadIdx === -1 || probeIdx < refReadIdx,
    `${label}: the open-PR probe must precede any branch ref read`,
  );
  console.log(`ok: ${label} — open-PR probe runs before any ref read or write`);

  // 3. No open PR, branch absent: create it and open a PR. Normal operation
  //    must survive the guard.
  r = await run({ branch: null });
  assert.ok(r.names.includes('git.createRef'), `${label}: fresh repo must get a sync branch`);
  assert.ok(r.names.includes('pulls.create'), `${label}: fresh repo must get a sync PR`);
  console.log(`ok: ${label} — repo with no open PR is still synced`);

  // 4. No open PR, branch already exists: reset is permitted (nothing is in
  //    flight), so drift remediation is not deadlocked by the guard.
  r = await run({ branch: { sha: 'stale-sync-branch' } });
  assert.ok(r.names.includes('git.updateRef'), `${label}: stale branch with no PR should refresh`);
  assert.ok(r.names.includes('pulls.create'), `${label}: refreshed branch should get a PR`);
  console.log(`ok: ${label} — stale branch with no open PR is refreshed`);

  // 5. Dry run writes nothing at all.
  r = await run({ branch: { sha: 'stale-sync-branch' }, dry: true });
  assert.strictEqual(r.mutated, false, `${label}: dry run performed a write`);
  console.log(`ok: ${label} — dry run performs no writes`);

  console.log('\nall continuous-sync branch-guard scenarios passed');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
