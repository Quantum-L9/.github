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
const path = require('node:path');
const fs = require('node:fs');
const {
  notFound,
  loadScriptModule,
  makeScopedRequire,
  makeScriptRunner,
  makeBranchStubs,
} = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = '.github/workflows/continuous-sync.yml';
const BRANCH = 'chore/governance-sync';
const ORG = 'Quantum-L9';

/** Any successful write to the consumer repo. A read is not a mutation. */
const MUTATIONS = new Set([
  'git.createRef',
  'git.updateRef',
  'repos.createOrUpdateFileContents',
  'repos.deleteFile',
  'pulls.create',
]);

const SYNC_COMMIT = { commit: { message: 'chore(governance): restore .github/CODEOWNERS to org standard' } };

/**
 * @param {null|{sha:string}} branch  stubbed sync-branch state (null = absent)
 * @param {number[]} openPRs         open PR numbers with head BRANCH
 */
function makeGithub({ branch = null, openPRs = [], branchCommits = [SYNC_COMMIT] }) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'pulls.create') return { data: { number: 999 } };
    if (name === 'git.createRef') state.sha = args.sha;
    if (name === 'git.updateRef') state.sha = args.sha;
    return { data: {} };
  };

  const shared = makeBranchStubs({ branch: BRANCH, state, calls, openPRs, record });

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
          deleteFile: record('repos.deleteFile'),
          compareCommits: async (args) => {
            calls.push({ name: 'repos.compareCommits', args });
            return { data: { ahead_by: branchCommits.length, commits: branchCommits } };
          },
        },
        pulls: shared.pulls,
        git: {
          getRef: shared.getRef,
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

const run = makeScriptRunner({
  file: path.join(root, WORKFLOW),
  root,
  tmpTag: 'sync-guard-',
  envFor: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', FILTER: '' }),
  makeGithub,
  mutations: MUTATIONS,
});

/**
 * Class-aware management of the PR template and governance caller. Driven
 * with a per-path repository fixture so each scenario states exactly what the
 * consumer holds; statuses are read from the run's own summary table.
 */
const TEMPLATE = '.github/pull_request_template.md';
const CALLER = '.github/workflows/governance.yml';
const canonicalTemplate = fs.readFileSync(path.join(root, TEMPLATE), 'utf8');
const canonicalPin = fs
  .readFileSync(path.join(root, 'policies/governance-caller.yml'), 'utf8')
  .match(/governance-pr\.yml@([0-9a-f]{40})/)[1];
const managedOk = {
  '.github/CODEOWNERS': fs.readFileSync(path.join(root, 'policies/CODEOWNERS'), 'utf8'),
  '.github/dependabot.yml': fs.readFileSync(path.join(root, '.github/dependabot.yml'), 'utf8'),
};
const syncScript = loadScriptModule(path.join(root, WORKFLOW), 'sync-class-');

async function runClass({ name = 'consumer', files = {}, dirs = {}, errors = {}, dry = false }) {
  const calls = [];
  const enc = (t) => Buffer.from(t).toString('base64');
  const github = {
    paginate: async () => [{ name, owner: { login: ORG }, default_branch: 'main', archived: false, fork: false }],
    rest: {
      repos: {
        listForOrg: () => {},
        getContent: async (args) => {
          calls.push({ name: 'repos.getContent', args });
          if (errors[args.path]) throw Object.assign(new Error('boom'), { status: errors[args.path] });
          if (args.path in dirs) return { data: dirs[args.path].map((n) => ({ name: n, type: n.includes('.') ? 'file' : 'dir' })) };
          if (args.path in files) return { data: { sha: `sha-${args.path}`, content: enc(files[args.path]) } };
          throw notFound('Not Found');
        },
        createOrUpdateFileContents: async (args) => { calls.push({ name: 'repos.createOrUpdateFileContents', args }); return { data: {} }; },
        deleteFile: async (args) => { calls.push({ name: 'repos.deleteFile', args }); return { data: {} }; },
        compareCommits: async () => ({ data: { ahead_by: 0, commits: [] } }),
      },
      pulls: {
        list: async () => ({ data: [] }),
        create: async (args) => { calls.push({ name: 'pulls.create', args }); return { data: { number: 5 } }; },
      },
      git: {
        getRef: async () => ({ data: { object: { sha: 'base-sha' } } }),
        createRef: async (args) => { calls.push({ name: 'git.createRef', args }); return { data: {} }; },
        updateRef: async (args) => { calls.push({ name: 'git.updateRef', args }); return { data: {} }; },
      },
    },
  };
  const tables = [];
  const failures = [];
  const summary = { addHeading: () => summary, addRaw: () => summary, addTable: (t) => { tables.push(t); return summary; }, write: async () => summary };
  const core = { info() {}, error() {}, setFailed: (m) => failures.push(m), summary };
  const prev = process.cwd();
  const prevEnv = { DRY_RUN: process.env.DRY_RUN, FILTER: process.env.FILTER };
  process.chdir(root);
  Object.assign(process.env, { DRY_RUN: dry ? 'true' : 'false', FILTER: '' });
  try {
    await syncScript(github, core, {}, makeScopedRequire(root));
  } finally {
    process.chdir(prev);
    for (const [k, v] of Object.entries(prevEnv)) {
      if (v === undefined) delete process.env[k];
      else process.env[k] = v;
    }
  }
  const [, klass, status, detail] = tables[0][1];
  const writes = calls.filter((c) => c.name === 'repos.createOrUpdateFileContents');
  const deletes = calls.filter((c) => c.name === 'repos.deleteFile');
  return { klass, status, detail, writes, deletes, failures, calls };
}

async function classScenarios() {
  const label = 'continuous-sync (class-aware)';
  const marker = (cls) => ({ '.l9/org-birth-profile.yaml': `profile: ${cls}\n` });
  const strictCaller = (pin) =>
    `name: Governance\njobs:\n  pr:\n    uses: Quantum-L9/.github/.github/workflows/governance-pr.yml@${pin}  # v1\n    with:\n      strict: true\n  issue:\n    uses: Quantum-L9/.github/.github/workflows/governance-issue.yml@${pin}  # v1\n`;

  // default class: a divergent template is replaced with the canonical bytes.
  let r = await runClass({ files: { ...managedOk, [TEMPLATE]: '## My own template\n' } });
  assert.strictEqual(r.klass, 'default');
  assert.strictEqual(r.status, 'UPDATE_PR_OPEN');
  assert.deepStrictEqual(r.writes.map((w) => w.args.path), [TEMPLATE]);
  assert.strictEqual(Buffer.from(r.writes[0].args.content, 'base64').toString(), canonicalTemplate);
  console.log(`ok: ${label} — default class: divergent template replaced with canonical bytes`);

  // default class, already canonical: nothing written, reported as such.
  r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate } });
  assert.strictEqual(r.status, 'CANONICAL_COPY');
  assert.strictEqual(r.calls.some((c) => c.name === 'pulls.create'), false);
  console.log(`ok: ${label} — canonical copy is a no-op (idempotent)`);

  // inherit classes: a local copy blocks inheritance and is removed; absence is the target.
  for (const cls of ['self_governed', 'non_constellation_python']) {
    r = await runClass({ files: { ...managedOk, ...marker(cls), [TEMPLATE]: canonicalTemplate } });
    assert.strictEqual(r.klass, cls);
    assert.deepStrictEqual(r.deletes.map((d) => d.args.path), [TEMPLATE], `${cls}: local copy not removed`);
    assert.strictEqual(r.writes.length, 0, `${cls}: inherit class must not get a copy`);
    r = await runClass({ files: { ...managedOk, ...marker(cls) } });
    assert.strictEqual(r.status, 'INHERITED');
  }
  console.log(`ok: ${label} — inherit classes: local copy removed; absence reported INHERITED`);

  // An unresolvable declared class touches nothing class-dependent.
  r = await runClass({ files: { ...managedOk, ...marker('no_such_class'), [TEMPLATE]: '## x\n' } });
  assert.strictEqual(r.status, 'BLOCKED_POLICY');
  assert.strictEqual(r.writes.length + r.deletes.length, 0);
  console.log(`ok: ${label} — unresolved class: template left alone, BLOCKED_POLICY`);

  // The caller is re-pinned, and only re-pinned: strict: true survives.
  const old = '3'.repeat(40);
  r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate, [CALLER]: strictCaller(old) } });
  assert.deepStrictEqual(r.writes.map((w) => w.args.path), [CALLER]);
  const repinned = Buffer.from(r.writes[0].args.content, 'base64').toString();
  assert.strictEqual(repinned, strictCaller(canonicalPin));
  assert.match(repinned, /strict: true/);
  r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate, [CALLER]: strictCaller(canonicalPin) } });
  assert.strictEqual(r.status, 'CANONICAL_COPY');
  console.log(`ok: ${label} — caller pins follow governance-caller.yml; consumer settings kept`);

  // Alternate templates are reported, never edited.
  r = await runClass({
    files: { ...managedOk, [TEMPLATE]: canonicalTemplate },
    dirs: { '.github': ['PULL_REQUEST_TEMPLATE', 'pull_request_template.md'], docs: ['PULL_REQUEST_TEMPLATE.md'] },
  });
  assert.strictEqual(r.status, 'CANONICAL_COPY');
  assert.match(r.detail, /alternate template dir \.github\/PULL_REQUEST_TEMPLATE/);
  assert.match(r.detail, /alternate template docs\/PULL_REQUEST_TEMPLATE\.md/);
  assert.strictEqual(r.writes.length + r.deletes.length, 0);
  console.log(`ok: ${label} — alternate templates reported, not edited`);

  // An unreadable repo is not "in sync", and the run says so.
  r = await runClass({ files: managedOk, errors: { [TEMPLATE]: 500 } });
  assert.strictEqual(r.status, 'UNREACHABLE');
  assert.strictEqual(r.failures.length, 1);
  r = await runClass({ files: managedOk, errors: { '.l9/no-sync': 403 } });
  assert.strictEqual(r.status, 'BLOCKED_PERMISSION');
  console.log(`ok: ${label} — unreadable repos fail the run instead of reading as in sync`);

  // Dry run reports drift and writes nothing.
  r = await runClass({ files: { ...managedOk, [TEMPLATE]: '## stale\n' }, dry: true });
  assert.strictEqual(r.status, 'DRIFT');
  assert.strictEqual(r.writes.length + r.deletes.length, 0);
  console.log(`ok: ${label} — dry run reports drift only`);
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

  // 4b. No open PR, but the branch carries a commit this workflow did not
  //     write (a closed PR's leftover human fix): never reset it.
  r = await run({
    branch: { sha: 'branch-with-a-human-fix' },
    branchCommits: [SYNC_COMMIT, { commit: { message: 'fix: maintainer tweak' } }],
  });
  // createRef is attempted (it 422s on an existing branch); nothing after it may run.
  for (const write of ['git.updateRef', 'repos.createOrUpdateFileContents', 'repos.deleteFile', 'pulls.create']) {
    assert.ok(!r.names.includes(write), `${label}: ${write} on a branch carrying foreign commits`);
  }
  assert.strictEqual(r.state.sha, 'branch-with-a-human-fix');
  console.log(`ok: ${label} — branch with a foreign commit is never reset`);

  // 5. Dry run writes nothing at all.
  r = await run({ branch: { sha: 'stale-sync-branch' }, dry: true });
  assert.strictEqual(r.mutated, false, `${label}: dry run performed a write`);
  console.log(`ok: ${label} — dry run performs no writes`);

  await classScenarios();
  console.log('\nall continuous-sync branch-guard scenarios passed');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
