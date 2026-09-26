"use strict";

/**
 * Runs the real `script:` bodies of the PR-body workflows (pr-gates.yml,
 * governance-pr.yml, pr-files.yml) against fixture bodies.
 *
 * The friction this pins: `make pr` (Cursor-Governance compose_pr_body.py)
 * wrote unchecked gates as "— n/a — not this change", and the old reason
 * regex /(sep)\s*\S{4,}/ needed a 4+ character WORD straight after the
 * separator, so every composed body failed six Gate lines; "— no IAM change"
 * failed the same way for humans. governance-pr kept the template's own
 * "paste the error" fence in Problem, so an untouched template passed. Each
 * of those cases fails against the pre-fix workflows.
 *
 * pr-files keys a rename as "old -> new" and matches declarations exactly.
 * That stays strict: the producer (make pr) declares the canonical row key,
 * and a declaration naming only one endpoint is asserted to fail.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-pr-body-gates.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { extractScript, makeCore } = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const wf = (name) => path.join(root, ".github", "workflows", name);

/**
 * Load a script body, substituting the `${{ }}` expressions the runner would.
 * `rewrites` are [RegExp, replacement] pairs applied after, used to point the
 * runner's scratch paths at a private temp directory.
 */
function load(file, expressions = {}, rewrites = []) {
	let body = extractScript(file);
	for (const [expr, value] of Object.entries(expressions))
		body = body.split(expr).join(value);
	for (const [pattern, value] of rewrites) body = body.replace(pattern, value);
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), "pr-body-gates-"));
	const mod = path.join(dir, `${path.basename(file, ".yml")}.script.js`);
	fs.writeFileSync(
		mod,
		`'use strict';\nmodule.exports = async (github, core, context, require) => {\n${body}\n};\n`,
	);
	try {
		return require(mod);
	} finally {
		fs.rmSync(dir, { recursive: true, force: true });
	}
}

const makeGateCore = () => {
	const core = makeCore();
	const summary = {
		addHeading: () => summary,
		addList: () => summary,
		write: async () => summary,
	};
	return { ...core, summary, notice() {} };
};

const context = (body) => ({
	payload: { pull_request: { body, number: 1 } },
	repo: { owner: "o", repo: "r" },
});

const GATE_WORKFLOWS = [
	{ name: "pr-gates.yml", run: load(wf("pr-gates.yml")) },
	{
		name: "governance-pr.yml",
		run: load(wf("governance-pr.yml"), { "${{ inputs.strict }}": "true" }),
	},
];

const body = (
	gates,
	problem = "The composed body failed the org Gate reason check on every line.",
) => `
## Problem

${problem}

Closes #

## Risk

- [ ] Low — additive — n/a — not this change
- [x] Medium — touches shared code, config, or a public interface

## Evidence

\`\`\`
gate-receipt.json present
\`\`\`

## Gates

${gates.map((g) => `- [ ] ${g}`).join("\n")}

## Reviewer focus
`;

async function gateFailures(run, text) {
	const core = makeGateCore();
	await run({}, core, context(text), require);
	return core.failures;
}

async function main() {
	const reasoned = [
		"Regression test added — n/a — not this change",
		"Regression test added — unverified — make pr cannot measure this gate; reviewer ticks it",
		"New IAM / workflow permissions are least privilege — no IAM change",
		"Public interface change is documented — n/a — because no public interface change",
		"Observability exists (n/a: docs only)",
	];
	const unreasoned = [
		"Regression test added",
		"Third-party actions pinned — n/a",
	];

	for (const { name, run } of GATE_WORKFLOWS) {
		assert.deepStrictEqual(
			await gateFailures(run, body(reasoned)),
			[],
			`${name}: reasoned gates must pass`,
		);
		for (const gate of unreasoned) {
			assert.strictEqual(
				(await gateFailures(run, body([gate]))).length,
				1,
				`${name}: "${gate}" states no reason and must fail`,
			);
		}
		const untouched = body(
			reasoned,
			"```\npaste the error / failing output here, or delete this block and describe the gap\n```",
		);
		assert.strictEqual(
			(await gateFailures(run, untouched)).length,
			1,
			`${name}: the template's own placeholder is not a Problem`,
		);
	}

	// pr-files: a rename declared by its new path, by its row key, or by make
	// pr's "(renamed: `old -> new`)" form is declared. The script reads the
	// diff the preceding `run:` step wrote to the runner's scratch dir; point
	// it at a private temp dir so the suite never writes a shared path.
	const scratch = fs.mkdtempSync(path.join(os.tmpdir(), "pr-files-"));
	const run = load(wf("pr-files.yml"), {}, [
		[
			/(["'])\/tmp\/(changed|shortstat)\.txt\1/g,
			(_m, q, n) => q + path.join(scratch, n + ".txt") + q,
		],
	]);
	fs.writeFileSync(
		path.join(scratch, "changed.txt"),
		"M\tsrc/a.py\nR100\told/name.py\tnew/name.py\n",
	);
	fs.writeFileSync(
		path.join(scratch, "shortstat.txt"),
		" 2 files changed, 3 insertions(+)\n",
	);
	try {
		for (const declared of [
			"`old/name.py -> new/name.py` — moved",
			"`new/name.py` — moved (renamed: `old/name.py -> new/name.py`)",
		]) {
			const text = `## Changes by intent\n\n- \`src/a.py\` — edit\n- ${declared}\n\n## Files touched\n\n<!-- FILES-TOUCHED:START -->\n_pending_\n<!-- FILES-TOUCHED:END -->\n`;
			const core = makeGateCore();
			let updated = "";
			const github = {
				rest: {
					pulls: {
						update: async ({ body: b }) => {
							updated = b;
						},
					},
				},
			};
			await run(github, core, context(text), require);
			assert.deepStrictEqual(
				core.failures,
				[],
				`pr-files: rename declared as ${declared} must pass`,
			);
			assert.ok(
				updated.includes("FILES-TOUCHED:START"),
				`pr-files: ${declared} still gets the file list`,
			);
		}
		// The matcher stays strict: a rename is declared by its row key, not by
		// either endpoint. make pr emits the key; see the regression above.
		const endpointOnly = makeGateCore();
		await run(
			{ rest: { pulls: { update: async () => {} } } },
			endpointOnly,
			context(
				"## Changes by intent\n\n- `src/a.py` — edit\n- `new/name.py` — moved\n",
			),
			require,
		);
		assert.strictEqual(
			endpointOnly.failures.length,
			1,
			"pr-files: a rename declared by its new path alone still fails",
		);
		const core = makeGateCore();
		await run(
			{ rest: { pulls: { update: async () => {} } } },
			core,
			context("## Changes by intent\n\n- `src/a.py` — edit\n"),
			require,
		);
		assert.strictEqual(
			core.failures.length,
			1,
			"pr-files: an undeclared rename still fails",
		);
	} finally {
		fs.rmSync(scratch, { recursive: true, force: true });
	}

	console.log(
		"ok — pr-gates, governance-pr and pr-files accept make pr bodies and still reject unreasoned gates",
	);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
