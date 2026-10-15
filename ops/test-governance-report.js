'use strict';

/**
 * Asserts the weekly advisory posture report (governance-report.yml, #102).
 *
 * The load-bearing claim: the report never prints an all-clear it has no
 * evidence for. An Actions policy that could not be read is UNKNOWN — counted
 * and listed, never folded into "allowed" — and the sentence "All repos
 * permit cross-repo reusable workflows" appears only when every repository
 * was verified allowed. Presence percentages are labelled as presence.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-governance-report.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const {
  STATES,
  callerRefs,
  patternCovers,
  workflowActionRefs,
  reusableWorkflowActionRefs,
  classifyActionsPermission,
  buildPostureReport,
} = require('./governance-report.js');
const { loadScriptModule, makeCore, makeScopedRequire } = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const ALL_CLEAR = 'All repos permit cross-repo reusable workflows';
const httpError = (status) => Object.assign(new Error(`HTTP ${status}`), { status });

(async () => {
  // ── caller references come from the distributed caller itself ──────────
  const refs = callerRefs(fs.readFileSync(path.join(root, 'policies/governance-caller.yml'), 'utf8'));
  assert.strictEqual(refs.length, 2, 'governance-pr.yml and governance-issue.yml');
  for (const r of refs) assert.match(r, /^Quantum-L9\/\.github\/\.github\/workflows\/governance-(pr|issue)\.yml@[0-9a-f]{40}$/);

  // ── allow-list pattern matching ─────────────────────────────────────────
  assert.ok(patternCovers('Quantum-L9/*', refs[0]));
  assert.ok(patternCovers('quantum-l9/.github/*', refs[0]), 'owner/repo compare case-insensitively');
  assert.ok(patternCovers('Quantum-L9/.github/.github/workflows/*@*', refs[0]));
  assert.ok(!patternCovers('actions/*', refs[0]));
  assert.ok(!patternCovers('Quantum-L9/l9-ci-core/*', refs[0]));
  assert.ok(!patternCovers('Quantum-L9.github*', refs[0]), '"." is literal, not any character');
  assert.ok(!patternCovers('', refs[0]));

  // ── actions the reusable workflows run in turn ──────────────────────────
  const actionRefs = reusableWorkflowActionRefs(refs, (p) => fs.readFileSync(path.join(root, p), 'utf8'));
  assert.ok(actionRefs.length >= 2, 'the reusable workflows run GitHub-owned actions');
  assert.ok(actionRefs.every((r) => /^actions\/(checkout|github-script)@[0-9a-f]{40}$/.test(r)), actionRefs.join(', '));
  assert.deepStrictEqual(workflowActionRefs('steps:\n  - uses: ./local\n  - uses: docker://alpine\n  - uses: actions/checkout@abc # v1\n'), ['actions/checkout@abc']);
  assert.throws(() => reusableWorkflowActionRefs(['Other/repo/.github/workflows/x.yml@abc'], () => ''), /not a Quantum-L9\/\.github/);

  // ── classification ──────────────────────────────────────────────────────
  const classify = (perms, selected) => classifyActionsPermission({
    readPermissions: async () => { if (perms instanceof Error) throw perms; return perms; },
    readSelected: async () => { if (selected instanceof Error) throw selected; return selected; },
    refs,
    actionRefs,
  });
  const SEL = { enabled: true, allowed_actions: 'selected' };
  const cases = [
    [httpError(403), undefined, STATES.UNKNOWN, /permissions unreadable \(403\)/],
    [httpError(404), undefined, STATES.UNKNOWN, /permissions unreadable \(404\)/],
    [new Error('network'), undefined, STATES.UNKNOWN, /permissions unreadable \(error\)/],
    [{ enabled: false }, undefined, STATES.BLOCKED, /^disabled$/],
    [{ enabled: true, allowed_actions: 'local_only' }, undefined, STATES.BLOCKED, /^local_only$/],
    [{ enabled: true, allowed_actions: 'all' }, undefined, STATES.ALLOWED, /^all$/],
    [{ enabled: true, allowed_actions: 'selected' }, httpError(403), STATES.UNKNOWN, /allow-list unreadable \(403\)/],
    [{ enabled: true, allowed_actions: 'selected' }, {}, STATES.UNKNOWN, /no patterns field/],
    // Same-organization workflows need no pattern; the GitHub-owned actions they
    // run follow github_owned_allowed or a positive pattern.
    [SEL, { patterns_allowed: [], github_owned_allowed: true }, STATES.ALLOWED, /^selected \(admits/],
    [SEL, { patterns_allowed: ['actions/*'], github_owned_allowed: false }, STATES.ALLOWED, /^selected \(admits/],
    [SEL, { patterns_allowed: ['Quantum-L9/*'], github_owned_allowed: false }, STATES.BLOCKED, /selected-denied \(actions\/(checkout|github-script)\)/],
    [SEL, { patterns_allowed: ['Quantum-L9/*'] }, STATES.UNKNOWN, /cannot verify actions\//],
    // A `!` pattern blocks even under a broader allow.
    [SEL, { patterns_allowed: ['Quantum-L9/*', '!Quantum-L9/.github/*'], github_owned_allowed: true }, STATES.BLOCKED, /selected-denied \(Quantum-L9\/\.github\/\.github\/workflows\/governance-/],
    [SEL, { patterns_allowed: ['*', '!actions/checkout@*'], github_owned_allowed: true }, STATES.BLOCKED, /selected-denied \(actions\/checkout\)/],
    [SEL, { patterns_allowed: ['!Other/*'], github_owned_allowed: true }, STATES.ALLOWED, /^selected \(admits/],
    [{ enabled: true, allowed_actions: 'something_new' }, undefined, STATES.UNKNOWN, /allowed_actions=something_new/],
    [{ allowed_actions: 'all' }, undefined, STATES.UNKNOWN, /enabled=undefined/],
    [null, undefined, STATES.UNKNOWN, /empty/],
  ];
  for (const [perms, selected, state, detail] of cases) {
    const got = await classify(perms, selected);
    assert.strictEqual(got.state, state, `${JSON.stringify(perms)} / ${JSON.stringify(selected)}`);
    assert.match(got.detail, detail);
  }
  // `selected` with nothing to verify against is not a pass.
  assert.strictEqual((await classifyActionsPermission({
    readPermissions: async () => ({ enabled: true, allowed_actions: 'selected' }),
    readSelected: async () => ({ patterns_allowed: ['Quantum-L9/*'], github_owned_allowed: true }),
    refs: [],
    actionRefs,
  })).state, STATES.UNKNOWN);
  // Unread reusable workflows are not a pass either.
  assert.match((await classifyActionsPermission({
    readPermissions: async () => SEL,
    readSelected: async () => ({ patterns_allowed: [], github_owned_allowed: true }),
    refs,
    actionRefs: null,
  })).detail, /actions used by the reusable workflows were not read/);
  console.log('ok: Actions policy — unreadable/unverifiable is UNKNOWN; disabled, local_only and selected-denied are blocked; only all, or a selected policy that admits the caller and every action it runs, is allowed; `!` patterns block');

  // ── rendering ───────────────────────────────────────────────────────────
  const row = (name, actions, presence = {}) => ({ name, co: true, caller: true, dep: true, ...presence, actions });
  const unknown403 = { state: STATES.UNKNOWN, detail: 'permissions unreadable (403)' };
  const allowedAll = { state: STATES.ALLOWED, detail: 'all' };
  const date = '2026-10-15';

  // All-unreadable: the false all-clear (#102). Negative witness.
  let rep = buildPostureReport([row('a', unknown403), row('b', unknown403)], { date });
  assert.ok(!rep.body.includes(ALL_CLEAR), 'all-unreadable must not print the all-clear');
  assert.match(rep.body, /2 repo\(s\) have an Actions policy that could not be verified \(UNKNOWN, not counted as allowed\): `a` \(permissions unreadable \(403\)\), `b`/);
  assert.match(rep.body, /0 verified allowed · 0 blocked · 2 UNKNOWN/);
  assert.match(rep.body, /❓ UNKNOWN: permissions unreadable \(403\)/);
  assert.deepStrictEqual(rep.counts, { allowed: 0, blocked: 0, unknown: 2 });
  assert.match(rep.refresh, /Actions: 0 allowed, 0 blocked, 2 UNKNOWN\.$/);

  // Mixed: allowed, blocked and unknown are each counted and listed.
  rep = buildPostureReport([
    row('ok', allowedAll),
    row('off', { state: STATES.BLOCKED, detail: 'disabled' }),
    row('sel', { state: STATES.BLOCKED, detail: 'selected-denied (actions/checkout)' }),
    row('unk', unknown403, { co: null, dep: false }),
  ], { date });
  assert.ok(!rep.body.includes(ALL_CLEAR));
  assert.match(rep.body, /1 verified allowed · 2 blocked · 1 UNKNOWN/);
  assert.match(rep.body, /2 repo\(s\) have an Actions policy that would prevent the governance caller from running: `off` \(disabled\), `sel` \(selected-denied/);
  assert.match(rep.body, /1 repo\(s\) have an Actions policy that could not be verified .*`unk`/);
  assert.match(rep.body, /\*\*Raw file presence across 4 active repos\*\* \(presence, not class-normalized compliance\) — CODEOWNERS 75% \(1 unobserved\) · governance caller 100% · dependabot 75%/);
  assert.match(rep.body, /\| `unk` \| ❓ \| ✅ \| ⬜ \| ❓ UNKNOWN/);

  // Verified-all-allowed: the only state that earns the all-clear. Positive witness.
  rep = buildPostureReport([row('a', allowedAll), row('b', { state: STATES.ALLOWED, detail: 'selected (admits the caller and the actions it runs)' })], { date });
  assert.ok(rep.body.includes(ALL_CLEAR), 'verified-all-allowed prints the all-clear');
  assert.doesNotMatch(rep.body, /UNKNOWN, not counted|would prevent/);
  assert.match(rep.body, /2 verified allowed · 0 blocked · 0 UNKNOWN/);

  // No repos: nothing verified, so no all-clear.
  rep = buildPostureReport([], { date });
  assert.ok(!rep.body.includes(ALL_CLEAR));
  assert.match(rep.body, /No active repositories were observed/);
  // The advisory posture is stated, never a gate.
  assert.match(rep.body, /Nothing here blocks anything/);
  console.log('ok: posture report — all-unreadable and mixed never print the all-clear; verified-all-allowed does; presence is labelled presence');

  // ── the real governance-report.yml script, against a stubbed API ────────
  const script = loadScriptModule(path.join(root, '.github/workflows/governance-report.yml'), 'governance-report-');
  const scoped = makeScopedRequire(root);
  const runReport = async ({ repos, existing = null }) => {
    const calls = [];
    const github = {
      paginate: async () => Object.keys(repos).map((name) => ({ name, archived: false, fork: false })),
      rest: {
        repos: {
          listForOrg: () => {},
          getContent: async ({ repo, path: p }) => {
            const r = repos[repo];
            if (r.contentError) throw httpError(r.contentError);
            if ((r.files || []).includes(p)) return { data: { type: 'file', content: '' } };
            throw httpError(404);
          },
        },
        actions: {
          getGithubActionsPermissionsRepository: async ({ repo }) => {
            const r = repos[repo];
            if (r.permsError) throw httpError(r.permsError);
            return { data: r.perms };
          },
          getAllowedActionsRepository: async ({ repo }) => {
            const r = repos[repo];
            if (r.selectedError) throw httpError(r.selectedError);
            return { data: r.selected };
          },
        },
        issues: {
          listForRepo: async (args) => { calls.push(['listForRepo', args]); return { data: existing ? [existing] : [] }; },
          update: async (args) => { calls.push(['update', args]); return { data: {} }; },
          createComment: async (args) => { calls.push(['createComment', args]); return { data: {} }; },
          create: async (args) => { calls.push(['create', args]); return { data: { number: 102 } }; },
        },
      },
    };
    const core = makeCore();
    const prev = process.cwd();
    process.chdir(root);
    try {
      await script(github, core, { repo: { owner: 'Quantum-L9', repo: '.github' } }, scoped);
    } finally {
      process.chdir(prev);
    }
    assert.deepStrictEqual(core.failures, [], 'the advisory report never fails a run');
    return calls;
  };
  const FILES = ['.github/CODEOWNERS', '.github/workflows/governance.yml', '.github/dependabot.yml'];

  // All-unreadable via the real script (the GITHUB_TOKEN cannot read other
  // repos' Actions settings): UNKNOWN, no all-clear, issue identity kept.
  let calls = await runReport({
    repos: { a: { files: FILES, permsError: 403 }, b: { files: FILES, permsError: 404 } },
    existing: { number: 102, title: 'Governance posture (advisory, weekly)' },
  });
  assert.deepStrictEqual(calls[0][1], { owner: 'Quantum-L9', repo: '.github', state: 'open', labels: 'advisory', per_page: 20 });
  const update = calls.find((c) => c[0] === 'update')[1];
  assert.strictEqual(update.issue_number, 102, 'the weekly issue is updated in place');
  assert.ok(!update.body.includes(ALL_CLEAR));
  assert.match(update.body, /0 verified allowed · 0 blocked · 2 UNKNOWN/);
  assert.match(calls.find((c) => c[0] === 'createComment')[1].body, /2 UNKNOWN/);
  assert.ok(!calls.some((c) => c[0] === 'create'), 'no second weekly issue');

  // Verified-all-allowed via the real script, first run: create with `advisory`.
  calls = await runReport({
    repos: {
      a: { files: FILES, perms: { enabled: true, allowed_actions: 'all' } },
      b: { files: FILES, perms: { enabled: true, allowed_actions: 'selected' }, selected: { patterns_allowed: [], github_owned_allowed: true } },
    },
  });
  const created = calls.find((c) => c[0] === 'create')[1];
  assert.strictEqual(created.title, 'Governance posture (advisory, weekly)');
  assert.deepStrictEqual(created.labels, ['advisory']);
  assert.ok(created.body.includes(ALL_CLEAR));

  // Mixed via the real script: a selected allow-list that cannot be read is UNKNOWN.
  calls = await runReport({
    repos: {
      a: { files: FILES, perms: { enabled: true, allowed_actions: 'all' } },
      b: { files: [], perms: { enabled: false } },
      c: { contentError: 500, perms: { enabled: true, allowed_actions: 'selected' }, selectedError: 403 },
    },
  });
  const mixedBody = calls.find((c) => c[0] === 'create')[1].body;
  assert.ok(!mixedBody.includes(ALL_CLEAR));
  assert.match(mixedBody, /1 verified allowed · 1 blocked · 1 UNKNOWN/);
  assert.match(mixedBody, /`c` \(selected; allow-list unreadable \(403\)\)/);
  assert.match(mixedBody, /\| `c` \| ❓ \| ❓ \| ❓ \|/);
  console.log('ok: governance-report.yml — real script: all-unreadable is UNKNOWN with no all-clear, verified-all-allowed earns it, weekly issue identity and advisory posture kept');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
