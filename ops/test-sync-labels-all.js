'use strict';

/**
 * Runs the real `script:` body of sync-labels-all.yml against a stubbed
 * GitHub API and asserts the org label sweep actually fans the taxonomy out.
 *
 * The defects this pins (the sweep had never succeeded):
 *   - `.github` itself was excluded, so the repo that declares the taxonomy
 *     was missing a declared label;
 *   - every non-422 write error was counted as "skipped" and the run stayed
 *     green, so a sweep that wrote nothing looked like one with nothing to do;
 *   - it ignored the repo class, which decides remote_apply.labels at birth.
 * The auth defect (an unset vars.GOVERNANCE_APP_ID) is asserted on the YAML.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-sync-labels-all.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { notFound, makeScriptRunner } = require('./workflow-script-harness.js');
const { parseLabels } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = path.join(root, '.github/workflows/sync-labels-all.yml');
const TAXONOMY = parseLabels(fs.readFileSync(path.join(root, '.github/labels.yml'), 'utf8'));
const MARKER = '.l9/org-birth-profile.yaml';

const httpError = (status, msg) => Object.assign(new Error(msg), { status });

/**
 * @param {object} o
 * @param {Array<object>} o.repos           listForOrg result
 * @param {Record<string, Array>} o.labels  existing labels per repo
 * @param {Record<string, string|Error>} [o.markers] marker text or error per repo
 * @param {Set<string>} [o.denyWrites]      repos whose label writes 403
 */
function makeGithub({ repos, labels, markers = {}, denyWrites = new Set() }) {
  const calls = [];
  const state = { labels: JSON.parse(JSON.stringify(labels)) };
  const write = (name) => async (args) => {
    calls.push({ name, args });
    if (denyWrites.has(args.repo)) throw httpError(403, 'Resource not accessible by integration');
    if (!state.labels[args.repo]) state.labels[args.repo] = [];
    const list = state.labels[args.repo];
    if (name === 'issues.createLabel') {
      list.push({
        name: args.name,
        color: args.color,
        description: args.description,
      });
    } else {
      const i = list.findIndex((l) => l.name === args.name);
      list[i] = {
        name: args.new_name,
        color: args.color,
        description: args.description,
      };
    }
    return { data: {} };
  };
  const github = {
    paginate: async (fn, args) => (await fn(args)).data,
    rest: {
      repos: {
        listForOrg: async (args) => {
          calls.push({ name: 'repos.listForOrg', args });
          return { data: repos };
        },
        getContent: async (args) => {
          calls.push({ name: 'repos.getContent', args });
          const m = markers[args.repo];
          if (args.path !== MARKER || m === undefined) throw notFound('Not Found');
          if (m instanceof Error) throw m;
          return { data: { content: Buffer.from(m).toString('base64') } };
        },
      },
      issues: {
        listLabelsForRepo: async (args) => {
          calls.push({ name: 'issues.listLabelsForRepo', args });
          return { data: state.labels[args.repo] || [] };
        },
        createLabel: write('issues.createLabel'),
        updateLabel: write('issues.updateLabel'),
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
  calls.filter(
    (c) =>
      c.name.startsWith('issues.') && c.name !== 'issues.listLabelsForRepo' && c.args.repo === name,
  );

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
  assert.strictEqual(writesTo(fresh.calls, '.github').length, TAXONOMY.length - 1);
  assert.strictEqual(fresh.state.labels['.github'].length, TAXONOMY.length);
  // A consumer gets every label; its own extra label is left alone.
  assert.strictEqual(fresh.state.labels.consumer.length, TAXONOMY.length + 1);
  assert.ok(fresh.state.labels.consumer.some((l) => l.name === 'deps'));
  assert.strictEqual(writesTo(fresh.calls, 'old').length, 0, 'archived repos are not swept');
  assert.strictEqual(writesTo(fresh.calls, 'someones-fork').length, 0, 'forks are not swept');
  console.log(
    'ok: .github and consumers receive the full taxonomy; extras, archives and forks untouched',
  );

  // Idempotent: a second sweep over the result writes nothing.
  const again = await run({ repos, labels: fresh.state.labels });
  assert.strictEqual(again.mutated, false, 're-running on a synced org writes nothing');
  assert.deepStrictEqual(again.failures, []);
  console.log('ok: re-run on a synced org is a no-op');

  // A write the API refuses is a red run, not a quiet "skipped".
  const denied = await run({
    repos: [repo('consumer'), repo('locked')],
    labels: {},
    denyWrites: new Set(['locked']),
  });
  assert.strictEqual(denied.failures.length, 1, 'a refused write fails the run');
  assert.match(denied.failures[0], /1 of 2 repositories failed/);
  assert.strictEqual(
    denied.state.labels.consumer.length,
    TAXONOMY.length,
    'one bad repo does not stop the sweep',
  );
  console.log('ok: a refused write fails the run and the sweep still finishes the other repos');

  // Class marker: an unparseable declaration and an unreadable marker are
  // both failures, never a silent fall-through to the default class.
  const marked = await run({
    repos: [repo('bad-marker'), repo('marker-500'), repo('consumer')],
    labels: {},
    markers: {
      'bad-marker': 'profile: no-such-class\n',
      'marker-500': httpError(500, 'boom'),
    },
  });
  assert.strictEqual(writesTo(marked.calls, 'bad-marker').length, 0);
  assert.strictEqual(writesTo(marked.calls, 'marker-500').length, 0);
  assert.strictEqual(marked.state.labels.consumer.length, TAXONOMY.length);
  assert.match(marked.failures[0] || '', /2 of 3 repositories failed/);
  console.log('ok: bad or unreadable class markers fail that repo only');

  // Dry run reports the plan and writes nothing.
  const dry = await run({ dry: true, repos, labels: {} });
  assert.strictEqual(dry.mutated, false, 'dry run writes nothing');
  assert.deepStrictEqual(dry.failures, []);
  console.log('ok: dry run is read-only');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
