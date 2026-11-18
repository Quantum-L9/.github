"use strict";

/**
 * L9_GITHUB_READ_TOKEN stays out of every workflow a pull request can rewrite.
 *
 * A same-repository pull_request workflow runs from the merge ref, and a
 * workflow_call workflow receives secrets only from its caller. Either file
 * can be changed by a pull request and print a secret it names.
 * policies/governance-caller.yml is that caller, copied into every consumer.
 *
 * The token is allowed on workflows that run from the default branch, and
 * only as the actions/checkout token for Cursor-Governance.
 * persist-credentials stays false, so later steps do not keep the credential.
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
assert.ok(
	!caller.includes(SECRET),
	"policies/governance-caller.yml must not name L9_GITHUB_READ_TOKEN",
);

const workflowDir = path.join(root, ".github", "workflows");
for (const name of fs.readdirSync(workflowDir)) {
	if (!name.endsWith(".yml") && !name.endsWith(".yaml")) continue;
	const rel = path.join(".github", "workflows", name);
	const text = read(rel);
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
const suiteJob = composerWorkflow.split(/^ {2}validate:/m)[1];
assert.ok(suiteJob, "validate-starters-composer.yml has a validate job");
assert.ok(
	!suiteJob.includes(SECRET),
	"the starter suite job must not name the read token",
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
	"ok: L9_GITHUB_READ_TOKEN is absent from pull_request, workflow_call, and the governance caller",
);
