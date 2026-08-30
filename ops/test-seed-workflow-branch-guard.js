'use strict';

/**
 * Runs the real `script:` body of both seed workflows against a stubbed GitHub
 * API and asserts neither ever rewrites a seed branch that carries work the
 * seeder did not author.
 *
 * The 2026-08-22 incident: while a consumer seed PR was being remediated, two
 * cron ticks rebuilt `chore/auto-seed-governance` from the default branch and
 * force-updated the ref, discarding the remediation commits. Scenario 1 below
 * is that exact sequence; it fails against the pre-fix workflow.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-workflow-branch-guard.js
 */
const assert = require('node:assert');
const path = require('node:path');
const {
  notFound,
  makeScriptRunner,
  makeBranchStubs,
} = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');

const SEEDER_LOGIN = 'seeder-bot';

// Both seeders share the rebuild-then-move-ref shape, so both get the same proof.
const WORKFLOWS = [
  {
    file: '.github/workflows/auto-seed-new-repo.yml',
    branch: 'chore/auto-seed-governance',
    seedSubject: 'chore(governance): auto-seed 28 org template file(s)',
    env: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', TARGET_REPO: '' }),
  },
  {
    file: '.github/workflows/seed-governance.yml',
    branch: 'chore/seed-governance',
    seedSubject: 'chore(governance): seed 28 org template file(s)',
    env: (dry) => ({
      SEED_MODE: dry ? 'dry-run' : 'seed',
      SEED_REPO_FILTER: '',
      SEED_CATEGORIES: 'all',
    }),
  },
];

// Successful writes only — a rejected compare-and-swap attempt is not a mutation.
const MUTATIONS = new Set([
  'git.createRef',
  'git.createCommit',
  'pulls.create',
  'graphql.updateRefs',
]);

/**
 * @param {string} BRANCH               seed branch the workflow under test uses
 * @param {null|{sha,aheadBy,commits}} branch  stubbed remote branch state;
 *   commits are `{message, committer, verified}` fixtures, oldest first
 * @param {number[]} openPRs            open PR numbers with head BRANCH
 */
function makeGithub(BRANCH, { branch = null, openPRs = [] }) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'git.createBlob') return { data: { sha: 'blob-sha' } };
    if (name === 'git.createTree') return { data: { sha: 'tree-sha' } };
    if (name === 'git.createCommit') return { data: { sha: 'new-commit-sha' } };
    if (name === 'pulls.create') return { data: { number: 999 } };
    if (name === 'git.createRef') state.sha = args.sha;
    return { data: {} };
  };

  const shared = makeBranchStubs({ branch: BRANCH, state, calls, openPRs, record });

  const github = {
    paginate: async () => [
      {
        name: 'consumer-repo',
        owner: { login: 'Quantum-L9' },
        default_branch: 'main',
        archived: false,
        fork: false,
      },
    ],
    request: async (route, args) => {
      calls.push({ name: `request ${route}`, args });
      assert.strictEqual(route, 'GET /repos/{owner}/{repo}/compare/{basehead}');
      assert.strictEqual(args.basehead, `main...${BRANCH}`);
      assert.ok(branch, 'compare requested for a branch that does not exist');
      return {
        data: {
          ahead_by: branch.aheadBy,
          commits: branch.commits.map((c, i) => ({
            sha: `c${i}`,
            commit: {
              message: c.message,
              verification: { verified: c.verified === true },
              author: c.authorDate ? { date: c.authorDate } : undefined,
              committer: c.committerDate ? { date: c.committerDate } : undefined,
            },
            committer: c.committer ? { login: c.committer } : null,
          })),
        },
      };
    },
    graphql: async (doc, vars) => {
      if (!/mutation/.test(doc)) {
        calls.push({ name: 'graphql repositoryId', args: vars });
        return { repository: { id: 'R_stub' } };
      }
      assert.match(doc, /updateRefs/, 'only updateRefs mutations are expected');
      if (state.sha === null || vars.beforeOid !== state.sha) {
        calls.push({ name: 'graphql.updateRefs.rejected', args: vars });
        throw new Error(`could not update refs: expected "${vars.beforeOid}"`);
      }
      calls.push({ name: 'graphql.updateRefs', args: vars });
      state.sha = vars.afterOid;
      return { updateRefs: { clientMutationId: null } };
    },
    rest: {
      users: {
        getAuthenticated: async () => {
          calls.push({ name: 'users.getAuthenticated', args: {} });
          return { data: { login: SEEDER_LOGIN } };
        },
      },
      repos: {
        // Every seed path is missing on the consumer: the full payload is selected.
        getContent: async () => {
          throw notFound('Not Found');
        },
        get: async () => {
          throw notFound('Not Found');
        },
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

function makeRunner(wf) {
  return makeScriptRunner({
    file: path.join(root, wf.file),
    root,
    tmpTag: 'seed-guard-',
    envFor: wf.env,
    makeGithub: (o) => makeGithub(wf.branch, o),
    mutations: MUTATIONS,
  });
}

(async () => {
  for (const wf of WORKFLOWS) {
    const run = makeRunner(wf);
    const SEED = wf.seedSubject;
    const seedCommit = { message: SEED, committer: SEEDER_LOGIN, verified: true };
    const label = path.basename(wf.file);

    // 1. The incident: remediation commits stacked on the seed commit.
    let r = await run({
      branch: {
        sha: 'branch-sha',
        aheadBy: 2,
        commits: [
          seedCommit,
          { message: 'fix(governance): make the seeded templates safe to run here', committer: 'human-dev', verified: true },
        ],
      },
    });
    assert.strictEqual(r.mutated, false, `${label}: rewrote a branch carrying remediation commits`);
    assert.deepStrictEqual(r.failures, [], `${label}: leaving a branch alone is not a failure`);
    console.log(`ok: ${label} — branch carrying non-seeder commits is left alone`);

    // 2. An open seed PR is work in flight — skip before any git read/write.
    r = await run({
      branch: { sha: 'branch-sha', aheadBy: 1, commits: [seedCommit] },
      openPRs: [42],
    });
    assert.strictEqual(r.mutated, false, `${label}: wrote to a repo with an open seed PR`);
    assert.ok(
      !r.names.some((n) => n.startsWith('request ')),
      `${label}: open PR must short-circuit before the compare call`,
    );
    console.log(`ok: ${label} — repo with an open seed PR is skipped`);

    // 3. Fresh repo: create the branch, never rewrite one.
    r = await run({ branch: null });
    assert.ok(r.names.includes('git.createRef'), `${label}: fresh repo must get a seed branch`);
    assert.ok(!r.names.includes('graphql.updateRefs'), `${label}: fresh repo must not rewrite a ref`);
    assert.ok(r.names.includes('pulls.create'), `${label}: fresh repo must get a seed PR`);
    console.log(`ok: ${label} — fresh repo is seeded with a created ref and a PR`);

    // 4. Pristine seeder branch with no open PR: refresh is allowed, and the
    //    ref move is a compare-and-swap pinned to the sha the verdict saw.
    r = await run({ branch: { sha: 'branch-sha', aheadBy: 1, commits: [seedCommit] } });
    const update = r.calls.find((c) => c.name === 'graphql.updateRefs');
    assert.ok(update, `${label}: pristine seeder branch should be refreshable`);
    assert.strictEqual(update.args.beforeOid, 'branch-sha', `${label}: CAS must pin the verdict sha`);
    assert.strictEqual(update.args.afterOid, 'new-commit-sha', `${label}: CAS must move to the new seed commit`);
    console.log(`ok: ${label} — pristine seeder branch is refreshed via compare-and-swap`);

    // 4b. Seed-subject commit with foreign or unverified provenance: left alone.
    for (const tampered of [
      { message: SEED, committer: 'mallory', verified: true },
      { message: SEED, committer: SEEDER_LOGIN, verified: false },
    ]) {
      r = await run({ branch: { sha: 'branch-sha', aheadBy: 1, commits: [tampered] } });
      assert.strictEqual(
        r.mutated,
        false,
        `${label}: rewrote a branch whose seed-subject commit has foreign provenance`,
      );
    }
    console.log(`ok: ${label} — seed-subject commit with foreign provenance is left alone`);

    // PAT Git Data commits are unsigned; matching author/committer dates prove no amend.
    r = await run({
      branch: {
        sha: 'branch-sha',
        aheadBy: 1,
        commits: [{
          message: SEED,
          committer: SEEDER_LOGIN,
          verified: false,
          authorDate: '2026-08-25T23:04:56Z',
          committerDate: '2026-08-25T23:04:56Z',
        }],
      },
    });
    assert.ok(
      r.calls.some((c) => c.name === 'graphql.updateRefs'),
      `${label}: unsigned PAT seed commit with matching dates should refresh`,
    );
    console.log(`ok: ${label} — unsigned PAT seed commit with matching dates is refreshed`);

    // 5. Compare-and-swap: the branch moves between the verdict and the ref write.
    r = await run({
      branch: { sha: 'branch-sha', aheadBy: 1, commits: [seedCommit] },
      mutateGithub: (github, state) => {
        const BRANCH = wf.branch;
        const realGetRef = github.rest.git.getRef;
        let seen = 0;
        github.rest.git.getRef = async (args) => {
          const res = await realGetRef(args);
          if (args.ref === `heads/${BRANCH}` && seen++ === 0) {
            // Someone pushes right after the verdict read.
            state.sha = 'someone-else-pushed';
          }
          return res;
        };
      },
    });
    assert.ok(
      !r.names.includes('graphql.updateRefs'),
      `${label}: a branch that moved mid-run must not be overwritten`,
    );
    assert.ok(
      r.names.includes('graphql.updateRefs.rejected'),
      `${label}: the guarded move must be attempted and rejected server-side`,
    );
    assert.strictEqual(r.state.sha, 'someone-else-pushed', `${label}: the moved ref must be untouched`);
    console.log(`ok: ${label} — branch that moves mid-run is left alone`);

    // 6. Dry run never writes.
    r = await run({ branch: null, dry: true });
    assert.strictEqual(r.mutated, false, `${label}: dry run must not write`);
    console.log(`ok: ${label} — dry run performs no writes`);
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
