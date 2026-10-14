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
  loadGovernanceGates,
} = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');

const SEEDER_LOGIN = 'seeder-bot';
const SOURCE_SHA = 'f'.repeat(40);

// Both seeders share the rebuild-then-move-ref shape, so both get the same proof.
const WORKFLOWS = [
  {
    file: '.github/workflows/auto-seed-new-repo.yml',
    branch: 'chore/auto-seed-governance',
    seedSubject: 'chore(governance): auto-seed 28 org template file(s)',
    env: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', TARGET_REPO: '', GITHUB_SHA: SOURCE_SHA }),
    autoSeed: true,
  },
  {
    file: '.github/workflows/seed-governance.yml',
    branch: 'chore/seed-governance',
    seedSubject: 'chore(governance): seed 28 org template file(s)',
    env: (dry) => ({
      SEED_MODE: dry ? 'dry-run' : 'seed',
      SEED_REPO_FILTER: '',
      SEED_CATEGORIES: 'all',
      GITHUB_SHA: SOURCE_SHA,
    }),
    explicitCategoriesEnv: (list) => ({ SEED_CATEGORIES: list }),
  },
];

// Successful writes only — a rejected compare-and-swap attempt is not a mutation.
const MUTATIONS = new Set([
  'git.createRef',
  'git.createCommit',
  'pulls.create',
  'graphql.updateRefs',
]);

const MARKER_PATH = '.l9/org-birth-profile.yaml';

/**
 * @param {string} BRANCH               seed branch the workflow under test uses
 * @param {null|{sha,aheadBy,commits}} branch  stubbed remote branch state;
 *   commits are `{message, committer, verified}` fixtures, oldest first
 * @param {number[]} openPRs            open PR numbers with head BRANCH
 * @param {{name: string, marker?: string, files?: object, errors?: object}[]} repos
 *   org repos the sweep sees; a repo with `marker` serves it at MARKER_PATH,
 *   `files` serves path -> content, `errors` throws path -> HTTP status, and
 *   every other path is missing
 * @param {object[]} otherPRs  other open PRs (see makeBranchStubs)
 * @param {number} [listError] HTTP status listing all open PRs throws
 */
function makeGithub(BRANCH, { branch = null, openPRs = [], otherPRs = [], listError, repos = [{ name: 'consumer-repo' }] }) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const repoFor = (repo) => repos.find((r) => r.name === repo) || {};
  // The branch state is one shared `sha`, which is exactly what the
  // single-repo guard scenarios observe. A multi-repo sweep must not let the
  // first repo's createRef make every later repo look like it already has a
  // seed branch, so with several repos the ref stays per-run fresh.
  const sharedBranchState = repos.length === 1;
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'git.createBlob') return { data: { sha: 'blob-sha' } };
    if (name === 'git.createTree') return { data: { sha: 'tree-sha' } };
    if (name === 'git.createCommit') return { data: { sha: 'new-commit-sha' } };
    if (name === 'pulls.create') return { data: { number: 999 } };
    if (name === 'git.createRef' && sharedBranchState) state.sha = args.sha;
    return { data: {} };
  };

  const shared = makeBranchStubs({ branch: BRANCH, state, calls, openPRs, otherPRs, listError, record });

  const github = {
    paginate: shared.paginateWith(() => repos.map((r) => ({
      name: r.name,
      owner: { login: 'Quantum-L9' },
      default_branch: 'main',
      archived: false,
      fork: false,
    }))),
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
        // Every seed path is missing on the consumer, so the whole class
        // payload is selected. Only a declared class marker is served.
        getContent: async (args) => {
          calls.push({ name: 'repos.getContent', args });
          const r = repoFor(args.repo);
          if (r.errors?.[args.path]) {
            throw Object.assign(new Error(`HTTP ${r.errors[args.path]}`), { status: r.errors[args.path] });
          }
          // `atBase` is content committed at the pinned base (`base-sha`,
          // what heads/main resolves to) that an unpinned read — one that
          // ran before the pin, against an older tip — does not see.
          const files = {
            ...(r.files || {}),
            ...(r.marker !== undefined ? { [MARKER_PATH]: r.marker } : {}),
            ...(args.ref === 'base-sha' ? r.atBase || {} : {}),
          };
          if (args.path in files) {
            return { data: { type: 'file', content: Buffer.from(files[args.path], 'utf8').toString('base64') } };
          }
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

const gates = loadGovernanceGates(root);
const WRITES = new Set([...MUTATIONS, 'git.createBlob', 'git.createTree']);
const wrote = (r) => r.names.some((n) => WRITES.has(n));
const one = (name, extra = {}) => [{ name, ...extra }];

/**
 * Reads that fail, competing PRs, a moving base, an empty repository, and the
 * PR body: every case either writes exactly the class payload or nothing.
 */
async function failClosedScenarios(wf, run, label) {
  const rowOf = (r, name = 'consumer-repo') => r.rows.find((row) => row[0] === name);

  // V03: an unreadable marker (403) or destination (500) is not "absent".
  for (const [what, errors] of [
    ['marker 403', { [MARKER_PATH]: 403 }],
    ['destination 500', { 'SECURITY.md': 500 }],
    ['root CODEOWNERS 409', { CODEOWNERS: 409 }],
  ]) {
    const r = await run({ branch: null, repos: one('consumer-repo', { errors }) });
    assert.strictEqual(wrote(r), false, `${label}: ${what} must write nothing`);
    assert.ok(!r.names.includes('pulls.list'), `${label}: ${what} must stop before the branch gate`);
    assert.strictEqual(r.failures.length, 1, `${label}: ${what} must fail the run`);
    assert.match(rowOf(r)[2], /failed:/, `${label}: ${what} must be reported, not planned under default`);
  }
  // A directory where a file belongs is not a file.
  {
    const r = await run({
      branch: null,
      repos: one('consumer-repo'),
      mutateGithub: (github) => {
        const real = github.rest.repos.getContent;
        github.rest.repos.getContent = async (args) => (args.path === MARKER_PATH ? { data: [{ name: 'x' }] } : real(args));
      },
    });
    assert.strictEqual(wrote(r), false, `${label}: a directory marker must write nothing`);
    assert.match(rowOf(r)[2], /is not a readable file/);
  }
  console.log(`ok: ${label} — 403/409/5xx and non-file reads fail closed: no default class, no write`);

  // F2: the plan is read at the base it is committed onto. The base sha is
  // pinned before the first policy read, and every getContent — root
  // CODEOWNERS, class marker, each destination, and the second missing-only
  // pass — names that sha. A marker committed between an unpinned plan and
  // the pin would otherwise be planned as `default` and committed onto a base
  // that declares non_constellation_python: a stale-class write that the
  // final BASE_MOVED check cannot see, because the base did not move after
  // the pin.
  for (const dry of [false, true]) {
    const r = await run({
      branch: null,
      dry,
      repos: one('consumer-repo', { atBase: { [MARKER_PATH]: 'profile: non_constellation_python\n' } }),
    });
    const reads = r.calls.filter((c) => c.name === 'repos.getContent');
    assert.ok(reads.some((c) => c.args.path === 'CODEOWNERS'), `${label}: root CODEOWNERS was not read`);
    assert.ok(reads.some((c) => c.args.path === MARKER_PATH), `${label}: class marker was not read`);
    for (const c of reads) {
      assert.strictEqual(c.args.ref, 'base-sha', `${label}: ${c.args.path} read off the pinned base (dry=${dry})`);
    }
    const pin = r.calls.findIndex((c) => c.name === 'git.getRef' && c.args.ref === 'heads/main');
    const firstRead = r.calls.findIndex((c) => c.name === 'repos.getContent');
    assert.ok(pin !== -1 && pin < firstRead, `${label}: base must be pinned before the first policy read (dry=${dry})`);
    assert.strictEqual(rowOf(r)[1], 'non_constellation_python', `${label}: planned under a stale class (dry=${dry})`);
    if (dry) {
      assert.match(rowOf(r)[2], /would seed 4/);
      assert.strictEqual(wrote(r), false);
    } else {
      const tree = r.calls.find((c) => c.name === 'git.createTree').args.tree.map((t) => t.path).sort();
      assert.deepStrictEqual(tree, ['.github/CODEOWNERS', '.github/dependabot.yml', '.github/labels.yml', 'SECURITY.md'],
        `${label}: stale-class write`);
      assert.ok(!tree.includes('.github/workflows/governance.yml'));
    }
  }
  // A destination committed at the pinned base is present, not missing.
  {
    const r = await run({ branch: null, repos: one('consumer-repo', { atBase: { 'SECURITY.md': '# consumer-owned\n' } }) });
    const tree = r.calls.find((c) => c.name === 'git.createTree').args.tree.map((t) => t.path);
    assert.ok(!tree.includes('SECURITY.md'), `${label}: overwrote a file present at the pinned base`);
  }
  // A base that cannot be pinned plans nothing: no policy read, no write.
  for (const status of [403, 500]) {
    const r = await run({
      branch: null,
      mutateGithub: (github) => {
        const real = github.rest.git.getRef;
        github.rest.git.getRef = async (args) => {
          if (args.ref === 'heads/main') throw Object.assign(new Error(`HTTP ${status}`), { status });
          return real(args);
        };
      },
    });
    assert.strictEqual(r.names.includes('repos.getContent'), false, `${label}: planned without a pinned base (${status})`);
    assert.strictEqual(wrote(r), false);
    assert.match(rowOf(r)[2], /^failed:/);
    assert.strictEqual(r.failures.length, 1);
  }
  console.log(`ok: ${label} — base pinned before planning; every read names it; no stale-class write; unpinnable base fails closed`);

  // V11: a different open PR changes a planned path (directly, or by rename).
  for (const files of [[{ filename: 'SECURITY.md' }], [{ filename: 'docs/security.md', previous_filename: 'SECURITY.md' }]]) {
    const r = await run({ branch: null, otherPRs: [{ number: 77, ref: 'feature/sec', files }] });
    assert.strictEqual(wrote(r), false, `${label}: seeded over a pending PR's path`);
    assert.match(rowOf(r)[2], /^BLOCKED_CONFLICT: open PR #77 \(feature\/sec\) also changes SECURITY\.md/);
    assert.deepStrictEqual(r.failures, [], `${label}: a conflict refusal is not a run failure`);
    assert.ok(r.warnings.some((w) => /another open PR/.test(w)));
  }
  // Dry run reports the same refusal.
  {
    const r = await run({ branch: null, dry: true, otherPRs: [{ number: 77, ref: 'feature/sec', files: [{ filename: 'SECURITY.md' }] }] });
    assert.match(rowOf(r)[2], /^BLOCKED_CONFLICT/);
  }
  console.log(`ok: ${label} — a pending PR on a planned path (incl. rename) blocks the seed: BLOCKED_CONFLICT, no write`);

  // V12: a PR on an unrelated path does not block.
  {
    const r = await run({ branch: null, otherPRs: [{ number: 78, ref: 'feature/readme', files: [{ filename: 'README.md' }] }] });
    assert.ok(r.names.includes('git.createRef') && r.names.includes('pulls.create'), `${label}: unrelated PR blocked the seed`);
  }
  console.log(`ok: ${label} — an unrelated open PR does not block`);

  // V13: open PRs or their files cannot be read → named blocker, no write.
  for (const [what, opts, status] of [
    ['files 403', { otherPRs: [{ number: 79, ref: 'x', filesError: 403 }] }, 'BLOCKED_PERMISSION'],
    ['files 502', { otherPRs: [{ number: 79, ref: 'x', filesError: 502 }] }, 'UNREACHABLE'],
    ['list 500', { listError: 500 }, 'UNREACHABLE'],
  ]) {
    const r = await run({ branch: null, ...opts });
    assert.strictEqual(wrote(r), false, `${label}: ${what} must write nothing`);
    assert.match(rowOf(r)[2], new RegExp(`^${status}:`), `${label}: ${what}`);
    assert.strictEqual(r.failures.length, 1, `${label}: ${what} must fail the run`);
  }
  console.log(`ok: ${label} — unreadable PR listings block with BLOCKED_PERMISSION / UNREACHABLE`);

  // V15: the default branch moves between plan and commit.
  {
    const r = await run({
      branch: null,
      mutateGithub: (github) => {
        const real = github.rest.git.getRef;
        let baseReads = 0;
        github.rest.git.getRef = async (args) => {
          const res = await real(args);
          if (args.ref === 'heads/main' && baseReads++ > 0) return { data: { object: { sha: 'base-moved' } } };
          return res;
        };
      },
    });
    assert.ok(!r.names.some((n) => ['git.createRef', 'graphql.updateRefs', 'pulls.create'].includes(n)), `${label}: published a commit built on a stale base`);
    assert.match(rowOf(r)[2], /^BASE_MOVED:/);
  }
  console.log(`ok: ${label} — a base that moves before publication stops the run; no ref or PR`);

  // V16: the seed PR body passes the org validator, strictly, and is honest.
  {
    const r = await run({ branch: null });
    const body = r.calls.find((c) => c.name === 'pulls.create').args.body;
    assert.deepStrictEqual(await gates(body), [], `${label}: seed PR body fails governance-pr gates`);
    assert.match(body, new RegExp(`source: Quantum-L9/\\.github@${SOURCE_SHA}`));
    assert.match(body, /base: {3}main@base-sha/);
    assert.match(body, /^ {2}SECURITY\.md$/m, `${label}: evidence lists the actual paths`);
    assert.match(body, /- \[x\] Medium/, `${label}: a CODEOWNERS/workflow seed is Medium`);
    assert.match(body, /- \[ \] Consumer CI passes on this PR — unverified/);
    assert.doesNotMatch(body, /- \[x\][^\n]*CI passes/i, `${label}: claims CI it did not observe`);
    assert.doesNotMatch(body, /Closes #\d/, `${label}: invents an issue number`);
    // An inherit-heavy class adds only SECURITY.md + labels via explicit ask: Low.
    const low = await run({ branch: null, repos: one('ncp', { marker: 'profile: non_constellation_python\n', files: { '.github/CODEOWNERS': 'x', '.github/dependabot.yml': 'x' } }) });
    const lowBody = low.calls.find((c) => c.name === 'pulls.create').args.body;
    assert.deepStrictEqual(await gates(lowBody), []);
    assert.match(lowBody, /- \[x\] Low/);
  }
  console.log(`ok: ${label} — seed PR body passes governance-pr gates (strict) with real paths, base and source; no invented CI`);

  // V21: everything eligible is present → no bytes, branch or PR.
  {
    const files = Object.fromEntries([
      '.github/CODEOWNERS', '.github/dependabot.yml', '.github/workflows/governance.yml', 'SECURITY.md',
      '.github/ISSUE_TEMPLATE/1-bug.yml', '.github/ISSUE_TEMPLATE/2-feature.yml', '.github/ISSUE_TEMPLATE/3-task.yml',
      '.github/ISSUE_TEMPLATE/4-incident.yml', '.github/ISSUE_TEMPLATE/ci-failure.yml', '.github/ISSUE_TEMPLATE/gov-violation.yml',
      '.github/ISSUE_TEMPLATE/config.yml', '.github/pull_request_template.md', '.github/PULL_REQUEST_TEMPLATE/release.md',
    ].map((p) => [p, 'local\n']));
    const r = await run({ branch: null, repos: one('consumer-repo', { files }) });
    assert.strictEqual(wrote(r), false, `${label}: re-seed of a complete repo wrote`);
    assert.match(rowOf(r)[2], /already seeded/);
  }
  console.log(`ok: ${label} — a repo holding every eligible file gets no write`);

  if (wf.autoSeed) {
    // V19: an empty repository is UNINITIALIZED_NOT_SEEDED, and the sweep goes on.
    const emptyRepo = (status, message) => (github) => {
      const real = github.rest.git.getRef;
      github.rest.git.getRef = async (args) => {
        if (args.repo === 'empty-repo') throw Object.assign(new Error(message), { status });
        return real(args);
      };
    };
    let r = await run({ branch: null, repos: [{ name: 'empty-repo' }, { name: 'plain-repo' }], mutateGithub: emptyRepo(409, 'Git Repository is empty.') });
    assert.match(rowOf(r, 'empty-repo')[2], /^UNINITIALIZED_NOT_SEEDED/);
    assert.ok(!r.calls.some((c) => c.args && c.args.repo === 'empty-repo' && WRITES.has(c.name)), `${label}: wrote to an empty repo`);
    assert.ok(r.calls.some((c) => c.name === 'pulls.create' && c.args.repo === 'plain-repo'), `${label}: sweep stopped at the empty repo`);
    assert.deepStrictEqual(r.failures, [], `${label}: an empty repo is not a failure`);
    assert.ok(r.warnings.some((w) => /no commits and were NOT seeded: empty-repo/.test(w)));
    // The base pin runs first in a dry run too, so a preview reports the same
    // state rather than "would seed" onto a branch that does not exist.
    r = await run({ branch: null, dry: true, repos: [{ name: 'empty-repo' }], mutateGithub: emptyRepo(409, 'Git Repository is empty.') });
    assert.match(rowOf(r, 'empty-repo')[2], /^UNINITIALIZED_NOT_SEEDED/);
    assert.deepStrictEqual(r.failures, []);
    assert.ok(!r.names.includes('repos.getContent'), `${label}: planned an empty repo`);
    console.log(`ok: ${label} — empty repository reported UNINITIALIZED_NOT_SEEDED; sweep continues`);

    // V20: any other 409, or a 403, at the ref stage is a failure, never seeded.
    for (const [status, message] of [[409, 'Reference update conflict'], [403, 'Resource not accessible by integration']]) {
      r = await run({ branch: null, repos: [{ name: 'empty-repo' }], mutateGithub: emptyRepo(status, message) });
      assert.match(rowOf(r, 'empty-repo')[2], /^failed:/, `${label}: ${status} ${message} must fail`);
      assert.strictEqual(r.failures.length, 1);
      assert.strictEqual(wrote(r), false);
    }
    console.log(`ok: ${label} — other 409s and 403s at the ref stage fail; never reported seeded`);
  }
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

    // ── Repo-class policy: both seeders classify every target the same way ──
    // marker > override > default; a malformed explicit marker is skipped and
    // reported; FORBID destinations are never written; INHERIT destinations
    // are never copied. Proven on the written blobs (seed) and on the
    // reported rows (dry run), so neither mode can emit a forbidden path.
    const blobPaths = (res) => res.calls
      .filter((c) => c.name === 'git.createTree')
      .flatMap((c) => c.args.tree.map((t) => t.path))
      .sort();
    const rowFor = (res, name) => res.rows.find((row) => row[0] === name);
    const FORBIDDEN_FOR_GOVERNED = [
      '.github/workflows/governance.yml',
      '.github/workflows/l9-analysis.yml',
      '.github/workflows/l9-lint-test.yml',
      '.github/workflows/on-org-update.yml',
    ];
    const INHERITED_BY_DEFAULT = [
      'CODE_OF_CONDUCT.md', 'CONTRIBUTING.md', 'SUPPORT.md',
      '.github/FUNDING.yml', '.github/VULNERABILITY_REPORT.yml',
    ];
    const classRepos = [
      { name: 'plain-repo' },
      { name: 'ncp-repo', marker: 'schema: l9.org-birth-profile-marker/v1\nprofile: non_constellation_python\n' },
      { name: 'self-repo', marker: 'profile: self_governed\n' },
      { name: 'typo-repo', marker: 'profile: non_constelation_python\n' },
      { name: 'l9-ci-core' }, // no marker; classified by the org override
    ];

    // 7. Seed mode: the blobs written per repo are exactly the class payload.
    r = await run({ branch: null, repos: classRepos });
    const treesByRepo = {};
    for (const c of r.calls) {
      if (c.name === 'git.createTree') {
        treesByRepo[c.args.repo] = c.args.tree.map((t) => t.path).sort();
      }
    }
    assert.ok(treesByRepo['plain-repo'], `${label}: default-class repo must be seeded`);
    assert.ok(treesByRepo['plain-repo'].includes('.github/workflows/governance.yml'));
    assert.ok(treesByRepo['plain-repo'].includes('SECURITY.md'));
    assert.ok(treesByRepo['plain-repo'].includes('.github/PULL_REQUEST_TEMPLATE/release.md'));
    for (const inherited of INHERITED_BY_DEFAULT) {
      assert.ok(!treesByRepo['plain-repo'].includes(inherited), `${label}: default must not copy ${inherited}`);
    }
    assert.deepStrictEqual(
      treesByRepo['ncp-repo'],
      ['.github/CODEOWNERS', '.github/dependabot.yml', '.github/labels.yml', 'SECURITY.md'],
      `${label}: non_constellation_python must receive exactly its class payload`,
    );
    for (const denied of FORBIDDEN_FOR_GOVERNED) {
      assert.ok(!treesByRepo['ncp-repo'].includes(denied), `${label}: wrote forbidden ${denied} to ncp-repo`);
    }
    assert.strictEqual(treesByRepo['self-repo'], undefined, `${label}: self_governed must get no tree`);
    assert.strictEqual(treesByRepo['l9-ci-core'], undefined, `${label}: override-classified self_governed repo must get no tree`);
    assert.strictEqual(treesByRepo['typo-repo'], undefined, `${label}: malformed marker must not be seeded`);
    assert.match(rowFor(r, 'typo-repo')[2], /skipped: .*unknown class non_constelation_python/, `${label}: malformed marker is reported`);
    assert.strictEqual(rowFor(r, 'typo-repo')[1], 'unresolved');
    assert.match(rowFor(r, 'self-repo')[2], /nothing safe to seed/);
    assert.strictEqual(rowFor(r, 'ncp-repo')[1], 'non_constellation_python');
    assert.strictEqual(rowFor(r, 'plain-repo')[1], 'default');
    assert.deepStrictEqual(r.failures, [], `${label}: class skips are not run failures`);
    assert.ok(r.warnings.some((w) => /typo-repo/.test(w)), `${label}: unresolved marker must raise a warning`);
    console.log(`ok: ${label} — seed mode writes exactly each class's payload; forbidden paths never, malformed markers skipped`);

    // 8. Dry run: the reported preview carries the same class decision.
    r = await run({ branch: null, dry: true, repos: classRepos });
    assert.strictEqual(r.mutated, false, `${label}: dry run with classes must not write`);
    assert.strictEqual(blobPaths(r).length, 0);
    const ncpPreview = rowFor(r, 'ncp-repo')[2];
    assert.match(ncpPreview, /would seed 4/, `${label}: ncp dry run previews 4 files (got ${ncpPreview})`);
    for (const denied of FORBIDDEN_FOR_GOVERNED) {
      assert.ok(!ncpPreview.includes(denied), `${label}: dry-run preview names forbidden ${denied}`);
    }
    assert.match(rowFor(r, 'self-repo')[2], /nothing safe to seed/);
    assert.match(rowFor(r, 'typo-repo')[2], /skipped: .*unknown class/);
    assert.match(rowFor(r, 'plain-repo')[2], /would seed 13/);
    console.log(`ok: ${label} — dry run previews the class payload and never a forbidden path`);

    // 9. An explicit category the class forbids skips the repo with the class
    //    and path named, writes nothing, and the run still succeeds. Only the
    //    dispatch seeder takes an explicit category list.
    if (wf.explicitCategoriesEnv) {
      r = await run({ branch: null, repos: classRepos, envExtra: wf.explicitCategoriesEnv('governance') });
      const forbidRow = rowFor(r, 'ncp-repo');
      assert.match(forbidRow[2], /class forbids requested category/, `${label}: explicit forbidden category must be a reported skip`);
      assert.match(forbidRow[2], /governance\.yml/);
      assert.strictEqual(forbidRow[1], 'non_constellation_python');
      assert.ok(!r.calls.some((c) => c.name === 'git.createTree' && c.args.repo === 'ncp-repo'), `${label}: wrote to a repo whose class forbids the request`);
      assert.ok(!r.calls.some((c) => c.name === 'git.createTree' && c.args.repo === 'self-repo'));
      assert.ok(r.calls.some((c) => c.name === 'git.createTree' && c.args.repo === 'plain-repo'), `${label}: default class still receives the explicit category`);
      assert.deepStrictEqual(r.failures, []);
      assert.ok(r.warnings.some((w) => /forbids a requested category/.test(w)));
      // Same request, dry run: the same skip, still nothing written.
      r = await run({ branch: null, dry: true, repos: classRepos, envExtra: wf.explicitCategoriesEnv('governance') });
      assert.match(rowFor(r, 'ncp-repo')[2], /class forbids requested category/);
      assert.strictEqual(r.mutated, false);
      // An explicit category the class inherits drops out, never copies.
      r = await run({ branch: null, repos: classRepos, envExtra: wf.explicitCategoriesEnv('community-health,pr-templates') });
      const ncpTree = r.calls.find((c) => c.name === 'git.createTree' && c.args.repo === 'ncp-repo');
      assert.deepStrictEqual(ncpTree.args.tree.map((t) => t.path), ['SECURITY.md'], `${label}: inherited PR templates must drop for ncp`);
      assert.ok(!r.calls.some((c) => c.name === 'git.createTree' && c.args.repo === 'self-repo'), `${label}: self_governed inherits SECURITY.md and templates`);
      console.log(`ok: ${label} — explicit categories pass through the class: FORBID skips with reason, INHERIT drops`);
    }

    await failClosedScenarios(wf, run, label);
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
