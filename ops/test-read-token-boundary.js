"use strict";

/**
 * L9_GITHUB_READ_TOKEN stays out of every workflow a pull request can rewrite.
 *
 * A same-repository pull_request workflow runs from the merge ref, and a
 * workflow_call workflow receives secrets only from its caller. Either file
 * can be changed by a pull request and print a secret it names.
 * policies/governance-caller.yml is copied into every consumer. It may name the
 * secret once, as the pass-through to governance-pr.yml, and must not set the
 * checkout token.
 *
 * governance-pr.yml may name the secret once as the optional checkout token
 * for callers that pass it, and once as the token of the sparse org PR
 * template checkout (falling back to github.token), never in an env: block.
 * Pull-request jobs restore the composer cache and do not name the secret.
 * persist-credentials stays false.
 * push, when allowed, is limited to main. A file that also has pull_request
 * or workflow_call is still forbidden from naming the token. Pull-request
 * jobs restore the composer cache that fetch saved; they do not check out
 * the private repository.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-read-token-boundary.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const SECRET = "L9_GITHUB_READ_TOKEN";
const CHECKOUT_TOKEN = `token: \${{ secrets.${SECRET} }}`;
const PASS_THROUGH = `${SECRET}: \${{ secrets.${SECRET} }}`;
// Quantum-L9/.github is private: the body job checks the org PR template out
// with this token and hands the composer a local file, never the token.
const TEMPLATE_TOKEN = `token: \${{ secrets.${SECRET} || github.token }}`;
const GOVERNANCE_PR = ".github/workflows/governance-pr.yml";
const PR_FILES = ".github/workflows/pr-files.yml";
const ALLOWED = {
	".github/workflows/seed-governance.yml": new Set(["workflow_dispatch"]),
	".github/workflows/continuous-sync.yml": new Set(["workflow_dispatch"]),
	".github/workflows/auto-seed-new-repo.yml": new Set([
		"workflow_dispatch",
		"repository_dispatch",
	]),
	".github/workflows/secret-drift.yml": new Set(["workflow_dispatch", "schedule"]),
	".github/workflows/validate-starters-composer.yml": new Set([
		"push",
		"workflow_dispatch",
	]),
};
const FORBIDDEN_EVENTS = new Set(["pull_request", "workflow_call"]);

function read(rel) {
	return fs.readFileSync(path.join(root, rel), "utf8");
}

function onBlock(text) {
	const lines = text.split("\n");
	const start = lines.findIndex((line) => /^on:\s*(#.*)?$/.test(line));
	assert.ok(start !== -1, 'no top-level "on:" block');
	const block = [];
	for (const line of lines.slice(start + 1)) {
		if (/^\S/.test(line) && !line.startsWith("#")) break;
		if (line.trim() === "" || line.trim().startsWith("#")) continue;
		block.push(line);
	}
	return block;
}

function events(block) {
	return block.flatMap((line) => {
		const match = line.match(/^ {2}([A-Za-z_]+):/);
		return match ? [match[1]] : [];
	});
}

const caller = read("policies/governance-caller.yml");
assert.strictEqual(
	caller.split(PASS_THROUGH).length - 1,
	1,
	"policies/governance-caller.yml must pass L9_GITHUB_READ_TOKEN by name exactly once",
);
assert.ok(
	!caller.includes(CHECKOUT_TOKEN),
	"policies/governance-caller.yml must not set the checkout token",
);

function assertGovernancePr(text) {
	assert.strictEqual(
		text.split(CHECKOUT_TOKEN).length - 1,
		1,
		`${GOVERNANCE_PR} must set ${CHECKOUT_TOKEN} exactly once`,
	);
	assert.strictEqual(
		text.split(TEMPLATE_TOKEN).length - 1,
		1,
		`${GOVERNANCE_PR} must set ${TEMPLATE_TOKEN} exactly once (org PR template checkout)`,
	);
	const templateStep = text.slice(
		text.lastIndexOf("- uses: actions/checkout", text.indexOf(TEMPLATE_TOKEN)),
		text.indexOf("- uses:", text.indexOf(TEMPLATE_TOKEN)),
	);
	assert.match(
		templateStep,
		/sparse-checkout: \|\n\s+\.github\/pull_request_template\.md\n\s+sparse-checkout-cone-mode: false/,
		`${GOVERNANCE_PR} org template checkout must be sparse to the template alone`,
	);
	assert.match(
		templateStep,
		/persist-credentials: false/,
		`${GOVERNANCE_PR} org template checkout must not persist credentials`,
	);
	const besidesToken = text
		.replace(CHECKOUT_TOKEN, "")
		.replace(TEMPLATE_TOKEN, "");
	assert.strictEqual(
		besidesToken.split(SECRET).length - 1,
		1,
		`${GOVERNANCE_PR} names ${SECRET} only as the checkout token, plus its workflow_call declaration`,
	);
	assert.match(
		besidesToken,
		new RegExp(`${SECRET}:\\n\\s+required: false\\b`),
		`${GOVERNANCE_PR} must declare ${SECRET} optional`,
	);
	assert.match(text, /composer_from_cache:/);
	assert.ok(
		!besidesToken.includes(PASS_THROUGH),
		`${GOVERNANCE_PR} must not use the pr-files pass-through line`,
	);
	assert.match(text, /persist-credentials: false/);
}

function assertPrFiles(text) {
	assert.ok(
		!text.includes(SECRET),
		`${PR_FILES} restores the composer cache and must not name ${SECRET}`,
	);
}

const workflowDir = path.join(root, ".github", "workflows");
for (const name of fs.readdirSync(workflowDir)) {
	if (!name.endsWith(".yml") && !name.endsWith(".yaml")) continue;
	const rel = path.join(".github", "workflows", name);
	const text = read(rel);
	if (rel === GOVERNANCE_PR) {
		assertGovernancePr(text);
		continue;
	}
	if (rel === PR_FILES) {
		assertPrFiles(text);
		continue;
	}
	const found = text.includes(SECRET);
	const trigger = new Set(events(onBlock(text)));
	const forbidden = [...trigger].filter((event) => FORBIDDEN_EVENTS.has(event));
	if (forbidden.length > 0) {
		assert.ok(
			!found,
			`${rel} runs on ${forbidden.join(", ")} and must not name ${SECRET}`,
		);
		continue;
	}
	if (!Object.hasOwn(ALLOWED, rel)) {
		assert.ok(!found, `${rel} is not a default-branch read-token checkout`);
		continue;
	}
	assert.ok(found, `${rel} must check out with ${SECRET}`);
	if (rel === ".github/workflows/continuous-sync.yml") {
		assert.strictEqual(
			text.split(CHECKOUT_TOKEN).length - 1,
			1,
			`${rel} sets ${CHECKOUT_TOKEN} exactly once`,
		);
		assert.match(text, /function passReadToken/);
		assert.match(text, /persist-credentials: false/);
		continue;
	}
	assert.strictEqual(
		text.split(SECRET).length - 1,
		1,
		`${rel} names ${SECRET} once`,
	);
	assert.match(
		text,
		/^ *token: \$\{\{ secrets\.L9_GITHUB_READ_TOKEN \}\}$/m,
		`${rel} must set the checkout token`,
	);
	assert.match(text, /persist-credentials: false/);
	for (const event of trigger) {
		assert.ok(
			ALLOWED[rel].has(event),
			`${rel} event ${event} is not default-branch-only`,
		);
	}
	if (trigger.has("push")) {
		const body = onBlock(text).join("\n");
		const pushAt = body.search(/^ {2}push:/m);
		assert.ok(pushAt !== -1, `${rel} allows push but has no push trigger`);
		const after = body.slice(pushAt);
		const nextEvent = after.slice(1).search(/\n {2}[A-Za-z_]+:/);
		const pushBlock = nextEvent === -1 ? after : after.slice(0, nextEvent + 1);
		assert.match(pushBlock, /branches:\n {6}- main$/);
		assert.ok(!pushBlock.includes("*"), `${rel} push branches must be main only`);
	}
}

const composerWorkflow = read(".github/workflows/validate-starters-composer.yml");
assert.ok(
	!/^ {2}validate:/m.test(composerWorkflow),
	"validate-starters-composer.yml runs no suite job; repo-test is its only run",
);
// The read token belongs to the default-branch composer fetch alone, so the
// fetch is the workflow's only job; a second job would inherit its cache and
// run the suite beside Core's required `test` phase.
const composerJobs = [
	...composerWorkflow
		.slice(composerWorkflow.indexOf("\njobs:\n"))
		.matchAll(/^ {2}([a-z][a-z0-9-]*):$/gm),
].map((match) => match[1]);
assert.deepStrictEqual(
	composerJobs,
	["fetch-composer"],
	"the composer workflow's only job is the fetch",
);
assert.ok(
	!composerWorkflow.includes("pull_request_target"),
	"the composer fetch must not run as pull_request_target",
);
assert.ok(
	!composerWorkflow.includes("github.event.pull_request"),
	"the composer workflow must not check out a pull request",
);

console.log(
	"ok: L9_GITHUB_READ_TOKEN is the optional governance-pr checkout token, the caller pass-through, or a default-branch checkout",
);
