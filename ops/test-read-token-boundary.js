"use strict";

/**
 * L9_GITHUB_READ_TOKEN stays out of every workflow a pull request can rewrite.
 *
 * A same-repository pull_request workflow runs from the merge ref, and a
 * workflow_call workflow receives secrets only from its caller. Either file
 * can be changed by a pull request and print a secret it names.
 * policies/governance-caller.yml is that caller, copied into every consumer.
 *
 * The token is allowed on the four workflows that run only from the default
 * branch, and only as the actions/checkout token for Cursor-Governance.
 * persist-credentials stays false, so later steps do not keep the credential.
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
const ALLOWED = {
	".github/workflows/seed-governance.yml": new Set(["workflow_dispatch"]),
	".github/workflows/continuous-sync.yml": new Set(["workflow_dispatch"]),
	".github/workflows/auto-seed-new-repo.yml": new Set([
		"workflow_dispatch",
		"repository_dispatch",
	]),
	".github/workflows/secret-drift.yml": new Set(["workflow_dispatch", "schedule"]),
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
		`${rel} names ${SECRET} once, on the checkout step`,
	);
	assert.ok(text.includes(CHECKOUT_TOKEN), `${rel} must set ${CHECKOUT_TOKEN}`);
	for (const event of trigger) {
		assert.ok(
			ALLOWED[rel].has(event),
			`${rel} event ${event} is not default-branch-only`,
		);
	}
	assert.match(text, /persist-credentials: false/);
}

console.log(
	"ok: L9_GITHUB_READ_TOKEN is absent from pull_request, workflow_call, and the governance caller",
);
