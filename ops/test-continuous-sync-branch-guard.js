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
const {
  notFound,
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
  'pulls.create',
]);

/**
 * @param {null|{sha:string}} branch  stubbed sync-branch state (null = absent)
 * @param {number[]} openPRs         open PR numbers with head BRANCH
 */
function makeGithub({ branch = null, openPRs = [] }) {
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
