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

  // Neither workflow may force-update a seed branch without consulting the gate.
  assert.ok(
    /classifySeedBranch/.test(text),
    `${wf} must call classifySeedBranch before moving the seed branch`,
  );
  assert.ok(
    !/force: true/.test(text) || /safeToReplace/.test(text),
    `${wf} force-updates a ref without a safety verdict`,
  );
}

console.log('ok: seed branch gate rebuilds only pristine seeder branches');
console.log('ok: gate fails closed on unprovable comparisons');
console.log('ok: workflow seed commit subjects match the gate pattern');
