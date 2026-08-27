'use strict';

/**
 * Shared harness for testing a workflow's `github-script` body directly.
 *
 * Both branch-guard suites (`test-seed-workflow-branch-guard.js`,
 * `test-continuous-sync-branch-guard.js`) prove a negative — that a workflow
 * never clobbers a branch carrying work it did not author — by running the
 * REAL `script:` body from the YAML against a stubbed GitHub API. The stubs
 * differ per workflow (the seeders use createCommit + a GraphQL
 * compare-and-swap; continuous-sync uses REST updateRef + file writes), but
 * the scaffolding to extract, load and drive the script is identical.
 *
 * That scaffolding lives here so the two suites do not carry a second copy of
 * it. Per-workflow stubs stay in their own files, where they are readable
 * next to the assertions they support.
 */
const assert = require('node:assert');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

/**
 * Extract the `script: |` block from a workflow, without a YAML dependency.
 * Deliberately literal: the test must run the same text the runner does, not
 * a re-serialized round trip through a YAML library.
 */
function extractScript(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const start = lines.findIndex((l) => /^\s*script:\s*\|\s*$/.test(l));
  assert.ok(start !== -1, `no "script: |" block in ${file}`);
  const indent = lines[start].match(/^\s*/)[0].length + 2;
  const body = [];
  for (const line of lines.slice(start + 1)) {
    if (line.trim() !== '' && line.match(/^\s*/)[0].length < indent) break;
    body.push(line.slice(indent));
  }
  return body.join('\n');
}

/**
 * Load the extracted body as a real CommonJS module: it is written to a temp
 * file and `require`d, so no string is turned into code in-process (no `eval`
 * / `new Function`) and stack traces point at a real file. The exported
 * function receives the same bindings github-script provides, with `require`
 * shadowed by the scoped resolver the caller passes.
 *
 * @param {string} file      absolute path to the workflow YAML
 * @param {string} [tmpTag]  prefix for the temp dir, for readable failures
 * @returns {(github: object, core: object, context: object, require: Function) => Promise<void>}
 */
function loadScriptModule(file, tmpTag = 'workflow-script-') {
  const body = extractScript(file);
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), tmpTag));
  const mod = path.join(dir, `${path.basename(file, '.yml')}.script.js`);
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

/** An octokit-shaped 404, which the workflows branch on by `.status`. */
const notFound = (msg) => Object.assign(new Error(msg), { status: 404 });

/**
 * Minimal `core` stub. `setFailed` is captured rather than thrown so a test
 * can assert that leaving a branch alone is NOT reported as a failure.
 */
function makeCore() {
  const failures = [];
  const summary = {
    addHeading: () => summary,
    addRaw: () => summary,
    addTable: () => summary,
    write: async () => summary,
  };
  return { info() {}, error() {}, setFailed: (m) => failures.push(m), failures, summary };
}

/**
 * github-script resolves relative `require()` against the workspace root.
 * Mirror that so a script body can pull in ops/ modules the way it does live.
 */
const makeScopedRequire = (root) => (m) =>
  require(m.startsWith('.') ? path.resolve(root, m) : m);


/**
 * Build the `run()` a branch-guard suite drives its workflow with.
 *
 * Owns everything that is identical across suites — loading the script body,
 * pinning cwd to the repo root (the script reads templates by relative path),
 * setting and restoring the workflow's env, and reducing the recorded calls
 * to a verdict. What differs per workflow — the API stub and the set of call
 * names that count as a mutation — is injected.
 *
 * @param {object}   opts
 * @param {string}   opts.file        absolute path to the workflow YAML
 * @param {string}   opts.root        repo root; cwd during the run
 * @param {string}   [opts.tmpTag]    temp-dir prefix, for readable failures
 * @param {(dry: boolean) => Record<string,string>} opts.envFor  workflow env
 * @param {(o: object) => {github: object, calls: object[], state: object}} opts.makeGithub
 * @param {Set<string>} opts.mutations  call names that count as a write
 * @returns {(o?: object) => Promise<{calls, names, state, failures, mutated}>}
 */
function makeScriptRunner({ file, root, tmpTag, envFor, makeGithub, mutations }) {
  const fn = loadScriptModule(file, tmpTag);
  const scopedRequire = makeScopedRequire(root);

  return async function run({ dry = false, mutateGithub, ...stubOpts } = {}) {
    const prevCwd = process.cwd();
    const env = envFor(dry);
    const prevEnv = Object.fromEntries(Object.keys(env).map((k) => [k, process.env[k]]));
    process.chdir(root);
    Object.assign(process.env, env);
    const { github, calls, state } = makeGithub(stubOpts);
    if (mutateGithub) mutateGithub(github, state);
    const core = makeCore();
    try {
      await fn(github, core, {}, scopedRequire);
    } finally {
      process.chdir(prevCwd);
      for (const [k, v] of Object.entries(prevEnv)) {
        if (v === undefined) delete process.env[k];
        else process.env[k] = v;
      }
    }
    const names = calls.map((c) => c.name);
    return {
      calls,
      names,
      state,
      failures: core.failures,
      mutated: names.some((n) => mutations.has(n)),
    };
  };
}

module.exports = {
  extractScript,
  loadScriptModule,
  notFound,
  makeCore,
  makeScopedRequire,
  makeScriptRunner,
};
