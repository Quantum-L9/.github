'use strict';

/**
 * Runs the real `script:` body of labeler.yml's type step against a stubbed
 * GitHub API: this repo dogfoods the taxonomy by giving every PR a type:*
 * label derived from its Conventional Commits title, not only area:*.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-pr-type-label.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { extractScript } = require('./workflow-script-harness.js');
const { parseLabels } = require('./label-taxonomy.js');

const root = path.resolve(__dirname, '..');
const WORKFLOW = path.join(root, '.github/workflows/labeler.yml');

function load() {
  const body = extractScript(WORKFLOW);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pr-type-'));
  const mod = path.join(dir, 'labeler.script.js');
  fs.writeFileSync(
    mod,
    `'use strict';\nmodule.exports = async (github, core, context, require) => {\n${body}\n};\n`,
  );
  try {
    return require(mod);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
const script = load();

async function run(title, labels = []) {
  const calls = [];
  const github = {
    rest: {
      issues: {
        addLabels: async (a) => calls.push(['add', ...a.labels]),
        removeLabel: async (a) => calls.push(['remove', a.name]),
      },
    },
  };
  const core = { info() {} };
  const context = {
    repo: { owner: 'Quantum-L9', repo: '.github' },
    payload: { pull_request: { number: 1, title, labels: labels.map((name) => ({ name })) } },
  };
  await script(github, core, context, require);
  const added = calls.filter((c) => c[0] === 'add').flatMap((c) => c.slice(1));
  const removed = calls.filter((c) => c[0] === 'remove').map((c) => c[1]);
  return { added, removed };
}

(async () => {
  // Every label the step can apply is declared in the taxonomy.
  const declared = new Set(
    parseLabels(fs.readFileSync(path.join(root, '.github/labels.yml'), 'utf8')).map((l) => l.name),
  );
  for (const l of ['type:feature', 'type:bug', 'type:task', 'breaking']) {
    assert.ok(declared.has(l), `${l} must be declared in .github/labels.yml`);
  }

  assert.deepStrictEqual((await run('feat(seed): x')).added, ['type:feature']);
  assert.deepStrictEqual((await run('fix: x')).added, ['type:bug']);
  for (const t of ['chore(deps): bump x', 'ci(seed): x', 'docs: x', 'refactor(y): x', 'test: x']) {
    assert.deepStrictEqual((await run(t)).added, ['type:task'], t);
  }
  assert.deepStrictEqual((await run('feat(birth)!: x')).added, ['type:feature', 'breaking']);
  console.log(
    'ok: feat/fix/other Conventional Commits types map to type:feature/bug/task; ! adds breaking',
  );

  // Title edits move the label; area:* and other labels are never touched.
  const retitled = await run('fix: x', ['type:feature', 'breaking', 'area:ci']);
  assert.deepStrictEqual(retitled.added, ['type:bug']);
  assert.deepStrictEqual(retitled.removed.sort(), ['breaking', 'type:feature']);
  const same = await run('fix: x', ['type:bug', 'area:ci']);
  assert.deepStrictEqual(same, { added: [], removed: [] }, 'already correct: no API writes');
  console.log('ok: a retitle swaps only the labels this step owns; a correct PR is left alone');

  // A non-conventional title changes nothing (no guess, no removal).
  const free = await run('Add root ISSUE_TEMPLATE so org defaults cascade', ['type:task']);
  assert.deepStrictEqual(free, { added: [], removed: [] });
  assert.deepStrictEqual(await run('feature: x'), { added: [], removed: [] });
  console.log('ok: a non-Conventional-Commits title leaves type labels untouched');
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
