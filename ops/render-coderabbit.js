"use strict";

/**
 * Render the organization's `.coderabbit.yaml` from this repository's
 * fragments. ADR: docs/adr/0020-coderabbit-central-config-seeded.md.
 *
 * One render, three uses: the organization central configuration (repository
 * Quantum-L9/coderabbit), the missing-only `coderabbit` seed category
 * (ops/build-seed-payload.js), and this repository's own `.coderabbit.yaml`.
 *
 * Pure: `fs` is injected (as in renderDependabot) and every path is
 * repository-relative, so every caller writes the same bytes on every runner.
 *
 * The contract it enforces is the one CodeRabbit's path-filter semantics make
 * fragile: `reviews.path_filters` is exclusions only. A pattern without a
 * leading `!` turns the list into an allowlist and CodeRabbit skips every file
 * the list does not name (the bug that silenced reviews in
 * cryptoxdog/IB-Odoo_19 until its PR #468). Such a pattern throws here; it is
 * never rendered.
 */

const FRAGMENT_DIR = "policies/coderabbit";
const HEADER = `${FRAGMENT_DIR}/header.yaml.tpl`;
const FILTER_DIR = `${FRAGMENT_DIR}/path-filters`;
const FILTERS_TOKEN = "{{path_filters}}";

// Named, never swept: a fragment added to the directory is not rendered until
// it is listed here, and a listed fragment that disappears fails the render.
const PATH_FILTER_FRAGMENTS = Object.freeze([
	"dependencies",
	"build-output",
	"generated",
]);

// The header must state inheritance at the top level: without it a consumer
// that keeps its own file never receives the central exclusions.
const INHERITANCE_RE = /^inheritance: true$/m;
// An exclusion: `!`, then a non-empty glob with no whitespace.
const EXCLUSION_RE = /^!\S+$/;
// `!!glob` is a double negation: a glob engine may read it as an include,
// which would turn the list into an allowlist. Refused.
const DOUBLE_NEGATION_RE = /^!!/;
// A glob made only of `*` and `/` (`!**`, `!*`, `!**/*`, `!**/**`) excludes
// every file and silences review entirely. Refused.
const MATCH_ALL_RE = /^![*/]+$/;

function readRequired(fs, path) {
	try {
		return fs.readFileSync(path).toString("utf8").replaceAll("\r\n", "\n");
	} catch (err) {
		throw new Error(
			`seed source ${path} is missing or not a file (${err.code || err.message}) — refusing to render .coderabbit.yaml`,
		);
	}
}

function trimTrailingEmpty(lines) {
	const out = [...lines];
	while (out.length && out.at(-1) === "") out.pop();
	return out;
}

/**
 * Read one path-filter fragment: one pattern per line, `#` comment lines and
 * blank lines ignored. Every pattern must be an exclusion.
 * @returns {{comments: string[], patterns: string[]}}
 */
function readFilterFragment(fs, name) {
	const path = `${FILTER_DIR}/${name}.txt`;
	const comments = [];
	const patterns = [];
	readRequired(fs, path)
		.split("\n")
		.forEach((raw, i) => {
			const line = raw.trim();
			if (!line) return;
			if (line.startsWith("#")) {
				if (patterns.length) {
					throw new Error(
						`${path}:${i + 1}: comments belong above the patterns, not between them`,
					);
				}
				comments.push(line);
				return;
			}
			if (!line.startsWith("!")) {
				throw new Error(
					`${path}:${i + 1}: path filter ${JSON.stringify(line)} has no leading "!" — ` +
						"an include pattern turns reviews.path_filters into an allowlist and CodeRabbit " +
						"skips every file it does not name; path_filters is exclusions only",
				);
			}
			if (!EXCLUSION_RE.test(line)) {
				throw new Error(
					`${path}:${i + 1}: path filter ${JSON.stringify(line)} is not a single glob after "!"`,
				);
			}
			if (DOUBLE_NEGATION_RE.test(line)) {
				throw new Error(
					`${path}:${i + 1}: path filter ${JSON.stringify(line)} starts with "!!" — ` +
						"a double negation may be read as an include and turn path_filters into an allowlist",
				);
			}
			if (MATCH_ALL_RE.test(line)) {
				throw new Error(
					`${path}:${i + 1}: path filter ${JSON.stringify(line)} excludes every file — ` +
						"it would silence CodeRabbit review entirely",
				);
			}
			patterns.push(line);
		});
	if (!patterns.length) {
		throw new Error(`${path} names no path filter`);
	}
	return { comments, patterns };
}

/**
 * Every listed fragment, in render order. A pattern listed twice, in one
 * fragment or across two, throws.
 * @returns {{name: string, comments: string[], patterns: string[]}[]}
 */
function loadFragments(fs) {
	const seen = new Map();
	return PATH_FILTER_FRAGMENTS.map((name) => {
		const fragment = readFilterFragment(fs, name);
		for (const p of fragment.patterns) {
			if (seen.has(p)) {
				throw new Error(
					`path filter ${JSON.stringify(p)} is listed in both ${seen.get(p)} and ${name}`,
				);
			}
			seen.set(p, name);
		}
		return { name, ...fragment };
	});
}

/** The exclusions in render order. */
function loadPathFilters(fs) {
	return loadFragments(fs).flatMap((f) => f.patterns);
}

/**
 * @param {object} o
 * @param {typeof import('fs')} o.fs
 * @returns {string} .coderabbit.yaml bytes: LF, exactly one trailing newline
 */
function renderCoderabbit({ fs } = {}) {
	if (!fs) throw new Error("renderCoderabbit requires fs");
	const header = trimTrailingEmpty(readRequired(fs, HEADER).split("\n"));
	if (!INHERITANCE_RE.test(header.join("\n"))) {
		throw new Error(
			`${HEADER} must set top-level "inheritance: true" — refusing to render .coderabbit.yaml`,
		);
	}
	const tokens = header.filter((l) => l.includes(FILTERS_TOKEN));
	if (tokens.length !== 1) {
		throw new Error(
			`${HEADER} must carry exactly one ${FILTERS_TOKEN} (found ${tokens.length})`,
		);
	}
	if (tokens[0].trim() !== FILTERS_TOKEN) {
		throw new Error(`${HEADER}: ${FILTERS_TOKEN} must stand alone on its line`);
	}
	const indent = tokens[0].slice(0, tokens[0].indexOf(FILTERS_TOKEN));
	// Fragment by fragment, so its comment travels with its patterns. Patterns
	// are double-quoted: a bare leading `!` is a YAML tag, not a string.
	const block = loadFragments(fs).flatMap(({ comments, patterns }) => [
		...comments.map((c) => `${indent}${c}`),
		...patterns.map((p) => `${indent}- ${JSON.stringify(p)}`),
	]);
	const lines = header.flatMap((l) => (l === tokens[0] ? block : [l]));
	return `${lines.join("\n")}\n`;
}

/**
 * CLI: `node ops/render-coderabbit.js` prints the render. It is this
 * repository's `.coderabbit.yaml` and the central Quantum-L9/coderabbit file:
 *   node ops/render-coderabbit.js > .coderabbit.yaml
 */
if (require.main === module) {
	const fs = require("node:fs");
	const path = require("node:path");
	try {
		process.chdir(path.resolve(__dirname, ".."));
		process.stdout.write(renderCoderabbit({ fs }));
	} catch (err) {
		console.error(`❌ ERROR: ${err.message}`);
		process.exit(2);
	}
}

module.exports = {
	FRAGMENT_DIR,
	HEADER,
	FILTER_DIR,
	PATH_FILTER_FRAGMENTS,
	loadPathFilters,
	renderCoderabbit,
};
