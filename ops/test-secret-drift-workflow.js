"use strict";

/**
 * Contract of .github/workflows/secret-drift.yml (Cursor-Governance #870, #892).
 *
 * The workflow reports drift between the org's Actions and Dependabot secrets
 * and Infisical. It must stay a read-only report:
 *   - triggers: workflow_dispatch plus one weekly schedule, nothing else;
 *   - job in the governance-distribution environment, App token minted with
 *     the pinned create-github-app-token, Infisical identity from
 *     L9_INFISICAL_CLIENT_ID / L9_INFISICAL_CLIENT_SECRET;
 *   - the frozen Cursor-Governance CLI, `--check` for both `--app actions`
 *     and `--app dependabot`, each with `--report-json`;
 *   - no secret is ever written (no `gh secret set`, no write permission);
 *   - any non-zero exit fails the job; the summary and the JSON artifact are
 *     produced even when it fails.
 *
 * Read literally, without a YAML dependency, like test-distribution-triggers.js.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-secret-drift-workflow.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const FILE = ".github/workflows/secret-drift.yml";
const text = fs.readFileSync(path.join(root, FILE), "utf8");
const code = text
	.split("\n")
	.filter((l) => !l.trim().startsWith("#"))
	.join("\n");

// ── Triggers: dispatch + one weekly cron, nothing else ──────────────────────
{
	const lines = text.split("\n");
	const start = lines.findIndex((l) => /^on:\s*$/.test(l));
	assert.ok(start !== -1, `${FILE}: no top-level on: block`);
	const block = [];
	for (const l of lines.slice(start + 1)) {
		if (/^\S/.test(l)) break;
		if (l.trim() && !l.trim().startsWith("#")) block.push(l);
	}
	const events = block.flatMap((l) => {
		const m = l.match(/^ {2}([A-Za-z_]+):/);
		return m ? [m[1]] : [];
	});
	assert.deepStrictEqual(
		events.sort(),
		["schedule", "workflow_dispatch"],
		`${FILE}: triggers must be workflow_dispatch and schedule only`,
	);
	const crons = block.filter((l) => /^\s+- cron:/.test(l));
	assert.strictEqual(crons.length, 1, `${FILE}: exactly one schedule`);
	const fields = crons[0].match(/cron:\s*"([^"]+)"/)[1].split(/\s+/);
	assert.strictEqual(fields.length, 5);
	assert.ok(
		fields[2] === "*" && fields[3] === "*" && /^[0-6]$/.test(fields[4]),
		`${FILE}: the schedule must be weekly (one day of week), got ${fields.join(" ")}`,
	);
	console.log("ok: triggers — workflow_dispatch plus one weekly schedule");
}

// ── Credentials: governance-distribution, App token, Infisical identity ─────
{
	assert.match(code, /\n {4}environment: governance-distribution\n/);
	assert.match(
		code,
		/uses: actions\/create-github-app-token@[0-9a-f]{40}/,
		`${FILE}: App token from the pinned create-github-app-token`,
	);
	assert.match(code, /app-id: \$\{\{ vars\.GOVERNANCE_APP_ID \}\}/);
	assert.match(
		code,
		/private-key: \$\{\{ secrets\.GOVERNANCE_APP_PRIVATE_KEY \}\}/,
	);
	assert.match(code, /permission-organization-secrets: read/);
	assert.doesNotMatch(
		code,
		/permission-[a-z-]+: write/,
		`${FILE}: no token may request a write permission`,
	);
	for (const name of ["L9_INFISICAL_CLIENT_ID", "L9_INFISICAL_CLIENT_SECRET"]) {
		assert.match(
			code,
			new RegExp(`${name}: \\$\\{\\{ secrets\\.${name} \\}\\}`),
			`${FILE}: ${name} comes from the environment secret`,
		);
	}
	assert.match(code, /\npermissions:\n {2}contents: read\n/);
	console.log(
		"ok: credentials — governance-distribution, governance App token (read), Infisical identity",
	);
}

// ── The frozen CLI, --check only, both stores ───────────────────────────────
{
	assert.match(code, /repository: Quantum-L9\/Cursor-Governance\n\s+ref: main\n/);
	assert.match(code, /persist-credentials: false/);
	const call = code.match(
		/python3 ops\/secrets\/sync_actions_secrets\.py \\\n([\s\S]*?)\n\s+rc=\$\?/,
	);
	assert.ok(call, `${FILE}: the sync_actions_secrets.py call is missing`);
	const args = call[1];
	for (const want of [
		/--org Quantum-L9/,
		/--app "\$app"/,
		/--check/,
		/--report-json "\$REPORT_DIR\/\$app\.json"/,
	]) {
		assert.match(args, want, `${FILE}: the CLI call misses ${want}`);
	}
	assert.match(code, /for app in actions dependabot; do/);
	assert.doesNotMatch(code, /gh secret set|secrets\/\S+ -X PUT|--method PUT/);
	assert.strictEqual(
		(code.match(/python3 \S*sync_actions_secrets\.py/g) || []).length,
		1,
		`${FILE}: the tool is invoked once, as --check; never a writing call`,
	);
	console.log(
		"ok: CLI — sync_actions_secrets.py --check for actions and dependabot, with --report-json, no writes",
	);
}

// ── Failure, summary and artifact ───────────────────────────────────────────
{
	assert.match(code, /\[ "\$rc" -eq 0 \] \|\| worst=1/);
	assert.match(code, /exit "\$worst"/);
	assert.match(code, /0\) echo "\$app: in sync"/);
	assert.match(code, /1\) echo "::error::\$app: drift or missing/);
	assert.match(code, /2\) echo "::error::\$app: plan or transport error/);
	const summary = code.match(
		/- name: Write job summary\n\s+if: always\(\)\n[\s\S]*?\$GITHUB_STEP_SUMMARY/,
	);
	assert.ok(summary, `${FILE}: the job summary must be written even on failure`);
	assert.match(code, /l9\.secret-drift\.v1/);
	assert.match(
		code,
		/- name: Upload reports\n\s+if: always\(\)\n\s+uses: actions\/upload-artifact@[0-9a-f]{40}/,
		`${FILE}: the JSON reports are uploaded even on failure`,
	);
	console.log(
		"ok: outcome — exit 1 or 2 fails the job; summary and JSON artifact always produced",
	);
}

console.log("\nall secret-drift workflow checks passed");
