'use strict';

/**
 * Contract of the canonical PR template, .github/pull_request_template.md.
 *
 * The template is the one source every governed PR body is composed from
 * (Cursor-Governance ops/scripts/compose_pr_body.py resolves it at an exact
 * commit of this repository). Composers already pinned in consumers read it
 * too, so its machine contract is fixed text, not style:
 *
 * - the L9_PROTECTED_ROOT_PR stamp is the first line;
 * - the changed-file inventory leads, Protected-root disclosures close;
 * - each machine-owned region is declared exactly once, START before END;
 * - no placeholder the composer cannot honestly complete (a bare `Closes #`,
 *   sample paths, sample evidence commands);
 * - the comments older composers replace verbatim are byte-identical.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-pr-template.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const template = fs.readFileSync(path.join(root, '.github/pull_request_template.md'), 'utf8');

const ORDER = [
  'Files touched',
  'Changes by intent',
  'Problem',
  'Type of Change',
  'Fix',
  'Risk',
  'Evidence',
  'Gates',
  'Semantic change',
  'Reviewer focus',
  'Protected-root',
];
const REGIONS = ['FILES-TOUCHED', 'CHANGES-BY-INTENT', 'EVIDENCE', 'PROTECTED-ROOT-PATHS'];
// Replaced verbatim by every composer revision since 47ffe6f; changing one
// silently stops older pinned composers from filling that field.
const FILL_COMMENTS = [
  '<!-- What you changed to make the problem above go away. Note alternatives you rejected and why. -->',
  '<!-- Where to look hardest. Trade-offs accepted. Deferred follow-ups, with issue links. -->',
  '<!-- What cannot be done in a non-root path. Composer fills. -->',
  '<!-- Issue, failing gate, or law citation. Empty if every path is append-only. -->',
  '```\npaste the error / failing output here, or delete this block and describe the gap\n```',
];

let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (e) {
    failures += 1;
    console.log(`not ok - ${name}\n  ${e.message.split('\n').join('\n  ')}`);
  }
}

/** Visible text: HTML comments removed, so a hint inside one is not content. */
const visible = template.replace(/<!--[\s\S]*?-->/g, '');

check('the protected-root stamp is the first line', () => {
  assert.strictEqual(template.split('\n')[0], '<!-- L9_PROTECTED_ROOT_PR -->');
});

check('sections follow the canonical order, inventory first', () => {
  const headings = [...template.matchAll(/^## (.+?)\s*$/gm)].map((m) => m[1]);
  assert.deepStrictEqual(headings, ORDER);
});

check('every machine-owned region is declared exactly once, START before END', () => {
  for (const name of REGIONS) {
    const start = `<!-- ${name}:START -->`;
    const end = `<!-- ${name}:END -->`;
    assert.strictEqual(template.split(start).length - 1, 1, `${start} count`);
    assert.strictEqual(template.split(end).length - 1, 1, `${end} count`);
    assert.ok(template.indexOf(start) < template.indexOf(end), `${name} order`);
  }
});

check('each region sits under its own section', () => {
  const owner = {
    'FILES-TOUCHED': 'Files touched',
    'CHANGES-BY-INTENT': 'Changes by intent',
    EVIDENCE: 'Evidence',
    'PROTECTED-ROOT-PATHS': 'Protected-root',
  };
  for (const [name, heading] of Object.entries(owner)) {
    const at = template.indexOf(`<!-- ${name}:START -->`);
    const before = [...template.slice(0, at).matchAll(/^## (.+?)\s*$/gm)].map((m) => m[1]);
    assert.strictEqual(before[before.length - 1], heading, name);
  }
});

check('no placeholder the composer cannot honestly complete', () => {
  assert.doesNotMatch(visible, /Closes #(?!\d)/, 'bare "Closes #" renders dangling with no issue');
  assert.doesNotMatch(template, /path\/to\//, 'sample paths read as changed files');
  assert.doesNotMatch(template, /^\$ (pytest|ruff)/m, 'a sample command reads as evidence');
});

check('fill comments older composers replace are byte-identical', () => {
  for (const comment of FILL_COMMENTS) assert.ok(template.includes(comment), comment.slice(0, 60));
});

if (failures) {
  console.log(`pr template: ${failures} check(s) failed`);
  process.exit(1);
}
console.log('pr template: all checks passed');
