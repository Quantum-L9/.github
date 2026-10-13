'use strict';

/**
 * Trigger and credential contract of the two manual distribution workflows.
 *
 * continuous-sync.yml (Manual Update) is manual only: no schedule, no push,
 * no other event may start it, and its dispatch defaults to Preview.
 * seed-governance.yml stays a dispatch with its dry-run / seed modes.
 * Both run in the governance-distribution environment, which is where their
 * credentials live (CANONICAL_LAW §14); Manual Update's token step failed with
 * "Input required and not supplied: app-id" on every run while it did not.
 *
 * Read literally, without a YAML dependency, like workflow-script-harness.js:
 * the assertion is about the text the runner reads.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-distribution-triggers.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

/** Lines of the top-level `on:` block, comments and blanks dropped. */
function onBlock(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^on:\s*(#.*)?$/.test(l));
  assert.ok(start !== -1, 'no top-level "on:" block');
  const block = [];
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line) && !line.startsWith('#')) break;
    if (line.trim() === '' || line.trim().startsWith('#')) continue;
    block.push(line);
  }
  return block;
}

/** Event names directly under `on:` (two-space indent). */
const events = (block) => block.flatMap((l) => {
  const m = l.match(/^ {2}([A-Za-z_]+):/);
  return m ? [m[1]] : [];
});

/** The indented body of a dispatch input, e.g. `dry_run:` or `mode:`. */
function input(block, name) {
  const i = block.findIndex((l) => new RegExp(String.raw`^ {6}${name}:\s*$`).test(l));
  assert.ok(i !== -1, `no workflow_dispatch input "${name}"`);
  const body = [];
  for (const l of block.slice(i + 1)) {
    if (l.match(/^\s*/)[0].length <= 6) break;
    body.push(l.trim());
  }
  return body;
}

const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');

// ── continuous-sync.yml: manual only, Preview by default ────────────────────
{
  const label = 'continuous-sync.yml';
  const text = read('.github/workflows/continuous-sync.yml');
  const block = onBlock(text);

  assert.deepStrictEqual(events(block), ['workflow_dispatch'], `${label}: workflow_dispatch must be the only trigger`);
  for (const forbidden of ['schedule', 'push', 'cron', 'pull_request', 'workflow_run', 'repository_dispatch', 'workflow_call']) {
    assert.ok(!block.some((l) => new RegExp(String.raw`^\s*-?\s*${forbidden}:`).test(l)), `${label}: automatic trigger "${forbidden}" present`);
  }
  console.log(`ok: ${label} — workflow_dispatch is the only trigger (no schedule, no push)`);

  const dry = input(block, 'dry_run');
  assert.ok(dry.includes('type: boolean'), `${label}: dry_run must be a boolean`);
  assert.ok(dry.includes('default: true'), `${label}: dispatch must default to Preview`);
  assert.ok(input(block, 'repo_filter').includes('type: string'));
  // Only an explicit false reaches Apply; no fallback may default to writing.
  assert.ok(text.split('\n').some((l) => l.trim() === 'DRY_RUN: ${{ inputs.dry_run }}'), `${label}: DRY_RUN must come from the input alone`);
  assert.doesNotMatch(text, /DRY_RUN:.*\|\|/, `${label}: DRY_RUN must not carry a fallback`);
  assert.match(text, /const DRY = process\.env\.DRY_RUN !== 'false';/, `${label}: Preview unless DRY_RUN is exactly "false"`);
  console.log(`ok: ${label} — Preview is the default and the fail-closed state; Apply needs dry_run=false`);

  assert.match(text, /^ {4}environment: governance-distribution\s*$/m, `${label}: job must run in governance-distribution`);
  assert.match(text, /app-id: \$\{\{ vars\.GOVERNANCE_APP_ID \}\}/);
  assert.match(text, /private-key: \$\{\{ secrets\.GOVERNANCE_APP_PRIVATE_KEY \}\}/);
  // Branch provenance is checked against the App's own bot identity.
  assert.match(text, /APP_SLUG: \$\{\{ steps\.token\.outputs\.app-slug \}\}/);
  assert.match(text, /github-token: \$\{\{ steps\.token\.outputs\.token \}\}/);
  assert.doesNotMatch(text, /secrets\.GH_TOKEN/, `${label}: credential must stay the governance App`);
  console.log(`ok: ${label} — governance App credential read inside governance-distribution; provenance identity unchanged`);

  assert.match(text, /^ {2}group: continuous-sync\s*$/m, `${label}: single fleet writer`);
  assert.match(text, /^ {2}cancel-in-progress: false\s*$/m);
  assert.match(text, /^permissions:\n {2}contents: read\s*$/m, `${label}: GITHUB_TOKEN stays read-only`);
  console.log(`ok: ${label} — one writer at a time; workflow token read-only`);
}

// ── seed-governance.yml: dispatch with dry-run and seed modes ───────────────
{
  const label = 'seed-governance.yml';
  const text = read('.github/workflows/seed-governance.yml');
  const block = onBlock(text);

  assert.deepStrictEqual(events(block), ['workflow_dispatch'], `${label}: workflow_dispatch must be the only trigger`);
  const mode = input(block, 'mode');
  assert.ok(mode.includes('type: choice'));
  assert.ok(mode.includes('options: [dry-run, seed]'), `${label}: modes must be dry-run and seed`);
  assert.ok(mode.includes('default: dry-run'), `${label}: dispatch must default to dry-run`);
  assert.match(text, /^ {4}environment: governance-distribution\s*$/m);
  assert.match(text, /SEED_MODE: \$\{\{ inputs\.mode \}\}/);
  console.log(`ok: ${label} — dispatch only; dry-run (default) and seed modes; governance-distribution`);
}

console.log('\nall distribution trigger scenarios passed');
