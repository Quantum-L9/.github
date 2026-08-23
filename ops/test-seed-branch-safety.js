'use strict';

/**
 * Asserts the seed-branch safety gate never authorizes a rebuild over work the
 * seeder did not author. Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-branch-safety.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
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
let v = classifySeedBranch({ aheadBy: 1, commits: [{ sha: 'a1', message: autoSeedSubject }] });
assert.strictEqual(v.safeToReplace, true, 'pristine seeder branch must be rebuildable');

v = classifySeedBranch({ aheadBy: 1, commits: [{ sha: 'a1', message: seedSubject }] });
assert.strictEqual(v.safeToReplace, true, 'manual seed branch must be rebuildable');

v = classifySeedBranch({ aheadBy: 0, commits: [] });
assert.strictEqual(v.safeToReplace, true, 'branch with nothing ahead of base loses nothing');

// --- must be left alone ------------------------------------------------------
// The reported incident: remediation commits stacked on the seed commit.
v = classifySeedBranch({
  aheadBy: 2,
  commits: [
    { sha: 'a1', message: autoSeedSubject },
    { sha: 'b2', message: 'fix(governance): make the seeded templates safe to run here' },
  ],
});
assert.strictEqual(v.safeToReplace, false, 'remediation commit must block the rebuild');
assert.match(v.reason, /2 commits/);

// A single foreign commit on the branch.
v = classifySeedBranch({ aheadBy: 1, commits: [{ sha: 'b2', message: 'chore: unrelated' }] });
assert.strictEqual(v.safeToReplace, false, 'foreign single commit must block the rebuild');

// Fail closed on anything unprovable.
for (const bad of [
  undefined,
  {},
  { aheadBy: 1 },
  { commits: [] },
  { aheadBy: null, commits: [] },
  { aheadBy: '1', commits: [{ message: autoSeedSubject }] },
  { aheadBy: -1, commits: [] },
  { aheadBy: 1, commits: [] },
  { aheadBy: 1, commits: [{ sha: 'a1' }] },
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
  for (const forbidden of ['git.createRef', 'git.updateRef', 'force: true']) {
    assert.ok(
      !text.includes(forbidden),
      `${wf} touches a seed ref directly ("${forbidden}") instead of via moveSeedBranch`,
    );
  }
}

// --- assessSeedBranch / moveSeedBranch over a stubbed client ----------------
const notFound = (m) => Object.assign(new Error(m), { status: 404 });

function stub({ openPRs = [], branchSha = null, aheadBy = 1, commits = [autoSeedSubject] } = {}) {
  const calls = [];
  return {
    calls,
    github: {
      request: async (route, args) => {
        calls.push(`request ${route}`);
        return {
          data: {
            ahead_by: aheadBy,
            commits: commits.map((message, i) => ({ sha: `c${i}`, commit: { message } })),
          },
        };
      },
      rest: {
        pulls: {
          list: async () => {
            calls.push('pulls.list');
            return { data: openPRs.map((number) => ({ number })) };
          },
        },
        git: {
          getRef: async () => {
            calls.push('git.getRef');
            if (branchSha === null) throw notFound('Branch not found');
            return { data: { object: { sha: branchSha } } };
          },
          createRef: async () => {
            calls.push('git.createRef');
            return { data: {} };
          },
          updateRef: async (args) => {
            calls.push(`git.updateRef force=${args.force}`);
            return { data: {} };
          },
        },
      },
    },
  };
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
  s = stub({ branchSha: 'abc123', aheadBy: 2, commits: [autoSeedSubject, 'fix: review feedback'] });
  g = await assessSeedBranch({ github: s.github, ...where });
  assert.strictEqual(g.action, 'skip');

  // A non-404 getRef error must surface, not be swallowed into "create".
  s = stub({ branchSha: 'abc123' });
  s.github.rest.git.getRef = async () => {
    throw Object.assign(new Error('boom'), { status: 500 });
  };
  await assert.rejects(() => assessSeedBranch({ github: s.github, ...where }), /boom/);

  // moveSeedBranch: create path never force-updates.
  s = stub({ branchSha: null });
  let m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: null, commitSha: 'new1',
  });
  assert.strictEqual(m.moved, true);
  assert.ok(s.calls.includes('git.createRef'));
  assert.ok(!s.calls.some((c) => c.startsWith('git.updateRef')));

  // moveSeedBranch: rebuild path is a compare-and-swap.
  s = stub({ branchSha: 'abc123' });
  m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: 'abc123', commitSha: 'new1',
  });
  assert.strictEqual(m.moved, true);
  assert.ok(s.calls.includes('git.updateRef force=true'));

  s = stub({ branchSha: 'someone-else-pushed' });
  m = await moveSeedBranch({
    github: s.github, owner: where.owner, repo: where.repo, branch: where.branch,
    expectedSha: 'abc123', commitSha: 'new1',
  });
  assert.strictEqual(m.moved, false, 'a moved branch must not be overwritten');
  assert.ok(!s.calls.some((c) => c.startsWith('git.updateRef')));

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
  console.log('ok: gate fails closed on unprovable comparisons');
  console.log('ok: assessSeedBranch/moveSeedBranch own every seed ref move');
  console.log('ok: workflow seed commit subjects match the gate pattern');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
