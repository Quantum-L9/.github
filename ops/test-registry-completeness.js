"use strict";

/**
 * Asserts ops/registry-completeness.js and registry-completeness.yml (ADR-040).
 *
 * The load-bearing claims:
 *   - the real registry is COMPLETE against the organization listing observed
 *     on 2026-11-17 (ops/fixtures/org-listing-2026-11-17.json, 61 repositories);
 *   - one synthetic unregistered repository makes it INCOMPLETE and is named;
 *   - an archived repository registered current, and a case-only mismatch,
 *     are violations too;
 *   - an unreadable or empty listing is UNKNOWN, never COMPLETE;
 *   - the workflow's real script fails the job on anything but COMPLETE and
 *     writes nothing.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-registry-completeness.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const childProcess = require("node:child_process");
const { pythonYamlParser } = require("./governance-report.js");
const {
	VERDICTS,
	assessRegistryCompleteness,
	loadRegistry,
	renderCompletenessReport,
} = require("./registry-completeness.js");
const {
	loadScriptModule,
	makeCore,
	makeScopedRequire,
} = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const ORG = "Quantum-L9";
const REVISION = "f".repeat(40);
const io = {
	readBytes: (p) => fs.readFileSync(path.join(root, p)),
	parseYaml: pythonYamlParser(childProcess.execFileSync),
	revision: REVISION,
};
const registry = loadRegistry(io);
const listing = JSON.parse(
	fs.readFileSync(
		path.join(root, "ops/fixtures/org-listing-2026-11-17.json"),
		"utf8",
	),
);
const observed = listing.repositories;
const clone = (v) => JSON.parse(JSON.stringify(v));

function historicalRegistry() {
	const names = new Set(observed.map((repo) => repo.name));
	const scoped = clone(registry);
	scoped.repositories = registry.repositories.filter((entry) =>
		names.has(entry?.coordinate?.repository),
	);
	return scoped;
}

// ── the real registry against the observed organization ─────────────────────
{
	assert.strictEqual(
		observed.length,
		61,
		"fixture records 61 hosted repositories",
	);
	const result = assessRegistryCompleteness({
		registry: historicalRegistry(),
		discovered: observed,
		org: ORG,
	});
	assert.strictEqual(result.verdict, VERDICTS.COMPLETE, JSON.stringify(result));
	assert.strictEqual(result.hosted, 61);
	assert.strictEqual(result.registered, 61);
	assert.deepStrictEqual(result.unregistered, []);
	assert.deepStrictEqual(result.archivedCurrent, []);
	assert.deepStrictEqual(result.notHosted, []);
	const golden = registry.repositories.find((e) => e.id === "golden-repo");
	assert.strictEqual(
		golden.lifecycle,
		"retired",
		"archived golden-repo is registered retired",
	);
	console.log(
		"ok: registry completeness — the real registry covers all 61 observed repositories",
	);
}

// ── a synthetic unregistered repository fails, and is named ─────────────────
{
	const discovered = [
		...clone(observed),
		{ name: "Unregistered.Fixture", archived: false },
	];
	const result = assessRegistryCompleteness({
		registry: historicalRegistry(),
		discovered,
		org: ORG,
	});
	assert.strictEqual(result.verdict, VERDICTS.INCOMPLETE);
	assert.deepStrictEqual(result.unregistered, ["Unregistered.Fixture"]);
	const md = renderCompletenessReport(result, ORG);
	assert.match(md, /INCOMPLETE/);
	assert.match(md, /`Quantum-L9\/Unregistered\.Fixture`/);
	// Archived repositories are in scope too.
	const archived = [
		...clone(observed),
		{ name: "old-archive", archived: true },
	];
	assert.deepStrictEqual(
		assessRegistryCompleteness({
			registry: historicalRegistry(),
			discovered: archived,
			org: ORG,
		})
			.unregistered,
		["old-archive"],
	);
	console.log(
		"ok: registry completeness — an unregistered hosted repository (archived or not) fails and is named",
	);
}

// ── archived but current, and case drift, are violations ────────────────────
{
	const discovered = clone(observed).map((r) =>
		r.name === "l9-wip" ? { ...r, archived: true } : r,
	);
	const result = assessRegistryCompleteness({
		registry: historicalRegistry(),
		discovered,
		org: ORG,
	});
	assert.strictEqual(result.verdict, VERDICTS.INCOMPLETE);
	assert.deepStrictEqual(result.archivedCurrent, ["l9-wip"]);

	const drifted = clone(observed).map((r) =>
		r.name === "Gate_SDK" ? { ...r, name: "gate_sdk" } : r,
	);
	const drift = assessRegistryCompleteness({
		registry: historicalRegistry(),
		discovered: drifted,
		org: ORG,
	});
	assert.strictEqual(drift.verdict, VERDICTS.INCOMPLETE);
	assert.deepStrictEqual(drift.caseDrift, [
		{ hosted: "gate_sdk", registered: "Gate_SDK" },
	]);
	assert.deepStrictEqual(drift.notHosted, ["Gate_SDK"]);
	console.log(
		"ok: registry completeness — archived-but-current and case-only drift are violations",
	);
}

// ── registered but not listed is reported, not failed ───────────────────────
{
	const discovered = clone(observed).filter((r) => r.name !== "l9-goose");
	const result = assessRegistryCompleteness({
		registry: historicalRegistry(),
		discovered,
		org: ORG,
	});
	assert.strictEqual(result.verdict, VERDICTS.COMPLETE);
	assert.deepStrictEqual(result.notHosted, ["l9-goose"]);
	assert.match(
		renderCompletenessReport(result, ORG),
		/not returned by the listing/,
	);
	console.log(
		"ok: registry completeness — a registered repository the listing omits is noted, not failed",
	);
}

// ── no evidence is never complete ───────────────────────────────────────────
{
	for (const discovered of [null, undefined, [], [{ archived: false }]]) {
		const result = assessRegistryCompleteness({
			registry,
			discovered,
			org: ORG,
		});
		assert.strictEqual(
			result.verdict,
			VERDICTS.UNKNOWN,
			JSON.stringify(discovered),
		);
		assert.match(
			renderCompletenessReport(result, ORG),
			/never reported as complete/,
		);
	}
	const broken = clone(registry);
	broken.repositories.push(clone(broken.repositories[0]));
	assert.strictEqual(
		assessRegistryCompleteness({
			registry: broken,
			discovered: observed,
			org: ORG,
		}).verdict,
		VERDICTS.UNKNOWN,
		"a registry with a duplicated coordinate assesses nothing",
	);
	console.log(
		"ok: registry completeness — unreadable or empty listing and a malformed registry are UNKNOWN",
	);
}

// ── registry-completeness.yml: the real script ──────────────────────────────
(async () => {
	const WORKFLOW = path.join(
		root,
		".github/workflows/registry-completeness.yml",
	);
	const text = fs.readFileSync(WORKFLOW, "utf8");
	assert.match(text, /^ {4}environment: governance-distribution\s*$/m);
	assert.match(text, /github-token: \$\{\{ secrets\.GH_TOKEN \}\}/);
	assert.match(
		text,
		/^permissions:\n {2}contents: read\n/m,
		"read-only workflow",
	);
	const run = loadScriptModule(WORKFLOW, "registry-completeness-");
	const scopedRequire = makeScopedRequire(root);
	const drive = async (listFor) => {
		const calls = [];
		const github = {
			rest: { repos: { listForOrg: "listForOrg" } },
			paginate: async (fn, args) => {
				calls.push({ fn, args });
				return listFor();
			},
		};
		const core = makeCore();
		const raws = [];
		core.summary.addRaw = (s) => {
			raws.push(s);
			return core.summary;
		};
		const prev = process.cwd();
		process.chdir(root);
		try {
			await run(github, core, { sha: REVISION }, scopedRequire);
		} finally {
			process.chdir(prev);
		}
		return { calls, core, raws };
	};
	const ok = await drive(() => clone(observed));
	assert.deepStrictEqual(ok.core.failures, []);
	assert.deepStrictEqual(ok.calls[0].args, {
		org: ORG,
		type: "all",
		per_page: 100,
	});
	assert.match(ok.raws.join("\n"), /COMPLETE/);

	const extra = await drive(() => [
		...clone(observed),
		{ name: "New-Repo", archived: false },
	]);
	assert.strictEqual(extra.core.failures.length, 1);
	assert.match(extra.core.failures[0], /incomplete; unregistered: New-Repo/);

	const down = await drive(() => {
		const e = new Error("boom");
		e.status = 502;
		throw e;
	});
	assert.strictEqual(down.core.failures.length, 1);
	assert.match(down.core.failures[0], /unknown/);
	assert.match(down.core.failures[0], /organization listing/);
	console.log(
		"ok: registry-completeness.yml — real script fails on INCOMPLETE and UNKNOWN, passes on COMPLETE, read-only",
	);
})().catch((e) => {
	console.error(e);
	process.exit(1);
});
