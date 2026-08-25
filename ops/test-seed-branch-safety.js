'use strict';

/**
 * Asserts the seed-branch safety gate never authorizes a rebuild over work the
 * seeder did not author. Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-branch-safety.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const {
  SEED_COMMIT_SUBJECT,
  isSeedCommitMessage,
  classifySeedBranch,
  assessSeedBranch,
  moveSeedBranch,
} = require('./seed-branch-safety.js');

const root = path.resolve(__dirname, '..');

const autoSeedSubject = 'chore(governance): auto-seed 28 org template file(s)';
const seedSubject = 'chore(governance): seed 3 org template file(s)';

const SEEDER = 'seeder-bot';
const seedCommit = (message, over = {}) => ({
  sha: 'a1', message, committerLogin: SEEDER, verified: true, ...over,
});

// --- subject recognition -----------------------------------------------------
assert.strictEqual(isSeedCommitMessage(autoSeedSubject), true);
assert.strictEqual(isSeedCommitMessage(seedSubject), true);
assert.strictEqual(isSeedCommitMessage(`${autoSeedSubject}\n\nbody text`), true);
assert.strictEqual(isSeedCommitMessage('fix(ci): stop the seeder clobbering branches'), false);
assert.strictEqual(isSeedCommitMessage('chore(governance): auto-seed org template file(s)'), false);
assert.strictEqual(
  isSeedCommitMessage('Merge pull request #31 from Quantum-L9/feat/x'),
  false,
);
assert.strictEqual(isSeedCommitMessage(''), false);
assert.strictEqual(isSeedCommitMessage(null), false);
assert.strictEqual(isSeedCommitMessage(undefined), false);
assert.strictEqual(isSeedCommitMessage(42), false);

// --- safe to rebuild ---------------------------------------------------------
let v = classifySeedBranch({
  aheadBy: 1, commits: [seedCommit(autoSeedSubject)], seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, true, 'pristine seeder branch must be rebuildable');

v = classifySeedBranch({
  aheadBy: 1, commits: [seedCommit(seedSubject)], seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, true, 'manual seed branch must be rebuildable');

v = classifySeedBranch({ aheadBy: 0, commits: [], seederLogin: SEEDER });
assert.strictEqual(v.safeToReplace, true, 'branch with nothing ahead of base loses nothing');

// --- must be left alone ------------------------------------------------------
// The reported incident: remediation commits stacked on the seed commit.
v = classifySeedBranch({
  aheadBy: 2,
  commits: [
    seedCommit(autoSeedSubject),
    { sha: 'b2', message: 'fix(governance): make the seeded templates safe to run here' },
  ],
  seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, false, 'remediation commit must block the rebuild');
assert.match(v.reason, /2 commits/);

// A single foreign commit on the branch.
v = classifySeedBranch({
  aheadBy: 1, commits: [seedCommit('chore: unrelated')], seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, false, 'foreign single commit must block the rebuild');

// Provenance beyond the mutable subject line: a matching subject committed by
// someone else, or an amended (unverified) commit, must block the rebuild.
v = classifySeedBranch({
  aheadBy: 1,
  commits: [seedCommit(autoSeedSubject, { committerLogin: 'mallory' })],
  seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, false, 'seed subject from a foreign committer must block');
assert.match(v.reason, /mallory/);

v = classifySeedBranch({
  aheadBy: 1,
  commits: [seedCommit(autoSeedSubject, { verified: false })],
  seederLogin: SEEDER,
});
assert.strictEqual(v.safeToReplace, false, 'unverified seed-subject commit must block');
assert.match(v.reason, /verified/);

v = classifySeedBranch({
  aheadBy: 1, commits: [seedCommit(autoSeedSubject)], seederLogin: null,
});
assert.strictEqual(v.safeToReplace, false, 'unresolvable seeder identity must fail closed');

// Fail closed on anything unprovable.
for (const bad of [
  undefined,
  {},
  { aheadBy: 1 },
  { commits: [] },
  { aheadBy: null, commits: [] },
  { aheadBy: '1', commits: [seedCommit(autoSeedSubject)], seederLogin: SEEDER },
  { aheadBy: -1, commits: [] },
  { aheadBy: 1, commits: [], seederLogin: SEEDER },
  { aheadBy: 1, commits: [{ sha: 'a1' }], seederLogin: SEEDER },
]) {
  const verdict = classifySeedBranch(bad);
  assert.strictEqual(
    verdict.safeToReplace,
    false,
    `unprovable comparison must fail closed: ${JSON.stringify(bad)}`,
  );
  assert.ok(verdict.reason, 'every verdict carries a reason');
}

// --- workflows must agree with this module -----------------------------------
// The commit subjects the workflows write have to keep matching the pattern the
// gate recognizes, or the gate silently starts refusing every rebuild.
for (const [wf, subject] of [
  ['.github/workflows/auto-seed-new-repo.yml', autoSeedSubject],
  ['.github/workflows/seed-governance.yml', seedSubject],
]) {
  const text = fs.readFileSync(path.join(root, wf), 'utf8');
  const m = text.match(/message: `(chore\(governance\): [^`]*)`/);
  assert.ok(m, `${wf} must declare a seed commit message`);
  const rendered = m[1].replace(/\$\{[^}]*\}/g, '7');
  assert.ok(
    SEED_COMMIT_SUBJECT.test(rendered),
    `${wf} commit subject "${rendered}" is not recognized by the safety gate`,
  );
  assert.ok(isSeedCommitMessage(subject));

  // Neither workflow may reach a seed ref on its own: the gate and the ref
  // move are owned by this module so both seeders cannot drift apart.
  for (const fn of ['assessSeedBranch', 'moveSeedBranch']) {
    assert.ok(new RegExp(fn).test(text), `${wf} must call ${fn}`);
  }
  for (const forbidden of ['git.createRef', 'git.updateRef', 'updateRefs', 'force: true']) {
    assert.ok(
      !text.includes(forbidden),
      `${wf} touches a seed ref directly ("${forbidden}") instead of via moveSeedBranch`,
    );
  }
}

// --- assessSeedBranch / moveSeedBranch over a stubbed client ----------------
const notFound = (m) => Object.assign(new Error(m), { status: 404 });

function stub({ openPRs = [], branchSha = null, aheadBy = 1, commits = [seedCommit(autoSeedSubject)] } = {}) {
  const calls = [];
  const state = { sha: branchSha };
  const github = {
    request: async (route, args) => {
      calls.push(`request ${route}`);
      return {
        data: {
          ahead_by: aheadBy,
          commits: commits.map((c, i) => ({
            sha: c.sha || `c${i}`,
            commit: {
              message: c.message,
              verification: { verified: c.verified === true },
            },
            committer: c.committerLogin ? { login: c.committerLogin } : null,
          })),
        },
      };
    },
    graphql: async (doc, vars) => {
      if (!/mutation/.test(doc)) {
        calls.push('graphql repositoryId');
        return { repository: { id: 'R_stub' } };
      }
      assert.match(doc, /updateRefs/, 'only updateRefs mutations are expected');
      if (state.sha === null || vars.beforeOid !== state.sha) {
        calls.push('graphql.updateRefs.rejected');
        throw new Error(`could not update refs: expected "${vars.beforeOid}"`);
      }
      calls.push(`graphql.updateRefs before=${vars.beforeOid} after=${vars.afterOid}`);
      state.sha = vars.afterOid;
      return { updateRefs: { clientMutationId: null } };
    },
    rest: {
      users: {
        getAuthenticated: async () => {
          calls.push('users.getAuthenticated');
          return { data: { login: SEEDER } };
        },
      },
      pulls: {
        list: async () => {
          calls.push('pulls.list');
          return { data: openPRs.map((number) => ({ number })) };
        },
      },
      git: {
        getRef: async () => {
          calls.push('git.getRef');
          if (state.sha === null) throw notFound('Branch not found');
          return { data: { object: { sha: state.sha } } };
        },
        createRef: async () => {
          calls.push('git.createRef');
          return { data: {} };
        },
      },
    },
  };
  return { calls, state, github };
}

const where = { owner: 'Quantum-L9', repo: 'consumer', base: 'main', branch: 'chore/seed' };

(async () => {
  // Open PR short-circuits before any git read.
  let s = stub({ openPRs: [7] });
  let g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');
  assert.match(g.reason, /PR #7 already open/);
  assert.deepStrictEqual(s.calls, ['pulls.list'], 'open PR must not trigger a git read');

  // Absent branch → create, no compare call.
  s = stub({ branchSha: null });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'create');
  assert.strictEqual(g.sha, null);
  assert.ok(!s.calls.some((c) => c.startsWith('request ')), 'absent branch needs no compare');

  // Pristine branch → rebuild, carrying the sha the verdict was computed from.
  s = stub({ branchSha: 'abc123' });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'rebuild');
  assert.strictEqual(g.sha, 'abc123');

  // Branch with foreign work → skip.
  s = stub({
    branchSha: 'abc123',
    aheadBy: 2,
    commits: [seedCommit(autoSeedSubject), { sha: 'b2', message: 'fix: review feedback' }],
  });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');

  // Seed subject, wrong committer → skip (provenance, not string trust).
  s = stub({
    branchSha: 'abc123',
    commits: [seedCommit(autoSeedSubject, { committerLogin: 'mallory' })],
  });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');
  assert.match(g.reason, /mallory/);

  // Seed subject, unverified (amended) commit → skip.
  s = stub({
    branchSha: 'abc123',
    commits: [seedCommit(autoSeedSubject, { verified: false })],
  });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');

  // Seeder identity unresolvable → skip, never rebuild.
  s = stub({ branchSha: 'abc123' });
  s.github.rest.users.getAuthenticated = async () => {
    throw Object.assign(new Error('bad credentials'), { status: 401 });
  };
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');

  // A non-404 getRef error must surface, not be swallowed into "create".
  s = stub({ branchSha: 'abc123' });
  s.github.rest.git.getRef = async () => {
    throw Object.assign(new Error('boom'), { status: 500 });
  };
  await assert.rejects(() => assessSeedBranch({ github: s.github, ...where }), /boom/);

  // moveSeedBranch: create path never touches updateRefs.
  s = stub({ branchSha: null });
  let m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: null, commitSha: 'new1',
  });
  assert.strictEqual(m.moved, true);
  assert.ok(s.calls.includes('git.createRef'));
  assert.ok(!s.calls.some((c) => c.startsWith('graphql.updateRefs')));

  // moveSeedBranch: rebuild path is a server-side compare-and-swap.
  s = stub({ branchSha: 'abc123' });
  m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: 'abc123', commitSha: 'new1',
  });
  assert.strictEqual(m.moved, true);
  assert.ok(
    s.calls.includes('graphql.updateRefs before=abc123 after=new1'),
    'rebuild must pin beforeOid to the sha the verdict was computed from',
  );

  s = stub({ branchSha: 'someone-else-pushed' });
  m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: 'abc123', commitSha: 'new1',
  });
  assert.strictEqual(m.moved, false, 'a moved branch must not be overwritten');
  assert.ok(s.calls.includes('graphql.updateRefs.rejected'));
  assert.ok(!s.calls.some((c) => c.startsWith('graphql.updateRefs before=')));
  assert.strictEqual(s.state.sha, 'someone-else-pushed', 'the moved ref must be untouched');

  // A branch that appears mid-run is reported, not force-updated.
  s = stub({ branchSha: null });
  s.github.rest.git.createRef = async () => {
    throw Object.assign(new Error('Reference already exists'), { status: 422 });
  };
  m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: null, commitSha: 'new1',
  });
  assert.strictEqual(m.moved, false);
  assert.match(m.reason, /appeared during the run/);

  console.log('ok: seed branch gate rebuilds only pristine seeder branches');
  console.log('ok: gate fails closed on unprovable comparisons and foreign provenance');
  console.log('ok: assessSeedBranch/moveSeedBranch own every seed ref move');
  console.log('ok: ref moves are a server-side compare-and-swap (beforeOid)');
  console.log('ok: workflow seed commit subjects match the gate pattern');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
