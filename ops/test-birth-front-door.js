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

function makeGithub({ name = 'newborn', files = {}, settings = {} } = {}) {
  const calls = [];
  const record = (callName, data = {}) => async (args) => {
    calls.push({ name: callName, args });
    return { data };
  };
  const repoData = { name, owner: { login: 'Quantum-L9' }, default_branch: 'main', has_wiki: true, ...settings };
  const shared = makeBranchStubs({
    branch: 'chore/auto-seed-governance',
    state: { sha: null },
    calls,
    openPRs: [],
    record: (n) => record(n, { number: 5 }),
  });
  const github = {
    rest: {
      repos: {
        getContent: async ({ path: p }) => {
          calls.push({ name: 'repos.getContent', args: { path: p } });
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
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
