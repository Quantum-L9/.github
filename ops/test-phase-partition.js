"use strict";

/**
 * The phase partition of Repo.mk, the repository-owned make-v1 implementation.
 *
 * repo-validate is the SHA-pin and semantic-foundation closure gate; it no
 * longer runs the starter suite. repo-check stays the SHA-pin audit.
 * repo-test runs ops/validate-starters.sh — the suite's only run, so a
 * starter-contract change is exercised exactly once even though Core runs
 * all four phases in order. The root Makefile facade routes validate, check
 * and test to those leaves and is never edited here.
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

	// repo-validate keeps its pins and closure, and repo-check stays the
	// SHA-pin audit.
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
		/ops\/audit-sha-pins\.sh/,
		"repo-check stays the SHA-pin audit",
	);

	// The facade routes each make-v1 phase to its repository-owned leaf.
	assert.match(facade, /^validate: repo-validate ##/m);
	assert.match(facade, /^check: repo-check ##/m);
	assert.match(facade, /^test: repo-test ##/m);
}

const mk = read("Repo.mk");
const facade = read("Makefile");

assertPartition(mk, facade);
console.log(
	"ok: repo-validate keeps the SHA-pin audit and semantic closure; the starter suite runs exactly once, in repo-test",
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

const auditGone = mk.replace(
	"repo-check: ## Static check: audit this repo for floating action refs\n\t@bash ops/audit-sha-pins.sh",
	"repo-check: ## Static check: audit this repo for floating action refs\n\t@true",
);
assert.notStrictEqual(auditGone, mk, "negative control did not change its fixture");
assert.throws(
	() => assertPartition(auditGone, facade),
	assert.AssertionError,
	"the SHA-pin audit out of repo-check is not caught",
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

console.log("\nall phase partition scenarios passed");
