"use strict";

/**
 * L9_GITHUB_READ_TOKEN stays out of every workflow a pull request can rewrite,
 * except the two body-refresh files that check out Cursor-Governance.
 *
 * A same-repository pull_request workflow runs from the merge ref, and a
 * workflow_call workflow receives secrets only from its caller. Either file
 * can be changed by a pull request and print a secret it names.
 * policies/governance-caller.yml is copied into every consumer. It may name the
 * secret once, as the pass-through to governance-pr.yml, and must not set the
 * checkout token.
 *
 * governance-pr.yml may name the secret once, as the composer checkout token,
 * with persist-credentials: false. pr-files.yml may name it once, as the
 * pass-through L9_GITHUB_READ_TOKEN: ${{ secrets.L9_GITHUB_READ_TOKEN }}, and
 * must not set the checkout token. Every other pull_request or workflow_call
 * workflow must not name it.
 *
 * The token is also allowed on the four workflows that run only from the
 * default branch, and only as the actions/checkout token for Cursor-Governance.
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
const PASS_THROUGH = `${SECRET}: \${{ secrets.${SECRET} }}`;
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
	const besidesToken = text.replace(CHECKOUT_TOKEN, "");
	assert.strictEqual(
		besidesToken.split(SECRET).length - 1,
		1,
		`${GOVERNANCE_PR} names ${SECRET} only as the checkout token, plus its workflow_call declaration`,
	);
	assert.match(
		besidesToken,
		new RegExp(`${SECRET}:\\n\\s+required: true\\b`),
		`${GOVERNANCE_PR} must declare ${SECRET} required`,
	);
	assert.ok(
		!besidesToken.includes(PASS_THROUGH),
		`${GOVERNANCE_PR} must not use the pr-files pass-through line`,
	);
	assert.match(text, /persist-credentials: false/);
}

function assertPrFiles(text) {
	assert.strictEqual(
		text.split(PASS_THROUGH).length - 1,
		1,
		`${PR_FILES} must pass ${SECRET} by name exactly once`,
	);
	assert.strictEqual(
		text.split(SECRET).length - 1,
		2,
		`${PR_FILES} names ${SECRET} only on the pass-through line`,
	);
	assert.ok(
		!text.includes(CHECKOUT_TOKEN),
		`${PR_FILES} must not contain the checkout token line`,
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
	if (rel === ".github/workflows/validate-starters.yml") {
		assert.strictEqual(
			text.split(CHECKOUT_TOKEN).length - 1,
			1,
			`${rel} must set ${CHECKOUT_TOKEN} exactly once`,
		);
		assert.strictEqual(
			text.split(SECRET).length - 1,
			1,
			`${rel} names ${SECRET} only as the composer checkout token`,
		);
		assert.match(text, /persist-credentials: false/);
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
	"ok: L9_GITHUB_READ_TOKEN is the composer checkout token, the pr-files pass-through, or a default-branch checkout",
);
