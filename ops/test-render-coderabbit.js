"use strict";

/**
 * ops/render-coderabbit.js renders the organization `.coderabbit.yaml` from
 * policies/coderabbit/ (ADR docs/adr/0020-coderabbit-central-config-seeded.md).
 *
 * Covers: deterministic bytes and this repository's reference copy; the
 * exclusions-only contract (an include pattern throws, the bug class that
 * silenced CodeRabbit in cryptoxdog/IB-Odoo_19); fail-closed input handling;
 * that tests and docs stay reviewable; validity against CodeRabbit's published
 * schema (fetched with `curl -L`, validated by python3 jsonschema); and the
 * missing-only `coderabbit` seed category.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-render-coderabbit.js
 */
const assert = require("node:assert");
const { spawnSync } = require("node:child_process");

// python3 and curl are resolved from PATH on purpose: `make validate` prepends
// the .venv that `make setup` provisions with PyYAML and jsonschema
// (Repo.mk USE_VENV), and CI puts the pinned interpreter first. Python runs
// isolated (-I). No credential is in this suite's environment.
const tool = (cmd, args, opts) =>
	spawnSync(cmd, args, { encoding: "utf8", ...opts }); // NOSONAR S4036: runner PATH by design (see above)
const python = (args, opts) => tool("python3", ["-I", ...args], opts);
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {
	HEADER,
	FILTER_DIR,
	PATH_FILTER_FRAGMENTS,
	loadPathFilters,
	renderCoderabbit,
} = require("./render-coderabbit.js");
const {
	ALL_CATEGORIES,
	DEFAULT_CATEGORIES,
	MANAGED_SEED_PATHS,
	buildSeedPayload,
	classSeedPaths,
	selectSeedWrites,
	renderCoderabbit: reexported,
} = require("./build-seed-payload.js");
const { loadRepoClasses, resolveProfile } = require("./repo-class-profile.js");

const root = path.resolve(__dirname, "..");
process.chdir(root);

const SCHEMA_URL = "https://coderabbit.ai/integrations/schema.v2.json";
const DEST = ".coderabbit.yaml";

/** fs whose reads of the named repository paths are overridden. */
function fsWith(overrides) {
	return {
		readFileSync(p, ...rest) {
			if (Object.hasOwn(overrides, p)) {
				const v = overrides[p];
				if (v === null) {
					const err = new Error(`ENOENT: ${p}`);
					err.code = "ENOENT";
					throw err;
				}
				return Buffer.from(v, "utf8");
			}
			return fs.readFileSync(p, ...rest);
		},
	};
}

const fragmentPath = (name) => `${FILTER_DIR}/${name}.txt`;
const realFragment = (name) => fs.readFileSync(fragmentPath(name), "utf8");

// CodeRabbit glob semantics, as far as these patterns use them: `**/` is any
// directory prefix (including none), `**` any path, `*` within one segment.
function globToRegExp(glob) {
	let re = "";
	for (let i = 0; i < glob.length; i += 1) {
		if (glob.startsWith("**/", i)) {
			re += "(?:.*/)?";
			i += 2;
		} else if (glob.startsWith("**", i)) {
			re += ".*";
			i += 1;
		} else if (glob[i] === "*") {
			re += "[^/]*";
		} else {
			re += glob[i].replace(/[.+?^${}()|[\]\\]/g, String.raw`\$&`);
		}
	}
	return new RegExp(`^${re}$`);
}

// ── 1. render: deterministic, LF, one trailing newline, reference copy ──────
const out = renderCoderabbit({ fs });
assert.strictEqual(out, renderCoderabbit({ fs }), "render is deterministic");
assert.ok(!out.includes("\r"), "render is LF only");
assert.ok(
	out.endsWith("\n") && !out.endsWith("\n\n"),
	"exactly one trailing newline",
);
assert.strictEqual(
	reexported,
	renderCoderabbit,
	"build-seed-payload re-exports the renderer",
);
assert.strictEqual(
	fs.readFileSync(DEST, "utf8"),
	out,
	`${DEST} must equal the render: node ops/render-coderabbit.js > ${DEST}`,
);
// CRLF fragments render the same bytes.
const crlf = {};
crlf[HEADER] = fs.readFileSync(HEADER, "utf8").replaceAll("\n", "\r\n");
for (const n of PATH_FILTER_FRAGMENTS)
	crlf[fragmentPath(n)] = realFragment(n).replaceAll("\n", "\r\n");
assert.strictEqual(
	renderCoderabbit({ fs: fsWith(crlf) }),
	out,
	"CRLF input renders identical bytes",
);
console.log("ok: render is deterministic and equals .coderabbit.yaml");

// ── 2. contract on the parsed document ──────────────────────────────────────
const parsed = python(
	[
		"-c",
		"import sys, json, yaml; json.dump(yaml.safe_load(sys.stdin.read()), sys.stdout)",
	],
	{ input: out },
);
assert.strictEqual(
	parsed.status,
	0,
	`python3 yaml parse failed: ${parsed.stderr}`,
);
const doc = JSON.parse(parsed.stdout);
assert.strictEqual(doc.inheritance, true, "top-level inheritance: true");
const filters = doc.reviews.path_filters;
assert.deepStrictEqual(
	filters,
	loadPathFilters(fs),
	"parsed filters are the fragments in order",
);
assert.ok(filters.length > 0);
for (const p of filters) assert.match(p, /^!\S+$/, `${p} is an exclusion`);
assert.strictEqual(
	new Set(filters).size,
	filters.length,
	"no duplicate filter",
);
for (const p of [
	"!**/node_modules/**",
	"!**/.venv/**",
	"!**/__pycache__/**",
	"!**/dist/**",
	"!**/*.min.js",
]) {
	assert.ok(filters.includes(p), `required exclusion ${p}`);
}
// Generic only: the reviewed set below is the whole render. Every pattern is
// one depth-independent segment (a directory, a file name or a `*.ext`), so
// no repository-specific path or repository name can enter the central file;
// repository exclusions belong in that repository's own .coderabbit.yaml,
// which inheritance merges with this one.
const GENERIC_PATTERNS = [
	"!**/node_modules/**",
	"!**/.venv/**",
	"!**/venv/**",
	"!**/vendor/**",
	"!**/.tox/**",
	"!**/dist/**",
	"!**/build/**",
	"!**/__pycache__/**",
	"!**/*.pyc",
	"!**/*.egg-info/**",
	"!**/.mypy_cache/**",
	"!**/.pytest_cache/**",
	"!**/.ruff_cache/**",
	"!**/htmlcov/**",
	"!**/.coverage",
	"!**/*.min.js",
	"!**/*.min.css",
	"!**/*.map",
	"!**/package-lock.json",
	"!**/pnpm-lock.yaml",
	"!**/yarn.lock",
	"!**/uv.lock",
	"!**/poetry.lock",
	"!**/*.zip",
	"!**/*.tar.gz",
	"!**/*.tgz",
];
assert.deepStrictEqual(
	filters,
	GENERIC_PATTERNS,
	"the render carries exactly the reviewed generic exclusions",
);
const ONE_SEGMENT = /^!\*\*\/\*?[\w.-]+(?:\/\*\*)?$/;
for (const p of filters) {
	assert.match(
		p,
		ONE_SEGMENT,
		`${p} is one generic, depth-independent segment`,
	);
}
for (const name of [
	"plasticos",
	"erp_extracted_data",
	"odoo",
	"quantum-l9/",
	"cryptoxdog",
]) {
	assert.ok(
		!filters.some((p) => p.toLowerCase().includes(name)),
		`no repository-specific pattern (${name})`,
	);
}
// Depth-independent: every directory or name pattern starts with **/.
for (const p of filters)
	assert.ok(p.startsWith("!**/"), `${p} is depth-independent`);
const excluded = (file) =>
	filters.some((p) => globToRegExp(p.slice(1)).test(file));
for (const f of [
	"node_modules/a/b.js",
	"pkg/node_modules/x.js",
	"a/b/__pycache__/m.pyc",
	"web/dist/app.js",
	"s/app.min.js",
	".venv/lib/x.py",
]) {
	assert.ok(excluded(f), `${f} must be excluded`);
}
// Tests, docs and source stay reviewable.
for (const f of [
	"tests/test_app.py",
	"src/pkg/tests/test_unit.py",
	"test/app.test.js",
	"__tests__/x.spec.ts",
	"docs/README.md",
	"docs/adr/0001-x.md",
	"README.md",
	"src/app.py",
	"ops/render-coderabbit.js",
	".github/workflows/ci.yml",
]) {
	assert.ok(!excluded(f), `${f} must stay reviewable`);
}
console.log(
	"ok: inheritance true, path_filters exclusions only, tests and docs reviewable",
);

// ── 3. the include-pattern refusal and fail-closed inputs ───────────────────
for (const bad of ["src/**", "**/*.py", "  docs/**  "]) {
	assert.throws(
		() =>
			renderCoderabbit({
				fs: fsWith({
					[fragmentPath("generated")]: `${realFragment("generated")}${bad}\n`,
				}),
			}),
		/has no leading "!".*allowlist/,
		`include pattern ${JSON.stringify(bad)} must throw`,
	);
}
const fails = [
	[{ [HEADER]: null }, /missing or not a file/],
	[{ [fragmentPath("dependencies")]: null }, /missing or not a file/],
	[
		{ [fragmentPath("dependencies")]: "# only a comment\n" },
		/names no path filter/,
	],
	[
		{ [fragmentPath("generated")]: "!**/node_modules/**\n" },
		/listed in both dependencies and generated/,
	],
	[
		{ [fragmentPath("generated")]: "!**/a/**\n!**/a/**\n" },
		/listed in both generated and generated/,
	],
	[{ [fragmentPath("generated")]: "!\n" }, /not a single glob/],
	[{ [fragmentPath("generated")]: "!**/a b/**\n" }, /not a single glob/],
	[{ [fragmentPath("generated")]: "!!src/**\n" }, /starts with "!!"/],
	[{ [fragmentPath("generated")]: "!!**/*.py\n" }, /starts with "!!"/],
	[{ [fragmentPath("generated")]: "!**\n" }, /excludes every file/],
	[{ [fragmentPath("generated")]: "!*\n" }, /excludes every file/],
	[{ [fragmentPath("generated")]: "!**/*\n" }, /excludes every file/],
	[{ [fragmentPath("generated")]: "!**/**\n" }, /excludes every file/],
	[{ [fragmentPath("generated")]: "!/**\n" }, /excludes every file/],
	[
		{ [fragmentPath("generated")]: "!**/a/**\n# late\n!**/b/**\n" },
		/comments belong above/,
	],
	[
		{
			[HEADER]: fs
				.readFileSync(HEADER, "utf8")
				.replace(/^inheritance: true$/m, "inheritance: false"),
		},
		/inheritance: true/,
	],
	[
		{
			[HEADER]: fs.readFileSync(HEADER, "utf8").replace("{{path_filters}}", ""),
		},
		/exactly one \{\{path_filters\}\} \(found 0\)/,
	],
	[
		{
			[HEADER]: fs
				.readFileSync(HEADER, "utf8")
				.replace("{{path_filters}}", "- {{path_filters}}"),
		},
		/must stand alone/,
	],
];
for (const [over, re] of fails) {
	assert.throws(() => renderCoderabbit({ fs: fsWith(over) }), re);
}
assert.throws(() => renderCoderabbit({}), /requires fs/);
// The CLI fails closed too: a refused render exits 2 and prints nothing.
const cli = spawnSync(process.execPath, ["ops/render-coderabbit.js"], {
	encoding: "utf8",
});
assert.strictEqual(cli.status, 0, cli.stderr);
assert.strictEqual(cli.stdout, out, "CLI prints the render");
console.log(
	"ok: an include pattern, a double negation, a match-everything exclusion, a missing or malformed fragment, and a header without inheritance all throw",
);

// ── 4. schema validity (CodeRabbit schema.v2.json; the URL 301-redirects) ───
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "coderabbit-schema-"));
try {
	const schemaFile = path.join(tmp, "schema.v2.json");
	const curl = tool(
		"curl",
		[
			"-sSL",
			"--fail",
			"--retry",
			"3",
			"--max-time",
			"60",
			"-o",
			schemaFile,
			SCHEMA_URL,
		],
		{ encoding: "utf8" },
	);
	assert.strictEqual(
		curl.status,
		0,
		`could not fetch ${SCHEMA_URL} with curl -L (${curl.error?.message || curl.stderr}) — schema validity is unproven`,
	);
	const check = python(
		[
			"-c",
			[
				"import json, sys, yaml",
				"from jsonschema import Draft202012Validator",
				"schema = json.load(open(sys.argv[1]))",
				"Draft202012Validator.check_schema(schema)",
				"errors = sorted(Draft202012Validator(schema).iter_errors(yaml.safe_load(sys.stdin.read())), key=str)",
				"[print(e.json_path, e.message) for e in errors]",
				"sys.exit(1 if errors else 0)",
			].join("\n"),
			schemaFile,
		],
		{ input: out },
	);
	assert.strictEqual(
		check.status,
		0,
		`render is not valid against ${SCHEMA_URL}:\n${check.stdout}${check.stderr}`,
	);
	// The validator is live: a document the schema forbids is rejected.
	const negative = python(
		[
			"-c",
			"import json, sys\nfrom jsonschema import Draft202012Validator\nschema = json.load(open(sys.argv[1]))\nsys.exit(0 if list(Draft202012Validator(schema).iter_errors({'inheritance': 'yes', 'reviews': {'path_filters': [1]}})) else 1)",
			schemaFile,
		],
		{ encoding: "utf8" },
	);
	assert.strictEqual(
		negative.status,
		0,
		`schema validator accepted an invalid document: ${negative.stderr}`,
	);
} finally {
	fs.rmSync(tmp, { recursive: true, force: true });
}
console.log(`ok: render validates against ${SCHEMA_URL}`);

// ── 5. seed payload: the coderabbit category, missing-only ──────────────────
assert.ok(DEFAULT_CATEGORIES.includes("coderabbit"));
assert.ok(ALL_CATEGORIES.includes("coderabbit"));
assert.deepStrictEqual(buildSeedPayload({ fs, categories: ["coderabbit"] }), {
	[DEST]: out,
});
assert.ok(
	!MANAGED_SEED_PATHS.includes(DEST),
	"coderabbit is missing-only, never managed",
);
const existing = "reviews:\n  path_instructions: []\n";
const sel = selectSeedWrites(
	{ [DEST]: out },
	{ [DEST]: existing },
	{ managed: MANAGED_SEED_PATHS },
);
assert.deepStrictEqual(
	sel,
	{ writes: [], replaced: [], kept: [DEST] },
	"an existing file is kept",
);
assert.deepStrictEqual(
	selectSeedWrites(
		{ [DEST]: out },
		{ [DEST]: null },
		{ managed: MANAGED_SEED_PATHS },
	).writes,
	[DEST],
	"a missing file is written",
);
const classes = loadRepoClasses(fs);
const ACTIONS_ONLY = {
	uvLock: false,
	requirements: [],
	pep621: false,
	preCommit: false,
	npm: false,
};
for (const [name, cls] of Object.entries(classes.classes)) {
	const profile = resolveProfile(classes, name);
	const wantsDependabot = cls.seed_categories.includes("dependabot");
	assert.strictEqual(
		cls.seed_categories.includes("coderabbit"),
		wantsDependabot,
		`${name}: coderabbit is wired wherever dependabot is`,
	);
	const payload = buildSeedPayload({
		fs,
		profile,
		repoShape: ACTIONS_ONLY,
		repository: "Quantum-L9/x",
	});
	assert.strictEqual(
		DEST in payload,
		wantsDependabot,
		`${name}: seeds ${DEST} iff it seeds dependabot`,
	);
	if (wantsDependabot) assert.strictEqual(payload[DEST], out);
	assert.strictEqual(
		classSeedPaths({ fs, profile }).includes(DEST),
		wantsDependabot,
	);
}
console.log(
	"ok: coderabbit seeds .coderabbit.yaml missing-only, in every class that seeds dependabot",
);
