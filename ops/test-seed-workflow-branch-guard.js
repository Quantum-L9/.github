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
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

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
  },
];

const MUTATIONS = ['git.createRef', 'git.updateRef', 'git.createCommit', 'pulls.create'];

/** Extract the github-script `script: |` block without a YAML dependency. */
function extractScript(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const start = lines.findIndex((l) => /^\s*script:\s*\|\s*$/.test(l));
  assert.ok(start !== -1, `no "script: |" block in ${file}`);
  const indent = lines[start].match(/^\s*/)[0].length + 2;
  const body = [];
  for (const line of lines.slice(start + 1)) {
    if (line.trim() !== '' && line.match(/^\s*/)[0].length < indent) break;
    body.push(line.slice(indent));
  }
  return body.join('\n');
}

const notFound = (msg) => Object.assign(new Error(msg), { status: 404 });

/**
 * @param {string} BRANCH               seed branch the workflow under test uses
 * @param {null|{sha,aheadBy,commits}} branch  stubbed remote branch state
 * @param {number[]} openPRs            open PR numbers with head BRANCH
 */
function makeGithub(BRANCH, { branch, openPRs }) {
  const calls = [];
  const record = (name) => async (args) => {
    calls.push({ name, args });
    if (name === 'git.createBlob') return { data: { sha: 'blob-sha' } };
    if (name === 'git.createTree') return { data: { sha: 'tree-sha' } };
    if (name === 'git.createCommit') return { data: { sha: 'new-commit-sha' } };
    if (name === 'pulls.create') return { data: { number: 999 } };
    return { data: {} };
  };

  const github = {
    paginate: async () => [
      {
        name: 'consumer-repo',
        owner: { login: 'Quantum-L9' },
        default_branch: 'main',
        archived: false,
        fork: false,
      },
    ],
    request: async (route, args) => {
      calls.push({ name: `request ${route}`, args });
      assert.strictEqual(route, 'GET /repos/{owner}/{repo}/compare/{basehead}');
      assert.strictEqual(args.basehead, `main...${BRANCH}`);
      assert.ok(branch, 'compare requested for a branch that does not exist');
      return {
        data: {
          ahead_by: branch.aheadBy,
          commits: branch.commits.map((message, i) => ({ sha: `c${i}`, commit: { message } })),
        },
      };
    },
    rest: {
      repos: {
        // Every seed path is missing on the consumer: the full payload is selected.
        getContent: async () => {
          throw notFound('Not Found');
        },
        get: async () => {
          throw notFound('Not Found');
        },
      },
      pulls: {
        list: async (args) => {
          calls.push({ name: 'pulls.list', args });
          return { data: openPRs.map((number) => ({ number })) };
        },
        create: record('pulls.create'),
      },
      git: {
        getRef: async (args) => {
          calls.push({ name: 'git.getRef', args });
          if (args.ref === `heads/${BRANCH}`) {
            if (!branch) throw notFound('Branch not found');
            return { data: { object: { sha: branch.sha } } };
          }
          return { data: { object: { sha: 'base-sha' } } };
        },
        getCommit: async () => ({ data: { tree: { sha: 'base-tree-sha' } } }),
        createBlob: record('git.createBlob'),
        createTree: record('git.createTree'),
        createCommit: record('git.createCommit'),
        createRef: record('git.createRef'),
        updateRef: record('git.updateRef'),
      },
    },
  };
  return { github, calls };
}

function makeCore() {
  const failures = [];
  const summary = {
    addHeading: () => summary,
    addRaw: () => summary,
    addTable: () => summary,
    write: async () => summary,
  };
  return { info() {}, error() {}, setFailed: (m) => failures.push(m), summary, failures };
}

const scopedRequire = (m) => require(m.startsWith('.') ? path.resolve(root, m) : m);

function makeRunner(wf) {
  const body = extractScript(path.join(root, wf.file));
  const fn = new Function(
    'github',
    'core',
    'context',
    'require',
    `return (async () => {\n${body}\n})()`,
  );

  return async function run({ branch, openPRs = [], dry = false, mutateGithub } = {}) {
    const prevCwd = process.cwd();
    const env = wf.env(dry);
    const prevEnv = Object.fromEntries(Object.keys(env).map((k) => [k, process.env[k]]));
    process.chdir(root);
    Object.assign(process.env, env);
    const { github, calls } = makeGithub(wf.branch, { branch, openPRs });
    if (mutateGithub) mutateGithub(github, wf.branch);
    const core = makeCore();
    try {
      await fn(github, core, {}, scopedRequire);
    } finally {
      process.chdir(prevCwd);
      for (const [k, v] of Object.entries(prevEnv)) {
        if (v === undefined) delete process.env[k];
        else process.env[k] = v;
      }
    }
    const names = calls.map((c) => c.name);
    return {
      calls,
      names,
      failures: core.failures,
      mutated: names.some((n) => MUTATIONS.includes(n)),
    };
  };
}

(async () => {
  for (const wf of WORKFLOWS) {
    const run = makeRunner(wf);
    const SEED = wf.seedSubject;
    const label = path.basename(wf.file);

    // 1. The incident: remediation commits stacked on the seed commit.
    let r = await run({
      branch: {
        sha: 'branch-sha',
        aheadBy: 2,
        commits: [SEED, 'fix(governance): make the seeded templates safe to run here'],
      },
    });
    assert.strictEqual(r.mutated, false, `${label}: rewrote a branch carrying remediation commits`);
    assert.deepStrictEqual(r.failures, [], `${label}: leaving a branch alone is not a failure`);
    console.log(`ok: ${label} — branch carrying non-seeder commits is left alone`);

    // 2. An open seed PR is work in flight — skip before any git read/write.
    r = await run({
      branch: { sha: 'branch-sha', aheadBy: 1, commits: [SEED] },
      openPRs: [42],
    });
    assert.strictEqual(r.mutated, false, `${label}: wrote to a repo with an open seed PR`);
    assert.ok(
      !r.names.some((n) => n.startsWith('request ')),
      `${label}: open PR must short-circuit before the compare call`,
    );
    console.log(`ok: ${label} — repo with an open seed PR is skipped`);

    // 3. Fresh repo: create the branch, never force-update it.
    r = await run({ branch: null });
    assert.ok(r.names.includes('git.createRef'), `${label}: fresh repo must get a seed branch`);
    assert.ok(!r.names.includes('git.updateRef'), `${label}: fresh repo must not force-update`);
    assert.ok(r.names.includes('pulls.create'), `${label}: fresh repo must get a seed PR`);
    console.log(`ok: ${label} — fresh repo is seeded with a created ref and a PR`);

    // 4. Pristine seeder branch with no open PR: refresh is allowed.
    r = await run({ branch: { sha: 'branch-sha', aheadBy: 1, commits: [SEED] } });
    const update = r.calls.find((c) => c.name === 'git.updateRef');
    assert.ok(update, `${label}: pristine seeder branch should be refreshable`);
    assert.strictEqual(update.args.force, true, `${label}: rebuild onto a newer base needs force`);
    console.log(`ok: ${label} — pristine seeder branch is refreshed`);

    // 5. Compare-and-swap: the branch moves between the verdict and the ref write.
    r = await run({
      branch: { sha: 'branch-sha', aheadBy: 1, commits: [SEED] },
      mutateGithub: (github, BRANCH) => {
        const realGetRef = github.rest.git.getRef;
        let seen = 0;
        github.rest.git.getRef = async (args) => {
          const res = await realGetRef(args);
          if (args.ref === `heads/${BRANCH}` && seen++ > 0) {
            return { data: { object: { sha: 'someone-else-pushed' } } };
          }
          return res;
        };
      },
    });
    assert.ok(
      !r.names.includes('git.updateRef'),
      `${label}: a branch that moved mid-run must not be overwritten`,
    );
    console.log(`ok: ${label} — branch that moves mid-run is left alone`);

    // 6. Dry run never writes.
    r = await run({ branch: null, dry: true });
    assert.strictEqual(r.mutated, false, `${label}: dry run must not write`);
    console.log(`ok: ${label} — dry run performs no writes`);
  }
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
