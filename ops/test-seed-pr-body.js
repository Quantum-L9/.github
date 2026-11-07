#!/usr/bin/env node
"use strict";

// Seed and Manual Update PR bodies are the org PR template rendered by the one
// renderer (Cursor-Governance ops/scripts/compose_pr_body.py, at the commit
// governance-pr.yml pins). This suite proves it twice:
//   1. ops/seed-pr-body.js in isolation: the commit message the composer reads,
//      and renderSeedPrBody's fail-closed checks (fake exec).
//   2. End to end with the REAL pinned composer: a seed commit on a local
//      repository is fetched and composed from the UNCHANGED org template; the
//      body must be complete — no template placeholder, no field needing an
//      author, a measured Reviewer focus — and pass the org PR gates
//      (governance-pr.yml) strictly, with nothing written in by the seeder.
//
// SEED_COMPOSER_ROOT names a checkout holding ops/scripts/compose_pr_body.py
// at the pin; ops/validate-starters.sh provides it (CI: actions/checkout,
// locally: ops/fetch-composer.sh). Its absence is a failure, never a skip.

const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const {
	TEMPLATE_PATH,
	seedCommitMessage,
	seedNarrative,
	syncNarrative,
	renderSeedPrBody,
	composerEnv,
} = require("./seed-pr-body.js");
const { loadGovernanceGates } = require("./workflow-script-harness.js");

const root = path.resolve(__dirname, "..");
const template = fs.readFileSync(path.join(root, TEMPLATE_PATH), "utf8");
const SOURCE = "0123456789abcdef0123456789abcdef01234567";
const profile = {
	name: "default",
	resolved_from: "fallback",
	inherit: ["CODE_OF_CONDUCT.md"],
};

// ── 1. Unit ──────────────────────────────────────────────────────────────────
{
	const story = seedNarrative({
		added: ["SECURITY.md"],
		profile,
		branch: "chore/auto-seed-governance",
		sourceSha: SOURCE,
		seeder: "auto-seed-new-repo.yml",
	});
	assert.deepStrictEqual(
		Object.keys(story).sort((a, b) => a.localeCompare(b)),
		["details", "problem"],
		"the seeder writes only the commit message",
	);
	const message = seedCommitMessage({
		subject: "ci(governance): seed 1 org template file(s)",
		problem: story.problem,
		details: story.details,
		trailers: ["Seed-Payload: sha256:x"],
	});
	const paras = message.split("\n\n");
	assert.strictEqual(paras[0], "ci(governance): seed 1 org template file(s)");
	assert.strictEqual(
		paras[1],
		story.problem,
		"the Problem paragraph comes first, where the composer reads it",
	);
	assert.deepStrictEqual(
		paras.slice(2, -1),
		story.details,
		"the Fix details follow",
	);
	assert.strictEqual(paras.at(-1), "Seed-Payload: sha256:x", "trailers last");
	assert.throws(
		() => seedCommitMessage({ subject: "s", problem: "Seed-Payload: x" }),
		/must not read as a trailer/,
	);
	assert.throws(
		() =>
			seedCommitMessage({ subject: "s", problem: "p", details: ["Key: v"] }),
		/must not read as trailers/,
	);
	assert.throws(
		() => seedCommitMessage({ subject: "a\nb", problem: "p" }),
		TypeError,
	);
	assert.throws(
		() =>
			seedNarrative({
				added: [],
				profile,
				branch: "b",
				sourceSha: "s",
				seeder: "x",
			}),
		/at least one path/,
	);
	assert.throws(
		() => syncNarrative({ plan: [], profile, branch: "b", sourceSha: "s" }),
		/at least one path/,
	);
	const restoreOnly = seedNarrative({
		restored: [".github/dependabot.yml"],
		profile,
		branch: "b",
		sourceSha: SOURCE,
		seeder: "x.yml",
	});
	assert.match(
		restoreOnly.details[0],
		/^Restores 1 managed file\(s\)/,
		"a restore-only seed says so",
	);
	assert.doesNotMatch(
		restoreOnly.details[0],
		/Adds/,
		"a restore-only seed claims no added file",
	);
	console.log(
		"ok: the seed commit message carries the Problem and Fix details; nothing else is written",
	);
}

// The composer runs the target repository's own validator, so its environment
// is an allowlist: no seed token, git auth header, github-script input or
// runner token reaches it.
{
	const env = composerEnv({
		PATH: "/usr/bin",
		HOME: "/home/runner",
		LC_ALL: "C.UTF-8",
		pythonLocation: "/py",
		SEED_GIT_TOKEN: "tok",
		GH_TOKEN: "tok",
		GITHUB_TOKEN: "tok",
		"INPUT_GITHUB-TOKEN": "tok",
		ACTIONS_RUNTIME_TOKEN: "tok",
		ACTIONS_ID_TOKEN_REQUEST_TOKEN: "tok",
		GIT_CONFIG_COUNT: "1",
		GIT_CONFIG_KEY_0: "http.extraheader",
		GIT_CONFIG_VALUE_0: "AUTHORIZATION: basic x",
	});
	assert.deepStrictEqual(env, {
		PATH: "/usr/bin",
		HOME: "/home/runner",
		LC_ALL: "C.UTF-8",
		pythonLocation: "/py",
		GIT_TERMINAL_PROMPT: "0",
	});
	assert.ok(!Object.values(env).includes("tok"), "no credential survives");
	console.log(
		"ok: the composer environment is an allowlist that carries no credential",
	);
}

// renderSeedPrBody against a scripted exec: what it runs, and when it refuses.
{
	const composerRoot = fs.mkdtempSync(path.join(os.tmpdir(), "fake-composer-"));
	fs.mkdirSync(path.join(composerRoot, "ops/scripts"), { recursive: true });
	fs.writeFileSync(
		path.join(composerRoot, "ops/scripts/compose_pr_body.py"),
		"# stub\n",
	);
	const scripted = ({ fetched = "head", parent = "base", needs = [] } = {}) => {
		const calls = [];
		const exec = (cmd, args, opts) => {
			calls.push({ cmd, args, env: opts.env });
			if (cmd === "git" && args.includes("rev-parse"))
				return args.at(-1) === "HEAD^" ? `${parent}\n` : `${fetched}\n`;
			if (cmd === "python3") {
				const handoff = args[args.indexOf("--handoff") + 1];
				fs.writeFileSync(handoff, JSON.stringify({ needs_completion: needs }));
				return "BODY\n";
			}
			return "";
		};
		return { exec, calls };
	};
	const base = {
		fs,
		remoteUrl: "https://github.com/o/r.git",
		branch: "seed",
		headSha: "head",
		baseSha: "base",
		template: "T",
		composerRoot,
		token: "tok-123",
	};

	const s = scripted();
	assert.strictEqual(
		renderSeedPrBody({ ...base, exec: s.exec }).body,
		"BODY\n",
	);
	for (const c of s.calls) {
		assert.ok(
			!c.args.join(" ").includes("tok-123"),
			"the token never appears in argv",
		);
	}
	const fetch = s.calls.find((c) => c.args.includes("fetch"));
	assert.match(
		fetch.env.GIT_CONFIG_VALUE_0,
		/^AUTHORIZATION: basic /,
		"the token travels as an HTTP header via env",
	);
	assert.ok(fetch.args.includes("--depth=2"));
	const py = s.calls.find((c) => c.cmd === "python3");
	assert.ok(
		py.args.includes("--remote") && py.args.includes("--template"),
		"composed remotely from the prepared template",
	);
	for (const k of [
		"GIT_CONFIG_COUNT",
		"GIT_CONFIG_KEY_0",
		"GIT_CONFIG_VALUE_0",
	]) {
		assert.ok(
			!(k in py.env),
			`the composer does not get the git auth header (${k})`,
		);
	}

	assert.throws(
		() =>
			renderSeedPrBody({ ...base, exec: scripted({ fetched: "other" }).exec }),
		/not the seed commit/,
	);
	assert.throws(
		() =>
			renderSeedPrBody({
				...base,
				exec: scripted({ parent: "elsewhere" }).exec,
			}),
		/is not built on/,
	);
	assert.throws(
		() =>
			renderSeedPrBody({
				...base,
				exec: scripted({ needs: ["reviewer_focus: x"] }).exec,
			}),
		/incomplete: reviewer_focus/,
	);
	assert.throws(
		() =>
			renderSeedPrBody({
				...base,
				remoteUrl: "https://x:y@github.com/o/r.git",
				exec: scripted().exec,
			}),
		/must not carry credentials/,
	);
	assert.throws(
		() =>
			renderSeedPrBody({
				...base,
				composerRoot: "/nonexistent",
				exec: scripted().exec,
			}),
		/composer not found/,
	);
	fs.rmSync(composerRoot, { recursive: true });
	console.log(
		"ok: renderSeedPrBody fetches by header, checks the head and its base, and refuses an incomplete body",
	);
}

// ── 2. End to end with the real pinned composer ──────────────────────────────
const composerRoot = process.env.SEED_COMPOSER_ROOT;
if (!composerRoot) {
	console.error(
		"❌ SEED_COMPOSER_ROOT is unset — run via ops/validate-starters.sh, which fetches the pinned composer",
	);
	process.exit(1);
}

// The fixture's git is the runner image's, the same binary the seed workflows
// call; this test builds throwaway local repositories with it and never runs
// with a credential in its environment.
const sh = (cwd, ...args) =>
	execFileSync(
		"git",
		[
			"-c",
			"user.name=seeder",
			"-c",
			"user.email=seeder@example.invalid",
			"-c",
			"init.defaultBranch=main",
			...args,
		],
		{ cwd, encoding: "utf8" },
	).trim(); // NOSONAR S4036: test fixture, runner PATH (see above)

/** A bare "remote" with a default branch and a seed branch one commit ahead. */
function seedRemote({ files, message, branch, existing = {} }) {
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), "seed-remote-"));
	const work = path.join(dir, "work");
	const bare = path.join(dir, "remote.git");
	fs.mkdirSync(work);
	sh(work, "init", "-q");
	fs.writeFileSync(path.join(work, "README.md"), "# consumer\n");
	for (const [p, text] of Object.entries(existing)) {
		fs.mkdirSync(path.dirname(path.join(work, p)), { recursive: true });
		fs.writeFileSync(path.join(work, p), text);
	}
	sh(work, "add", "-A");
	sh(work, "commit", "-q", "-m", "init");
	const baseSha = sh(work, "rev-parse", "HEAD");
	sh(work, "checkout", "-q", "-b", branch);
	for (const [p, text] of Object.entries(files)) {
		fs.mkdirSync(path.dirname(path.join(work, p)), { recursive: true });
		fs.writeFileSync(path.join(work, p), text);
	}
	sh(work, "add", "-A");
	sh(work, "commit", "-q", "-m", message);
	const headSha = sh(work, "rev-parse", "HEAD");
	sh(dir, "clone", "-q", "--bare", work, bare);
	return { dir, remoteUrl: `file://${bare}`, baseSha, headSha };
}

// Every placeholder the canonical template carries, and every marker by which
// a composer once left a field to an author.
const PLACEHOLDERS = [
	"_pending —",
	"paste the error / failing output here",
	"<!-- What you changed to make the problem above go away.",
	"<!-- Where to look hardest.",
	"<!-- One-sentence description of what this PR does. -->",
	"_Unresolved —",
	"_unresolved —",
	"Rewrite it before review",
	"author ticks one",
	"reviewer ticks it or states why not",
];

async function assertComplete(label, rendered, paths) {
	const { body, handoff } = rendered;
	for (const p of PLACEHOLDERS)
		assert.ok(
			!body.includes(p),
			`${label}: placeholder left in the body: ${p}`,
		);
	assert.deepStrictEqual(
		handoff.needs_completion,
		[],
		`${label}: a field still needs an author`,
	);
	for (const p of paths)
		assert.ok(
			body.includes(path.basename(p)),
			`${label}: Files touched misses ${p}`,
		);
	assert.match(
		body,
		/^- \[x\] CI \/ governance change$/m,
		`${label}: type ticked from the ci commit`,
	);
	assert.match(
		body,
		/<!-- FILES-TOUCHED:START -->\n\*\*\d+ files?\*\*/,
		`${label}: Files touched is rendered`,
	);
	assert.match(
		body,
		/<!-- REVIEWER-FOCUS:START -->\n_Ranked from the measured diff/,
		`${label}: Reviewer focus is composed`,
	);
	for (const [field, entry] of Object.entries(handoff.fields)) {
		assert.notStrictEqual(
			entry.status,
			"needs_author",
			`${label}: ${field} is left for an author`,
		);
	}
	const gates = loadGovernanceGates(root);
	assert.deepStrictEqual(
		await gates(body),
		[],
		`${label}: the composed body fails the org PR gates`,
	);
}

(async () => {
	// Auto-seed: missing files only.
	{
		const files = {
			"SECURITY.md": "# Security\n",
			".github/ISSUE_TEMPLATE/ci-failure.yml": "name: CI\n",
		};
		const branch = "chore/auto-seed-governance";
		const story = seedNarrative({
			added: Object.keys(files),
			profile,
			branch,
			sourceSha: SOURCE,
			seeder: "auto-seed-new-repo.yml",
		});
		const message = seedCommitMessage({
			subject: "ci(governance): auto-seed 2 org template file(s)",
			problem: story.problem,
			details: story.details,
			trailers: [`Seed-Payload: sha256:${"0".repeat(64)}`],
		});
		const r = seedRemote({ files, message, branch });
		const rendered = renderSeedPrBody({
			exec: execFileSync,
			fs,
			remoteUrl: r.remoteUrl,
			branch,
			headSha: r.headSha,
			baseSha: r.baseSha,
			template,
			composerRoot,
		});
		await assertComplete("auto-seed", rendered, Object.keys(files));
		assert.ok(
			rendered.body.includes(story.problem),
			"auto-seed: Problem is the commit paragraph",
		);
		assert.ok(
			rendered.body.includes(`Quantum-L9/.github@${SOURCE}`),
			"auto-seed: Fix carries the commit details",
		);
		assert.ok(
			rendered.body.includes(story.details[0]),
			"auto-seed: Fix starts from the first detail paragraph",
		);
		fs.rmSync(r.dir, { recursive: true });
		console.log(
			"ok: auto-seed PR body composed by the pinned composer is complete and passes the org PR gates",
		);
	}

	// Auto-seed restore of a drifted managed file.
	{
		const branch = "chore/auto-seed-governance";
		const files = { ".github/dependabot.yml": "version: 2\nupdates: []\n" };
		const story = seedNarrative({
			added: [],
			restored: [".github/dependabot.yml"],
			profile,
			branch,
			sourceSha: SOURCE,
			seeder: "auto-seed-new-repo.yml",
		});
		const message = seedCommitMessage({
			subject: "ci(governance): auto-seed 1 org template file(s)",
			problem: story.problem,
			details: story.details,
			trailers: [`Seed-Payload: sha256:${"1".repeat(64)}`],
		});
		const r = seedRemote({
			files,
			message,
			branch,
			existing: { ".github/dependabot.yml": "version: 2\n" },
		});
		const rendered = renderSeedPrBody({
			exec: execFileSync,
			fs,
			remoteUrl: r.remoteUrl,
			branch,
			headSha: r.headSha,
			baseSha: r.baseSha,
			template,
			composerRoot,
		});
		await assertComplete("restore", rendered, Object.keys(files));
		fs.rmSync(r.dir, { recursive: true });
		console.log("ok: a managed-file restore renders complete");
	}

	// Manual Update (continuous-sync).
	{
		const branch = "chore/governance-sync";
		const files = { ".github/CODEOWNERS": "* @org/owners\n" };
		const plan = [
			{
				path: ".github/CODEOWNERS",
				why: "restore",
				action: "write",
				existed: true,
			},
		];
		const story = syncNarrative({ plan, profile, branch, sourceSha: SOURCE });
		const message = seedCommitMessage({
			subject: "ci(governance): sync 1 org-managed file(s)",
			problem: story.problem,
			details: story.details,
			trailers: ["Sync-Restore: .github/CODEOWNERS"],
		});
		const r = seedRemote({
			files,
			message,
			branch,
			existing: { ".github/CODEOWNERS": "* @someone\n" },
		});
		const rendered = renderSeedPrBody({
			exec: execFileSync,
			fs,
			remoteUrl: r.remoteUrl,
			branch,
			headSha: r.headSha,
			baseSha: r.baseSha,
			template,
			composerRoot,
		});
		await assertComplete("sync", rendered, Object.keys(files));
		fs.rmSync(r.dir, { recursive: true });
		console.log("ok: a Manual Update PR body renders complete");
	}
})().catch((e) => {
	console.error(e);
	process.exit(1);
});
