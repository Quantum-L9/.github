"use strict";

/**
 * Runs the REAL `register` job script from repo-birth-bootstrap.yml (ADR-039)
 * against a stubbed GitHub API and proves it:
 *   - opens one PR on a new `birth-registry/<repo>` branch,
 *   - does nothing when the entry is already registered,
 *   - advances its own stale branch with a merge commit (never a force move),
 *   - leaves an up-to-date branch alone,
 *   - refuses to touch a branch carrying commits it did not author,
 *   - never merges.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-birth-registry-workflow.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { loadScriptModule, notFound } = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const WORKFLOW = path.join(root, ".github/workflows/repo-birth-bootstrap.yml");
const OWNER = "Quantum-L9";
const REPO = ".github";
const BASE_SHA = "a".repeat(40);
const BRANCH = "birth-registry/l9-state";
const SUBJECT = "chore(registry): register factory-born Quantum-L9/l9-state";

// The register job's PR script is the third `script: |` block in the file.
const scriptIndex = (() => {
	const lines = fs.readFileSync(WORKFLOW, "utf8").split("\n");
	const starts = lines.flatMap((l, i) =>
		/^\s*script:\s*\|\s*$/.test(l) ? [i] : [],
	);
	const marker = lines.findIndex((l) =>
		l.includes("Open or update the registration PR"),
	);
	const idx = starts.findIndex((s) => s > marker);
	assert.ok(marker !== -1 && idx !== -1, "register job script not found");
	return idx;
})();
const run = loadScriptModule(WORKFLOW, "birth-registry-", scriptIndex);

const entry = {
	id: "l9-state",
	coordinate: {
		provider: "github",
		organization: OWNER,
		repository: "l9-state",
	},
	lifecycle: "current",
	class_ref: "l9.repository-class/l9@1",
	birth_provenance: {
		factory: "Quantum-L9/l9-repo-template",
		receipt_schema: "l9.birth-receipt/v1",
		receipt_digest: `sha256:${"b".repeat(64)}`,
		root_commit: "c".repeat(40),
		template_sha: "d".repeat(40),
		template_version: "2.3.0",
		org_policy_sha: "e".repeat(40),
		birth_profile: "org_seeded_self_governed",
		born_at: "2026-11-13T12:00:00Z",
	},
};

async function scenario({
	status = "added",
	branch = null,
	openPRs = [],
	treeMatches = false,
}) {
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), "birth-registry-case-"));
	const changed = [
		"semantics/repository_registry.yaml",
		"docs/semantic-foundation/v3.42.1/HASHES.sha256",
	];
	for (const rel of changed) {
		fs.mkdirSync(path.dirname(path.join(dir, rel)), { recursive: true });
		fs.writeFileSync(path.join(dir, rel), `content of ${rel}\n`);
	}
	const resultPath = path.join(dir, "registration.json");
	fs.writeFileSync(
		resultPath,
		JSON.stringify({
			status,
			entry,
			release: status === "added" ? "v3.42.1" : undefined,
			changed_paths: status === "added" ? changed : [],
		}),
	);
	const calls = [];
	const rec = (name, fn) => async (args) => {
		calls.push({ name, args });
		return fn(args);
	};
	const github = {
		rest: {
			git: {
				getCommit: rec("getCommit", ({ commit_sha }) => ({
					data: {
						tree: {
							sha:
								commit_sha === BASE_SHA
									? "base-tree"
									: treeMatches
										? "new-tree"
										: "old-tree",
						},
					},
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
	const childProcess = { execFileSync: () => `${BASE_SHA}\n` };
	const scopedRequire = (m) =>
		m === "child_process" ? childProcess : require(m);
	const prevCwd = process.cwd();
	const prevEnv = {
		RESULT_PATH: process.env.RESULT_PATH,
		BASE_BRANCH: process.env.BASE_BRANCH,
	};
	process.env.RESULT_PATH = resultPath;
	process.env.BASE_BRANCH = "main";
	process.chdir(dir);
	try {
		await run(
			github,
			core,
			{ repo: { owner: OWNER, repo: REPO } },
			scopedRequire,
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
	assert.ok(!names.includes("pulls.merge"), "the registrar never merges");
	for (const c of calls.filter((c) => c.name === "updateRef")) {
		assert.strictEqual(
			c.args.force,
			false,
			"the registration branch is never force-moved",
		);
	}
	return {
		calls,
		names,
		failures,
		notices,
		find: (n) => calls.find((c) => c.name === n),
	};
}

(async () => {
	// 1. First birth: new branch, one commit on base, one PR.
	{
		const r = await scenario({});
		assert.deepStrictEqual(r.failures, []);
		assert.deepStrictEqual(r.find("createCommit").args.parents, [BASE_SHA]);
		assert.ok(r.find("createCommit").args.message.startsWith(SUBJECT));
		assert.strictEqual(r.find("createRef").args.ref, `refs/heads/${BRANCH}`);
		assert.strictEqual(r.find("pulls.create").args.head, BRANCH);
		assert.strictEqual(r.find("pulls.create").args.base, "main");
		assert.match(
			r.find("pulls.create").args.body,
			/birth_provenance\.receipt_digest/,
		);
		assert.ok(!r.names.includes("updateRef"));
		const tree = r.find("createTree").args;
		assert.strictEqual(tree.base_tree, "base-tree");
		assert.deepStrictEqual(
			tree.tree.map((t) => t.path),
			[
				"semantics/repository_registry.yaml",
				"docs/semantic-foundation/v3.42.1/HASHES.sha256",
			],
		);
		console.log("ok: first birth opens one PR on a new birth-registry branch");
	}
	// 2. Already registered on base: no API call at all.
	{
		const r = await scenario({ status: "present" });
		assert.deepStrictEqual(r.failures, []);
		assert.deepStrictEqual(r.names, []);
		console.log("ok: an already-registered repository is a no-op");
	}
	// 3. Re-run with a stale registrar branch and an open PR: merge commit, same PR.
	{
		const r = await scenario({
			branch: { sha: "9".repeat(40), messages: [`${SUBJECT}\n\nold`] },
			openPRs: [7],
		});
		assert.deepStrictEqual(r.failures, []);
		assert.deepStrictEqual(r.find("createCommit").args.parents, [
			"9".repeat(40),
			BASE_SHA,
		]);
		assert.strictEqual(r.find("updateRef").args.ref, `heads/${BRANCH}`);
		assert.strictEqual(r.find("pulls.update").args.pull_number, 7);
		assert.ok(
			!r.names.includes("pulls.create"),
			"a re-run never opens a second PR",
		);
		console.log(
			"ok: a re-run advances its own branch by merge commit and updates the same PR",
		);
	}
	// 4. Re-run with an up-to-date branch: no commit, PR body refreshed.
	{
		const r = await scenario({
			branch: { sha: "9".repeat(40), messages: [`${SUBJECT}\n\nsame`] },
			openPRs: [7],
			treeMatches: true,
		});
		assert.deepStrictEqual(r.failures, []);
		assert.ok(
			!r.names.includes("createCommit") && !r.names.includes("updateRef"),
		);
		assert.strictEqual(r.find("pulls.update").args.pull_number, 7);
		console.log("ok: an up-to-date registration branch is left alone");
	}
	// 5. A branch carrying foreign work is never rewritten.
	{
		const r = await scenario({
			branch: {
				sha: "9".repeat(40),
				messages: [`${SUBJECT}\n\nold`, "fix: hand remediation"],
			},
			openPRs: [7],
		});
		assert.strictEqual(r.failures.length, 1);
		assert.match(r.failures[0], /did not author/);
		for (const n of [
			"createTree",
			"createCommit",
			"updateRef",
			"createRef",
			"pulls.update",
			"pulls.create",
		]) {
			assert.ok(!r.names.includes(n), `foreign work: ${n} must not run`);
		}
		console.log(
			"ok: a branch with commits the registrar did not author is refused",
		);
	}
	// Static: the job is chained after a passing, non-dry-run attestation.
	{
		const text = fs.readFileSync(WORKFLOW, "utf8");
		const job = text.slice(text.indexOf("\n  register:\n"));
		assert.match(job, /\n {4}needs: bootstrap\n/);
		assert.match(
			job,
			/\n {4}if: \$\{\{ success\(\) && inputs\.dry_run != true \}\}\n/,
		);
		assert.match(job, /python3 ops\/register-birth\.py apply/);
		assert.doesNotMatch(
			job,
			/--skip-factory-verifier/,
			"the live job always runs the factory verifier",
		);
		assert.doesNotMatch(job, /force: true|pulls\.merge|merge_pull_request/);
		console.log(
			"ok: register runs after bootstrap, never on a dry run, never skips the factory verifier",
		);
	}
})().catch((err) => {
	console.error(err);
	process.exit(1);
});
