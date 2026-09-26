'use strict';

/**
 * The org PR-body contract, proven against the real checks.
 *
 * Every repository seeded from Quantum-L9/.github gets
 * templates/pr-templates/pull_request_template.md and a governance.yml caller
 * that runs .github/workflows/governance-pr.yml. This repository's own
 * pr-gates.yml runs the same check strictly. This suite asserts:
 *   - pr-gates.yml delegates to governance-pr.yml (one contract, no copy)
 *   - an untouched template fails Problem AND Evidence (placeholders are not
 *     content)
 *   - a filled template passes
 *   - an unchecked gate needs a written reason: honest multi-word reasons
 *     pass, bare separators / "n/a" / short noise fail
 *   - the template's instructions name the real check and a passing example
 *   - the org-default copy is byte-identical to the seeded template
 *
 * Run from the repo root: node ops/test-pr-body-contract.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { CONTRACT_WORKFLOW, runGate } = require('./check-pr-body.js');

const root = path.resolve(__dirname, '..');
const read = (p) => fs.readFileSync(path.join(root, p), 'utf8');
const TEMPLATE = 'templates/pr-templates/pull_request_template.md';
const template = read(TEMPLATE);

const GATE_LINES = [
  'Regression test added that fails without this fix',
  'No secrets, tokens, or customer data in code, tests, fixtures, or logs',
  '`semgrep` clean, or findings triaged below',
  'New IAM / workflow permissions are least privilege and enumerated',
  'Third-party actions pinned to a full commit SHA',
  'Public interface change is documented and versioned',
  'Observability exists for the new path (metric, log, trace, or alert)',
];

function filled({ gates } = {}) {
  const gateBlock =
    gates ||
    [
      `- [x] ${GATE_LINES[0]}`,
      `- [x] ${GATE_LINES[1]}`,
      `- [ ] ${GATE_LINES[2]} — n/a: not run locally, CI scans every push`,
      `- [ ] ${GATE_LINES[3]} — n/a — no workflow or token permission changes`,
      `- [ ] ${GATE_LINES[4]} — unchanged: no new actions`,
      `- [ ] ${GATE_LINES[5]} — n/a — no API change`,
      `- [ ] ${GATE_LINES[6]} — n/a — not this change`,
    ].join('\n');
  return [
    '## Problem',
    '',
    'Seeded repositories kept an outdated PR template forever because seeding is missing-only.',
    '',
    '## Fix',
    '',
    'Seed PRs replace a stale template.',
    '',
    '## Risk',
    '',
    '- [ ] Low — additive, reversible, no data or contract change',
    '- [x] Medium — touches shared code, config, or a public interface',
    '- [ ] High — breaking change, migration, IAM/network, or irreversible',
    '',
    '## Evidence',
    '',
    '```',
    '$ bash ops/validate-starters.sh',
    'Results: 40 passed, 0 failed',
    '```',
    '',
    '## Gates',
    '',
    gateBlock,
    '',
    '## Reviewer focus',
    '',
    'The write-mode change.',
  ].join('\n');
}

const withGate = (line) =>
  filled({ gates: [`- [x] ${GATE_LINES[0]}`, `- [x] ${GATE_LINES[1]}`, line].join('\n') });

(async () => {
  // ── one contract: pr-gates.yml delegates, it does not copy ──────────────
  const prGates = read('.github/workflows/pr-gates.yml');
  assert.match(prGates, /uses:\s*\.\/\.github\/workflows\/governance-pr\.yml/, 'pr-gates.yml calls governance-pr.yml');
  assert.match(prGates, /strict:\s*true/, 'this repository runs the contract strictly');
  assert.ok(!/script:\s*\|/.test(prGates), 'pr-gates.yml carries no second copy of the rules');
  console.log('ok: pr-gates.yml delegates to governance-pr.yml (one contract)');

  const check = (body) => runGate(CONTRACT_WORKFLOW, body);

  // ── placeholders are not content ────────────────────────────────────────
  const untouched = await check(template);
  assert.ok(untouched.failed, 'the untouched template fails');
  assert.ok(untouched.findings.some((f) => /\*\*Problem\*\*/.test(f)), `Problem placeholder must fail: ${untouched.findings}`);
  assert.ok(untouched.findings.some((f) => /\*\*Evidence\*\*/.test(f)), `Evidence placeholder must fail: ${untouched.findings}`);
  assert.ok(untouched.findings.some((f) => /\*\*Risk\*\*/.test(f)), 'no risk ticked fails');
  console.log('ok: an untouched template fails Problem, Risk, and Evidence');

  const ok = await check(filled());
  assert.deepStrictEqual(ok.findings, [], `a filled body passes: ${ok.findings}`);
  assert.strictEqual(ok.failed, false);
  console.log('ok: a filled body passes');

  // ── a written reason, not a token shape ─────────────────────────────────
  const pass = [
    `- [ ] ${GATE_LINES[2]} — n/a — no API change`,
    `- [ ] ${GATE_LINES[2]} — n/a — not this change`,
    `- [ ] ${GATE_LINES[2]} — unchanged: no workflow edits`,
    `- [ ] ${GATE_LINES[2]} — n/a: docs only`,
    `- [ ] ${GATE_LINES[2]} -- not run in CI`,
    `- [ ] ${GATE_LINES[2]}: not applicable, no code`,
    `- [ ] ${GATE_LINES[2]} (n/a — seed-only change)`,
  ];
  for (const line of pass) {
    const r = await check(withGate(line));
    assert.deepStrictEqual(r.findings, [], `must pass: ${line} → ${r.findings}`);
  }
  const fail = [
    `- [ ] ${GATE_LINES[2]}`,
    `- [ ] ${GATE_LINES[2]} — n/a`,
    `- [ ] ${GATE_LINES[2]} — n/a —`,
    `- [ ] ${GATE_LINES[2]} —`,
    `- [ ] ${GATE_LINES[2]} -- x`,
    `- [ ] ${GATE_LINES[2]}: ok`,
    `- [ ] ${GATE_LINES[2]} — not applicable`,
  ];
  for (const line of fail) {
    const r = await check(withGate(line));
    assert.ok(r.failed, `must fail: ${line}`);
    assert.ok(
      r.findings.some((f) => /\*\*Gate\*\*/.test(f) && /— n\/a: <why/.test(f)),
      `failure names the accepted form: ${r.findings}`,
    );
  }
  console.log(`ok: ${pass.length} written reasons pass; ${fail.length} bare or noise reasons fail with the accepted form`);

  // Evidence may be a CI run link instead of pasted output.
  const linked = filled().replace(/```\n\$ bash[\s\S]*?```/, 'https://github.com/Quantum-L9/example/actions/runs/123456');
  assert.deepStrictEqual((await check(linked)).findings, []);
  console.log('ok: a CI run link counts as evidence');

  // ── advisory mode reports without failing ───────────────────────────────
  const advisory = await runGate(CONTRACT_WORKFLOW, template, { strict: false });
  assert.strictEqual(advisory.failed, false, 'advisory mode never fails the job');
  assert.ok(advisory.findings.length > 0, 'advisory mode still reports findings');
  console.log('ok: advisory (default consumer) mode reports without failing');

  // ── the template tells the truth about its check ────────────────────────
  assert.strictEqual(read('.github/pull_request_template.md'), template, 'org-default copy is byte-identical to the seeded template');
  assert.match(template, /governance-pr\.yml/, 'template names the check that enforces it');
  assert.ok(!/Enforce-PR-Policies/.test(template), 'no reference to a check that does not exist');
  assert.ok(!/see \.github\/workflows\/pr-gates\.yml/.test(template), 'no unqualified pointer to a this-repo-only workflow');
  const example = (template.match(/^\s*-\s*\[ \]\s*.+—\s*n\/a:.+$/m) || [])[0];
  assert.ok(example, 'template shows a passing unchecked-gate example');
  assert.deepStrictEqual((await check(withGate(example.replace(/^\s*/, '')))).findings, [], `template example passes: ${example}`);
  console.log('ok: template names governance-pr.yml, shows a passing example, and matches the org default');

  // ── the CLI agents run locally ──────────────────────────────────────────
  const tmp = fs.mkdtempSync(path.join(require('node:os').tmpdir(), 'pr-body-cli-'));
  fs.writeFileSync(path.join(tmp, 'good.md'), filled());
  const good = spawnSync(process.execPath, [path.join(root, 'ops/check-pr-body.js'), path.join(tmp, 'good.md')], { encoding: 'utf8' });
  assert.strictEqual(good.status, 0, good.stdout + good.stderr);
  const bad = spawnSync(process.execPath, [path.join(root, 'ops/check-pr-body.js'), path.join(root, TEMPLATE)], { encoding: 'utf8' });
  assert.strictEqual(bad.status, 1);
  assert.match(bad.stdout, /Accepted form:/);
  assert.strictEqual(spawnSync(process.execPath, [path.join(root, 'ops/check-pr-body.js')], { encoding: 'utf8' }).status, 2);
  fs.rmSync(tmp, { recursive: true, force: true });
  console.log('ok: node ops/check-pr-body.js exits 0 on pass, 1 with the accepted form on fail, 2 on usage');
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
