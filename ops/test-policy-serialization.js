'use strict';

/**
 * Asserts that the JSON-in-YAML policy files parse to exactly the objects their
 * former block-YAML form produced (dev pack GOV-026 / AC-REG-004).
 *
 * `policies/repo-settings.yml` and `policies/mandatory-files.yml` are read by
 * two stacks: Node, through parseJsonInYaml() with no YAML dependency, and the
 * `yaml.safe_load()` steps in enforce-policies.yml and repo-birth-bootstrap.yml.
 * Both must see the same object, and it must be the object the block-YAML
 * files produced before the conversion — key order included, because the
 * settings merge in both workflows spreads `defaults` then overrides in order.
 *
 * EXPECTED below was captured from the block-YAML files at 77587b7 with
 * PyYAML. A deliberate policy edit updates the policy file and EXPECTED in the
 * same commit; a parse difference with no policy edit is the defect this test
 * exists to catch.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-policy-serialization.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { parseJsonInYaml } = require('./repo-class-profile.js');

const root = path.resolve(__dirname, '..');
const origCwd = process.cwd();
process.chdir(root);

const EXPECTED = {
  'policies/repo-settings.yml': {
    defaults: {
      has_issues: true,
      has_wiki: false,
      has_projects: false,
      allow_squash_merge: true,
      allow_merge_commit: false,
      allow_rebase_merge: false,
      delete_branch_on_merge: true,
      allow_auto_merge: false,
      has_vulnerability_alerts: true,
      default_branch: 'main',
    },
    overrides: [
      { repos: ['Quantum-Website-Cursor', 'quantum-dashboard'], has_wiki: true },
      { repos: ['l9-assurance'], has_projects: true },
      { repos: ['l9-assurance'], allow_merge_commit: true },
    ],
  },
  'policies/mandatory-files.yml': {
    files: [
      { path: '.github/CODEOWNERS', source: 'templates/CODEOWNERS.repo', mode: 'managed' },
      { path: '.github/dependabot.yml', source: 'templates/dependabot.yml', mode: 'managed' },
      { path: 'LICENSE', source: 'templates/community-health/LICENSE', mode: 'seeded' },
      { path: '.github/workflows/governance.yml', source: 'templates/governance-caller.yml', mode: 'seeded' },
      { path: 'README.md', mode: 'present' },
    ],
    exceptions: [
      { repo: '.github', reason: 'This IS the template source' },
      { repo: 'Cursor-Governance', reason: 'Policy SSOT — has its own governance model' },
    ],
  },
};

// deepStrictEqual ignores key order; the settings merge does not.
function assertSameKeyOrder(actual, expected, where) {
  if (Array.isArray(expected)) {
    for (let i = 0; i < expected.length; i++) assertSameKeyOrder(actual[i], expected[i], `${where}[${i}]`);
  } else if (expected && typeof expected === 'object') {
    assert.deepStrictEqual(Object.keys(actual), Object.keys(expected), `key order at ${where}`);
    for (const k of Object.keys(expected)) assertSameKeyOrder(actual[k], expected[k], `${where}.${k}`);
  }
}

// Absolute interpreter paths only: resolving `python3` through PATH would let a
// writable PATH entry substitute the interpreter (Sonar S4036). GitHub-hosted
// runners ship /usr/bin/python3 with PyYAML.
const PYTHON = ['/usr/bin/python3', '/usr/local/bin/python3'].find((p) => fs.existsSync(p));

function pyyamlAvailable() {
  if (!PYTHON) return false;
  const probe = spawnSync(PYTHON, ['-c', 'import yaml'], { encoding: 'utf8' });
  return probe.status === 0;
}

function parseWithPyYaml(file) {
  const out = spawnSync(
    PYTHON,
    ['-c', 'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))))', file],
    { encoding: 'utf8' },
  );
  assert.strictEqual(out.status, 0, `yaml.safe_load failed on ${file}: ${out.stderr}`);
  return JSON.parse(out.stdout);
}

try {
  for (const [file, expected] of Object.entries(EXPECTED)) {
    const text = fs.readFileSync(file, 'utf8');
    const parsed = parseJsonInYaml(text);
    assert.deepStrictEqual(parsed, expected, `${file}: Node parse differs from the baseline object`);
    assertSameKeyOrder(parsed, expected, file);
    console.log(`ok: ${file} — Node parseJsonInYaml matches the baseline object`);
  }

  // The workflows read these files with PyYAML. It is present on GitHub-hosted
  // runners and in both consuming workflows; a local shell without it cannot
  // run this half, and says so rather than passing silently.
  if (pyyamlAvailable()) {
    for (const [file, expected] of Object.entries(EXPECTED)) {
      const parsed = parseWithPyYaml(file);
      assert.deepStrictEqual(parsed, expected, `${file}: yaml.safe_load differs from the baseline object`);
      assertSameKeyOrder(parsed, expected, file);
      console.log(`ok: ${file} — yaml.safe_load matches the baseline object`);
    }
  } else {
    console.log('SKIP: python3 with PyYAML not available — yaml.safe_load parity not checked here');
  }

  // A trailing comment on a value line is not stripped by parseJsonInYaml and
  // would make the file unreadable to Node; the header rule forbids it.
  assert.throws(() => parseJsonInYaml('{ "a": true # note\n}'), /not JSON-in-YAML/);
  console.log('ok: an inline trailing comment is rejected, not silently accepted');
} finally {
  process.chdir(origCwd);
}
