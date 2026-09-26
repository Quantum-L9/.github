'use strict';

/**
 * Check a PR body against the org PR-body contract before opening the PR.
 *
 * Runs the REAL `script:` body of .github/workflows/governance-pr.yml — the
 * check every seeded repository runs through its governance.yml caller — so
 * there is no second copy of the rules to drift. Strict mode, so every
 * finding is a failure.
 *
 * Usage:
 *   node ops/check-pr-body.js path/to/body.md
 *   gh pr view 12 --json body -q .body | node ops/check-pr-body.js -
 * Exit 0 = passes, 1 = fails (findings printed), 2 = usage error.
 */

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { extractScript } = require('./workflow-script-harness.js');

const ROOT = path.resolve(__dirname, '..');
const CONTRACT_WORKFLOW = path.join(ROOT, '.github/workflows/governance-pr.yml');

const ACCEPTED_FORMS = [
  'Problem: the error or gap in your own words (30+ characters), not the placeholder block.',
  'Risk: tick exactly one of Low / Medium / High.',
  'Evidence: pasted command output in a ``` block, or a link to an actions/runs/<id> run — not the placeholder block.',
  'Gates: tick the box, or leave it unchecked with a reason after a separator:',
  '  - [ ] Regression test added that fails without this fix — n/a: docs-only change',
];

/**
 * Load a workflow's github-script body as a function. `${{ inputs.strict }}`
 * is the only expression the contract script interpolates; it is bound here.
 * @param {string} workflowFile
 * @param {{strict?: boolean}} [opts]
 */
function loadGate(workflowFile, { strict = true } = {}) {
  const body = extractScript(workflowFile).replace(/\$\{\{\s*inputs\.strict\s*\}\}/g, String(strict));
  if (/\$\{\{/.test(body)) {
    throw new Error(`${workflowFile}: unsupported \${{ }} expression in script`);
  }
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pr-body-gate-'));
  const mod = path.join(dir, 'gate.js');
  fs.writeFileSync(mod, `'use strict';\nmodule.exports = async (core, context) => {\n${body}\n};\n`);
  try {
    return require(mod);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/**
 * Run a gate script against a PR body.
 * @param {string} workflowFile
 * @param {string} prBody
 * @param {{strict?: boolean}} [opts]
 * @returns {Promise<{findings: string[], failed: boolean}>}
 */
async function runGate(workflowFile, prBody, opts = {}) {
  const gate = loadGate(workflowFile, opts);
  const findings = [];
  let failed = false;
  const summary = {
    addHeading: () => summary,
    addList: (items) => {
      findings.push(...items);
      return summary;
    },
    addRaw: () => summary,
    write: async () => summary,
  };
  const core = {
    summary,
    notice() {},
    info() {},
    setFailed: () => {
      failed = true;
    },
  };
  const context = { payload: { pull_request: { body: prBody, draft: false, user: { login: 'someone' } } } };
  await gate(core, context);
  return { findings, failed };
}

async function main(argv) {
  const [arg] = argv;
  if (!arg) {
    process.stderr.write('usage: node ops/check-pr-body.js <body.md | ->\n');
    return 2;
  }
  const prBody = arg === '-' ? fs.readFileSync(0, 'utf8') : fs.readFileSync(arg, 'utf8');
  const { findings, failed } = await runGate(CONTRACT_WORKFLOW, prBody);
  if (!failed) {
    process.stdout.write('PASS: PR body meets the org PR-body contract\n');
    return 0;
  }
  process.stdout.write(`FAIL: ${findings.length} finding(s)\n`);
  for (const f of findings) process.stdout.write(`  - ${f}\n`);
  process.stdout.write('\nAccepted form:\n');
  for (const line of ACCEPTED_FORMS) process.stdout.write(`  ${line}\n`);
  return 1;
}

if (require.main === module) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (err) => {
      process.stderr.write(`check-pr-body: ${err.message}\n`);
      process.exit(2);
    },
  );
}

module.exports = { CONTRACT_WORKFLOW, ACCEPTED_FORMS, loadGate, runGate };
