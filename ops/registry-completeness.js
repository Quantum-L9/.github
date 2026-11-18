"use strict";

/**
 * Organization completeness of semantics/repository_registry.yaml (ADR-040).
 *
 * Since v3.43.0 every repository the Quantum-L9 organization hosts, archived
 * and forked ones included, must be registered. This module compares the live
 * organization listing with the registry and says whether that holds. It is
 * observational (L9-VALIDATION-001): it never writes the registry, never opens
 * a pull request and never admits anything. Admission stays the owner's merge
 * of an explicit entry (auto-seed-new-repo.yml `admit` job,
 * ops/register-org-repository.py).
 *
 * Verdicts:
 *   COMPLETE    every hosted repository is registered under its exact,
 *               case-sensitive name, and no archived one is registered current
 *   INCOMPLETE  at least one violation (named in the report)
 *   UNKNOWN     the listing or the registry could not be read; never a pass
 *
 * The registry is parsed with the same pinned PyYAML the semantic validator
 * uses (governance-report.js pythonYamlParser), so both read the same bytes
 * the same way.
 */

const {
	REGISTRY_SOURCE,
	loadCanonicalSource,
} = require("./governance-report.js");

const VERDICTS = Object.freeze({
	COMPLETE: "complete",
	INCOMPLETE: "incomplete",
	UNKNOWN: "unknown",
});

const isMap = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
// Code-unit order: deterministic, independent of the runner's locale.
const byCodeUnit = (a, b) => (a < b ? -1 : Number(a > b));

/**
 * The registry's coordinates under one organization, by exact name.
 *
 * @param {object} registry parsed semantics/repository_registry.yaml
 * @param {string} org
 * @returns {Map<string, {id: string, lifecycle: string}>}
 */
function registeredCoordinates(registry, org) {
	if (!isMap(registry) || !Array.isArray(registry.repositories))
		throw new Error("registry lists no repositories");
	const out = new Map();
	for (const entry of registry.repositories) {
		const c = isMap(entry) ? entry.coordinate : null;
		if (!isMap(c) || typeof c.repository !== "string")
			throw new Error(
				`registry entry ${JSON.stringify(entry?.id)} has no coordinate`,
			);
		if (c.provider !== "github" || c.organization !== org) continue;
		if (out.has(c.repository))
			throw new Error(
				`registry coordinate ${org}/${c.repository} is registered twice`,
			);
		out.set(c.repository, { id: entry.id, lifecycle: entry.lifecycle });
	}
	return out;
}

/**
 * Compare the organization listing with the registry.
 *
 * @param {{registry: object, discovered: Array<{name: string, archived?: boolean}>|null, org: string}} o
 *   discovered is the full listForOrg result (type=all), or null when the
 *   listing failed
 * @returns {{verdict: string, hosted: number, registered: number,
 *   unregistered: string[], caseDrift: Array<{hosted: string, registered: string}>,
 *   archivedCurrent: string[], notHosted: string[], reason: string|null}}
 */
function assessRegistryCompleteness({ registry, discovered, org }) {
	const empty = {
		hosted: 0,
		registered: 0,
		unregistered: [],
		caseDrift: [],
		archivedCurrent: [],
		notHosted: [],
	};
	if (!Array.isArray(discovered)) {
		return {
			...empty,
			verdict: VERDICTS.UNKNOWN,
			reason: "organization listing unavailable",
		};
	}
	// A listing with no repositories cannot be the organization this registry
	// describes (it lists at least .github): it is unreadable, not complete.
	if (!discovered.length) {
		return {
			...empty,
			verdict: VERDICTS.UNKNOWN,
			reason: "organization listing returned no repositories",
		};
	}
	let coords;
	try {
		coords = registeredCoordinates(registry, org);
	} catch (e) {
		return { ...empty, verdict: VERDICTS.UNKNOWN, reason: e.message };
	}
	const folded = new Map([...coords.keys()].map((n) => [n.toLowerCase(), n]));
	const unregistered = [];
	const caseDrift = [];
	const archivedCurrent = [];
	const hostedNames = new Set();
	for (const repo of discovered) {
		if (!isMap(repo) || typeof repo.name !== "string" || !repo.name)
			return {
				...empty,
				verdict: VERDICTS.UNKNOWN,
				reason: "organization listing returned an entry without a name",
			};
		hostedNames.add(repo.name);
		const entry = coords.get(repo.name);
		if (!entry) {
			const near = folded.get(repo.name.toLowerCase());
			if (near) caseDrift.push({ hosted: repo.name, registered: near });
			else unregistered.push(repo.name);
			continue;
		}
		if (repo.archived === true && entry.lifecycle === "current")
			archivedCurrent.push(repo.name);
	}
	// Registered but not returned: reported, never a failure here. A private
	// repository the token cannot see looks exactly like a deleted one, and
	// a removed repository keeps its entry with lifecycle retired.
	const notHosted = [...coords.keys()].filter((n) => !hostedNames.has(n));
	unregistered.sort(byCodeUnit);
	archivedCurrent.sort(byCodeUnit);
	notHosted.sort(byCodeUnit);
	caseDrift.sort((a, b) => byCodeUnit(a.hosted, b.hosted));
	const violations =
		unregistered.length + caseDrift.length + archivedCurrent.length;
	return {
		verdict: violations ? VERDICTS.INCOMPLETE : VERDICTS.COMPLETE,
		hosted: hostedNames.size,
		registered: coords.size,
		unregistered,
		caseDrift,
		archivedCurrent,
		notHosted,
		reason: null,
	};
}

/**
 * Load the registry exactly as the governance report does: the canonical
 * source contract (schema, artifact_id, canonical) and the pinned parser.
 *
 * @param {{readBytes: (p: string) => Buffer, parseYaml: (b: Buffer) => unknown, revision: string}} io
 */
function loadRegistry(io) {
	return loadCanonicalSource(REGISTRY_SOURCE, io).doc;
}

/**
 * Markdown for the job summary. Every violation is named; nothing is folded.
 *
 * @param {ReturnType<typeof assessRegistryCompleteness>} result
 * @param {string} org
 */
function renderCompletenessReport(result, org) {
	const lines = [
		`## Registry completeness — ${org}`,
		"",
		`Verdict: **${result.verdict.toUpperCase()}**`,
	];
	if (result.reason) lines.push("", `Reason: ${result.reason}`);
	if (result.verdict === VERDICTS.UNKNOWN) {
		lines.push(
			"",
			"Nothing was assessed. An unreadable listing is never reported as complete.",
		);
		return lines.join("\n");
	}
	lines.push(
		"",
		`${result.hosted} hosted repositories, ${result.registered} registered coordinates under ${org}.`,
	);
	if (result.unregistered.length) {
		lines.push(
			"",
			`### Hosted but not registered (${result.unregistered.length})`,
			"",
			...result.unregistered.map((n) => `- \`${org}/${n}\``),
			"",
			"Each needs an explicit admission. Propose it with",
			"`gh workflow run auto-seed-new-repo.yml -f target_repo=<name> -f dry_run=false`,",
			"which opens a registry-admission PR (ADR-040); the owner's merge admits it.",
		);
	}
	if (result.caseDrift.length) {
		lines.push(
			"",
			`### Registered under a different case (${result.caseDrift.length})`,
			"",
			...result.caseDrift.map(
				(d) =>
					`- GitHub \`${org}/${d.hosted}\`, registry \`${org}/${d.registered}\``,
			),
		);
	}
	if (result.archivedCurrent.length) {
		lines.push(
			"",
			`### Archived but registered current (${result.archivedCurrent.length})`,
			"",
			...result.archivedCurrent.map(
				(n) => `- \`${org}/${n}\` — register it with lifecycle retired`,
			),
		);
	}
	if (result.notHosted.length) {
		lines.push(
			"",
			`> [!NOTE]\n> Registered but not returned by the listing (not a failure: it may be invisible to this token, or removed): ${result.notHosted
				.map((n) => `\`${n}\``)
				.join(", ")}.`,
		);
	}
	return lines.join("\n");
}

module.exports = {
	VERDICTS,
	registeredCoordinates,
	assessRegistryCompleteness,
	loadRegistry,
	renderCompletenessReport,
};
