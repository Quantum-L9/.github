'use strict';

/**
 * Asserts the shared label taxonomy parser.
 *
 * Three call sites read `.github/labels.yml` — the weekly org sweep, the
 * per-repo CLI, and the targeted birth bootstrap. They must all see the same
 * taxonomy, which is only true while they all call this one parser.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-label-taxonomy.js
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { parseLabels, parseLabelLines, extractLabelReferences, checkLabelClosure } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

try {
  const labels = parseLabels(fs.readFileSync('.github/labels.yml', 'utf8'));
  assert.ok(labels.length > 0, 'org labels.yml must parse to at least one label');
  for (const l of labels) {
    assert.ok(l.name, 'every label has a name');
    assert.match(l.color, /^[0-9a-fA-F]{6}$/, `label ${l.name} has a 6-hex color`);
    assert.strictEqual(typeof l.description, 'string');
  }

  // GitHub's API needs all three fields; a partial line is skipped, not
  // half-applied.
  assert.deepStrictEqual(parseLabels('  - { name: "a", color: "ff0000" }\n'), []);
  assert.deepStrictEqual(parseLabels('  - { color: "ff0000", description: "d" }\n'), []);

  // Key order is not significant.
  assert.deepStrictEqual(
    parseLabels('  - { description: "d", color: "ff0000", name: "a" }\n'),
    [{ name: 'a', color: 'ff0000', description: 'd' }],
  );

  // Empty descriptions are legal; comments and duplicates are not applied.
  assert.deepStrictEqual(
    parseLabels('# - { name: "x", color: "ff0000", description: "no" }\n'),
    [],
  );
  assert.strictEqual(
    parseLabels(
      '  - { name: "a", color: "ff0000", description: "" }\n' +
      '  - { name: "a", color: "00ff00", description: "dup" }\n',
    ).length,
    1,
    'first definition wins; a duplicate never re-colors a label mid-sweep',
  );

  assert.deepStrictEqual(parseLabels(null), []);
  assert.deepStrictEqual(parseLabels(''), []);

  console.log(`ok: org taxonomy parses (${labels.length} labels, all three fields, hex colors)`);
  console.log('ok: partial, commented, and duplicate label lines are skipped, not half-applied');

  // ── Producer-to-consumer closure (#132) ──────────────────────────────────
  // Every label a consumer names literally must resolve to exactly one
  // taxonomy entry. Consumers: every issue form, the stale workflow, the
  // Dependabot config, the PR labeler config, and every workflow script that
  // writes or filters by a literal label (the advisory report among them).
  const taxonomyText = fs.readFileSync('.github/labels.yml', 'utf8');
  const refs = [];
  const addRefs = (kind, file) => {
    for (const name of extractLabelReferences(kind, fs.readFileSync(file, 'utf8'))) {
      refs.push({ source: `${file} (${kind})`, name });
    }
  };
  const forms = fs.readdirSync('.github/ISSUE_TEMPLATE')
    .filter((f) => /\.ya?ml$/.test(f) && f !== 'config.yml');
  assert.ok(forms.length >= 6, 'issue forms discovered');
  for (const f of forms) addRefs('issue-form', `.github/ISSUE_TEMPLATE/${f}`);
  addRefs('stale', '.github/workflows/stale.yml');
  addRefs('dependabot', '.github/dependabot.yml');
  addRefs('labeler', '.github/labeler.yml');
  for (const f of fs.readdirSync('.github/workflows').filter((w) => /\.ya?ml$/.test(w))) {
    addRefs('workflow-script', `.github/workflows/${f}`);
  }
  const names = new Set(refs.map((r) => r.name));
  // Discovery is not empty by accident: each consumer kind is witnessed.
  for (const expected of ['pinned', 'stale', 'advisory', 'area:ci', 'area:governance', 'needs:triage',
    'area:ci-self', 'area:ops', 'dependencies', 'needs:external']) {
    assert.ok(names.has(expected), `closure discovery missed ${expected}`);
  }
  // The retired synonyms the two unnumbered forms used are no longer referenced.
  for (const retired of ['ci-failure', 'triage', 'governance', 'violation']) {
    assert.ok(!names.has(retired), `retired label ${retired} is still referenced`);
  }
  const closure = checkLabelClosure(taxonomyText, refs);
  assert.deepStrictEqual(closure.missing, [], 'every referenced label is declared in .github/labels.yml');
  assert.deepStrictEqual(closure.duplicated, [], 'every referenced label is declared exactly once');
  assert.ok(closure.ok && closure.resolved === refs.length);

  // #132: `dependencies` (Dependabot's implicit label) and `needs:external`
  // are declared exactly once, and needs:external is never staled.
  const declared = parseLabelLines(taxonomyText).map((l) => l.name);
  for (const name of ['dependencies', 'needs:external']) {
    assert.strictEqual(declared.filter((n) => n === name).length, 1, `${name} declared exactly once`);
  }
  assert.ok(refs.some((r) => r.name === 'dependencies' && /dependabot\.yml \(dependabot\)$/.test(r.source)),
    'dependabot.yml sets no labels, so its implicit dependencies label is a reference');
  const staleExempt = fs.readFileSync('.github/workflows/stale.yml', 'utf8').match(/^\s*exempt-issue-labels:\s*"([^"]*)"/m);
  assert.ok(staleExempt?.[1].split(',').includes('needs:external'), 'needs:external is exempt from stale');
  assert.ok(!/^\s*only-labels:.*needs:external/m.test(fs.readFileSync('.github/workflows/stale.yml', 'utf8')));
  // The pre-#132 taxonomy (neither label) fails this closure, naming both.
  const without = taxonomyText.split('\n')
    .filter((l) => !/name: "(dependencies|needs:external)"/.test(l)).join('\n');
  const before = checkLabelClosure(without, refs);
  assert.strictEqual(before.ok, false);
  assert.deepStrictEqual([...new Set(before.missing.map((m) => m.name))].sort(), ['dependencies', 'needs:external']);

  // Positive witness: a representative reference resolves.
  assert.deepStrictEqual(
    checkLabelClosure(taxonomyText, [{ source: 'witness', name: 'type:bug' }]),
    { ok: true, missing: [], duplicated: [], resolved: 1 },
  );
  // Negative witness: a missing reference is detected and named, not dropped.
  const bad = checkLabelClosure(taxonomyText, [
    { source: 'witness', name: 'type:bug' },
    { source: '.github/ISSUE_TEMPLATE/x.yml', name: 'ci-failure' },
  ]);
  assert.strictEqual(bad.ok, false);
  assert.deepStrictEqual(bad.missing, [{ source: '.github/ISSUE_TEMPLATE/x.yml', name: 'ci-failure' }]);
  // Negative witness: a doubly-declared name is ambiguous, not resolved.
  const dup = checkLabelClosure(`${taxonomyText}\n- { name: "stale", color: "000000", description: "dup" }\n`,
    [{ source: 'witness', name: 'stale' }]);
  assert.strictEqual(dup.ok, false);
  assert.strictEqual(dup.duplicated[0].count, 2);

  // Extractor witnesses on fixtures, so an empty real file is not mistaken
  // for a working extractor (dependabot.yml currently declares no labels).
  assert.deepStrictEqual(
    extractLabelReferences('dependabot', 'updates:\n  - package-ecosystem: pip\n    labels:\n      - "dependencies"\n      - area:ci\n    schedule:\n      interval: weekly\n'),
    ['dependencies', 'area:ci'],
  );
  assert.deepStrictEqual(extractLabelReferences('dependabot', '    labels: ["a", "b"]\n'), ['a', 'b']);
  // Implicit default: an entry without `labels:` applies `dependencies`; an
  // explicit list (empty included) replaces the default.
  assert.deepStrictEqual(
    extractLabelReferences('dependabot', 'updates:\n  - package-ecosystem: github-actions\n    directory: "/"\n    groups:\n      g:\n        patterns: ["*"]\n'),
    ['dependencies'],
  );
  assert.deepStrictEqual(
    extractLabelReferences('dependabot', 'updates:\n  - package-ecosystem: npm\n    labels: [ ]\n'),
    [],
  );
  // Two ecosystems: Dependabot adds an ecosystem label this module cannot
  // name, so an unlabelled entry fails closure instead of passing silently.
  const multi = extractLabelReferences('dependabot',
    'updates:\n  - package-ecosystem: pip\n    directory: /\n  - package-ecosystem: npm\n    labels: ["area:ci"]\n');
  assert.deepStrictEqual(multi.slice(0, 2), ['dependencies', '<dependabot default ecosystem label for pip>']);
  assert.ok(multi.includes('area:ci'));
  assert.strictEqual(checkLabelClosure(taxonomyText, multi.map((name) => ({ source: 'x', name }))).ok, false);
  assert.deepStrictEqual(extractLabelReferences('issue-form', 'name: x\nlabels:\n  - "a"\n  - b\nbody: []\n'), ['a', 'b']);
  assert.deepStrictEqual(extractLabelReferences('labeler', '"area:x":\n  - changed-files: []\n'), ['area:x']);
  assert.deepStrictEqual(
    extractLabelReferences('workflow-script', "labels: [...add] ; labels: 'a,b' ; labels: ['c'] ; add.add('d')"),
    ['a', 'b', 'c', 'd'],
  );
  assert.throws(() => extractLabelReferences('nope', ''), /unknown label consumer kind/);

  console.log(`ok: label closure — ${refs.length} literal references across forms, stale, dependabot, labeler and workflow scripts resolve to exactly one taxonomy entry`);
  console.log('ok: closure witnesses — a missing reference and a duplicated declaration are detected; a valid reference resolves');
} finally {
  process.chdir(origCwd);
}
