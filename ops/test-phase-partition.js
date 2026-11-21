"use strict";

/**
 * The phase partition of Repo.mk, the repository-owned make-v1 implementation.
 *
 * repo-validate is the SHA-pin and semantic-foundation closure gate; it no
 * longer runs the starter suite. repo-check is the tracked-bytecode guard; the
 * SHA-pin audit runs once, in repo-validate, not again in repo-check.
 * repo-test runs ops/validate-starters.sh — the suite's only run, so a
 * starter-contract change is exercised exactly once even though Core runs
 * all four phases in order. The root Makefile facade routes validate, check
 * and test to those leaves and is never edited here.
 *
 * The witness also reads .github/workflows: a workflow that invoked the
 * suite directly would re-run it beside Core's required `test` phase, so the
 * partition is only pinned if no workflow names it.
 *
 * Read literally, without executing make, like the other ops/test-*.js
 * suites: the assertion is about the text the runner reads.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-phase-partition.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const read = (rel) => fs.readFileSync(path.join(root, rel), "utf8");

/** The recipe lines (tab-indented) under one target definition in Repo.mk. */
function recipeOf(mk, target) {
	const lines = mk.split("\n");
	const start = lines.findIndex((line) => line.startsWith(`${target}:`));
	assert.ok(start !== -1, `no ${target} recipe in Repo.mk`);
	const body = [];
	for (const line of lines.slice(start + 1)) {
		if (!line.startsWith("\t")) break;
		body.push(line);
	}
	return body.join("\n");
}

/** The three phase leaves, keyed by recipe text. */
function phaseRecipes(mk) {
	return Object.fromEntries(
		["repo-validate", "repo-check", "repo-test"].map((target) => [
			target,
			recipeOf(mk, target),
		]),
	);
}

const times = (text, needle) => text.split(needle).length - 1;

/** The one partition this repository runs under make-v1. */
function assertPartition(mk, facade) {
	const phases = phaseRecipes(mk);

	// The starter suite runs once: in repo-test, and in no other phase.
	assert.doesNotMatch(
		phases["repo-validate"],
		/ops\/validate-starters\.sh/,
		"repo-validate must not run the starter suite",
	);
	assert.doesNotMatch(
		phases["repo-check"],
		/ops\/validate-starters\.sh/,
		"repo-check must not run the starter suite",
	);
	assert.strictEqual(
		times(phases["repo-test"], "ops/validate-starters.sh"),
		1,
		"repo-test runs the starter suite exactly once",
	);

	// repo-validate keeps its pins and closure; repo-check is the bytecode
	// guard; the SHA-pin audit runs in exactly one phase.
	assert.match(
		phases["repo-validate"],
		/ops\/audit-sha-pins\.sh/,
		"repo-validate keeps the SHA-pin audit",
	);
	assert.match(
		phases["repo-validate"],
		/scripts\/validate-semantics\.py/,
		"repo-validate keeps the semantic-foundation closure",
	);
	assert.match(
		phases["repo-check"],
		/ops\/check-no-bytecode\.sh/,
		"repo-check runs the tracked-bytecode guard",
	);
	const pinRuns = Object.values(phases).reduce(
		(n, recipe) => n + times(recipe, "ops/audit-sha-pins.sh"),
		0,
	);
	assert.strictEqual(pinRuns, 1, "the SHA-pin audit runs in exactly one phase");

	// The facade routes each make-v1 phase to its repository-owned leaf.
	assert.match(facade, /^validate: repo-validate ##/m);
	assert.match(facade, /^check: repo-check ##/m);
	assert.match(facade, /^test: repo-test ##/m);
}

/** Every workflow file, keyed by name, read as the runner reads it. */
function workflowTexts() {
	return Object.fromEntries(
		fs
			.readdirSync(path.join(root, ".github/workflows"))
			.filter((name) => name.endsWith(".yml"))
			.map((name) => [name, read(`.github/workflows/${name}`)]),
	);
}

/**
 * The suite's only run is repo-test. A workflow that invokes it directly
 * re-runs it beside Core's required `test` phase, which is the duplicate this
 * partition exists to remove.
 */
function assertNoWorkflowRunsTheSuite(workflows) {
	for (const [name, text] of Object.entries(workflows)) {
		assert.ok(
			!text.includes("ops/validate-starters.sh"),
			`${name} names the starter suite; repo-test is its only run`,
		);
	}
}

/**
 * The registration tool suites each re-run the semantic validator over a copy
 * of the tree (~170s together), so they are out of the required test phase.
 * They must still run somewhere: each one is named by registration-e2e.yml.
 */
const REGISTRATION_SUITES = [
	"ops/test-register-birth.py",
	"ops/test-register-org-repository.py",
	"ops/test-admit-profiles.py",
];
function assertRegistrationSuitesPlaced(starters, workflows) {
	const e2e = workflows["registration-e2e.yml"];
	assert.ok(e2e, "registration-e2e.yml is missing; the registration suites would run nowhere");
	for (const suite of REGISTRATION_SUITES) {
		assert.ok(
			!starters.includes(suite),
			`${suite} is back in ops/validate-starters.sh, the required test phase`,
		);
		assert.ok(e2e.includes(suite), `registration-e2e.yml does not run ${suite}`);
	}
}

const mk = read("Repo.mk");
const facade = read("Makefile");
const starters = read("ops/validate-starters.sh");

assertPartition(mk, facade);
assertNoWorkflowRunsTheSuite(workflowTexts());
assertRegistrationSuitesPlaced(starters, workflowTexts());
console.log(
	"ok: repo-validate keeps the SHA-pin audit and semantic closure, repo-check is the bytecode guard, the starter suite runs exactly once, in repo-test, no workflow names it, and registration-e2e.yml runs the registration suites",
);

// Negative controls: a partition that moves a phase role must fail.
const suiteBack = mk.replace(
	"\tbash ops/audit-sha-pins.sh; \\\n",
	"\tbash ops/validate-starters.sh; \\\n\tbash ops/audit-sha-pins.sh; \\\n",
);
assert.notStrictEqual(suiteBack, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(suiteBack, facade),
	assert.AssertionError,
	"the starter suite back in repo-validate is not caught",
);

const suiteGone = mk.replace(
	"\t@$(USE_VENV) bash ops/validate-starters.sh",
	"\t@true",
);
assert.notStrictEqual(suiteGone, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(suiteGone, facade),
	assert.AssertionError,
	"the starter suite out of repo-test is not caught",
);

const guardGone = mk.replace(
	"repo-check: ## Static check: no tracked Python bytecode\n\t@bash ops/check-no-bytecode.sh",
	"repo-check: ## Static check: no tracked Python bytecode\n\t@true",
);
assert.notStrictEqual(guardGone, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(guardGone, facade),
	assert.AssertionError,
	"the bytecode guard out of repo-check is not caught",
);

const pinsTwice = mk.replace(
	"\t@bash ops/check-no-bytecode.sh",
	"\t@bash ops/check-no-bytecode.sh && bash ops/audit-sha-pins.sh",
);
assert.notStrictEqual(pinsTwice, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(pinsTwice, facade),
	assert.AssertionError,
	"the SHA-pin audit run twice is not caught",
);

assert.throws(
	() =>
		assertRegistrationSuitesPlaced(
			`${starters}\npython3 ops/test-register-birth.py\n`,
			workflowTexts(),
		),
	assert.AssertionError,
	"a registration suite back in the required test phase is not caught",
);
const withoutE2e = { ...workflowTexts() };
delete withoutE2e["registration-e2e.yml"];
assert.throws(
	() => assertRegistrationSuitesPlaced(starters, withoutE2e),
	assert.AssertionError,
	"registration suites that run nowhere are not caught",
);

const semanticsGone = mk.replace(
	'"$$PY" scripts/validate-semantics.py',
	'"$$PY" true',
);
assert.notStrictEqual(semanticsGone, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(semanticsGone, facade),
	assert.AssertionError,
	"the semantic closure out of repo-validate is not caught",
);

const facadeMoved = facade.replace(
	"validate: repo-validate ##",
	"validate: repo-test ##",
);
assert.notStrictEqual(facadeMoved, facade, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(mk, facadeMoved),
	assert.AssertionError,
	"a facade phase routed to the wrong leaf is not caught",
);

assert.throws(
	() =>
		assertNoWorkflowRunsTheSuite({
			"fixture.yml": "run: ops/validate-starters.sh\n",
		}),
	assert.AssertionError,
	"a workflow that runs the starter suite beside repo-test is not caught",
);

console.log("\nall phase partition scenarios passed");
