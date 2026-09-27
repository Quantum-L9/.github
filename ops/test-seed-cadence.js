'use strict';

/**
 * Seeding is manual-only while it is under development.
 *
 * There must be no hourly seed: auto-seed-new-repo.yml and continuous-sync.yml
 * (the weekly drift re-seed) keep their schedules commented out, and both stay
 * runnable by hand through workflow_dispatch. The workflows are paused, not
 * deleted. Resuming a schedule is a reviewed change to this test.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-cadence.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const MANUAL_ONLY = ['auto-seed-new-repo.yml', 'continuous-sync.yml'];

/** The trimmed lines of a workflow's `on:` block, comments stripped. */
function triggers(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => l.trimEnd() === 'on:');
  assert.ok(start >= 0, 'workflow has a block-style `on:`');
  const out = [];
  for (const line of lines.slice(start + 1)) {
    if (line !== '' && line[0] !== ' ' && line[0] !== '\t') break;
    const hash = line.indexOf('#');
    const code = hash === -1 ? line : line.slice(0, hash);
    if (code.trim()) out.push(code);
  }
  return out.map((l) => l.trim());
}

for (const name of MANUAL_ONLY) {
  const file = path.join(root, '.github/workflows', name);
  assert.ok(fs.existsSync(file), `${name} is paused, not deleted`);
  const on = triggers(fs.readFileSync(file, 'utf8'));
  assert.ok(!on.some((l) => l.startsWith('schedule:')), `${name} must have no active schedule`);
  assert.ok(!on.some((l) => l.includes('cron:')), `${name} must have no active cron`);
  assert.ok(
    on.some((l) => l.startsWith('workflow_dispatch:')),
    `${name} stays runnable by hand`,
  );
}
console.log(
  `ok: ${MANUAL_ONLY.join(', ')} are manual-only (no active schedule, workflow_dispatch kept)`,
);
