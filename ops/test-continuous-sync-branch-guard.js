'use strict';

/**
 * Runs the real `script:` body of the continuous-sync workflow against a
 * stubbed GitHub API and asserts it never rewrites the sync branch while a PR
 * is open on it.
 *
 * Why this is separate from test-seed-workflow-branch-guard.js: continuous-sync
 * moves its branch through the same guarded path as the seeders (one atomic
 * commit, then a GraphQL `updateRefs` compare-and-swap via
 * ops/seed-branch-safety.js), but it plans differently — overwrite of managed
 * paths by class, not missing-only — and authenticates as the governance App,
 * whose provenance identity is `<app-slug>[bot]`. Its fixtures and verdicts
 * are therefore its own.
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
  loadGovernanceGates,
} = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = '.github/workflows/continuous-sync.yml';
const BRANCH = 'chore/governance-sync';
const ORG = 'Quantum-L9';

/** Successful writes only — a rejected compare-and-swap attempt is not a mutation. */
const MUTATIONS = new Set([
  'git.createRef',
  'git.createCommit',
  'graphql.updateRefs',
  'pulls.create',
]);

/** The root listing GitHub returns for a fixture's files: one entry per top-level name. */
const rootEntries = (files) => {
  const top = new Map();
  for (const p of Object.keys(files)) {
    const [head, ...rest] = p.split('/');
    if (top.get(head) !== 'dir') top.set(head, rest.length ? 'dir' : 'file');
  }
  return [...top].map(([name, type]) => ({ name, type }));
};

const APP_SLUG = 'l9-governance';
const SOURCE_SHA = 'f'.repeat(40);
const SYNC_LOGIN = `${APP_SLUG}[bot]`;
const SYNC_COMMIT_SUBJECT_RE = require('./seed-branch-safety.js').SYNC_COMMIT_SUBJECT;
const SYNC_COMMIT = {
  message: 'chore(governance): sync 2 org-managed file(s)',
  committer: SYNC_LOGIN,
  verified: true,
};

/**
 * The guarded write path continuous-sync shares with the seeders
 * (ops/seed-branch-safety.js): compare for provenance, one atomic commit,
 * then a GraphQL updateRefs compare-and-swap on the inspected sha.
 *
 * @param {object} o
 * @param {null|{sha:string, commits?:object[]}} [o.branch]  sync-branch state;
 *   commits are `{message, committer, verified}`, oldest first
 * @param {number[]} [o.openPRs]  open PR numbers with head BRANCH
 * @param {string} [o.movesTo]    the branch moves here after the compare (race)
 * @param {object} [o.files]      consumer files; anything else 404s
 * @param {object} [o.dirs]       directory listings
 * @param {object} [o.errors]     path -> HTTP status thrown on read
 * @param {object[]} [o.otherPRs] other open PRs (see makeBranchStubs)
 * @param {number} [o.listError]  HTTP status listing all open PRs throws
 * @param {string} [o.baseMovesTo] the default branch reads this sha after its first read
 * @param {object} [o.atBase]     files committed at the pinned base (`base-sha`)
 *   that an unpinned read — one made before the pin, against an older tip —
 *   does not see
 */
function makeGithub({ branch = null, openPRs = [], movesTo, files = {}, dirs = {}, errors = {}, otherPRs = [], listError, baseMovesTo, repoName = 'consumer-repo', baseError, atBase = {} } = {}) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const record = (name, ret = {}) => async (args) => {
    calls.push({ name, args });
    if (name === 'git.createRef') state.sha = args.sha;
    return { data: ret };
  };
  const shared = makeBranchStubs({ branch: BRANCH, state, calls, openPRs, otherPRs, listError, record });
  const enc = (t) => Buffer.from(t).toString('base64');
  let baseReads = 0;
  const getRef = async (args) => {
    if (baseError && args.ref === 'heads/main') {
      calls.push({ name: 'git.getRef', args });
      throw Object.assign(new Error(baseError.message), { status: baseError.status });
    }
    const res = await shared.getRef(args);
    if (baseMovesTo && args.ref === 'heads/main' && baseReads++ > 0) return { data: { object: { sha: baseMovesTo } } };
    return res;
  };

  const github = {
    paginate: shared.paginateWith(() => [
      { name: repoName, owner: { login: ORG }, default_branch: 'main', archived: false, fork: false },
    ]),
    request: async (route, args) => {
      calls.push({ name: `request ${route}`, args });
      assert.strictEqual(route, 'GET /repos/{owner}/{repo}/compare/{basehead}');
      assert.strictEqual(args.basehead, `main...${BRANCH}`);
      const commits = (branch && branch.commits) || [SYNC_COMMIT];
      if (movesTo) state.sha = movesTo; // a maintainer pushes right after the verdict
      return {
        data: {
          ahead_by: commits.length,
          commits: commits.map((c, i) => ({
            sha: `c${i}`,
            commit: { message: c.message, verification: { verified: c.verified === true } },
            committer: c.committer ? { login: c.committer } : null,
          })),
        },
      };
    },
    graphql: async (doc, vars) => {
      if (!/mutation/.test(doc)) return { repository: { id: 'R_stub' } };
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
        // An installation token cannot call /user; the workflow must not need it.
        getAuthenticated: async () => {
          throw Object.assign(new Error('Resource not accessible by integration'), { status: 403 });
        },
      },
      repos: {
        listForOrg: () => {},
        getContent: async (args) => {
          calls.push({ name: 'repos.getContent', args });
          if (errors[args.path]) throw Object.assign(new Error('boom'), { status: errors[args.path] });
          if (args.path in dirs) return { data: dirs[args.path].map((n) => ({ name: n, type: n.includes('.') ? 'file' : 'dir' })) };
          const visible = args.ref === 'base-sha' ? { ...files, ...atBase } : files;
          // A repository root always lists: what the fixture holds, by its top-level names.
          if (args.path === '') return { data: rootEntries(visible) };
          if (args.path in visible) return { data: { sha: `sha-${args.path}`, content: enc(visible[args.path]) } };
          throw notFound('Not Found');
        },
      },
      pulls: {
        list: shared.pulls.list,
        listFiles: shared.pulls.listFiles,
        create: async (args) => {
          calls.push({ name: 'pulls.create', args });
          return { data: { number: 999 } };
        },
      },
      git: {
        getRef,
        getCommit: async () => ({ data: { tree: { sha: 'base-tree-sha' } } }),
        createBlob: async (args) => {
          calls.push({ name: 'git.createBlob', args });
          return { data: { sha: `blob-${calls.length}` } };
        },
        createTree: async (args) => {
          calls.push({ name: 'git.createTree', args });
          return { data: { sha: 'tree-sha' } };
        },
        createCommit: async (args) => {
          calls.push({ name: 'git.createCommit', args });
          return { data: { sha: 'new-commit-sha' } };
        },
        createRef: record('git.createRef'),
      },
    },
  };
  return { github, calls, state };
}

const run = makeScriptRunner({
  file: path.join(root, WORKFLOW),
  root,
  tmpTag: 'sync-guard-',
  envFor: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', FILTER: '', APP_SLUG, GITHUB_SHA: SOURCE_SHA }),
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
// dependabot.yml is rendered for the consumer's root (ADR 0019). These
// fixtures hold no Python or pre-commit files at the root, so their canonical
// bytes are the github-actions-only render; the shape-specific cases are in
// dependabotShapeScenarios below.
const { renderDependabot, shapeFromRoot } = require('./render-dependabot.js');
const renderFor = (names, pyprojectText = null) => {
  const prev = process.cwd();
  process.chdir(root);
  try {
    return renderDependabot({ fs, shape: shapeFromRoot({ names, pyprojectText }) });
  } finally {
    process.chdir(prev);
  }
};
const actionsOnly = renderFor([]);
const managedOk = {
  '.github/CODEOWNERS': fs.readFileSync(path.join(root, 'policies/CODEOWNERS'), 'utf8'),
  '.github/dependabot.yml': actionsOnly,
};
const syncScript = loadScriptModule(path.join(root, WORKFLOW), 'sync-class-');
const gates = loadGovernanceGates(root);

async function runClass({ files = {}, dirs = {}, errors = {}, dry = false, branch = null, ...more }) {
  const { github, calls, state } = makeGithub({ files, dirs, errors, branch, ...more });
  const tables = [];
  const failures = [];
  const summary = { addHeading: () => summary, addRaw: () => summary, addTable: (t) => { tables.push(t); return summary; }, write: async () => summary };
  const core = { info() {}, error() {}, setFailed: (m) => failures.push(m), summary };
  const prev = process.cwd();
  const prevEnv = { DRY_RUN: process.env.DRY_RUN, FILTER: process.env.FILTER, APP_SLUG: process.env.APP_SLUG, GITHUB_SHA: process.env.GITHUB_SHA };
  process.chdir(root);
  Object.assign(process.env, { DRY_RUN: dry ? 'true' : 'false', FILTER: '', APP_SLUG, GITHUB_SHA: SOURCE_SHA });
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
  // What the one sync commit carries: tree entries with content, and deletions.
  const tree = (calls.find((c) => c.name === 'git.createTree') || { args: { tree: [] } }).args.tree;
  const blobs = calls.filter((c) => c.name === 'git.createBlob').map((c) => c.args.content);
  const writes = tree.filter((t) => t.sha !== null).map((t, i) => ({
    args: { path: t.path, content: blobs[i] },
  }));
  const deletes = tree.filter((t) => t.sha === null).map((t) => ({ args: { path: t.path } }));
  return { klass, status, detail, writes, deletes, failures, calls, state };
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
  for (const ref of ['v1', 'main', '3e841ea']) {
    r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate, [CALLER]: strictCaller(ref) } });
    assert.deepStrictEqual(r.writes.map((w) => w.args.path), [CALLER], `@${ref} must be re-pinned`);
    assert.strictEqual(Buffer.from(r.writes[0].args.content, 'base64').toString(), strictCaller(canonicalPin));
  }
  r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate, [CALLER]: 'name: Governance\njobs: {}\n' } });
  assert.strictEqual(r.writes.length, 0);
  assert.match(r.detail, /calls neither governance-pr\.yml nor governance-issue\.yml/);
  console.log(`ok: ${label} — caller pins follow governance-caller.yml (any ref form); consumer settings kept`);

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

/** The only calls a Preview may make: reads. Everything else writes. */
const READS = new Set(['repos.getContent', 'pulls.list', 'pulls.listFiles', 'git.getRef', 'request GET /repos/{owner}/{repo}/compare/{basehead}']);
const writesOf = (calls) => calls.filter((c) => !READS.has(c.name));

/**
 * Manual Update modes. Preview writes nothing however much drifted; Apply
 * opens one reviewable PR against the consumer's default branch and moves no
 * ref but the sync branch; consumer content outside the managed population,
 * and opted-out repositories, are never touched in either mode.
 */
async function manualModeScenarios() {
  const label = 'continuous-sync (manual modes)';
  const old = '3'.repeat(40);
  const callerAt = (pin) =>
    `name: Governance\njobs:\n  pr:\n    uses: Quantum-L9/.github/.github/workflows/governance-pr.yml@${pin}\n    with:\n      strict: true\n`;
  // Every kind of drift at once: managed files missing, template divergent,
  // caller pin stale, plus consumer-owned files the sync must never write.
  const consumerOwned = {
    'README.md': '# consumer\n',
    '.github/workflows/ci.yml': 'name: ci\n',
    'SECURITY.md': '# consumer policy\n',
  };
  const drifted = { [TEMPLATE]: '## stale\n', [CALLER]: callerAt(old), ...consumerOwned };
  const stale = { sha: 'stale-sync-branch', commits: [SYNC_COMMIT] };

  // Preview: drift is reported in full; not one non-read call is made.
  let r = await runClass({ files: drifted, branch: stale, dry: true });
  assert.strictEqual(r.status, 'DRIFT');
  for (const p of ['.github/CODEOWNERS', '.github/dependabot.yml', TEMPLATE, CALLER]) {
    assert.ok(r.detail.includes(p), `preview must report ${p}`);
  }
  assert.deepStrictEqual(writesOf(r.calls), [], `${label}: Preview made a write call`);
  assert.strictEqual(r.state.sha, 'stale-sync-branch');
  assert.deepStrictEqual(r.failures, []);
  console.log(`ok: ${label} — Preview reports every drifted path and makes only read calls`);

  // Preview is also the fail-closed state: only DRY_RUN exactly "false" applies.
  for (const value of ['', 'true', 'False', '0', 'undefined']) {
    const p = await run({ branch: stale, envExtra: { DRY_RUN: value } });
    assert.deepStrictEqual(writesOf(p.calls), [], `${label}: DRY_RUN=${JSON.stringify(value)} wrote`);
  }
  console.log(`ok: ${label} — any DRY_RUN other than "false" previews`);

  // Apply: one commit carrying only managed paths, one PR from the sync branch
  // into the default branch, and the only ref moved is the sync branch.
  r = await runClass({ files: drifted, branch: stale });
  assert.strictEqual(r.status, 'UPDATE_PR_OPEN');
  const pr = r.calls.find((c) => c.name === 'pulls.create');
  assert.ok(pr, `${label}: Apply must open a consumer PR`);
  assert.strictEqual(pr.args.head, BRANCH);
  assert.strictEqual(pr.args.base, 'main');
  assert.strictEqual(r.calls.filter((c) => c.name === 'pulls.create').length, 1);
  const moves = r.calls.filter((c) => ['git.createRef', 'graphql.updateRefs'].includes(c.name));
  assert.deepStrictEqual(moves.map((c) => c.args.ref || c.args.name), [`refs/heads/${BRANCH}`],
    `${label}: Apply may move the sync branch and nothing else`);
  const byName = (a, b) => a.localeCompare(b);
  const touched = r.writes.map((w) => w.args.path).sort(byName);
  assert.deepStrictEqual(touched, ['.github/CODEOWNERS', '.github/dependabot.yml', CALLER, TEMPLATE].sort(byName));
  for (const p of Object.keys(consumerOwned)) {
    assert.ok(!touched.includes(p) && !r.deletes.some((d) => d.args.path === p), `${label}: Apply touched ${p}`);
  }
  const caller = Buffer.from(r.writes.find((w) => w.args.path === CALLER).args.content, 'base64').toString();
  assert.strictEqual(caller, callerAt(canonicalPin), `${label}: caller changed beyond its pin`);
  console.log(`ok: ${label} — Apply opens one PR into the default branch; only the sync branch and managed paths move`);

  // Opt-out: drift everywhere, still nothing beyond the marker read, either mode.
  for (const dry of [true, false]) {
    r = await runClass({ files: { ...drifted, '.l9/no-sync': '' }, branch: stale, dry });
    assert.strictEqual(r.status, 'OPTED_OUT');
    // The base is pinned first, then the marker is read AT that pin; nothing
    // else is probed.
    assert.deepStrictEqual(r.calls.map((c) => c.name), ['git.getRef', 'repos.getContent'], `${label}: opted-out repo was probed past its marker`);
    assert.strictEqual(r.calls[0].args.ref, 'heads/main');
    assert.deepStrictEqual([r.calls[1].args.path, r.calls[1].args.ref], ['.l9/no-sync', 'base-sha'], `${label}: opt-out read off the pinned base`);
    assert.strictEqual(r.state.sha, 'stale-sync-branch');
  }
  console.log(`ok: ${label} — .l9/no-sync repos are left untouched in Preview and Apply`);

  // A .l9/no-sync that is a directory is a malformed opt-out, not "absent":
  // it fails closed like the class marker — unresolved, nothing planned.
  for (const dry of [true, false]) {
    r = await runClass({ files: drifted, dirs: { '.l9/no-sync': ['README.md'] }, branch: stale, dry });
    assert.strictEqual(r.status, 'UNREACHABLE', `${label}: no-sync directory was synced (${r.status})`);
    assert.match(r.detail, /\.l9\/no-sync is a directory/);
    assert.deepStrictEqual(writesOf(r.calls), [], `${label}: no-sync directory still wrote`);
    assert.deepStrictEqual(r.calls.map((c) => c.name), ['git.getRef', 'repos.getContent'], `${label}: no-sync directory was probed past its marker`);
    assert.strictEqual(r.state.sha, 'stale-sync-branch');
  }
  console.log(`ok: ${label} — a .l9/no-sync directory fails closed in Preview and Apply`);

  // F3: the opt-out is read at the same pinned commit as the plan.
  // (a) A marker committed between an unpinned probe and the pin is part of
  //     the snapshot: it opts the repo out. A probe made before the pin would
  //     miss it and publish into a repo that had opted out, and BASE_MOVED
  //     would not fire because the base did not move after the pin.
  for (const dry of [true, false]) {
    r = await runClass({ files: drifted, branch: stale, dry, atBase: { '.l9/no-sync': '' } });
    assert.strictEqual(r.status, 'OPTED_OUT', `${label}: opt-out committed at the pinned base ignored (dry=${dry})`);
    assert.deepStrictEqual(writesOf(r.calls), [], `${label}: wrote to an opted-out repo (dry=${dry})`);
    assert.strictEqual(r.state.sha, 'stale-sync-branch');
  }
  // (b) A marker committed after the pinned snapshot moves the base: the final
  //     BASE_MOVED check refuses publication. No ref moves, no PR.
  r = await runClass({ files: drifted, branch: stale, baseMovesTo: 'base-with-no-sync' });
  assert.strictEqual(r.status, 'BASE_MOVED');
  assert.ok(!r.calls.some((c) => ['git.createRef', 'graphql.updateRefs', 'pulls.create'].includes(c.name)),
    `${label}: published past an opt-out landed after the snapshot`);
  assert.strictEqual(r.state.sha, 'stale-sync-branch');
  // (c) An opt-out nobody could read is not "absent": named blocker, run
  //     fails, and not one non-read call is made in either mode.
  for (const [code, status] of [[403, 'BLOCKED_PERMISSION'], [500, 'UNREACHABLE'], [502, 'UNREACHABLE']]) {
    for (const dry of [true, false]) {
      r = await runClass({ files: drifted, branch: stale, dry, errors: { '.l9/no-sync': code } });
      assert.strictEqual(r.status, status, `${label}: opt-out ${code} (dry=${dry})`);
      assert.deepStrictEqual(writesOf(r.calls), [], `${label}: opt-out ${code} still wrote (dry=${dry})`);
      assert.strictEqual(r.failures.length, 1, `${label}: opt-out ${code} must fail the run`);
      assert.ok(!r.calls.some((c) => c.name === 'repos.getContent' && c.args.path !== '.l9/no-sync'),
        `${label}: planned past an unreadable opt-out (${code})`);
    }
  }
  console.log(`ok: ${label} — opt-out read at the pinned base; one landing after the snapshot is BASE_MOVED; 403/5xx blocks with no write`);
}

/**
 * Class before plan, exact bytes, ownership, overlap, a moving base, and the
 * PR body (GAR G3/G4/G5/G6, V06–V16).
 */
async function ownershipScenarios() {
  const label = 'continuous-sync (class, ownership, overlap)';
  const marker = (cls) => ({ '.l9/org-birth-profile.yaml': `profile: ${cls}\n` });
  const divergent = { '.github/CODEOWNERS': '* @someone-else\n', '.github/dependabot.yml': 'version: 2\nupdates: []\n' };
  const mutatedAny = (r) => writesOf(r.calls).length > 0;

  // V06: self_governed never plans CODEOWNERS / dependabot, however divergent.
  for (const dry of [true, false]) {
    const r = await runClass({ files: { ...divergent, ...marker('self_governed') }, dry });
    assert.strictEqual(r.klass, 'self_governed');
    assert.strictEqual(r.status, 'INHERITED', `${label}: self_governed planned a write (${r.detail})`);
    assert.strictEqual(mutatedAny(r), false);
  }
  // l9-ci-core is self_governed by org override: same answer with no marker.
  console.log(`ok: ${label} — self_governed: CODEOWNERS/dependabot never planned or written`);

  // A malformed or unknown marker plans nothing — not even CODEOWNERS.
  for (const text of ['profile: no_such_class\n', 'garbage\n']) {
    const r = await runClass({ files: { ...divergent, '.l9/org-birth-profile.yaml': text } });
    assert.strictEqual(r.status, 'BLOCKED_POLICY');
    assert.match(r.detail, /nothing planned/);
    assert.strictEqual(mutatedAny(r), false, `${label}: malformed marker still wrote`);
  }
  // A marker that cannot be read (403) is not "absent".
  {
    const r = await runClass({ files: divergent, errors: { '.l9/org-birth-profile.yaml': 403 } });
    assert.strictEqual(r.status, 'BLOCKED_PERMISSION');
    assert.strictEqual(mutatedAny(r), false);
  }
  console.log(`ok: ${label} — malformed/unknown/unreadable marker: no writes at all`);

  // V07: a root CODEOWNERS means .github/CODEOWNERS is not managed.
  {
    const r = await runClass({ files: { ...managedOk, [TEMPLATE]: canonicalTemplate, CODEOWNERS: '* @owner\n' } });
    assert.strictEqual(r.status, 'CANONICAL_COPY', r.detail);
    const r2 = await runClass({ files: { 'CODEOWNERS': '* @owner\n', '.github/dependabot.yml': managedOk['.github/dependabot.yml'], [TEMPLATE]: canonicalTemplate } });
    assert.ok(!r2.writes.some((w) => w.args.path === '.github/CODEOWNERS'), `${label}: wrote .github/CODEOWNERS over a root CODEOWNERS`);
    assert.strictEqual(r2.status, 'CANONICAL_COPY');
  }
  console.log(`ok: ${label} — root CODEOWNERS present: .github/CODEOWNERS never written`);

  // V08: whitespace-only difference in a fully managed file is drift.
  {
    const r = await runClass({ files: { ...managedOk, '.github/dependabot.yml': `${managedOk['.github/dependabot.yml']}\n`, [TEMPLATE]: canonicalTemplate } });
    assert.deepStrictEqual(r.writes.map((w) => w.args.path), ['.github/dependabot.yml']);
    assert.strictEqual(Buffer.from(r.writes[0].args.content, 'base64').toString(), managedOk['.github/dependabot.yml']);
  }
  console.log(`ok: ${label} — exact-byte comparison: trailing whitespace is drift`);

  // non_constellation_python: CODEOWNERS/dependabot managed; template inherited.
  {
    const r = await runClass({ files: { ...divergent, ...marker('non_constellation_python') } });
    assert.deepStrictEqual(r.writes.map((w) => w.args.path).sort(), ['.github/CODEOWNERS', '.github/dependabot.yml']);
  }

  // V10: a divergent local template under an INHERIT class is not deleted.
  for (const cls of ['self_governed', 'non_constellation_python']) {
    for (const dry of [true, false]) {
      const r = await runClass({ files: { ...managedOk, ...marker(cls), [TEMPLATE]: '## our own\n' }, dry });
      assert.strictEqual(r.deletes.length, 0, `${label}: ${cls} deleted an unproven local template`);
      assert.match(r.detail, /BLOCKED_OWNERSHIP \.github\/pull_request_template\.md/);
      if (cls === 'self_governed') assert.strictEqual(r.status, 'BLOCKED_OWNERSHIP');
    }
  }
  console.log(`ok: ${label} — divergent template under an INHERIT class: BLOCKED_OWNERSHIP, never deleted`);

  // V11: another open PR changes a planned path (directly or by rename).
  const drifted = { ...managedOk, [TEMPLATE]: '## stale\n' };
  for (const files of [[{ filename: TEMPLATE }], [{ filename: 'docs/t.md', previous_filename: TEMPLATE }]]) {
    for (const dry of [true, false]) {
      const r = await runClass({ files: drifted, dry, otherPRs: [{ number: 51, ref: 'chore/seed-governance', files }] });
      assert.strictEqual(r.status, 'BLOCKED_CONFLICT');
      assert.match(r.detail, /open PR #51 \(chore\/seed-governance\) also changes \.github\/pull_request_template\.md/);
      assert.strictEqual(mutatedAny(r), false);
      assert.deepStrictEqual(r.failures, []);
    }
  }
  // V12: an unrelated PR does not block.
  {
    const r = await runClass({ files: drifted, otherPRs: [{ number: 52, ref: 'x', files: [{ filename: 'README.md' }] }] });
    assert.strictEqual(r.status, 'UPDATE_PR_OPEN');
  }
  // V13: the PR listing cannot be read.
  for (const [opts, status] of [[{ otherPRs: [{ number: 53, ref: 'x', filesError: 403 }] }, 'BLOCKED_PERMISSION'], [{ listError: 503 }, 'UNREACHABLE']]) {
    const r = await runClass({ files: drifted, ...opts });
    assert.strictEqual(r.status, status);
    assert.strictEqual(mutatedAny(r), false);
  }
  console.log(`ok: ${label} — overlapping pending PR: BLOCKED_CONFLICT; unreadable listing: named blocker; no write`);

  // V15: the default branch moves between plan and commit.
  {
    const r = await runClass({ files: drifted, baseMovesTo: 'base-moved' });
    assert.strictEqual(r.status, 'BASE_MOVED');
    assert.ok(!r.calls.some((c) => ['git.createRef', 'graphql.updateRefs', 'pulls.create'].includes(c.name)));
  }
  console.log(`ok: ${label} — a base that moves before publication stops; no ref or PR`);

  // V16 / V23: the Apply PR body passes the org validator and states facts only.
  {
    const r = await runClass({ files: drifted });
    const body = r.calls.find((c) => c.name === 'pulls.create').args.body;
    assert.deepStrictEqual(await gates(body), [], `${label}: Manual Update PR body fails governance-pr gates`);
    assert.match(body, new RegExp(`source: Quantum-L9/\\.github@${SOURCE_SHA}`));
    assert.match(body, /base: {3}main@base-sha/);
    assert.match(body, /^ {2}modify {2}\.github\/pull_request_template\.md$/m);
    assert.match(body, /- \[x\] Medium/, 'overwriting consumer bytes is not Low');
    assert.doesNotMatch(body, /- \[x\][^\n]*CI passes/i);
    const add = await runClass({ files: { '.github/dependabot.yml': managedOk['.github/dependabot.yml'], [TEMPLATE]: canonicalTemplate } });
    const addBody = add.calls.find((c) => c.name === 'pulls.create').args.body;
    assert.deepStrictEqual(await gates(addBody), []);
    assert.match(addBody, /- \[x\] Low/, 'restoring an absent managed file is additive');
  }
  console.log(`ok: ${label} — Apply PR body passes governance-pr gates (strict) with exact base, source and changes`);

  // The plan is read at one pinned commit: every read, the opt-out probe
  // included, names the base sha, so a file changed on the default branch mid-plan is
  // judged against the same commit the final BASE_MOVED check pins.
  {
    const r = await runClass({ files: { ...managedOk, ...marker('non_constellation_python'), [TEMPLATE]: canonicalTemplate } });
    const reads = r.calls.filter((c) => c.name === 'repos.getContent');
    assert.strictEqual(reads[0].args.path, '.l9/no-sync', `${label}: the opt-out is the first read`);
    assert.ok(reads.length > 3);
    for (const c of reads) assert.strictEqual(c.args.ref, 'base-sha', `${label}: ${c.args.path} read off the pinned base`);
    assert.deepStrictEqual(r.deletes.map((d) => d.args.path), [TEMPLATE]);
  }
  console.log(`ok: ${label} — every planning read is pinned to the base sha`);

  // An org-override class is reported as such, not as a marker.
  {
    const r = await runClass({ repoName: 'l9-repo-template', files: divergent });
    assert.strictEqual(r.klass, 'non_constellation_python');
    const body = r.calls.find((c) => c.name === 'pulls.create').args.body;
    assert.match(body, /class: {2}non_constellation_python \(org override\)/);
    assert.doesNotMatch(body, /\(marker\)/);
  }
  console.log(`ok: ${label} — override-classified repo: PR body names the org override, not a marker`);

  // An empty repository has nothing to sync and is not a failure; any other
  // base-ref error is.
  {
    let r = await runClass({ files: divergent, baseError: { status: 409, message: 'Git Repository is empty.' } });
    assert.strictEqual(r.status, 'UNINITIALIZED');
    assert.deepStrictEqual(r.failures, []);
    assert.strictEqual(mutatedAny(r), false);
    r = await runClass({ files: divergent, baseError: { status: 409, message: 'Conflict' } });
    assert.strictEqual(r.status, 'UNREACHABLE');
    assert.strictEqual(r.failures.length, 1);
  }
  console.log(`ok: ${label} — empty repo reported UNINITIALIZED; other base-ref errors fail`);
}

/**
 * dependabot.yml is rendered for the repository's root (ADR 0019): the
 * comparison and the restore both use the render for the shape read at the
 * pinned base, and a root that cannot be listed plans nothing.
 */
async function dependabotShapeScenarios() {
  const label = 'continuous-sync (rendered dependabot)';
  const DEP = '.github/dependabot.yml';
  const uvRoot = { 'uv.lock': 'version = 1\n', 'pyproject.toml': '[project]\nname = "x"\n', 'requirements.txt': 'x==1\n' };
  const uvRender = renderFor(['pyproject.toml', 'requirements.txt', 'uv.lock'], uvRoot['pyproject.toml']);
  assert.match(uvRender, /package-ecosystem: uv/);
  // The bytes .github distributed before ADR 0019: github-actions only, for every repo.
  const legacyTemplate = [
    '# Managed by Quantum-L9/.github. dependabot.yml is NOT inheritable — it is seeded',
    '# per repo and must live at .github/dependabot.yml on the default branch.',
    '#',
    '# Default seed is github-actions only (SHA-pin freshness). pip / npm ecosystems',
    '# are not seeded unless a consumer adds them after a lockfile exists.',
    '# ADVISORY POSTURE: this opens PRs only. No auto-merge, no major groups.',
    'version: 2',
    'updates:',
    '  - package-ecosystem: github-actions',
    '    directory: "/"',
    '    schedule:',
    '      interval: weekly',
    '      day: monday',
    '    open-pull-requests-limit: 2',
    '    commit-message:',
    '      prefix: "chore(deps)"',
    '    groups:',
    '      actions-minor-patch:',
    '        patterns: ["*"]',
    '        update-types: ["minor", "patch"]',
    '',
  ].join('\n');
  const base = { '.github/CODEOWNERS': managedOk['.github/CODEOWNERS'], [TEMPLATE]: canonicalTemplate, ...uvRoot };

  // A uv repo already holding its uv render is in sync: no write, no PR.
  let r = await runClass({ files: { ...base, [DEP]: uvRender } });
  assert.strictEqual(r.status, 'CANONICAL_COPY', r.detail);
  assert.strictEqual(r.calls.some((c) => c.name === 'pulls.create'), false);
  console.log(`ok: ${label} — uv repo holding its uv render: CANONICAL_COPY, no write`);

  // The same repo holding the old actions-only bytes, or the actions-only
  // render, is restored to the uv render — never to actions-only.
  for (const [what, stale] of [['legacy template', legacyTemplate], ['actions-only render', actionsOnly]]) {
    r = await runClass({ files: { ...base, [DEP]: stale } });
    assert.strictEqual(r.status, 'UPDATE_PR_OPEN', `${what}: ${r.detail}`);
    assert.deepStrictEqual(r.writes.map((w) => w.args.path), [DEP]);
    assert.strictEqual(Buffer.from(r.writes[0].args.content, 'base64').toString(), uvRender, `${label}: ${what} not restored to the uv render`);
  }
  // Preview names the same restore and writes nothing.
  r = await runClass({ files: { ...base, [DEP]: legacyTemplate }, dry: true });
  assert.strictEqual(r.status, 'DRIFT');
  assert.match(r.detail, /restore \.github\/dependabot\.yml/);
  assert.deepStrictEqual(writesOf(r.calls), []);
  console.log(`ok: ${label} — legacy or actions-only bytes in a uv repo restore to the uv render`);

  // A root that cannot be listed, or a listed pyproject.toml that cannot be
  // read, is not an empty root: named blocker, run fails, nothing written.
  for (const [errors, status] of [
    [{ '': 403 }, 'BLOCKED_PERMISSION'],
    [{ '': 500 }, 'UNREACHABLE'],
    [{ 'pyproject.toml': 502 }, 'UNREACHABLE'],
  ]) {
    for (const dry of [true, false]) {
      r = await runClass({ files: { ...base, [DEP]: legacyTemplate }, errors, dry });
      assert.strictEqual(r.status, status, `${label}: ${JSON.stringify(errors)} (dry=${dry}) → ${r.status}`);
      assert.deepStrictEqual(writesOf(r.calls), [], `${label}: wrote with an unreadable root (${JSON.stringify(errors)})`);
      assert.strictEqual(r.failures.length, 1);
    }
  }
  // A root listing that answers 404 is not a directory listing either.
  r = await runClass({ files: { ...base, [DEP]: legacyTemplate }, errors: { '': 404 } });
  assert.strictEqual(r.status, 'UNREACHABLE');
  assert.deepStrictEqual(writesOf(r.calls), []);
  console.log(`ok: ${label} — unlistable root or unreadable pyproject.toml: no actions-only fallback, no write`);

  // The root listing and pyproject.toml are read at the pinned base.
  r = await runClass({ files: { ...base, [DEP]: uvRender } });
  for (const p of ['', 'pyproject.toml']) {
    const c = r.calls.find((x) => x.name === 'repos.getContent' && x.args.path === p);
    assert.ok(c, `${label}: ${p || 'root'} not read`);
    assert.strictEqual(c.args.ref, 'base-sha');
  }
  console.log(`ok: ${label} — root listing and pyproject.toml read at the pinned base`);
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
  const refReadIdx = r.calls.findIndex((c) => c.name === 'git.getRef' && c.args.ref === `heads/${BRANCH}`);
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

  // 4. No open PR, branch holds only this workflow's own verified commit:
  //    rebuilt through the compare-and-swap, so remediation is not deadlocked.
  r = await run({ branch: { sha: 'stale-sync-branch', commits: [SYNC_COMMIT] } });
  const swap = r.calls.find((c) => c.name === 'graphql.updateRefs');
  assert.ok(swap, `${label}: own stale branch with no PR should be rebuilt`);
  assert.strictEqual(swap.args.beforeOid, 'stale-sync-branch', `${label}: the move must pin the inspected sha`);
  assert.strictEqual(r.state.sha, 'new-commit-sha');
  assert.ok(r.names.includes('pulls.create'), `${label}: rebuilt branch should get a PR`);
  assert.strictEqual(r.names.filter((n) => n === 'git.createCommit').length, 1, `${label}: one atomic commit`);
  const message = r.calls.find((c) => c.name === 'git.createCommit').args.message;
  assert.match(message.split('\n')[0], SYNC_COMMIT_SUBJECT_RE, `${label}: commit subject must match the gate pattern`);
  console.log(`ok: ${label} — own stale branch is rebuilt via compare-and-swap, one commit`);

  // 4b. A branch carrying anything this workflow cannot prove it wrote is
  //     never rebuilt: a human commit, a spoofed subject with no verified
  //     signature, the right subject from another committer.
  for (const [what, commits] of [
    ['a human commit', [{ message: 'fix: maintainer tweak', committer: 'maintainer', verified: true }]],
    ['a spoofed subject, unverified', [{ ...SYNC_COMMIT, verified: false }]],
    ['the sync subject from another committer', [{ ...SYNC_COMMIT, committer: 'maintainer' }]],
    ['two commits', [SYNC_COMMIT, SYNC_COMMIT]],
  ]) {
    r = await run({ branch: { sha: 'branch-under-review', commits } });
    assert.strictEqual(r.mutated, false, `${label}: rebuilt a branch holding ${what}`);
    assert.strictEqual(r.state.sha, 'branch-under-review');
  }
  console.log(`ok: ${label} — branch with unproven provenance is never rebuilt`);

  // 4c. The branch moves after the verdict (a push lands mid-run): the
  //     compare-and-swap rejects the move, and nothing is opened.
  r = await run({ branch: { sha: 'stale-sync-branch', commits: [SYNC_COMMIT] }, movesTo: 'pushed-meanwhile' });
  assert.ok(r.names.includes('graphql.updateRefs.rejected'), `${label}: move was not compare-and-swap`);
  assert.strictEqual(r.state.sha, 'pushed-meanwhile', `${label}: overwrote a push that landed mid-run`);
  assert.ok(!r.names.includes('pulls.create'));
  console.log(`ok: ${label} — a push landing mid-run is never overwritten`);

  // 5. Dry run writes nothing at all.
  r = await run({ branch: { sha: 'stale-sync-branch' }, dry: true });
  assert.strictEqual(r.mutated, false, `${label}: dry run performed a write`);
  console.log(`ok: ${label} — dry run performs no writes`);

  await classScenarios();
  await manualModeScenarios();
  await ownershipScenarios();
  await dependabotShapeScenarios();
  console.log('\nall continuous-sync branch-guard scenarios passed');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
