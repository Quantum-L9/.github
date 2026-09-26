'use strict';

/**
 * Every workflow that mints the governance App token must run in the
 * environment that holds the App's credentials.
 *
 * GOVERNANCE_APP_ID / GOVERNANCE_APP_PRIVATE_KEY live on this repo's
 * `governance-distribution` environment (CANONICAL_LAW §14). Environment values
 * resolve only for a job that declares the environment, so a job that omits it
 * gets empty values and create-github-app-token fails with "Input required and
 * not supplied: app-id". That silently stopped sync-labels-all, continuous-sync,
 * dispatch-template-update and enforce-policies from ever reaching a
 * repository.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-app-token-environment.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const dir = path.join(root, '.github/workflows');
const ENV = 'governance-distribution';

/** Split a workflow into its jobs: [jobName, jobText]. */
function jobs(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^jobs:\s*$/.test(l));
  if (start < 0) return [];
  const out = [];
  let name = null;
  let buf = [];
  for (const line of lines.slice(start + 1)) {
    const head = line.match(/^ {2}([A-Za-z0-9_-]+):\s*$/);
    if (head) {
      if (name) out.push([name, buf.join('\n')]);
      name = head[1];
      buf = [];
    } else if (/^\S/.test(line)) {
      break;
    } else {
      buf.push(line);
    }
  }
  if (name) out.push([name, buf.join('\n')]);
  return out;
}

const checked = [];
const missing = [];
for (const f of fs.readdirSync(dir).filter((n) => /\.ya?ml$/.test(n))) {
  for (const [job, body] of jobs(fs.readFileSync(path.join(dir, f), 'utf8'))) {
    if (!/\b(vars|secrets)\.GOVERNANCE_APP_/.test(body)) continue;
    checked.push(`${f}:${job}`);
    if (!new RegExp(`^ {4}environment:\\s*["']?${ENV}["']?\\s*$`, 'm').test(body)) {
      missing.push(`${f}:${job}`);
    }
  }
}

assert.ok(checked.length > 0, 'expected at least one job that uses the governance App');
assert.deepStrictEqual(
  missing,
  [],
  `jobs reading GOVERNANCE_APP_* must declare environment: ${ENV}`,
);
console.log(
  `ok: ${checked.length} governance-App jobs all run in environment ${ENV}: ${checked.join(', ')}`,
);
