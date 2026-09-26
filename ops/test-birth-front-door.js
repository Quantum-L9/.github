'use strict';

/**
 * G5 proofs: repo-birth-bootstrap.yml is the single targeted front door and
 * one immutable governance transaction
 * (docs/adr/0003-immutable-authority-binding.md,
 * docs/adr/0004-single-targeted-bootstrap-front-door.md).
 *
 * Runs the real `script:` body against a stubbed GitHub API and asserts:
 *   - a stale or malformed authority SHA mutates nothing (AC-ADV-005, B-18)
 *   - mutation without an expected plan digest is refused (C-08)
 *   - a stale digest, a digest for another target, or target facts that moved
 *     since planning mutate nothing (AC-ADV-005, AC-ADV-010, B-17, GV-006)
 *   - plan-only mode reports the digest and touches nothing
 *   - a matching transaction materializes (seed PR), applies labels and
 *     settings, attests, and reports one green result (B-16, AC-INT-007)
 *   - a FORBID path on the remote fails the terminal result (AC-INT-006, GV-007)
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-birth-front-door.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { notFound, makeScriptRunner, makeBranchStubs } = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const MARKER = '.l9/org-birth-profile.yaml';
const git = ['/usr/bin/git', '/usr/local/bin/git'].find((p) => fs.existsSync(p));
const HEAD = spawnSync(git, ['-C', root, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).stdout.trim();
const OTHER_SHA = HEAD.replace(/^./, (c) => (c === 'a' ? 'b' : 'a'));
const MUTATIONS = new Set([
  'issues.createLabel',
  'issues.updateLabel',
  'repos.update',
  'git.createBlob',
  'git.createCommit',
  'git.createRef',
  'pulls.create',
]);

/**
 * @param {object} o
 * @param {Record<string, number|null>} [o.probeErrors]  paths whose reads fail
 *   with that HTTP status (null = network error with no status)
 * @param {string|null} [o.seedBranchSha]  existing seed branch tip (null = absent)
 * @param {number[]} [o.openPRs]  open PRs on the seed branch
 * @param {string[]} [o.failOn]  call names that throw a 500
 */
function makeGithub({ name = 'newborn', files = {}, settings = {}, probeErrors = {}, seedBranchSha = null, openPRs = [], failOn = [] } = {}) {
  const calls = [];
  const record = (callName, data = {}) => async (args) => {
    calls.push({ name: callName, args });
    if (failOn.includes(callName)) throw Object.assign(new Error(`${callName}: HTTP 500`), { status: 500 });
    return { data };
  };
  const repoData = { name, owner: { login: 'Quantum-L9' }, default_branch: 'main', has_wiki: true, ...settings };
  const shared = makeBranchStubs({
    branch: 'chore/auto-seed-governance',
    state: { sha: seedBranchSha },
    calls,
    openPRs,
    record: (n) => record(n, { number: 5 }),
  });
  const github = {
    rest: {
      repos: {
        getContent: async ({ path: p }) => {
          calls.push({ name: 'repos.getContent', args: { path: p } });
          if (Object.hasOwn(probeErrors, p)) {
            const status = probeErrors[p];
            throw Object.assign(new Error(status ? `HTTP ${status}` : 'socket hang up'), status ? { status } : {});
          }
          if (Object.hasOwn(files, p)) return { data: { content: Buffer.from(files[p]).toString('base64') } };
          throw notFound('Not Found');
        },
        get: async () => ({ data: repoData }),
        update: record('repos.update'),
      },
      issues: { createLabel: record('issues.createLabel'), updateLabel: record('issues.updateLabel') },
      pulls: shared.pulls,
      git: {
        getRef: shared.getRef,
        getCommit: async () => ({ data: { tree: { sha: 'base-tree' } } }),
        createBlob: record('git.createBlob', { sha: 'blob' }),
        createTree: record('git.createTree', { sha: 'tree' }),
        createCommit: record('git.createCommit', { sha: 'commit' }),
        createRef: record('git.createRef'),
      },
    },
  };
  return { github, calls, state: {} };
}

const door = (env) =>
  makeScriptRunner({
    file: path.join(root, '.github/workflows/repo-birth-bootstrap.yml'),
    root,
    tmpTag: 'front-door-',
    envFor: (dry) => ({
      DRY_RUN: dry ? 'true' : 'false',
      TARGET_REPO: 'newborn',
      REPO_CLASS: '',
      AUTHORITY_SHA: HEAD,
      EXPECTED_PLAN_DIGEST: '',
      ...env,
    }),
    makeGithub,
    mutations: MUTATIONS,
  });

const BORN = { [MARKER]: 'profile: default\n', 'README.md': '# newborn\n', LICENSE: 'MIT\n' };

async function planDigest(opts = {}, env = {}) {
  const r = await door(env)({ ...opts, dry: true });
  assert.strictEqual(r.mutated, false, 'plan-only never mutates');
  assert.deepStrictEqual(r.failures, [], `plan-only failed: ${r.failures}`);
  assert.match(r.outputs.plan_digest, /^[0-9a-f]{64}$/);
  assert.strictEqual(r.outputs.authority_sha, HEAD);
  return r;
}

(async () => {
  // ── plan-only mode ───────────────────────────────────────────────────────
  const planned = await planDigest({ files: BORN });
  assert.ok(!planned.names.some((n) => n.startsWith('git.') || n.startsWith('pulls.')), 'plan-only reads no branch state');
  const digest = planned.outputs.plan_digest;
  console.log('ok: plan-only compiles at the authority SHA, reports the digest, and mutates nothing');

  // ── the valid transaction (B-16, AC-INT-007) ─────────────────────────────
  const ok = await door({ EXPECTED_PLAN_DIGEST: digest })({ files: BORN });
  assert.deepStrictEqual(ok.failures, [], `valid transaction failed: ${ok.failures}`);
  assert.ok(ok.names.includes('pulls.create'), 'materialize opened the seed PR');
  assert.ok(ok.names.includes('issues.createLabel'), 'labels applied');
  assert.ok(ok.names.includes('repos.update'), 'settings drift corrected');
  const results = Object.fromEntries(ok.tables[0].slice(1).map((r) => [r[0], r[1]]));
  for (const check of ['plan', 'materialize', 'labels', 'repo_settings', 'forbid', `present:${MARKER}`]) {
    assert.strictEqual(results[check], 'PASS', `${check}: ${results[check]}`);
  }
  assert.strictEqual(ok.outputs.plan_digest, digest);
  console.log('ok: a matching transaction materializes, applies labels and settings, attests, and ends green');

  // ── refusals: zero mutation, before any target write ─────────────────────
  const refusals = [
    ['stale authority SHA', { AUTHORITY_SHA: OTHER_SHA, EXPECTED_PLAN_DIGEST: digest }, {}, /not the requested/],
    ['malformed authority SHA', { AUTHORITY_SHA: 'main', EXPECTED_PLAN_DIGEST: digest }, {}, /exact 40-hex/],
    ['no authority SHA', { AUTHORITY_SHA: '', EXPECTED_PLAN_DIGEST: digest }, {}, /exact 40-hex/],
    ['no expected digest', {}, {}, /expected_plan_digest is required/],
    ['malformed digest', { EXPECTED_PLAN_DIGEST: 'abc' }, {}, /64 hex/],
    ['stale digest (GV-006)', { EXPECTED_PLAN_DIGEST: 'f'.repeat(64) }, {}, /refused before any mutation.*not the expected/],
    ['digest of another target (AC-ADV-010)', { EXPECTED_PLAN_DIGEST: digest, TARGET_REPO: 'someone-else' }, {}, /refused before any mutation/],
    // Facts moved between planning and applying (B-17): a marker now declares
    // another class, so the recomputed plan differs.
    ['target moved since planning', { EXPECTED_PLAN_DIGEST: digest }, { files: { ...BORN, [MARKER]: 'profile: non_constellation_python\n' } }, /refused before any mutation/],
    ['unknown class', { EXPECTED_PLAN_DIGEST: digest }, { files: { ...BORN, [MARKER]: 'profile: totally_made_up\n' } }, /unknown class/],
  ];
  for (const [label, env, opts, pattern] of refusals) {
    const r = await door(env)({ files: BORN, ...opts });
    assert.strictEqual(r.mutated, false, `${label}: mutated`);
    assert.ok(r.failures.some((f) => pattern.test(f)), `${label}: ${JSON.stringify(r.failures)}`);
  }
  console.log(`ok: ${refusals.length} stale, missing, malformed, foreign, or moved inputs are refused with zero mutation`);

  // The refusal names the digest compiled now, so the caller can re-plan.
  const stale = await door({ EXPECTED_PLAN_DIGEST: 'f'.repeat(64) })({ files: BORN });
  assert.ok(stale.failures[0].includes(digest), 'refusal reports the current plan digest');

  // ── a FORBID path on the remote fails the transaction (GV-007) ───────────
  const sgFiles = { [MARKER]: 'profile: self_governed\n', 'README.md': 'x', LICENSE: 'x', '.github/workflows/governance.yml': 'x' };
  const sgDigest = (await planDigest({ files: sgFiles })).outputs.plan_digest;
  const leaked = await door({ EXPECTED_PLAN_DIGEST: sgDigest })({ files: sgFiles });
  assert.ok(leaked.failures.some((f) => /attestation check/.test(f)), 'forbidden remote path is a terminal failure');
  const leakedRows = Object.fromEntries(leaked.tables[0].slice(1).map((r) => [r[0], r[1]]));
  assert.strictEqual(leakedRows.forbid, 'FAIL');
  console.log('ok: a FORBID path present on the remote fails the transaction (GV-007)');

  const rowsOf = (r) => Object.fromEntries(r.tables[0].slice(1).map((row) => [row[0], row[1]]));
  const REMOTE_WRITES = ['issues.createLabel', 'issues.updateLabel', 'repos.update'];

  // ── materialization that cannot happen halts the whole transaction ───────
  // The seed branch carries an open PR: branch safety answers `skip`. That is
  // proven by a read-only preflight and refused before ANY write — never a
  // materialize PASS followed by labels and settings (ADR-0004).
  const unsafe = await door({ EXPECTED_PLAN_DIGEST: digest })({ files: BORN, seedBranchSha: 'foreign-tip', openPRs: [3] });
  assert.strictEqual(unsafe.mutated, false, 'an unwritable seed branch mutates nothing');
  assert.ok(unsafe.failures.some((f) => /refused before any mutation — seed branch not writable/.test(f)), `${unsafe.failures}`);
  const unsafeRows = rowsOf(unsafe);
  assert.strictEqual(unsafeRows.materialize, 'FAIL');
  for (const step of ['labels', 'repo_settings', 'attestation']) assert.strictEqual(unsafeRows[step], 'NOT RUN', step);
  // A materialization that fails mid-write halts before remote apply.
  const broken = await door({ EXPECTED_PLAN_DIGEST: digest })({ files: BORN, failOn: ['git.createCommit'] });
  assert.ok(broken.failures.some((f) => /materialization did not complete/.test(f)), `${broken.failures}`);
  assert.ok(!broken.names.some((n) => REMOTE_WRITES.includes(n)), 'no labels or settings after a failed materialize');
  assert.strictEqual(rowsOf(broken).labels, 'NOT RUN');
  console.log('ok: an unwritable seed branch is refused before any write; a failed materialize halts before remote apply');

  // ── a failed observation is never "absent" (AC-ADV-009) ──────────────────
  // `.github/CODEOWNERS` is a seed path: the preflight reads it before any write.
  for (const [probePath, status] of [[MARKER, 500], [MARKER, 403], [MARKER, null], ['CODEOWNERS', 429], ['.github/CODEOWNERS', 502]]) {
    const what = `${status || 'network'} on ${probePath}`;
    const r = await door({ EXPECTED_PLAN_DIGEST: digest })({ files: BORN, probeErrors: { [probePath]: status } });
    assert.strictEqual(r.mutated, false, `${what} must not mutate`);
    assert.ok(r.failures.some((f) => /refused before any mutation/.test(f)), `${what}: ${JSON.stringify(r.failures)}`);
  }
  // After the writes, a failed attestation read is a FAIL, not a pass.
  const late = await door({ EXPECTED_PLAN_DIGEST: digest })({ files: BORN, probeErrors: { 'README.md': 502 } });
  assert.strictEqual(rowsOf(late)['present:README.md'], 'FAIL');
  assert.ok(late.failures.some((f) => /attestation check/.test(f)));
  console.log('ok: a 403/5xx/429/network failure on a fact or a preflight read refuses before any write; a failed attestation read fails');

  // ── attestation derives from the plan: markerless classes attest green ───
  // An org override and an operator request legitimately carry no marker;
  // the plan does not require one, so its absence is not a failure.
  const tplFiles = { 'README.md': 'x', LICENSE: 'x' };
  for (const [label, env, opts] of [
    ['org override (l9-repo-template)', { TARGET_REPO: 'l9-repo-template' }, { name: 'l9-repo-template' }],
    ['operator request', { REPO_CLASS: 'self_governed' }, {}],
  ]) {
    const d = (await planDigest({ files: tplFiles, ...opts }, env)).outputs.plan_digest;
    const r = await door({ ...env, EXPECTED_PLAN_DIGEST: d })({ files: tplFiles, ...opts });
    assert.deepStrictEqual(r.failures, [], `${label}: ${r.failures}`);
    const rows = rowsOf(r);
    assert.ok(!(`present:${MARKER}` in rows), `${label}: marker not required`);
    assert.strictEqual(rows['marker:class'], 'SKIP', `${label}: no marker is legitimate`);
  }
  // A forced class the marker contradicts is refused before any write.
  const contra = await door({ REPO_CLASS: 'self_governed', EXPECTED_PLAN_DIGEST: digest })({ files: BORN });
  assert.strictEqual(contra.mutated, false);
  assert.ok(contra.failures.some((f) => /refused before any mutation.*declares default/.test(f)), `${contra.failures}`);
  console.log('ok: attestation follows the plan — markerless classes attest green; a contradicted forced class is refused before any write');

  // ── the authority must be on main before any of its code runs (ADR-0003) ─
  const wf = fs.readFileSync(path.join(root, '.github/workflows/repo-birth-bootstrap.yml'), 'utf8');
  const ancestry = wf.indexOf('git merge-base --is-ancestor "$AUTHORITY_SHA" refs/remotes/origin/main');
  const firstRequire = wf.indexOf("require('./ops/");
  assert.ok(ancestry > 0 && ancestry < firstRequire, 'the on-main check runs before any repository code is required');
  assert.match(wf, /fetch-depth: 0/, 'full history for the ancestry check');
  assert.ok(!/setup-python|pyyaml/i.test(wf), 'no Python toolchain: nothing in the job reads it');
  console.log('ok: the authority revision must be on main before any of its code runs');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
