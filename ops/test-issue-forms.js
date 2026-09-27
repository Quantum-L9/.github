'use strict';

/**
 * Contract for the org issue forms and the workflows that parse them.
 *
 * The forms mirror the PR template: every form opens with a required Problem,
 * evidence-bearing forms carry a required Evidence code block, routing is one
 * required single-select (Severity, or Scope where nothing is broken yet), and
 * every form closes on a required "Done when" — the issue-side twin of the PR
 * template's Gates. issue-triage.yml (this repo) and governance-issue.yml
 * (consumers) derive labels from the rendered `### <label>` headings, so a
 * label rename on either side silently breaks routing. Before this test the
 * triage workflow read `Environment` and `Breaking change?`, which no form
 * had, and the governance form's Severity carried no S1–S4 token at all.
 *
 * Forms are loaded with the system python3 and PyYAML, the same dependency
 * enforce-policies.yml and repo-birth-bootstrap.yml already take on the
 * ubuntu-latest runner. The interpreter is a fixed path, not a PATH lookup, and
 * a missing PyYAML fails with the install command rather than a traceback. The rendered body follows GitHub's issue
 * form output: `### <label>`, a blank line, the answer (`_No response_` when
 * empty; a fenced block when the field sets `render`).
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-issue-forms.js
 */
const assert = require('node:assert');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { loadScriptModule } = require('./workflow-script-harness.js');

const root = path.resolve(__dirname, '..');
const SOURCE = '.github/ISSUE_TEMPLATE';
const MIRRORS = ['ISSUE_TEMPLATE', 'templates/issue-templates'];
const TRIAGE = path.join(root, '.github/workflows/issue-triage.yml');
const GOV_ISSUE = path.join(root, '.github/workflows/governance-issue.yml');

const PYTHON = '/usr/bin/python3';
function loadYaml(file) {
  try {
    return JSON.parse(
      execFileSync(
        PYTHON,
        ['-c', 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))', file],
        { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
      ),
    );
  } catch (e) {
    if (/No module named .?yaml/.test(String(e.stderr))) {
      throw new Error(
        `${PYTHON} lacks PyYAML — install it (python3 -m pip install pyyaml) and re-run`,
      );
    }
    throw e;
  }
}
const ymlIn = (dir) =>
  fs
    .readdirSync(path.join(root, dir))
    .filter((n) => n.endsWith('.yml'))
    .sort((a, b) => a.localeCompare(b));

// ── 1. One source, two byte-identical mirrors ───────────────────────────────
const names = ymlIn(SOURCE);
for (const dir of MIRRORS) {
  assert.deepStrictEqual(ymlIn(dir), names, `${dir} carries a different set of forms`);
  for (const n of names) {
    assert.strictEqual(
      fs.readFileSync(path.join(root, dir, n), 'utf8'),
      fs.readFileSync(path.join(root, SOURCE, n), 'utf8'),
      `${dir}/${n} drifted from ${SOURCE}/${n}`,
    );
  }
}
console.log(`ok: ${names.length} files in ${SOURCE} are mirrored byte-identically`);

// ── 2. Every form has the PR-template shape ─────────────────────────────────
const EVIDENCE_FORMS = new Set([
  '1-bug.yml',
  '4-incident.yml',
  'ci-failure.yml',
  'seed-ci-failure.yml',
  'gov-violation.yml',
]);
const forms = {};
for (const n of names.filter((f) => f !== 'config.yml')) {
  const form = loadYaml(path.join(root, SOURCE, n));
  forms[n] = form;
  const fields = form.body.filter((el) => el.type !== 'markdown');
  const byId = Object.fromEntries(fields.map((el) => [el.id, el]));
  const required = (el) => el?.validations?.required === true;

  assert.ok(form.name && form.description && form.title, `${n}: name/description/title`);
  assert.strictEqual(new Set(fields.map((el) => el.id)).size, fields.length, `${n}: duplicate id`);
  assert.strictEqual(
    new Set(fields.map((el) => el.attributes.label)).size,
    fields.length,
    `${n}: duplicate label (parsers key on labels)`,
  );

  // Problem first, as in the PR template.
  const firstFree = fields.find((el) => el.type === 'textarea');
  assert.strictEqual(firstFree.id, 'problem', `${n}: first textarea must be Problem`);
  assert.strictEqual(firstFree.attributes.label, 'Problem');
  assert.ok(required(firstFree), `${n}: Problem is required`);

  // Done when closes every form, as Gates closes every PR.
  assert.ok(byId.done && required(byId.done), `${n}: required "Done when"`);
  assert.strictEqual(byId.done.attributes.label, 'Done when');
  assert.ok(byId.related?.attributes.label === 'Related', `${n}: Related link`);

  if (EVIDENCE_FORMS.has(n)) {
    assert.ok(byId.evidence && required(byId.evidence), `${n}: required Evidence`);
    assert.strictEqual(byId.evidence.attributes.label, 'Evidence');
    assert.strictEqual(byId.evidence.attributes.render, 'shell', `${n}: Evidence is a code block`);
  }

  // Exactly one routing input: Severity where something is broken, else Scope.
  const route = byId.severity || byId.scope;
  assert.ok(route && required(route), `${n}: required Severity or Scope`);
  assert.ok(route.type === 'dropdown' && !route.attributes.multiple, `${n}: single-select`);
  if (byId.severity) {
    assert.strictEqual(byId.severity.attributes.label, 'Severity');
    for (const o of byId.severity.attributes.options) {
      assert.match(o, /^S[1-4] — /, `${n}: Severity option "${o}" lacks an S1–S4 token`);
    }
  }

  // A pre-filled value satisfies `required` without the reporter typing anything.
  for (const el of fields.filter(required)) {
    assert.ok(el.attributes.value === undefined, `${n}: required ${el.id} is pre-filled`);
  }

  // Triage derives sev:/priority: from Severity; static ones contradict it.
  for (const l of form.labels) {
    assert.doesNotMatch(l, /^(sev|priority):/, `${n}: static ${l} label`);
  }
}
console.log('ok: every form is Problem-first, closes on Done when, and routes on one field');

// ── 3. Every field a parser reads exists in a form ──────────────────────────
const labelsInForms = new Set(
  Object.values(forms).flatMap((f) =>
    f.body.filter((el) => el.type !== 'markdown').map((el) => el.attributes.label),
  ),
);
const read = (file, fn) => {
  const text = fs.readFileSync(file, 'utf8');
  const out = [];
  for (const line of text.split('\n')) {
    let at = line.indexOf(`${fn}(`);
    while (at !== -1) {
      const close = line.indexOf(')', at);
      const first = line
        .slice(at + fn.length + 1, close)
        .split(',')[0]
        .trim();
      if (first.startsWith("'")) out.push(first.slice(1, -1));
      at = line.indexOf(`${fn}(`, close);
    }
  }
  return out;
};
const parsed = [...read(TRIAGE, 'field'), ...read(GOV_ISSUE, 'f')];
assert.ok(parsed.length >= 8, `expected parser field reads, found ${parsed.length}`);
for (const label of parsed) {
  assert.ok(labelsInForms.has(label), `a parser reads "### ${label}", which no form renders`);
}
console.log(`ok: all ${new Set(parsed).size} fields the parsers read exist in a form`);

// ── 4. The two parsers agree on severity and secrets ────────────────────────
const secretsOf = (file) =>
  fs
    .readFileSync(file, 'utf8')
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('[/'))
    .map((l) => l.slice(0, l.lastIndexOf('/,') + 1));
assert.deepStrictEqual(secretsOf(GOV_ISSUE), secretsOf(TRIAGE), 'secret patterns diverged');
console.log('ok: issue-triage.yml and governance-issue.yml scan for the same secrets');

// ── 5. Rendered forms route to the right labels ─────────────────────────────
function render(form, answers) {
  const out = [];
  for (const el of form.body) {
    if (el.type === 'markdown') continue;
    const a = el.attributes;
    const v = answers[el.id];
    let text;
    if (el.type === 'checkboxes') {
      text = a.options
        .map((o, i) => `- [${(v || []).includes(i) ? 'X' : ' '}] ${o.label}`)
        .join('\n');
    } else if (v === undefined || v === '') {
      text = '_No response_';
    } else if (el.type === 'dropdown') {
      const picks = Array.isArray(v) ? v : [v];
      for (const p of picks)
        assert.ok(a.options.includes(p), `"${p}" is not an option of ${el.id}`);
      text = picks.join(', ');
    } else if (a.render) {
      text = `\`\`\`${a.render}\n${v}\n\`\`\``;
    } else {
      text = v;
    }
    out.push(`### ${a.label}\n\n${text}`);
  }
  return out.join('\n\n');
}

const TRACE = 'Traceback (most recent call last):\n  File "x.py", line 1\nValueError: boom';
function fill(form, overrides = {}) {
  const answers = {};
  for (const el of form.body.filter((e) => e.type !== 'markdown')) {
    if (el.validations?.required !== true) continue;
    if (el.type === 'dropdown') answers[el.id] = el.attributes.options[0];
    else if (el.type === 'checkboxes') answers[el.id] = [0];
    else answers[el.id] = el.id === 'evidence' ? TRACE : `${el.id} answer, specific enough`;
  }
  return { ...answers, ...overrides };
}

const triage = loadScriptModule(TRIAGE, 'issue-triage-');
const govIssue = loadScriptModule(GOV_ISSUE, 'governance-issue-');

async function run(script, body, labels = [], action = 'opened') {
  const added = [];
  const removed = [];
  const comments = [];
  const github = {
    rest: {
      issues: {
        addLabels: async (a) => added.push(...a.labels),
        removeLabel: async (a) => removed.push(a.name),
        createComment: async (a) => comments.push(a.body),
      },
    },
  };
  const failures = [];
  const core = { info() {}, warning() {}, setFailed: (m) => failures.push(m) };
  const context = {
    repo: { owner: 'Quantum-L9', repo: '.github' },
    payload: { action, issue: { number: 7, body, labels: labels.map((name) => ({ name })) } },
  };
  await script(github, core, context, require);
  const sort = (a) => [...a].sort((x, y) => x.localeCompare(y));
  return { added: sort(added), removed: sort(removed), comments, failures };
}

(async () => {
  const bug = forms['1-bug.yml'];
  let r = await run(
    triage,
    render(
      bug,
      fill(bug, {
        severity: 'S2 — major function broken, no workaround',
        environment: 'Production',
        regression: 'v0.8.7',
        version: '4f2a1c9e0d7b3a55c21f0e8d9b6a4c3f2e1d0a9b',
      }),
    ),
  );
  assert.deepStrictEqual(r.added, ['env:prod', 'priority:P1', 'regression', 'sev:S2']);
  assert.deepStrictEqual(r.comments, [], 'a complete bug gets no nudge');
  assert.deepStrictEqual(r.failures, []);
  r = await run(triage, render(bug, fill(bug, { environment: 'CI' })));
  assert.ok(r.added.includes('area:ci') && !r.added.includes('env:prod'), 'CI routes to area:ci');
  console.log(
    'ok: bug Severity/Environment/Last known good route to sev, priority, env, regression',
  );

  const feat = forms['2-feature.yml'];
  r = await run(
    triage,
    render(
      feat,
      fill(feat, {
        scope: 'XL — needs a design doc first',
        breaking: 'Yes — consumers must change something',
      }),
    ),
  );
  assert.deepStrictEqual(r.added, ['breaking', 'scope:XL']);
  assert.match(r.comments.join('\n'), /design doc/);
  r = await run(triage, render(feat, fill(feat)));
  assert.ok(!r.added.includes('breaking'), 'No — additive is not breaking');
  const task = forms['3-task.yml'];
  r = await run(triage, render(task, fill(task, { scope: 'M — a few days, one repo' })));
  assert.deepStrictEqual(r.added, ['scope:M']);
  console.log('ok: feature/task Scope and Breaking change? route to scope:* and breaking');

  // Severity is the only priority input: a re-set severity moves the labels.
  const inc = forms['4-incident.yml'];
  const incBody = render(inc, fill(inc));
  r = await run(
    triage,
    incBody,
    ['type:incident', 'sev:untriaged', 'priority:P0', 'sev:S3'],
    'edited',
  );
  assert.deepStrictEqual(r.added, ['priority:P0', 'sev:S1']);
  assert.deepStrictEqual(r.removed, ['sev:S3', 'sev:untriaged']);
  r = await run(triage, incBody, ['type:incident', 'sev:S1', 'priority:P0'], 'edited');
  assert.deepStrictEqual(r.removed, [], 'a correct severity is left alone');
  console.log('ok: severity drives sev/priority, and a changed severity replaces them');

  for (const n of ['ci-failure.yml', 'seed-ci-failure.yml', 'gov-violation.yml']) {
    const form = forms[n];
    const s1 = form.body
      .find((el) => el.id === 'severity')
      .attributes.options.find((o) => o.startsWith('S1'));
    r = await run(triage, render(form, fill(form, { severity: s1 })));
    assert.ok(r.added.includes('sev:S1') && r.added.includes('priority:P0'), `${n}: S1 → P0`);
    const g = await run(govIssue, render(form, fill(form, { severity: s1 })));
    assert.deepStrictEqual(g.added, ['priority:P0', 'sev:S1'], `${n}: consumer parser agrees`);
  }
  console.log('ok: ci, seed-ci and governance Severity route in both parsers');

  // Evidence nudge: a run URL is evidence; prose is not. Old labels still parse.
  r = await run(triage, render(bug, fill(bug, { evidence: 'it just fails sometimes' })));
  assert.match(r.comments.join('\n'), /\*\*Evidence\*\* field has no traceback/);
  r = await run(
    triage,
    render(bug, fill(bug, { evidence: 'https://github.com/o/r/actions/runs/1' })),
  );
  assert.deepStrictEqual(r.comments, []);
  r = await run(triage, '### Error output\n\nit just fails sometimes\n\n### Severity\n\nS3 — x');
  assert.match(r.comments.join('\n'), /Evidence/, 'a pre-rename body still gets the nudge');
  assert.match(
    (await run(triage, render(bug, fill(bug, { evidence: 'nope' })))).comments.join('\n'),
    /https:\/\/github\.com\/Quantum-L9\/\.github\/blob\/main\/docs\/issue-templates\/EXAMPLE\.md/,
    'the worked-example link is absolute, so it resolves from a consumer repo',
  );
  console.log(
    'ok: Evidence nudge accepts a run URL, reads pre-rename bodies, links an absolute example',
  );

  // Consumers run governance-issue.yml, not issue-triage.yml: every routing
  // label a form advertises must come out of both parsers identically.
  const routing = {
    '1-bug.yml': {
      environment: 'Production',
      regression: 'v1.0.0',
      severity: 'S3 — degraded, workaround exists',
    },
    '2-feature.yml': {
      scope: 'L — multi-repo or migration',
      breaking: 'Yes — consumers must change something',
    },
    '3-task.yml': { scope: 'S — under a day' },
  };
  for (const [n, form] of Object.entries(forms)) {
    const body = render(form, fill(form, routing[n] || {}));
    const labels = ['sev:untriaged', 'priority:P0'];
    const t = await run(triage, body, labels, 'edited');
    const c = await run(govIssue, body, labels, 'edited');
    assert.deepStrictEqual(c.added, t.added, `${n}: consumer labels diverge from triage`);
    assert.deepStrictEqual(c.removed, t.removed, `${n}: consumer label removals diverge`);
  }
  r = await run(govIssue, render(bug, fill(bug, routing['1-bug.yml'])));
  assert.deepStrictEqual(r.added, ['env:prod', 'priority:P2', 'regression', 'sev:S3']);
  console.log(
    'ok: governance-issue.yml (consumers) routes every form exactly like issue-triage.yml',
  );

  const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig';
  r = await run(triage, render(bug, fill(bug, { context: jwt })));
  assert.ok(r.added.includes('security:possible-leak') && r.failures.length === 1);
  const g = await run(govIssue, render(bug, fill(bug, { context: jwt })));
  assert.ok(g.added.includes('security:possible-leak'), 'consumer parser catches a JWT too');
  assert.deepStrictEqual(g.failures, [], 'governance-issue.yml stays advisory');
  console.log('ok: both parsers flag a JWT; only this repo fails the run');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
