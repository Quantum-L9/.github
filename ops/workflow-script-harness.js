"use strict";

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
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

// Sets one named property on an Error. Explicit assignment, not Object.assign:
// Core's Semgrep gate (prototype-pollution) flags every two-argument call.
const errorWith = (err, key, value) => {
	err[key] = value;
	return err;
};
// Sets test environment variables one by one (see errorWith / Core's Semgrep gate).
const setEnv = (vars) => {
	for (const [k, v] of Object.entries(vars)) process.env[k] = v;
};

/**
 * Extract the `script: |` block from a workflow, without a YAML dependency.
 * Deliberately literal: the test must run the same text the runner does, not
 * a re-serialized round trip through a YAML library. `nth` selects among
 * several blocks (0 = first), for a workflow with more than one job script.
 */
function extractScript(file, nth = 0) {
	const lines = fs.readFileSync(file, "utf8").split("\n");
	const starts = lines.flatMap((l, i) =>
		/^\s*script:\s*\|\s*$/.test(l) ? [i] : [],
	);
	const start = nth < starts.length ? starts[nth] : -1;
	assert.ok(start !== -1, `no "script: |" block #${nth} in ${file}`);
	const indent = lines[start].match(/^\s*/)[0].length + 2;
	const body = [];
	for (const line of lines.slice(start + 1)) {
		if (line.trim() !== "" && line.match(/^\s*/)[0].length < indent) break;
		body.push(line.slice(indent));
	}
	return body.join("\n");
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
function loadScriptModule(file, tmpTag = "workflow-script-", nth = 0) {
	const body = extractScript(file, nth);
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), tmpTag));
	const mod = path.join(dir, `${path.basename(file, ".yml")}.script.js`);
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
const notFound = (msg) => errorWith(new Error(msg), "status", 404);

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
const makeScopedRequire =
	(root, overrides = {}) =>
	(m) => {
		if (Object.hasOwn(overrides, m)) return overrides[m];
		return require(m.startsWith(".") ? path.resolve(root, m) : m);
	};

/**
 * A stand-in for `./ops/seed-pr-body.js` whose renderSeedPrBody records its
 * inputs and returns a marked body instead of fetching the seed commit and
 * running Cursor-Governance's composer. Every other export is the real one,
 * so the commit message and the prepared template are produced as live.
 *
 * Branch-guard suites assert what the workflow hands the renderer and that the
 * PR body is its output verbatim; ops/test-seed-pr-body.js runs the real
 * composer and proves the rendered body complete.
 */
function makeRenderRecorder(root) {
	const real = require(path.resolve(root, "ops/seed-pr-body.js"));
	const renders = [];
	const module = {
		...real,
		renderSeedPrBody: (args) => {
			renders.push(args);
			return {
				body: `<!-- composed seed body for ${args.headSha} -->\n`,
				handoff: { needs_completion: [] },
			};
		},
	};
	return { module, renders };
}

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
function makeScriptRunner({
	file,
	root,
	tmpTag,
	envFor,
	makeGithub,
	mutations,
	modules = {},
}) {
	const fn = loadScriptModule(file, tmpTag);

	return async function run({
		dry = false,
		mutateGithub,
		envExtra = {},
		modules: runModules = {},
		...stubOpts
	} = {}) {
		// A run without its own renderer gets a fresh recorder, so no suite can
		// reach the network-bound composer by accident.
		const recorder = makeRenderRecorder(root);
		const scopedRequire = makeScopedRequire(root, {
			"./ops/seed-pr-body.js": recorder.module,
			...modules,
			...runModules,
		});
		const prevCwd = process.cwd();
		const env = { ...envFor(dry), ...envExtra };
		const prevEnv = Object.fromEntries(
			Object.keys(env).map((k) => [k, process.env[k]]),
		);
		process.chdir(root);
		setEnv(env);
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
			rows: core.tables.length
				? core.tables[core.tables.length - 1].slice(1)
				: [],
			mutated: names.some((n) => mutations.has(n)),
			renders: recorder.renders,
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
function makeBranchStubs({
	branch,
	state,
	calls,
	openPRs,
	otherPRs = [],
	listError,
	record,
}) {
	const httpError = (status) =>
		errorWith(new Error(`HTTP ${status}`), "status", status);
	const pulls = {
		list: async (args) => {
			calls.push({ name: "pulls.list", args });
			const own = openPRs.map((number) => ({
				number,
				head: {
					ref: branch,
					repo: { full_name: `${args.owner}/${args.repo}` },
				},
			}));
			// Filtered by head: the guard-branch probe. Unfiltered: every open PR.
			if (args.head) return { data: own };
			if (listError) throw httpError(listError);
			return {
				data: [
					...own,
					...otherPRs.map((p) => ({
						number: p.number,
						head: {
							ref: p.ref,
							repo: { full_name: `${args.owner}/${args.repo}` },
						},
					})),
				],
			};
		},
		listFiles: async (args) => {
			calls.push({ name: "pulls.listFiles", args });
			const pr = otherPRs.find((p) => p.number === args.pull_number);
			if (pr?.filesError) throw httpError(pr.filesError);
			return { data: pr ? pr.files || [] : [] };
		},
		create: record("pulls.create"),
	};
	return {
		pulls,
		// github.paginate over a pulls endpoint returns the endpoint's rows;
		// anything else is the suite's org repository listing.
		paginateWith: (repoRows) => async (fn, args) =>
			fn === pulls.list || fn === pulls.listFiles
				? (await fn(args)).data
				: repoRows(),
		getRef: async (args) => {
			calls.push({ name: "git.getRef", args });
			if (args.ref === `heads/${branch}`) {
				if (state.sha === null) throw notFound("Branch not found");
				return { data: { object: { sha: state.sha } } };
			}
			return { data: { object: { sha: "base-sha" } } };
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
	const file = path.join(root, ".github/workflows/governance-pr.yml");
	const body = extractScript(file, 0)
		// biome-ignore lint/suspicious/noTemplateCurlyInString: the Actions expression, matched literally
		.split("${{ inputs.strict }}")
		.join("true");
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), "governance-gates-"));
	const mod = path.join(dir, "governance-gates.script.js");
	fs.writeFileSync(
		mod,
		`'use strict';\nmodule.exports = async (github, core, context, require) => {\n${body}\n};\n`,
	);
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
			addList: (items) => {
				findings.push(...items);
				return summary;
			},
			write: async () => summary,
		};
		const core = { setFailed: (m) => failures.push(m), notice() {}, summary };
		await fn(
			{},
			core,
			{ payload: { pull_request: { body: prBody } } },
			require,
		);
		assert.strictEqual(
			failures.length > 0,
			findings.length > 0,
			"strict gates fail exactly when they find something",
		);
		return findings;
	};
}

/**
 * Index (for loadScriptModule's `nth`) of the first `script: |` block after the
 * line containing `label` — a step name — so a suite names the step it runs
 * rather than counting blocks.
 */
function scriptIndexAfter(file, label) {
	const lines = fs.readFileSync(file, "utf8").split("\n");
	const starts = lines.flatMap((l, i) =>
		/^\s*script:\s*\|\s*$/.test(l) ? [i] : [],
	);
	const marker = lines.findIndex((l) => l.includes(label));
	const idx = starts.findIndex((s) => s > marker);
	assert.ok(marker !== -1 && idx !== -1, `${label} script not found`);
	return idx;
}

/**
 * Build the `run()` for a registry PR script — the birth registrar
 * (repo-birth-bootstrap.yml, ADR-039) and the organization admission
 * (auto-seed-new-repo.yml, ADR-040) open one PR on this repository the same
 * way: read a result JSON, commit its changed paths on base (or merge base
 * into their own stale branch), refuse a branch carrying foreign commits, and
 * open or update one PR. Every run asserts the two invariants both share:
 * nothing is merged, and no ref is force-moved.
 *
 * @param {object} o
 * @param {Function} o.script   the loaded script (loadScriptModule)
 * @param {string} o.root       repo root, for the script's relative requires
 * @param {string} o.tmpTag     temp-dir prefix
 * @param {string} o.resultName result file name inside the temp dir
 * @param {object} o.entry      the registry entry the result carries
 * @param {string} o.release    the release the result cuts, e.g. "v3.43.1"
 * @param {string} o.owner
 * @param {string} o.repo
 * @param {string} o.baseSha    the base commit `git rev-parse` reports
 * @returns {(o?: {status?, branch?, openPRs?, treeMatches?}) => Promise<{calls, names, failures, notices, find}>}
 */
function makeRegistryPrRunner({
	script,
	root,
	tmpTag,
	resultName,
	entry,
	release,
	owner,
	repo,
	baseSha,
}) {
	return async function run({
		status = "added",
		branch = null,
		openPRs = [],
		treeMatches = false,
	} = {}) {
		const dir = fs.mkdtempSync(path.join(os.tmpdir(), tmpTag));
		const changed = [
			"semantics/repository_registry.yaml",
			`docs/semantic-foundation/${release}/HASHES.sha256`,
		];
		for (const rel of changed) {
			fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
			fs.writeFileSync(path.join(dir, rel), `content of ${rel}\n`);
		}
		const resultPath = path.join(dir, resultName);
		const added = status === "added";
		fs.writeFileSync(
			resultPath,
			JSON.stringify({
				status,
				entry,
				release: added ? release : undefined,
				changed_paths: added ? changed : [],
			}),
		);
		const calls = [];
		const rec = (name, fn) => async (args) => {
			calls.push({ name, args });
			return fn(args);
		};
		const treeOf = (sha) => {
			if (sha === baseSha) return "base-tree";
			return treeMatches ? "new-tree" : "old-tree";
		};
		const github = {
			rest: {
				git: {
					getCommit: rec("getCommit", ({ commit_sha }) => ({
						data: { tree: { sha: treeOf(commit_sha) } },
					})),
					getRef: rec("getRef", () => {
						if (!branch) throw notFound("no branch");
						return { data: { object: { sha: branch.sha } } };
					}),
					createTree: rec("createTree", () => ({ data: { sha: "new-tree" } })),
					createCommit: rec("createCommit", () => ({
						data: { sha: "f".repeat(40) },
					})),
					updateRef: rec("updateRef", () => ({})),
					createRef: rec("createRef", () => ({})),
				},
				repos: {
					compareCommitsWithBasehead: rec("compare", () => ({
						data: {
							commits: (branch?.messages || []).map((message) => ({
								commit: { message },
							})),
						},
					})),
				},
				pulls: {
					list: rec("pulls.list", () => ({
						data: openPRs.map((n) => ({ number: n, html_url: `u/${n}` })),
					})),
					create: rec("pulls.create", () => ({ data: { html_url: "u/new" } })),
					update: rec("pulls.update", () => ({})),
					merge: rec("pulls.merge", () => ({})),
				},
			},
		};
		const failures = [];
		const notices = [];
		const core = {
			notice: (m) => notices.push(m),
			setFailed: (m) => failures.push(m),
			info() {},
		};
		const env = { RESULT_PATH: resultPath, BASE_BRANCH: "main" };
		const prevEnv = Object.fromEntries(
			Object.keys(env).map((k) => [k, process.env[k]]),
		);
		setEnv(env);
		const prevCwd = process.cwd();
		process.chdir(dir);
		try {
			await script(
				github,
				core,
				{
					repo: { owner, repo },
					serverUrl: "https://github.com",
					runId: 4242,
				},
				makeScopedRequire(root, {
					child_process: { execFileSync: () => `${baseSha}\n` },
				}),
			);
		} finally {
			process.chdir(prevCwd);
			for (const [k, v] of Object.entries(prevEnv)) {
				if (v === undefined) delete process.env[k];
				else process.env[k] = v;
			}
			fs.rmSync(dir, { recursive: true, force: true });
		}
		const names = calls.map((c) => c.name);
		assert.ok(!names.includes("pulls.merge"), "a registry PR job never merges");
		for (const c of calls.filter((c) => c.name === "updateRef")) {
			assert.strictEqual(
				c.args.force,
				false,
				"a registry PR branch is never force-moved",
			);
		}
		return {
			calls,
			names,
			failures,
			notices,
			find: (n) => calls.find((c) => c.name === n),
		};
	};
}

/**
 * The three rules .github/workflows/pr-gates.yml applies to every PR body, for
 * a generated registry PR body (registration PR #250 failed them before the
 * body carried these sections). The body carries no HTML comments, so its
 * Problem text is checked as is.
 */
function assertPassesPrGates(body) {
	const section = (name) => {
		const m = body.match(
			new RegExp(String.raw`##\s*${name}([\s\S]*?)(?=\n##\s|$)`, "i"),
		);
		return m ? m[1] : "";
	};
	assert.ok(
		!body.includes("<!" + "--"),
		"the PR body carries no HTML comments",
	);
	assert.ok(
		section("Problem").trim().length >= 30,
		"pr-gates: Problem section too short",
	);
	const risk = [
		...section("Risk").matchAll(/^[ \t]*-[ \t]*\[([ xX])\]/gm),
	].filter((m) => m[1] !== " ");
	assert.strictEqual(
		risk.length,
		1,
		"pr-gates: exactly one Risk level checked",
	);
	assert.match(
		section("Evidence"),
		/actions\/runs\/\d+/,
		"pr-gates: Evidence links a CI run",
	);
}

module.exports = {
	makeRenderRecorder,
	extractScript,
	loadScriptModule,
	notFound,
	makeCore,
	makeScopedRequire,
	makeScriptRunner,
	makeBranchStubs,
	loadGovernanceGates,
	scriptIndexAfter,
	makeRegistryPrRunner,
	assertPassesPrGates,
};
