"use strict";

/**
 * ops/fetch-composer.sh authenticates a private composer fetch only through
 * git's environment. The token is not an argument and not part of the URL.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-fetch-composer.js
 */
const assert = require("node:assert");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const token = "test-read-token-value";
const basic = Buffer.from(`x-access-token:${token}`).toString("base64");

function run(withToken) {
	const dir = fs.mkdtempSync(path.join(os.tmpdir(), "fetch-composer-"));
	const bin = path.join(dir, "bin");
	const dest = path.join(dir, "dest");
	const log = path.join(dir, "git.log");
	fs.mkdirSync(bin);
	fs.writeFileSync(
		path.join(bin, "git"),
		`#!/bin/sh
{
  printf '%s\\n' "$*"
  printf 'ENV %s\\n' "\${GIT_CONFIG_VALUE_0:-}"
} >> "$GIT_LOG"
if [ "$1" = "-C" ]; then
  shift 2
fi
case "$1" in
  init|fetch) exit 0 ;;
  show) printf 'composer\\n' ;;
  *) exit 1 ;;
esac
`,
	);
	fs.chmodSync(path.join(bin, "git"), 0o755);
	const env = {
		PATH: `${bin}:${process.env.PATH}`,
		HOME: process.env.HOME,
		TMPDIR: process.env.TMPDIR || "/tmp",
		GIT_LOG: log,
	};
	if (withToken) env.L9_GITHUB_READ_TOKEN = token;
	const result = spawnSync("bash", ["ops/fetch-composer.sh", dest], {
		cwd: root,
		env,
		encoding: "utf8",
	});
	const recorded = fs.readFileSync(log, "utf8");
	fs.rmSync(dir, { recursive: true, force: true });
	return { result, recorded };
}

const authed = run(true);
assert.strictEqual(
	authed.result.status,
	0,
	authed.result.stderr || authed.result.stdout,
);
const argv = authed.recorded
	.split("\n")
	.filter((line) => !line.startsWith("ENV "))
	.join("\n");
assert.ok(!argv.includes(token), "the token must not appear in git's arguments");
assert.ok(
	argv.includes("https://github.com/Quantum-L9/Cursor-Governance.git"),
	"the fetch URL stays unauthenticated",
);
assert.ok(
	authed.recorded.includes(`ENV AUTHORIZATION: basic ${basic}`),
	"git receives the token as an Authorization header",
);
assert.ok(
	!argv.includes(basic),
	"the encoded credential must not appear in git's arguments",
);
const header = authed.result.stdout + authed.result.stderr;
assert.ok(!header.includes(token), "the token must not be printed");

const anon = run(false);
assert.strictEqual(anon.result.status, 0, anon.result.stderr || anon.result.stdout);
assert.ok(
	!anon.recorded.includes("AUTHORIZATION"),
	"an unset token does not send an Authorization header on the command line",
);

console.log(
	"ok: fetch-composer.sh keeps L9_GITHUB_READ_TOKEN out of argv and the remote URL",
);
