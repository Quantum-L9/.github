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
 * @param {{name: string, marker?: string}[]} repos  org repos the sweep sees;
 *   a repo with `marker` serves it at MARKER_PATH, every other path is missing
 */
function makeGithub(BRANCH, { branch = null, openPRs = [], repos = [{ name: 'consumer-repo' }] }) {
  const calls = [];
  const state = { sha: branch ? branch.sha : null };
  const markerFor = (repo) => repos.find((r) => r.name === repo)?.marker;
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

  const shared = makeBranchStubs({ branch: BRANCH, state, calls, openPRs, record });

  const github = {
    paginate: async () => repos.map((r) => ({
      name: r.name,
      owner: { login: 'Quantum-L9' },
      default_branch: 'main',
      archived: false,
      fork: false,
    })),
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
          const marker = markerFor(args.repo);
          if (args.path === MARKER_PATH && marker !== undefined) {
            return { data: { content: Buffer.from(marker, 'utf8').toString('base64') } };
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
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
