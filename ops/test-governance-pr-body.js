'use strict';

/**
 * Runs the real `body` job script of governance-pr.yml (the machine-owned PR
 * body refresh every consumer PR gets) against stubbed GitHub and process
 * surfaces, and asserts its write discipline:
 *
 *   - it PATCHes only when the composer reports a changed region;
 *   - it never describes a head it did not check out (stale event);
 *   - it never overwrites a PR that moved while it computed (compare-and-set);
 *   - a read-only token is a reported block, not a silent pass or a failure;
 *   - a composer or inventory failure is surfaced, never swallowed.
 *
 * The renderer itself (Cursor-Governance ops/scripts/compose_pr_body.py) is
 * tested where it lives. Set L9_COMPOSER_CHECKOUT to a Cursor-Governance
 * checkout to also run one scenario end to end with the real composer.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-governance-pr-body.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const childProcess = require('node:child_process');
const { loadScriptModule } = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = path.join(root, '.github/workflows/governance-pr.yml');
// Block 0 is the `gates` job, block 1 the `body` job.
const bodyJob = loadScriptModule(WORKFLOW, 'governance-pr-body-', 1);
const HEAD = 'a'.repeat(40);
const BASE = 'b'.repeat(40);

function makeCore() {
  const out = { failures: [], warnings: [], notices: [], tables: [] };
  const summary = {
    addHeading: () => summary,
    addTable: (rows) => {
      out.tables.push(rows);
      return summary;
    },
    write: async () => summary,
  };
  return Object.assign(out, {
    info() {},
    notice: (m) => out.notices.push(m),
    warning: (m) => out.warnings.push(m),
    setFailed: (m) => out.failures.push(m),
    summary,
  });
}

/**
 * @param {object[]} reads   successive pulls.get payloads (last one repeats)
 * @param {object} [o]
 * @param {number} [o.updateStatus]  HTTP status pulls.update throws with
 */
function makeGithub(reads, { updateStatus } = {}) {
  const calls = [];
  let n = 0;
  const github = {
    rest: {
      pulls: {
        get: async (args) => {
          calls.push({ name: 'pulls.get', args });
          const data = reads[Math.min(n, reads.length - 1)];
          n += 1;
          return { data };
        },
        update: async (args) => {
          calls.push({ name: 'pulls.update', args });
          if (updateStatus) throw Object.assign(new Error('denied'), { status: updateStatus });
          return { data: {} };
        },
      },
    },
  };
  return { github, calls };
}

/** The process surface: git rev-parse and the two composer modes. */
function makeProcess({ checkedOut = HEAD, status = 'updated', next = 'NEW BODY', composeError, checkError }) {
  const runs = [];
  const rendered = [];
  const execFileSync = (cmd, args) => {
    runs.push([cmd, ...args]);
    if (cmd === 'git') return `${checkedOut}\n`;
    if (args.includes('--refresh-body')) {
      rendered.push(fs.readFileSync('body.md', 'utf8'));
      if (composeError) throw Object.assign(new Error('exit 2'), { stderr: composeError });
      fs.writeFileSync('status.json', JSON.stringify({ status }));
      return next;
    }
    if (args.includes('--check-body')) {
      if (checkError) throw Object.assign(new Error('exit 1'), { stderr: checkError });
      return '';
    }
    throw new Error(`unexpected ${cmd} ${args.join(' ')}`);
  };
  return { runs, rendered, execFileSync };
}

const pr = (over = {}) => ({ state: 'open', head: { sha: HEAD }, base: { sha: BASE }, body: 'OLD', ...over });

async function run({ reads = [pr()], updateStatus, strict = 'false', proc = {} } = {}) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'pr-body-job-'));
  const prev = process.cwd();
  const prevEnv = { STRICT: process.env.STRICT, COMPOSER: process.env.COMPOSER };
  process.chdir(cwd);
  Object.assign(process.env, { STRICT: strict, COMPOSER: 'Quantum-L9/Cursor-Governance@test' });
  const { github, calls } = makeGithub(reads, { updateStatus });
  const fake = makeProcess(proc);
  const core = makeCore();
  const req = (m) => (m === 'child_process' ? { execFileSync: fake.execFileSync } : require(m));
  const context = { repo: { owner: 'Quantum-L9', repo: 'consumer' }, payload: { pull_request: { number: 7 } } };
  try {
    await bodyJob(github, core, context, req);
  } finally {
    process.chdir(prev);
    for (const [k, v] of Object.entries(prevEnv)) {
      if (v === undefined) delete process.env[k];
      else process.env[k] = v;
    }
    fs.rmSync(cwd, { recursive: true, force: true });
  }
  const updates = calls.filter((c) => c.name === 'pulls.update');
  const status = core.tables.length ? core.tables.at(-1)[1][0] : null;
  return { calls, updates, core, status, runs: fake.runs, rendered: fake.rendered };
}

const scenarios = [];
const scenario = (name, fn) => scenarios.push([name, fn]);

scenario('a changed region is written once, then the inventory is checked', async () => {
  const r = await run();
  assert.strictEqual(r.updates.length, 1);
  assert.strictEqual(r.updates[0].args.body, 'NEW BODY');
  assert.strictEqual(r.updates[0].args.pull_number, 7);
  assert.strictEqual(r.status, 'UPDATED');
  const refresh = r.runs.find((a) => a.includes('--refresh-body'));
  assert.ok(refresh.includes('--remote'), 'the event refresh never claims local receipts');
  assert.deepStrictEqual(refresh.slice(refresh.indexOf('--pr-base'), refresh.indexOf('--pr-base') + 2), ['--pr-base', BASE]);
  assert.ok(r.runs.some((a) => a.includes('--check-body')));
  assert.deepStrictEqual(r.core.failures, []);
});

scenario('an unchanged body is not PATCHed (no edited-event churn)', async () => {
  const r = await run({ proc: { status: 'unchanged', next: 'OLD' } });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.status, 'UNCHANGED');
});

scenario('a body without regions that make pr did not compose is left alone', async () => {
  const r = await run({ proc: { status: 'unmanaged', next: 'OLD' } });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.status, 'UNMANAGED');
  assert.ok(!r.runs.some((a) => a.includes('--check-body')), 'a person-owned body is not judged');
});

scenario('a stale event never describes a head it did not check out', async () => {
  const r = await run({ proc: { checkedOut: 'c'.repeat(40) } });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.status, 'SKIPPED_STALE_EVENT');
  assert.ok(!r.runs.some((a) => a[0] === 'python3'), 'the composer is not even run');
});

scenario('a closed PR is not edited', async () => {
  const r = await run({ reads: [pr({ state: 'closed' })] });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.status, 'SKIPPED_CLOSED');
});

for (const [what, moved] of [
  ['head', pr({ head: { sha: 'd'.repeat(40) } })],
  ['base', pr({ base: { sha: 'e'.repeat(40) } })],
]) {
  scenario(`a PR whose ${what} moved during the refresh is not overwritten`, async () => {
    const r = await run({ reads: [pr(), moved] });
    assert.strictEqual(r.updates.length, 0);
    assert.strictEqual(r.status, 'SKIPPED_MOVED');
  });
}

scenario('a reviewer edit during the refresh is re-rendered from, not overwritten', async () => {
  const edited = pr({ body: 'EDITED BY A REVIEWER MEANWHILE' });
  const r = await run({ reads: [pr(), edited, edited] });
  assert.deepStrictEqual(r.rendered, ['OLD', 'EDITED BY A REVIEWER MEANWHILE'], 'second render starts from their text');
  assert.strictEqual(r.updates.length, 1);
  assert.strictEqual(r.status, 'UPDATED');
});

scenario('a body that keeps changing is left for the next event', async () => {
  const r = await run({ reads: [pr(), pr({ body: 'e1' }), pr({ body: 'e2' }), pr({ body: 'e3' })] });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.status, 'SKIPPED_MOVED');
  assert.strictEqual(r.rendered.length, 3);
});

scenario('a read-only token is a reported block, not a pass or a failure', async () => {
  const r = await run({ updateStatus: 403 });
  assert.strictEqual(r.status, 'BLOCKED_PERMISSION');
  assert.strictEqual(r.core.warnings.length, 1);
  assert.deepStrictEqual(r.core.failures, []);
});

scenario('any other API error is not swallowed', async () => {
  await assert.rejects(run({ updateStatus: 500 }), /denied/);
});

scenario('a composer failure fails the job and writes nothing', async () => {
  const r = await run({ proc: { composeError: 'ERROR: git diff failed' } });
  assert.strictEqual(r.updates.length, 0);
  assert.strictEqual(r.core.failures.length, 1);
  assert.match(r.core.failures[0], /git diff failed/);
});

scenario('an inventory mismatch fails a strict caller and notifies an advisory one', async () => {
  const strict = await run({ strict: 'true', proc: { checkError: 'UNDECLARED: a.py' } });
  assert.strictEqual(strict.core.failures.length, 1);
  assert.strictEqual(strict.status, 'INVENTORY_MISMATCH');
  const advisory = await run({ proc: { checkError: 'UNDECLARED: a.py' } });
  assert.deepStrictEqual(advisory.core.failures, []);
  assert.strictEqual(advisory.core.notices.length, 1);
});

scenario('pr-files.yml delegates to the body job and runs no renderer of its own', async () => {
  const text = fs.readFileSync(path.join(root, '.github/workflows/pr-files.yml'), 'utf8');
  assert.match(text, /uses: \.\/\.github\/workflows\/governance-pr\.yml/);
  assert.match(text, /gates: false/);
  assert.doesNotMatch(text, /script:/);
  const gov = fs.readFileSync(WORKFLOW, 'utf8');
  const pins = [...gov.matchAll(/Quantum-L9\/Cursor-Governance@([0-9a-f]{40})|ref: ([0-9a-f]{40})/g)]
    .map((m) => m[1] || m[2]);
  assert.strictEqual(pins.length, 2, 'composer pin and checkout ref');
  assert.strictEqual(pins[0], pins[1], 'the env pin and the checkout ref name the same commit');
});

/** One end-to-end run with the real composer, when a checkout is supplied. */
// Absolute executables from a fixed system directory; nothing resolved via PATH.
const GIT = '/usr/bin/git';
const PYTHON = '/usr/bin/python3';
const FIXED_PATH = '/usr/bin:/bin';
if (process.env.L9_COMPOSER_CHECKOUT) {
  scenario('end to end: a push from another client refreshes the real body', async () => {
    const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'pr-body-e2e-'));
    const git = (...a) => childProcess.execFileSync(GIT, ['-C', path.join(cwd, 'pr'), ...a], {
      encoding: 'utf8',
      env: { PATH: FIXED_PATH, GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@x', GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@x' },
    });
    fs.mkdirSync(path.join(cwd, 'pr'));
    git('init', '-q', '-b', 'main');
    fs.writeFileSync(path.join(cwd, 'pr', 'a.py'), 'a\n');
    git('add', 'a.py');
    git('commit', '-q', '-m', 'base');
    const base = git('rev-parse', 'HEAD').trim();
    git('checkout', '-q', '-b', 'feat');
    fs.writeFileSync(path.join(cwd, 'pr', 'b.py'), 'b\n');
    git('add', 'b.py');
    git('commit', '-q', '-m', 'feat: add b');
    const template = fs.readFileSync(path.join(root, '.github/pull_request_template.md'), 'utf8');
    const composer = path.join(process.env.L9_COMPOSER_CHECKOUT, 'ops/scripts/compose_pr_body.py');
    fs.writeFileSync(path.join(cwd, 'template.md'), template);
    const first = childProcess.execFileSync(PYTHON, [composer, '--workspace', path.join(cwd, 'pr'),
      '--pr-base', base, '--template', path.join(cwd, 'template.md')], { encoding: 'utf8', env: { PATH: FIXED_PATH } });
    const reviewed = first.replace('<!-- EVIDENCE:END -->', '<!-- EVIDENCE:END -->\n\nReviewer note kept.');
    fs.writeFileSync(path.join(cwd, 'pr', 'c.py'), 'c\n');
    git('add', 'c.py');
    git('commit', '-q', '-m', 'feat: add c from the web editor');
    const head = git('rev-parse', 'HEAD').trim();
    fs.symlinkSync(process.env.L9_COMPOSER_CHECKOUT, path.join(cwd, 'composer'));
    const { github, calls } = makeGithub([{ state: 'open', head: { sha: head }, base: { sha: base }, body: reviewed }]);
    const core = makeCore();
    const prev = process.cwd();
    process.chdir(cwd);
    try {
      await bodyJob(github, core, { repo: { owner: 'Quantum-L9', repo: 'consumer' }, payload: { pull_request: { number: 7 } } }, require);
    } finally {
      process.chdir(prev);
    }
    const update = calls.find((c) => c.name === 'pulls.update');
    assert.ok(update, `no PATCH; failures=${core.failures} tables=${JSON.stringify(core.tables)}`);
    assert.match(update.args.body, /- `c\.py` — feat: add c from the web editor/);
    assert.match(update.args.body, /Reviewer note kept\./);
    assert.match(update.args.body, /STALE: receipts below were composed at/);
    assert.deepStrictEqual(core.failures, []);
    fs.rmSync(cwd, { recursive: true, force: true });
  });
}

(async () => {
  for (const [name, fn] of scenarios) {
    await fn();
    console.log(`ok - ${name}`);
  }
  console.log(`governance-pr body job: ${scenarios.length} scenarios passed`);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
