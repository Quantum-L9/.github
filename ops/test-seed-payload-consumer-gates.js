'use strict';

/**
 * Asserts the seed payload is clean against the gates a consumer applies to
 * the files the seeder writes into it.
 *
 * The seeder copies these files verbatim into consumer repositories, where
 * they become that repository's own tracked source. Consumer no-stub gates
 * (e.g. l9-constellation-topology scripts/validate_release_readiness.py
 * MARKER_RE) scan `.github/` and read the bare word `placeholder` as
 * unfinished work, so a seeded Issue Form `placeholder:` attribute failed that
 * repository's validate job on the org seed PR
 * (Quantum-L9/l9-constellation-topology#38: 7 blocking unfinished_marker
 * findings). Example text belongs in `description:`, which renders the same
 * guidance and carries no marker.
 *
 * Also pinned here, from the codex review of that seed PR:
 * - the incident form must not hard-code a priority label. issue-triage.yml
 *   derives `priority:P0..P3` from the Severity dropdown; a static
 *   `priority:P0` survived every S2/S3 report and contradicted the derived one.
 * - the governance-violation form must let a reporter name the repository the
 *   issue is filed in. The form is seeded into many repositories, so the
 *   choice is generic rather than a fixed name.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-seed-payload-consumer-gates.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { buildSeedPayload, ALL_CATEGORIES, RETIRED_CATEGORIES } = require('./build-seed-payload.js');
const { shapeFromRoot } = require('./render-dependabot.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

// The consumer no-stub marker pattern, kept equal to the strictest known
// consumer gate (l9-constellation-topology scripts/validate_release_readiness.py
// MARKER_RE). A seeded file that matches it fails that consumer's validate.
const CONSUMER_MARKER_RE = /\b(?:TODO|FIXME|XXX|HACK|placeholder|stub|scaffold)\b|not\s+implemented/i;

let failures = 0;
function check(name, fn) {
  try {
    fn();
    console.log(`  ok   ${name}`);
  } catch (err) {
    failures += 1;
    console.log(`  FAIL ${name}\n       ${err.message.replaceAll('\n', '\n       ')}`);
  }
}

try {
  const categories = ALL_CATEGORIES.filter((c) => !RETIRED_CATEGORIES.includes(c));
  const payload = buildSeedPayload({
    fs,
    categories,
    repository: 'Quantum-L9/example-consumer',
    repoShape: shapeFromRoot({ names: [] }),
  });
  const dests = Object.keys(payload).sort((a, b) => a.localeCompare(b));

  check('the full seed payload is non-empty and includes the issue forms', () => {
    assert.ok(dests.length > 0, 'seed payload is empty');
    for (const f of ['3-task.yml', '4-incident.yml', 'ci-failure.yml', 'gov-violation.yml']) {
      assert.ok(dests.includes(`.github/ISSUE_TEMPLATE/${f}`), `seed payload lacks .github/ISSUE_TEMPLATE/${f}`);
    }
  });

  check('no seeded file carries a consumer no-stub marker', () => {
    const hits = [];
    for (const dest of dests) {
      payload[dest].split('\n').forEach((line, i) => {
        if (CONSUMER_MARKER_RE.test(line)) hits.push(`${dest}:${i + 1}: ${line.trim()}`);
      });
    }
    assert.deepStrictEqual(hits, [], `seeded files match the consumer no-stub pattern:\n${hits.join('\n')}`);
  });

  const incident = payload['.github/ISSUE_TEMPLATE/4-incident.yml'];
  check('the incident form hard-codes no priority label', () => {
    const labels = incident.match(/^labels:\s*\[(.*)\]\s*$/m);
    assert.ok(labels, '4-incident.yml has no single-line labels: [...] list');
    const names = labels[1].split(',').map((s) => s.trim().replace(/^["']|["']$/g, ''));
    assert.ok(names.includes('type:incident'), 'incident form lost type:incident');
    const priorities = names.filter((n) => n.startsWith('priority:'));
    assert.deepStrictEqual(priorities, [], 'priority is derived from Severity by issue-triage.yml');
  });

  check('issue-triage still derives priority from incident Severity', () => {
    const triage = fs.readFileSync('.github/workflows/issue-triage.yml', 'utf8');
    assert.match(triage, /S1: 'P0', S2: 'P1', S3: 'P2', S4: 'P3'/, 'severity -> priority map moved; re-check the incident form');
    assert.ok(
      incident.split('\n').some((line) => line.trim() === 'label: Severity'),
      'incident form lost its Severity dropdown',
    );
  });

  check('the governance-violation form offers the repository it is filed in', () => {
    const gov = payload['.github/ISSUE_TEMPLATE/gov-violation.yml'];
    const block = gov.match(/id: affected-repos[\s\S]*?options:\n((?:\s+- .*\n)+)/);
    assert.ok(block, 'gov-violation.yml has no affected-repos options list');
    const options = block[1].split('\n').map((s) => s.replace(/^\s+- /, '').trim()).filter(Boolean);
    assert.ok(
      options.some((o) => /^This repository\b/.test(o)),
      `affected-repos has no current-repository choice: ${JSON.stringify(options)}`,
    );
  });
} finally {
  process.chdir(origCwd);
}

if (failures) {
  console.log(`\n${failures} check(s) failed`);
  process.exit(1);
}
console.log('\nseed payload consumer gates: PASS');
