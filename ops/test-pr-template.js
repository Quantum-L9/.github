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
    console.log(`not ok - ${name}\n  ${e.message.replaceAll('\n', '\n  ')}`);
  }
}

/** `## ` headings in order, by line — no regex, so no backtracking. */
function headingsOf(text) {
  return text
    .split('\n')
    .filter((line) => line.startsWith('## '))
    .map((line) => line.slice(3).trim());
}

check('the protected-root stamp is the first line', () => {
  assert.strictEqual(template.split('\n')[0], '<!-- L9_PROTECTED_ROOT_PR -->');
});

check('sections follow the canonical order, inventory first', () => {
  assert.deepStrictEqual(headingsOf(template), ORDER);
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
    assert.strictEqual(headingsOf(template.slice(0, at)).at(-1), heading, name);
  }
});

check('no placeholder the composer cannot honestly complete', () => {
  // Anywhere in the file, comments included: GitHub may read a closing
  // keyword wherever it appears, and with no issue it renders dangling.
  assert.doesNotMatch(template, /Closes #(?!\d)/, 'bare "Closes #" renders dangling with no issue');
  assert.doesNotMatch(template, /path\/to\//, 'sample paths read as changed files');
  assert.doesNotMatch(template, /^\$ (pytest|ruff)/m, 'a sample command reads as evidence');
});

check('fill comments older composers replace are byte-identical', () => {
  for (const comment of FILL_COMMENTS) assert.ok(template.includes(comment), comment.slice(0, 60));
});

/** 1-based line of a character offset, for a message a person can act on. */
function lineOf(offset) {
  return template.slice(0, offset).split('\n').length;
}

check('HTML comments never nest and every delimiter is balanced', () => {
  // A `<!--` written inside an open comment opens nothing: the next `-->`
  // closes the OUTER comment early and the rest of its text renders as PR
  // body. The explanatory comment at the top used to spell the region
  // markers out literally, so GitHub rendered half of it. Scan the
  // delimiters in order; the real machine markers must each be a comment of
  // their own, opened and closed at top level. HTML closes a comment on
  // "--!>" as well as "-->" (CodeQL js/bad-tag-filter), so both count.
  let open = -1;
  for (const match of template.matchAll(/<!--|--!?>/g)) {
    if (match[0] === '<!--') {
      assert.strictEqual(
        open,
        -1,
        `"<!--" on line ${lineOf(match.index)} is inside the comment opened on line ${lineOf(open)}`,
      );
      open = match.index;
    } else {
      assert.notStrictEqual(open, -1, `"-->" on line ${lineOf(match.index)} closes nothing`);
      open = -1;
    }
  }
  assert.strictEqual(open, -1, `the comment opened on line ${lineOf(open)} is never closed`);
  for (const name of REGIONS) {
    for (const marker of [`<!-- ${name}:START -->`, `<!-- ${name}:END -->`]) {
      const lines = template.split('\n').filter((line) => line.trim() === marker);
      assert.strictEqual(lines.length, 1, `${marker} must be exactly one whole line`);
    }
  }
});

if (failures) {
  console.log(`pr template: ${failures} check(s) failed`);
  process.exit(1);
}
console.log('pr template: all checks passed');
