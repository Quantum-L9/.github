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

/** The `on:` block of a workflow, comments stripped. */
function triggers(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^on:\s*$/.test(l));
  assert.ok(start >= 0, 'workflow has a block-style `on:`');
  const out = [];
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line)) break;
    const code = line.replace(/#.*$/, '');
    if (code.trim()) out.push(code);
  }
  return out.join('\n');
}

for (const name of MANUAL_ONLY) {
  const file = path.join(root, '.github/workflows', name);
  assert.ok(fs.existsSync(file), `${name} is paused, not deleted`);
  const on = triggers(fs.readFileSync(file, 'utf8'));
  assert.ok(!/^\s*schedule:/m.test(on), `${name} must have no active schedule`);
  assert.ok(!/cron:/.test(on), `${name} must have no active cron`);
  assert.match(on, /^\s*workflow_dispatch:/m, `${name} stays runnable by hand`);
}
console.log(`ok: ${MANUAL_ONLY.join(', ')} are manual-only (no active schedule, workflow_dispatch kept)`);
