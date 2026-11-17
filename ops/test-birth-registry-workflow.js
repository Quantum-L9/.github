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
const path = require("node:path");
const {
	assertPassesPrGates,
	loadScriptModule,
	makeRegistryPrRunner,
	scriptIndexAfter,
} = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const WORKFLOW = path.join(root, ".github/workflows/repo-birth-bootstrap.yml");
const OWNER = "Quantum-L9";
const REPO = ".github";
const BASE_SHA = "a".repeat(40);
const BRANCH = "birth-registry/l9-state";
const SUBJECT = "chore(registry): register factory-born Quantum-L9/l9-state";

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

// The register job's PR script, run against the shared registry-PR stub.
const scenario = makeRegistryPrRunner({
	script: loadScriptModule(
		WORKFLOW,
		"birth-registry-",
		scriptIndexAfter(WORKFLOW, "Open or update the registration PR"),
	),
	root,
	tmpTag: "birth-registry-case-",
	resultName: "registration.json",
	entry,
	release: "v3.42.1",
	owner: OWNER,
	repo: REPO,
	baseSha: BASE_SHA,
});

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
		assertPassesPrGates(r.find("pulls.create").args.body);
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
