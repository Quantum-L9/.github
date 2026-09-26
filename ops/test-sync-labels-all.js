'use strict';

/**
 * Runs the real `script:` body of sync-labels-all.yml against a stubbed
 * GitHub API and asserts the org label sweep actually fans the taxonomy out.
 *
 * The sweep had never succeeded. Defects this pins:
 *   - auth: it minted an App token from vars.GOVERNANCE_APP_ID, which is not
 *     set, so every scheduled run failed before writing anything;
 *   - `.github` itself was excluded, so the repo that declares the taxonomy
 *     was missing a declared label;
 *   - every non-422 write error was counted as "skipped" and the run stayed
 *     green, so a sweep that wrote nothing looked like one with nothing to do.
 * Against main's workflow this suite fails on the auth assertion and, with
 * that removed, on the `.github` exclusion.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-sync-labels-all.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { makeScriptRunner } = require('./workflow-script-harness.js');
const { parseLabels } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = path.join(root, '.github/workflows/sync-labels-all.yml');
const TAXONOMY = parseLabels(fs.readFileSync(path.join(root, '.github/labels.yml'), 'utf8'));

const httpError = (status, msg) => Object.assign(new Error(msg), { status });

/**
 * @param {object} o
 * @param {Array<object>} o.repos           listForOrg result
 * @param {Record<string, Array>} o.labels  existing labels per repo
 * @param {Set<string>} [o.denyWrites]      repos whose label writes 403
 */
function makeGithub({ repos, labels, denyWrites = new Set() }) {
  const calls = [];
  const state = { labels: JSON.parse(JSON.stringify(labels)) };
  const listFor = (repo) => {
    if (!state.labels[repo]) state.labels[repo] = [];
    return state.labels[repo];
  };
  const find = (repo, name) =>
    listFor(repo).findIndex((l) => l.name.toLowerCase() === name.toLowerCase());
  const github = {
    paginate: async (fn, args) => (await fn(args)).data,
    rest: {
      repos: {
        listForOrg: async (args) => {
          calls.push({ name: 'repos.listForOrg', args });
          return { data: repos };
        },
      },
      issues: {
        createLabel: async (args) => {
          calls.push({ name: 'issues.createLabel', args });
          if (denyWrites.has(args.repo)) throw httpError(403, 'Resource not accessible');
          if (find(args.repo, args.name) >= 0) throw httpError(422, 'already_exists');
          listFor(args.repo).push({
            name: args.name,
            color: args.color,
            description: args.description,
          });
          return { data: {} };
        },
        updateLabel: async (args) => {
          calls.push({ name: 'issues.updateLabel', args });
          if (denyWrites.has(args.repo)) throw httpError(403, 'Resource not accessible');
          const i = find(args.repo, args.name);
          listFor(args.repo)[i] = {
            name: args.name,
            color: args.color,
            description: args.description,
          };
          return { data: {} };
        },
      },
    },
  };
  return { github, calls, state };
}

const run = makeScriptRunner({
  file: WORKFLOW,
  root,
  tmpTag: 'sync-labels-',
  envFor: (dry) => ({ DRY_RUN: dry ? 'true' : 'false', FILTER: '' }),
  makeGithub,
  mutations: new Set(['issues.createLabel', 'issues.updateLabel']),
});

const repo = (name, extra = {}) => ({
  name,
  owner: { login: 'Quantum-L9' },
  archived: false,
  fork: false,
  ...extra,
});
const writesTo = (calls, name) =>
  calls.filter((c) => c.name.startsWith('issues.') && c.args.repo === name);

(async () => {
  // Auth: the credential birth bootstrap already writes labels with, not an
  // App id nobody set.
  const yaml = fs.readFileSync(WORKFLOW, 'utf8');
  assert.ok(
    !/\$\{\{\s*vars\.GOVERNANCE_APP_ID/.test(yaml),
    'sweep must not depend on the unset GOVERNANCE_APP_ID',
  );
  assert.match(yaml, /environment:\s*governance-distribution/);
  assert.match(yaml, /github-token:\s*\$\{\{\s*secrets\.GH_TOKEN\s*\}\}/);
  console.log('ok: auth uses governance-distribution + GH_TOKEN (as repo-birth-bootstrap does)');

  const repos = [
    repo('.github'),
    repo('consumer'),
    repo('old', { archived: true }),
    repo('someones-fork', { fork: true }),
  ];
  const fresh = await run({
    repos,
    labels: {
      '.github': [TAXONOMY[0]],
      consumer: [{ name: 'deps', color: '0366d6', description: '' }],
    },
  });
  assert.deepStrictEqual(fresh.failures, [], 'a clean sweep does not fail');
  // The repo that declares the taxonomy is swept too.
  assert.ok(writesTo(fresh.calls, '.github').length > 0, '.github is swept');
  assert.strictEqual(fresh.state.labels['.github'].length, TAXONOMY.length);
  // A consumer gets every label; its own extra label is left alone.
  assert.strictEqual(fresh.state.labels.consumer.length, TAXONOMY.length + 1);
  assert.ok(fresh.state.labels.consumer.some((l) => l.name === 'deps'));
  assert.strictEqual(writesTo(fresh.calls, 'old').length, 0, 'archived repos are not swept');
  assert.strictEqual(writesTo(fresh.calls, 'someones-fork').length, 0, 'forks are not swept');
  console.log('ok: .github and consumers receive the full taxonomy; extras, archives and forks untouched');

  // Re-running on a synced org converges to the same labels.
  const again = await run({ repos, labels: fresh.state.labels });
  assert.deepStrictEqual(again.failures, []);
  assert.deepStrictEqual(again.state.labels, fresh.state.labels, 're-run changes no label');
  console.log('ok: re-run on a synced org leaves every label as it was');

  // A write the API refuses is a red run, not a quiet "skipped".
  const denied = await run({
    repos: [repo('consumer'), repo('locked')],
    labels: {},
    denyWrites: new Set(['locked']),
  });
  assert.strictEqual(denied.failures.length, 1, 'a refused write fails the run');
  assert.match(denied.failures[0], /1 of 2 repositories had label write failures/);
  assert.strictEqual(
    denied.state.labels.consumer.length,
    TAXONOMY.length,
    'one bad repo does not stop the sweep',
  );
  console.log('ok: a refused write fails the run and the sweep still finishes the other repos');

  // Dry run writes nothing.
  const dry = await run({ dry: true, repos, labels: {} });
  assert.strictEqual(dry.mutated, false, 'dry run writes nothing');
  assert.deepStrictEqual(dry.failures, []);
  console.log('ok: dry run is read-only');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
