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
 * a re-serialized round trip through a YAML library. `nth` selects among
 * several blocks (0 = first), for a workflow with more than one job script.
 */
function extractScript(file, nth = 0) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const starts = lines.flatMap((l, i) => (/^\s*script:\s*\|\s*$/.test(l) ? [i] : []));
  const start = nth < starts.length ? starts[nth] : -1;
  assert.ok(start !== -1, `no "script: |" block #${nth} in ${file}`);
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
 * @param {number} [nth]     which `script: |` block (0 = first)
 * @returns {(github: object, core: object, context: object, require: Function) => Promise<void>}
 */
function loadScriptModule(file, tmpTag = 'workflow-script-', nth = 0) {
  const body = extractScript(file, nth);
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
  const warnings = [];
  // Summary tables are captured so a suite can read the per-repo verdict rows
  // a workflow reports, not only the API calls it made.
  const tables = [];
  const summary = {
    addHeading: () => summary,
    addRaw: () => summary,
    addTable: (rows) => {
      tables.push(rows);
      return summary;
    },
    write: async () => summary,
  };
  return {
    info() {},
    error() {},
    warning: (m) => warnings.push(m),
    setFailed: (m) => failures.push(m),
    failures,
    warnings,
    tables,
    summary,
  };
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

  return async function run({ dry = false, mutateGithub, envExtra = {}, ...stubOpts } = {}) {
    const prevCwd = process.cwd();
    const env = { ...envFor(dry), ...envExtra };
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
      warnings: core.warnings,
      // Verdict rows of the last summary table, header row dropped.
      rows: core.tables.length ? core.tables[core.tables.length - 1].slice(1) : [],
      mutated: names.some((n) => mutations.has(n)),
    };
  };
}


/**
 * The stub surfaces a branch guard always needs, with identical meaning in
 * every suite: "which PRs are open?" (on the guard branch, and elsewhere),
 * "which files does an open PR change?", and "where does the guard branch
 * point?".
 *
 * Kept here because the SEMANTICS are shared, not merely the text — `getRef`
 * must 404 while the branch is absent and otherwise report the live
 * `state.sha`, which is what lets a test observe whether a run moved the ref.
 * Everything workflow-specific (how a commit is built, how the ref is moved)
 * stays in the suite's own stub.
 *
 * @param {object} o
 * @param {string} o.branch   the guard branch name
 * @param {object} o.state    mutable `{ sha }` the suite also inspects
 * @param {object[]} o.calls  shared call log
 * @param {number[]} o.openPRs  open PR numbers whose head is the guard branch
 * @param {{number: number, ref: string, files?: object[], filesError?: number}[]} [o.otherPRs]
 *   other open PRs; `files` are pulls.listFiles rows, `filesError` an HTTP
 *   status that listing throws
 * @param {number} [o.listError]  HTTP status listing all open PRs throws
 * @param {Function} o.record recorder factory from the suite
 */
function makeBranchStubs({ branch, state, calls, openPRs, otherPRs = [], listError, record }) {
  const httpError = (status) => Object.assign(new Error(`HTTP ${status}`), { status });
  const pulls = {
    list: async (args) => {
      calls.push({ name: 'pulls.list', args });
      const own = openPRs.map((number) => ({
        number,
        head: { ref: branch, repo: { full_name: `${args.owner}/${args.repo}` } },
      }));
      // Filtered by head: the guard-branch probe. Unfiltered: every open PR.
      if (args.head) return { data: own };
      if (listError) throw httpError(listError);
      return {
        data: [...own, ...otherPRs.map((p) => ({
          number: p.number,
          head: { ref: p.ref, repo: { full_name: `${args.owner}/${args.repo}` } },
        }))],
      };
    },
    listFiles: async (args) => {
      calls.push({ name: 'pulls.listFiles', args });
      const pr = otherPRs.find((p) => p.number === args.pull_number);
      if (pr?.filesError) throw httpError(pr.filesError);
      return { data: pr ? pr.files || [] : [] };
    },
    create: record('pulls.create'),
  };
  return {
    pulls,
    // github.paginate over a pulls endpoint returns the endpoint's rows;
    // anything else is the suite's org repository listing.
    paginateWith: (repoRows) => async (fn, args) =>
      (fn === pulls.list || fn === pulls.listFiles ? (await fn(args)).data : repoRows()),
    getRef: async (args) => {
      calls.push({ name: 'git.getRef', args });
      if (args.ref === `heads/${branch}`) {
        if (state.sha === null) throw notFound('Branch not found');
        return { data: { object: { sha: state.sha } } };
      }
      return { data: { object: { sha: 'base-sha' } } };
    },
  };
}

/**
 * Run the `gates` job of governance-pr.yml — the org PR-body validator every
 * consumer PR is judged by — against one body, in strict mode.
 *
 * The job's script interpolates `${{ inputs.strict }}` into its text, which is
 * not JavaScript until Actions expands it; it is expanded here exactly as the
 * runner would for a strict caller.
 *
 * @param {string} root  repo root
 * @returns {(body: string) => Promise<string[]>} the findings; [] = passes
 */
function loadGovernanceGates(root) {
  const file = path.join(root, '.github/workflows/governance-pr.yml');
  // biome-ignore lint/suspicious/noTemplateCurlyInString: the Actions expression, matched literally
  const body = extractScript(file, 0).split('${{ inputs.strict }}').join('true');
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'governance-gates-'));
  const mod = path.join(dir, 'governance-gates.script.js');
  fs.writeFileSync(mod, `'use strict';\nmodule.exports = async (github, core, context, require) => {\n${body}\n};\n`);
  let fn;
  try {
    fn = require(mod);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
  return async (prBody) => {
    const findings = [];
    const failures = [];
    const summary = {
      addHeading: () => summary,
      addList: (items) => { findings.push(...items); return summary; },
      write: async () => summary,
    };
    const core = { setFailed: (m) => failures.push(m), notice() {}, summary };
    await fn({}, core, { payload: { pull_request: { body: prBody } } }, require);
    assert.strictEqual(failures.length > 0, findings.length > 0, 'strict gates fail exactly when they find something');
    return findings;
  };
}

module.exports = {
  extractScript,
  loadScriptModule,
  notFound,
  makeCore,
  makeScopedRequire,
  makeScriptRunner,
  makeBranchStubs,
  loadGovernanceGates,
};
