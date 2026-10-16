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
const crypto = require('node:crypto');
const childProcess = require('node:child_process');
const {
  STATES,
  REGISTRY_SOURCE,
  CLASSES_SOURCE,
  pythonYamlParser,
  loadCanonicalSource,
  projectGovernedCensus,
  loadGovernedCensus,
  reconcileDiscovery,
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

// ── canonical-source fixtures (governed census) ──────────────────────────
const CLASS = 'l9.repository-class/l9@1';
const classesDoc = (over = {}) => ({
  schema: CLASSES_SOURCE.schema,
  artifact_id: CLASSES_SOURCE.artifact_id,
  canonical: true,
  classes: { l9: { id: CLASS, status: 'current' } },
  catalog_status: { admitted_classes: [CLASS] },
  ...over,
});
const registryDoc = (repositories, over = {}) => ({
  schema: REGISTRY_SOURCE.schema,
  artifact_id: REGISTRY_SOURCE.artifact_id,
  canonical: true,
  class_catalog_ref: CLASSES_SOURCE.artifact_id,
  repository_lifecycle: { current: 'c', superseded: 's', retired: 'r' },
  repositories,
  aliases: [],
  ...over,
});
const entry = (id, repository, lifecycle = 'current', classRef = CLASS, organization = 'Quantum-L9') =>
  ({ id, coordinate: { provider: 'github', organization, repository }, lifecycle, class_ref: classRef });
// Fixture bytes are JSON, which is YAML: the digest moves with the fixture.
const fixtureIo = (docs, revision = 'a'.repeat(40)) => ({
  readBytes: (p) => {
    const d = docs[p];
    if (d instanceof Error) throw d;
    return Buffer.from(typeof d === 'string' ? d : JSON.stringify(d));
  },
  parseYaml: (b) => JSON.parse(b.toString('utf8')),
  revision,
});
const censusOf = (registry, classes = classesDoc(), revision) =>
  loadGovernedCensus(fixtureIo({ [REGISTRY_SOURCE.path]: registry, [CLASSES_SOURCE.path]: classes }, revision));

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

  // ── actions the reusable workflows run in turn, at the pinned commit ────
  // A reader over fixed bytes keyed by `<path>@<sha>`; anything else is a 404.
  const pinnedReader = (bytes, calls = []) => async (o) => {
    calls.push(o);
    const key = `${o.path}@${o.ref}`;
    if (!(key in bytes)) throw httpError(404);
    if (bytes[key] instanceof Error) throw bytes[key];
    return bytes[key];
  };
  const headText = (p) => fs.readFileSync(path.join(root, p), 'utf8');
  const pinOf = (r) => r.split('@')[1];
  const pathOf = (r) => r.replace(/^Quantum-L9\/\.github\//, '').split('@')[0];
  // Fixture: the bytes the caller's pinned commit serves for each workflow.
  const PINNED = Object.fromEntries(refs.map((r) => [`${pathOf(r)}@${pinOf(r)}`, headText(pathOf(r))]));
  const readCalls = [];
  const actionRefs = await reusableWorkflowActionRefs(refs, pinnedReader(PINNED, readCalls));
  assert.ok(actionRefs.length >= 2, 'the reusable workflows run GitHub-owned actions');
  assert.ok(actionRefs.every((r) => /^actions\/(checkout|github-script)@[0-9a-f]{40}$/.test(r)), actionRefs.join(', '));
  assert.deepStrictEqual(readCalls.map((c) => `${c.owner}/${c.repo}/${c.path}@${c.ref}`), refs, 'each workflow is read at its own pinned SHA');
  assert.deepStrictEqual(workflowActionRefs('steps:\n  - uses: ./local\n  - uses: docker://alpine\n  - uses: actions/checkout@abc # v1\n'), ['actions/checkout@abc']);

  // Drift: the pinned commit runs actions/setup-node, current HEAD does not.
  // The verdict follows the pinned bytes, never the checkout.
  const OLD = 'a'.repeat(40);
  const NODE = `actions/setup-node@${'b'.repeat(40)}`;
  const drifted = [`Quantum-L9/.github/.github/workflows/governance-pr.yml@${OLD}`];
  const pinnedOnly = { [`.github/workflows/governance-pr.yml@${OLD}`]: `jobs:\n  a:\n    steps:\n      - uses: ${NODE}\n` };
  const driftRefs = await reusableWorkflowActionRefs(drifted, pinnedReader(pinnedOnly));
  assert.deepStrictEqual(driftRefs, [NODE]);
  const headRefs = workflowActionRefs(headText('.github/workflows/governance-pr.yml'));
  assert.ok(!headRefs.includes(NODE) && headRefs.length, 'fixture: HEAD and the pinned commit differ');
  const onlyHeadActions = { patterns_allowed: ['actions/checkout@*', 'actions/github-script@*'], github_owned_allowed: false };
  const SELECTED = { enabled: true, allowed_actions: 'selected' };
  const verdictFor = (ars) => classifyActionsPermission({
    readPermissions: async () => SELECTED, readSelected: async () => onlyHeadActions, refs: drifted, actionRefs: ars,
  });
  assert.strictEqual((await verdictFor(headRefs)).state, STATES.ALLOWED, 'HEAD bytes would have admitted the caller');
  const pinnedVerdict = await verdictFor(driftRefs);
  assert.strictEqual(pinnedVerdict.state, STATES.BLOCKED, 'the pinned bytes run an action the policy denies');
  assert.match(pinnedVerdict.detail, /selected-denied \(actions\/setup-node\)/);

  // Missing pinned revision, unreadable or empty pinned workflow: rejects (UNKNOWN), no HEAD fallback.
  await assert.rejects(reusableWorkflowActionRefs(drifted, pinnedReader({})), (e) => e.status === 404);
  await assert.rejects(reusableWorkflowActionRefs(drifted, pinnedReader({ [`.github/workflows/governance-pr.yml@${OLD}`]: httpError(403) })), (e) => e.status === 403);
  await assert.rejects(reusableWorkflowActionRefs(drifted, pinnedReader({ [`.github/workflows/governance-pr.yml@${OLD}`]: null })), /returned no workflow text/);
  // Invalid or unsupported references are refused before any read.
  for (const bad of [
    `Other/repo/.github/workflows/x.yml@${OLD}`,
    'Quantum-L9/.github/.github/workflows/governance-pr.yml@main',
    'Quantum-L9/.github/.github/workflows/governance-pr.yml@abc1234',
    `Quantum-L9/.github/.github/workflows/governance-pr.yml@${'A'.repeat(40)}`,
    `Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml@${OLD}`,
    `Quantum-L9/.github/.github/actions/x@${OLD}`,
  ]) {
    const seen = [];
    await assert.rejects(reusableWorkflowActionRefs([bad], pinnedReader(PINNED, seen)), /not a Quantum-L9\/\.github reusable workflow pinned to a full SHA/, bad);
    assert.strictEqual(seen.length, 0, `${bad} was read`);
  }
  // A caller ref not pinned to a SHA is surfaced, not silently dropped.
  assert.deepStrictEqual(callerRefs('    uses: Quantum-L9/.github/.github/workflows/governance-pr.yml@main  # floating\n'),
    ['Quantum-L9/.github/.github/workflows/governance-pr.yml@main']);

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
  let pinnedReadLog = [];
  let probeLog = [];
  // The script reads the real canonical files; the parser stands in for
  // PyYAML and hands back a fixture for each, so a test controls the census
  // while the recorded digest is still that of the bytes actually read.
  const REAL_BYTES = {
    registry: fs.readFileSync(path.join(root, REGISTRY_SOURCE.path)),
    classes: fs.readFileSync(path.join(root, CLASSES_SOURCE.path)),
  };
  const RUN_SHA = 'c'.repeat(40);
  // By default every stubbed repository is registered, in stub order.
  const registryFor = (repos) => registryDoc(Object.keys(repos).map((n) => entry(`id-${n}`, n)));
  const runReport = async ({
    repos, existing = null, pinnedError = null,
    registry = registryFor(repos), classes = classesDoc(), discovery, sha = RUN_SHA,
  }) => {
    pinnedReadLog = [];
    probeLog = [];
    const calls = [];
    const parsed = (doc) => { if (doc instanceof Error) throw doc; return JSON.stringify(doc); };
    const execFileSync = (cmd, args, opts) => {
      assert.strictEqual(cmd, 'python3');
      if (opts.input.equals(REAL_BYTES.registry)) return parsed(registry);
      if (opts.input.equals(REAL_BYTES.classes)) return parsed(classes);
      throw new Error('unexpected parse input');
    };
    const req = (m) => (m === 'child_process' ? { execFileSync } : scoped(m));
    const github = {
      paginate: async () => {
        if (discovery instanceof Error) throw discovery;
        return discovery || Object.keys(repos).map((name) => ({ name, full_name: `Quantum-L9/${name}`, archived: false, fork: false }));
      },
      rest: {
        repos: {
          listForOrg: () => {},
          getContent: async ({ owner, repo, path: p, ref }) => {
            if (repo === '.github' && ref !== undefined) {
              // The caller's pinned reusable workflows, served at their SHA only.
              pinnedReadLog.push({ owner, repo, path: p, ref });
              if (pinnedError) throw httpError(pinnedError);
              const key = `${p}@${ref}`;
              if (!(key in PINNED)) throw httpError(404);
              return { data: { type: 'file', content: Buffer.from(PINNED[key]).toString('base64') } };
            }
            probeLog.push(`${owner}/${repo}:${p}`);
            const r = repos[repo];
            if (r.contentError) throw httpError(r.contentError);
            if ((r.files || []).includes(p)) return { data: { type: 'file', content: '' } };
            throw httpError(404);
          },
        },
        actions: {
          getGithubActionsPermissionsRepository: async ({ owner, repo }) => {
            probeLog.push(`${owner}/${repo}:actions`);
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
      await script(github, core, { sha, repo: { owner: 'Quantum-L9', repo: '.github' } }, req);
    } finally {
      process.chdir(prev);
    }
    assert.deepStrictEqual(core.failures, [], 'the advisory report never fails a run');
    calls.warnings = core.warnings;
    return calls;
  };
  const bodyOf = (calls) => (calls.find((c) => c[0] === 'create' || c[0] === 'update') || [])[1]?.body;
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
  assert.deepStrictEqual(pinnedReadLog.map((o) => `${o.owner}/${o.repo}/${o.path}@${o.ref}`), refs, 'the real script reads each workflow at its pinned SHA');

  // The pinned workflows cannot be read: a selected policy is UNKNOWN, never
  // judged against this checkout's workflows; `all` is unaffected.
  calls = await runReport({
    repos: {
      a: { files: FILES, perms: { enabled: true, allowed_actions: 'all' } },
      b: { files: FILES, perms: { enabled: true, allowed_actions: 'selected' }, selected: { patterns_allowed: [], github_owned_allowed: true } },
    },
    pinnedError: 403,
  });
  const unreadBody = calls.find((c) => c[0] === 'create')[1].body;
  assert.ok(!unreadBody.includes(ALL_CLEAR));
  assert.match(unreadBody, /1 verified allowed · 0 blocked · 1 UNKNOWN/);
  assert.match(unreadBody, /`b` \(selected; actions used by the reusable workflows were not read\)/);

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

  // ── governed census: membership is the registry's, discovery observes ──
  const ALL = { enabled: true, allowed_actions: 'all' };
  const rowCount = (body, name) => body.split('\n').filter((l) => l.startsWith(`| \`${name}\``)).length;

  // (1) A registered current repository appears exactly once — even when
  // discovery returns it twice — and carries its registry id.
  calls = await runReport({
    repos: { a: { files: FILES, perms: ALL } },
    discovery: [{ name: 'a', full_name: 'Quantum-L9/a' }, { name: 'a', full_name: 'Quantum-L9/a' }],
  });
  let body = bodyOf(calls);
  assert.strictEqual(rowCount(body, 'a'), 1);
  assert.match(body, /\| `a` \| ✅ \| ✅ \| ✅ \| allowed \| `id-a` \|/);
  assert.match(body, /\*\*Governed census\*\* — 1 repositories: registry lifecycle `current` with an admitted class \(`l9\.repository-class\/l9@1` ×1\)/);
  const digestOf = (b) => crypto.createHash('sha256').update(b).digest('hex');
  assert.ok(body.includes(`sha256 \`${digestOf(REAL_BYTES.registry).slice(0, 12)}\``), 'registry digest is the digest of the bytes read');
  assert.ok(body.includes(`sha256 \`${digestOf(REAL_BYTES.classes).slice(0, 12)}\``), 'class catalog digest recorded');
  assert.ok(body.includes(`both at \`${RUN_SHA.slice(0, 12)}\``), 'source revision is the run commit');
  assert.ok(body.includes(ALL_CLEAR), 'one verified member, verified allowed');

  // (2) Registered but missing from discovery: kept, every column UNKNOWN,
  // never probed (a 404 there would read as "absent"), and no all-clear.
  calls = await runReport({
    repos: { a: { files: FILES, perms: ALL }, ghost: { files: FILES, perms: ALL } },
    discovery: [{ name: 'a', full_name: 'Quantum-L9/a' }],
  });
  body = bodyOf(calls);
  assert.match(body, /\| `ghost` \| ❓ \| ❓ \| ❓ \| ❓ UNKNOWN: not returned by GitHub discovery \| `id-ghost` \|/);
  assert.match(body, /1 registered repo\(s\) were not observed.*`Quantum-L9\/ghost` \(not returned by GitHub discovery\)/);
  assert.match(body, /across 2 governed repos/);
  assert.match(body, /1 verified allowed · 0 blocked · 1 UNKNOWN/);
  assert.ok(!body.includes(ALL_CLEAR));
  assert.ok(!probeLog.some((p) => p.startsWith('Quantum-L9/ghost:')), probeLog.join(' '));
  // Discovery itself failing: every member UNKNOWN, unregistered unchecked.
  calls = await runReport({ repos: { a: { files: FILES, perms: ALL } }, discovery: httpError(502) });
  body = bodyOf(calls);
  assert.match(body, /GitHub discovery failed \(502\)/);
  assert.match(body, /\| `a` \| ❓ \| ❓ \| ❓ \| ❓ UNKNOWN: GitHub discovery unavailable \|/);
  assert.ok(!body.includes(ALL_CLEAR));
  assert.deepStrictEqual(probeLog, []);
  // A coordinate GitHub reports with different case is drift, not a match.
  calls = await runReport({
    repos: { 'Cased-Repo': { files: FILES, perms: ALL } },
    discovery: [{ name: 'cased-repo', full_name: 'Quantum-L9/cased-repo' }],
  });
  body = bodyOf(calls);
  assert.match(body, /Registry coordinate case differs from GitHub: `Quantum-L9\/Cased-Repo` → `Quantum-L9\/cased-repo`/);
  assert.doesNotMatch(body, /Registry discrepancy/, 'a case-drifted member is not also reported unregistered');
  assert.ok(!body.includes(ALL_CLEAR));

  // (3) Archived and forked registered repositories are not silently removed.
  calls = await runReport({
    repos: { old: { files: FILES, perms: ALL }, copy: { files: FILES, perms: ALL } },
    discovery: [
      { name: 'old', full_name: 'Quantum-L9/old', archived: true, fork: false },
      { name: 'copy', full_name: 'Quantum-L9/copy', archived: false, fork: true },
    ],
  });
  body = bodyOf(calls);
  assert.match(body, /\| `old` \(archived\) \| ✅/);
  assert.match(body, /\| `copy` \(fork\) \| ✅/);
  assert.match(body, /across 2 governed repos/);
  // Non-current registry entries are kept and listed, outside the census.
  calls = await runReport({
    repos: { a: { files: FILES, perms: ALL }, gone: { files: FILES, perms: ALL } },
    registry: registryDoc([entry('id-a', 'a'), entry('id-gone', 'gone', 'retired')]),
  });
  body = bodyOf(calls);
  assert.match(body, /Registered but not `current` \(kept, outside the census\): `Quantum-L9\/gone` \(retired\)/);
  assert.strictEqual(rowCount(body, 'gone'), 0);
  assert.doesNotMatch(body, /Registry discrepancy/, 'a retired registered repository is not "unregistered"');

  // (4)+(5) Unregistered repositories — l9- prefix or not — never enter the
  // denominator and are never probed; they are a reported registry discrepancy.
  calls = await runReport({
    repos: { a: { files: FILES, perms: ALL }, 'l9-shiny': { files: FILES, perms: ALL }, other: { files: FILES, perms: ALL } },
    registry: registryDoc([entry('id-a', 'a')]),
  });
  body = bodyOf(calls);
  assert.match(body, /across 1 governed repos/);
  assert.match(body, /1 verified allowed · 0 blocked · 0 UNKNOWN/);
  assert.strictEqual(rowCount(body, 'l9-shiny'), 0);
  assert.strictEqual(rowCount(body, 'other'), 0);
  assert.match(body, /Registry discrepancy: 2 repo\(s\) returned by GitHub discovery are not in the registry and are not counted: `Quantum-L9\/l9-shiny`, `Quantum-L9\/other`/);
  assert.ok(!probeLog.some((p) => /\/(l9-shiny|other):/.test(p)), probeLog.join(' '));
  // ...and a registered name with no L9-looking prefix is a member.
  assert.deepStrictEqual(
    censusOf(registryDoc([entry('seo-bot', 'SEO-Bot'), entry('x', 'l9-x')])).members.map((m) => m.full_name),
    ['Quantum-L9/SEO-Bot', 'Quantum-L9/l9-x'],
  );
  assert.deepStrictEqual(reconcileDiscovery(censusOf(registryDoc([entry('x', 'l9-x')])),
    [{ name: 'l9-x' }, { name: 'l9-y' }], 'Quantum-L9').unregistered, ['Quantum-L9/l9-y']);
  console.log('ok: governed census — registry admits, discovery observes: one row per member, missing/archived/fork/retired kept, unregistered and l9- prefixed repos outside the denominator');

  // (6) Invalid class, conflicting identity, malformed or unreadable sources:
  // no census, so no repository assessed and no all-clear.
  const good = () => [entry('a', 'a'), entry('b', 'b')];
  const broken = [
    ['class_ref unresolved', registryDoc([entry('a', 'a', 'current', 'l9.repository-class/nope@1')]), classesDoc(), /does not resolve/],
    ['class not admitted', registryDoc(good()), classesDoc({ classes: { l9: { id: CLASS }, x: { id: 'l9.repository-class/x@1' } }, catalog_status: { admitted_classes: ['l9.repository-class/x@1'] } }), /not an admitted class/],
    ['no admitted class', registryDoc(good()), classesDoc({ catalog_status: {} }), /admits no class/],
    ['duplicate id', registryDoc([entry('a', 'a'), entry('a', 'b')]), classesDoc(), /duplicate registry id a/],
    ['case-conflicting coordinates', registryDoc([entry('a', 'Repo'), entry('b', 'repo')]), classesDoc(), /claim the same coordinate/],
    ['unknown lifecycle', registryDoc([entry('a', 'a', 'live')]), classesDoc(), /lifecycle live is not defined/],
    ['incomplete coordinate', registryDoc([{ id: 'a', coordinate: { provider: 'gitlab', organization: 'Q', repository: 'a' }, lifecycle: 'current', class_ref: CLASS }]), classesDoc(), /not a complete github coordinate/],
    ['catalog ref mismatch', registryDoc(good(), { class_catalog_ref: 'l9.repository-classes/other@1' }), classesDoc(), /does not name/],
    ['wrong registry schema', registryDoc(good(), { schema: 'l9.repository-registry/v2' }), classesDoc(), /schema is l9\.repository-registry\/v2/],
    ['wrong registry artifact', registryDoc(good(), { artifact_id: 'l9.repository-registry/local@1' }), classesDoc(), /artifact_id is/],
    ['not canonical', registryDoc(good(), { canonical: false }), classesDoc(), /not marked canonical/],
    ['no repositories', registryDoc([]), classesDoc(), /lists no repositories/],
    ['repositories not a list', registryDoc({ a: 1 }), classesDoc(), /lists no repositories/],
    ['entry not a mapping', registryDoc(['a']), classesDoc(), /is not a mapping/],
    ['aliases not a list', registryDoc(good(), { aliases: 'x' }), classesDoc(), /aliases is not a list/],
    ['registry not a mapping', '[1, 2]', classesDoc(), /is not a mapping/],
    ['registry unparseable', '{not yaml', classesDoc(), /not parseable YAML/],
    ['registry empty', '', classesDoc(), /is empty/],
    ['registry unreadable', new Error('EACCES'), classesDoc(), /unreadable: EACCES/],
    ['classes unreadable', registryDoc(good()), new Error('ENOENT'), /repository_classes\.yaml unreadable/],
  ];
  for (const [label, registry, classes, why] of broken) {
    assert.throws(() => censusOf(registry, classes), why, label);
  }
  assert.throws(() => censusOf(registryDoc(good()), classesDoc(), 'main'), /not a full commit SHA/);
  assert.throws(() => projectGovernedCensus({ registry: null, classes: classesDoc() }), /must be mappings/);
  // Through the real script: a census failure assesses nothing and says so.
  for (const [label, registry, classes] of [
    ['invalid class', registryDoc([entry('id-a', 'a', 'current', 'l9.repository-class/nope@1')]), classesDoc()],
    ['conflicting identity', registryDoc([entry('id-a', 'a'), entry('id-a', 'b')]), classesDoc()],
    ['malformed registry', new Error('mapping values are not allowed here'), classesDoc()],
    ['unreadable class catalog', registryDoc([entry('id-a', 'a')]), new Error('parser crashed')],
  ]) {
    calls = await runReport({ repos: { a: { files: FILES, perms: ALL } }, registry, classes });
    body = bodyOf(calls);
    assert.ok(!body.includes(ALL_CLEAR), label);
    assert.match(body, /The governed census could not be derived from `semantics\/repository_registry\.yaml`/, label);
    assert.match(body, /0 verified allowed · 0 blocked · 0 UNKNOWN/, label);
    assert.deepStrictEqual(probeLog, [], `${label}: nothing probed`);
    assert.ok(calls.warnings.some((w) => /governed census not derived/.test(w)), label);
  }
  calls = await runReport({ repos: { a: { files: FILES, perms: ALL } }, sha: 'main' });
  assert.match(bodyOf(calls), /could not be derived .*not a full commit SHA/);
  // A caller that derives no census at all is told so, too.
  assert.ok(!buildPostureReport([row('a', allowedAll)], { date, census: { error: 'x' } }).body.includes(ALL_CLEAR));
  console.log('ok: governed census — invalid or unadmitted class, conflicting identity, malformed/unreadable source or revision: no census, nothing probed, no all-clear');

  // (7) Determinism: the same bytes project the same census; editing only the
  // registry fixture moves only the registry inventory and digest.
  const before = censusOf(registryDoc(good()));
  assert.deepStrictEqual(censusOf(registryDoc(good())), before);
  const after = censusOf(registryDoc([...good(), entry('c', 'c')]));
  assert.deepStrictEqual(after.members.map((m) => m.id), ['a', 'b', 'c'], 'registry order preserved');
  assert.deepStrictEqual(after.members.slice(0, 2), before.members);
  assert.notStrictEqual(after.provenance.registry.sha256, before.provenance.registry.sha256);
  assert.strictEqual(after.provenance.classes.sha256, before.provenance.classes.sha256);
  assert.deepStrictEqual(before.members[0], {
    id: 'a', coordinate: { provider: 'github', organization: 'Quantum-L9', repository: 'a' },
    full_name: 'Quantum-L9/a', lifecycle: 'current', class_ref: CLASS,
  });
  assert.deepStrictEqual(Object.keys(before.provenance.registry).sort((a, b) => a.localeCompare(b)), ['artifact_id', 'path', 'revision', 'sha256']);

  // (8) The leading-dot `.github` repository is a member like any other.
  calls = await runReport({
    repos: { '.github': { files: FILES, perms: ALL } },
    registry: registryDoc([entry('dot-github', '.github')]),
  });
  body = bodyOf(calls);
  assert.match(body, /\| `\.github` \| ✅ \| ✅ \| ✅ \| allowed \| `dot-github` \|/);
  assert.ok(probeLog.includes('Quantum-L9/.github:.github/CODEOWNERS') && probeLog.includes('Quantum-L9/.github:actions'), probeLog.join(' '));

  // The real canonical sources, through the real parser: every current entry
  // is projected once with its exact coordinate, `.github` included. The
  // expected set is read from the registry, not restated here.
  const realIo = {
    readBytes: (p) => fs.readFileSync(path.join(root, p)),
    parseYaml: pythonYamlParser(childProcess.execFileSync),
    // The witness checks the bytes and their digest; the revision is a fixture.
    revision: 'f'.repeat(40),
  };
  const real = loadGovernedCensus(realIo);
  const realRegistry = loadCanonicalSource(REGISTRY_SOURCE, realIo).doc;
  const currentIds = realRegistry.repositories.filter((e) => e.lifecycle === 'current').map((e) => e.id);
  assert.deepStrictEqual(real.members.map((m) => m.id), currentIds);
  assert.strictEqual(new Set(real.members.map((m) => m.full_name.toLowerCase())).size, real.members.length);
  assert.strictEqual(real.members.find((m) => m.id === 'dot-github')?.full_name, 'Quantum-L9/.github');
  assert.strictEqual(real.provenance.registry.sha256, digestOf(REAL_BYTES.registry));
  console.log(`ok: governed census — deterministic projection; .github is a member; the real registry projects ${real.members.length} current members at ${real.provenance.registry.sha256.slice(0, 12)}`);

  // (10) Reporting only: the workflow keeps read-only contents and writes
  // issues alone; it enrolls nothing in central CI and touches no ruleset.
  const wf = fs.readFileSync(path.join(root, '.github/workflows/governance-report.yml'), 'utf8');
  assert.match(wf, /^permissions:\n {2}contents: read\n {2}issues: write\n\n/m);
  assert.doesNotMatch(wf, /rulesets|Ruleset|setGithubActions|setAllowedActions|createOrUpdateFileContents|required_status_checks|createDispatchEvent/);
  assert.doesNotMatch(wf, /!r\.archived|!r\.fork/, 'no second, implicit list of governed repositories');
  const writes = calls.map((c) => c[0]).filter((n) => n !== 'listForRepo');
  assert.ok(writes.every((n) => ['update', 'createComment', 'create'].includes(n)), writes.join(', '));
  console.log('ok: governance-report.yml — registry membership changes reporting only: no enrollment, ruleset or Actions-policy write');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
