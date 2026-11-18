"use strict";

/**
 * Runs the REAL `admit` job scripts from auto-seed-new-repo.yml (ADR-040)
 * against a stubbed GitHub API and proves:
 *   - an ordinary new repository is admitted: the observe step reports its
 *     GitHub id, and the PR step opens one PR on `org-registry/<repo>`;
 *   - a factory-born repository (birth receipt present) and an archived one
 *     are skipped, and an unreadable receipt probe fails the job;
 *   - an already-registered repository is a no-op;
 *   - a stale admission branch is advanced by a merge commit, an up-to-date
 *     one is left alone, and a branch carrying foreign work is refused;
 *   - nothing is ever merged or force-moved, and the PR body passes pr-gates;
 *   - a dry run renders and opens nothing; a sweep runs no admission.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-org-admission-workflow.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const {
	assertPassesPrGates,
	loadScriptModule,
	makeRegistryPrRunner,
	makeScopedRequire,
	notFound,
	scriptIndexAfter,
} = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const WORKFLOW = path.join(root, ".github/workflows/auto-seed-new-repo.yml");
const OWNER = "Quantum-L9";
const REPO = ".github";
const BASE_SHA = "a".repeat(40);
const TARGET = "New.Org_Repo";
const BRANCH = `org-registry/${TARGET}`;
const SUBJECT = `chore(registry): admit organization repository ${OWNER}/${TARGET}`;

const observe = loadScriptModule(
	WORKFLOW,
	"org-admit-observe-",
	scriptIndexAfter(WORKFLOW, "Observe the repository"),
);

const entry = {
	id: "new-org-repo",
	coordinate: { provider: "github", organization: OWNER, repository: TARGET },
	lifecycle: "current",
	class_ref: "l9.repository-class/l9@1",
	organization_admission: {
		basis: "organization_completeness",
		decision_record: "ADR-040",
		github_repository_id: 4242,
		observed_at: "2026-11-17T12:00:00Z",
	},
};

async function runObserve({ repo = {}, receipt = 404, name = TARGET } = {}) {
	const calls = [];
	const rec = (n, fn) => async (args) => {
		calls.push({ name: n, args });
		return fn(args);
	};
	const github = {
		rest: {
			repos: {
				get: rec("repos.get", () => ({
					data: {
						id: 4242,
						name,
						archived: false,
						default_branch: "main",
						...repo,
					},
				})),
				getContent: rec("getContent", () => {
					if (receipt === 200) return { data: { type: "file", content: "" } };
					const e =
						receipt === 404 ? notFound("absent") : new Error("probe failed");
					e.status = receipt;
					throw e;
				}),
			},
		},
	};
	const outputs = {};
	const notices = [];
	const core = {
		setOutput: (k, v) => {
			outputs[k] = v;
		},
		notice: (m) => notices.push(m),
		setFailed() {},
		info() {},
	};
	const prev = process.env.TARGET_REPO;
	process.env.TARGET_REPO = name;
	const prevCwd = process.cwd();
	process.chdir(root);
	let error = null;
	try {
		await observe(github, core, {}, makeScopedRequire(root));
	} catch (e) {
		error = e;
	} finally {
		process.chdir(prevCwd);
		if (prev === undefined) delete process.env.TARGET_REPO;
		else process.env.TARGET_REPO = prev;
	}
	return { calls, outputs, notices, error };
}

const runPr = makeRegistryPrRunner({
	script: loadScriptModule(
		WORKFLOW,
		"org-admit-pr-",
		scriptIndexAfter(WORKFLOW, "Open or update the admission PR"),
	),
	root,
	tmpTag: "org-admission-case-",
	resultName: "admission.json",
	entry,
	release: "v3.43.1",
	owner: OWNER,
	repo: REPO,
	baseSha: BASE_SHA,
});

(async () => {
	// Observe: an ordinary repository is admitted with its GitHub id.
	{
		const r = await runObserve();
		assert.strictEqual(r.error, null);
		assert.strictEqual(r.outputs.action, "admit");
		assert.strictEqual(r.outputs.github_id, "4242");
		assert.strictEqual(r.outputs.repository, TARGET);
		const canonical = await runObserve({
			name: "new.repo",
			repo: { name: "New.Repo" },
		});
		assert.strictEqual(canonical.outputs.action, "admit");
		assert.strictEqual(canonical.outputs.repository, "New.Repo");
		assert.match(
			r.outputs.observed_at,
			/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/,
		);
		assert.deepStrictEqual(r.calls[1].args, {
			owner: OWNER,
			repo: TARGET,
			path: ".l9/birth-receipt.json",
			ref: "main",
		});
		const empty = await runObserve({ receipt: 409 });
		assert.strictEqual(
			empty.outputs.action,
			"admit",
			"an empty repository carries no receipt",
		);
		console.log(
			"ok: admit/observe — an ordinary repository is admitted with its GitHub id",
		);
	}
	// Observe: factory-born and archived repositories are skipped; unclear probes fail.
	{
		const born = await runObserve({ receipt: 200 });
		assert.strictEqual(born.outputs.action, "skip");
		assert.match(born.notices[0], /factory-born.*ADR-039/);
		const archived = await runObserve({ repo: { archived: true } });
		assert.strictEqual(archived.outputs.action, "skip");
		assert.match(archived.notices[0], /archived.*retired/);
		assert.strictEqual(
			archived.calls.length,
			1,
			"no receipt probe for an archived repository",
		);
		const unclear = await runObserve({ receipt: 500 });
		assert.ok(unclear.error, "an unreadable receipt probe fails the job");
		assert.strictEqual(unclear.outputs.action, undefined);
		const bad = await runObserve({ name: "bad/name" });
		assert.ok(bad.error && /invalid repository name/.test(bad.error.message));
		assert.deepStrictEqual(bad.calls, []);
		const self = await runObserve({ name: ".github" });
		assert.strictEqual(self.outputs.action, "skip");
		console.log(
			"ok: admit/observe — factory-born, archived and .github skipped; unclear probes and bad names fail",
		);
	}
	// PR: first admission opens one PR on a new branch.
	{
		const r = await runPr();
		assert.deepStrictEqual(r.failures, []);
		assert.deepStrictEqual(r.find("createCommit").args.parents, [BASE_SHA]);
		assert.ok(r.find("createCommit").args.message.startsWith(SUBJECT));
		assert.strictEqual(r.find("createRef").args.ref, `refs/heads/${BRANCH}`);
		const create = r.find("pulls.create").args;
		assert.strictEqual(create.head, BRANCH);
		assert.strictEqual(create.title, SUBJECT);
		assert.match(
			create.body,
			/organization_admission\.github_repository_id \| `4242`/,
		);
		assert.match(create.body, /no ProductKind, no Node, no constellation/);
		assertPassesPrGates(create.body);
		assert.deepStrictEqual(
			r.find("createTree").args.tree.map((t) => t.path),
			[
				"semantics/repository_registry.yaml",
				"docs/semantic-foundation/v3.43.1/HASHES.sha256",
			],
		);
		console.log(
			"ok: admit/pr — first admission opens one PR on a new org-registry branch",
		);
	}
	// PR: already registered is a no-op.
	{
		const r = await runPr({ status: "present" });
		assert.deepStrictEqual(r.failures, []);
		assert.deepStrictEqual(r.names, []);
		console.log("ok: admit/pr — an already-registered repository is a no-op");
	}
	// PR: stale own branch is advanced by merge commit; up-to-date is left alone.
	{
		const stale = await runPr({
			branch: { sha: "9".repeat(40), messages: [`${SUBJECT}\n\nold`] },
			openPRs: [7],
		});
		assert.deepStrictEqual(stale.failures, []);
		assert.deepStrictEqual(stale.find("createCommit").args.parents, [
			"9".repeat(40),
			BASE_SHA,
		]);
		assert.strictEqual(stale.find("pulls.update").args.pull_number, 7);
		assert.ok(!stale.names.includes("pulls.create"));
		const same = await runPr({
			branch: { sha: "9".repeat(40), messages: [`${SUBJECT}\n\nsame`] },
			openPRs: [7],
			treeMatches: true,
		});
		assert.ok(
			!same.names.includes("createCommit") && !same.names.includes("updateRef"),
		);
		console.log(
			"ok: admit/pr — stale branch merged forward, up-to-date branch left alone, same PR updated",
		);
	}
	// PR: foreign work is never rewritten.
	{
		const r = await runPr({
			branch: {
				sha: "9".repeat(40),
				messages: [`${SUBJECT}\n\nold`, "fix: hand edit"],
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
			"ok: admit/pr — a branch with commits the job did not author is refused",
		);
	}
	// Static: targeted only, dry run renders, never merges.
	{
		const text = fs.readFileSync(WORKFLOW, "utf8");
		const job = text.slice(text.indexOf("\n  admit:\n"));
		assert.match(
			job,
			/\n {4}if: \$\{\{ \(inputs\.target_repo \|\| github\.event\.client_payload\.repository \|\| ''\) != '' \}\}\n/,
			"a sweep admits nothing",
		);
		assert.match(job, /\n {4}environment: governance-distribution\n/);
		assert.match(
			job,
			/if \[ "\$\{DRY_RUN\}" = "true" \]; then mode=render; fi/,
		);
		assert.match(job, /python3 ops\/register-org-repository\.py "\$\{mode\}"/);
		assert.match(
			job,
			/--observed-at "\$\{OBSERVED_AT\}" \\\n {12}--write-result\n/,
			"the CLI carries no file path; the result goes to its one fixed file",
		);
		assert.match(
			job,
			/if: \$\{\{ steps\.observe\.outputs\.action == 'admit' && inputs\.dry_run != true \}\}/,
			"a dry run opens no PR",
		);
		assert.doesNotMatch(job, /force: true|pulls\.merge|merge_pull_request/);
		console.log(
			"ok: admit — targeted runs only, dry run renders and opens nothing, never merges",
		);
	}
})().catch((err) => {
	console.error(err);
	process.exit(1);
});
