'use strict';

/**
 * Shared adapter plumbing between the governance-plan compiler and the
 * workflows/scripts that execute a plan (docs/adr/0001-one-governance-brain.md).
 *
 * Adapters gather facts and apply compiled decisions; they never interpret
 * policy. Everything here is mechanics: collect the target facts the compiler
 * needs, compile and verify the plan before any write (GOV-028), and turn
 * `plan.materialize.files` into the dest → contents shape the existing seed
 * write machinery (build-seed-payload.js selectSeedWrites) consumes.
 */

const {
  loadAuthority,
  compileGovernancePlan,
  verifyPlan,
  narrowMaterialization,
  GovernanceCompileError,
} = require('./compile-repo-governance.js');
const { RETIRED_CATEGORIES } = require('./build-seed-payload.js');

// ── remote observation (fail closed) ────────────────────────────────────────

/**
 * The three outcomes of looking at one path on a remote repository. Only an
 * HTTP 404 proves ABSENT. A 403, 5xx, rate limit, or network failure proves
 * nothing, and treating it as absent would let an unreadable class marker
 * resolve to the widest class, an unreadable opt-out read as "not opted out",
 * an existing file look missing, or a FORBID path vanish from attestation.
 */
const PROBE = Object.freeze({ PRESENT: 'PRESENT', ABSENT: 'ABSENT', ERROR: 'ERROR' });

class RemoteProbeError extends Error {
  /**
   * @param {string} repository  owner/name
   * @param {string} path
   * @param {unknown} cause
   */
  constructor(repository, path, cause) {
    const status = cause && cause.status ? ` (HTTP ${cause.status})` : '';
    const detail = cause && cause.message ? cause.message : String(cause);
    super(`cannot observe ${repository}:${path}${status}: ${detail} — refusing to treat it as absent`);
    this.name = 'RemoteProbeError';
    this.repository = repository;
    this.path = path;
    this.status = cause && cause.status;
  }
}

/**
 * Observe one path. Never throws: the caller receives the tri-state.
 * @param {object} github  octokit
 * @param {{owner: string, repo: string, path: string, ref?: string}} where
 * @returns {Promise<{state: 'PRESENT', data: unknown} | {state: 'ABSENT'} | {state: 'ERROR', error: unknown}>}
 */
async function probeContent(github, { owner, repo, path, ref }) {
  try {
    const res = await github.rest.repos.getContent({ owner, repo, path, ...(ref ? { ref } : {}) });
    return { state: PROBE.PRESENT, data: res && res.data };
  } catch (error) {
    if (error && error.status === 404) return { state: PROBE.ABSENT };
    return { state: PROBE.ERROR, error };
  }
}

/**
 * `exists` / `readText` over one repository that fail closed: both throw
 * RemoteProbeError on ERROR, so a caller can only ever act on a PRESENT or a
 * proven ABSENT. Every governance adapter reads a target through this.
 *
 * `readText` returns null only for a proven ABSENT; a present path without
 * decodable file content (a directory, an oversized blob) reads as ''.
 *
 * @param {object} github
 * @param {string} owner
 * @param {string} repo
 * @returns {{exists: (path: string, ref?: string) => Promise<boolean>, readText: (path: string, ref?: string) => Promise<string|null>}}
 */
function remoteReader(github, owner, repo) {
  const observe = async (path, ref) => {
    const r = await probeContent(github, { owner, repo, path, ref });
    if (r.state === PROBE.ERROR) throw new RemoteProbeError(`${owner}/${repo}`, path, r.error);
    return r;
  };
  return {
    exists: async (path, ref) => (await observe(path, ref)).state === PROBE.PRESENT,
    readText: async (path, ref) => {
      const r = await observe(path, ref);
      if (r.state === PROBE.ABSENT) return null;
      const d = r.data;
      if (d && !Array.isArray(d) && typeof d.content === 'string' && d.content) {
        return Buffer.from(d.content, 'base64').toString('utf8');
      }
      return '';
    },
  };
}

/**
 * Collect the explicit target facts the compiler needs.
 *
 * `io` must fail closed (remoteReader): any observation that is not a proven
 * PRESENT or a proven 404 throws, so no fact is ever guessed. A marker that
 * exists but has no readable content becomes an empty (malformed) declaration
 * the compiler rejects — never "absent", which would fall through to the
 * widest class (AC-ADV-009).
 *
 * @param {object} io
 * @param {(path: string) => Promise<boolean>} io.exists
 * @param {(path: string) => Promise<string|null>} io.readText
 * @param {string} markerPath  the class marker path (from the authority)
 * @returns {Promise<object>} facts for compileGovernancePlan
 */
async function gatherTargetFacts({ exists, readText }, markerPath) {
  const facts = {
    marker_state: 'absent',
    has_root_codeowners: await exists('CODEOWNERS'),
    has_python: (await exists('pyproject.toml')) || (await exists('requirements.txt')),
    has_package_json: await exists('package.json'),
  };
  if (await exists(markerPath)) {
    facts.marker_state = 'present';
    facts.marker_text = (await readText(markerPath)) ?? '';
  }
  return facts;
}

/**
 * Compile the plan for one target and verify it before returning it, so no
 * caller can hold an unverified plan.
 *
 * @param {object} o
 * @param {typeof import('fs')} o.fs
 * @param {object} o.authority  from loadAuthority()
 * @param {string} o.authoritySha
 * @param {string} o.repository  owner/name
 * @param {object} o.facts
 * @param {string|null} [o.requestedClass]
 * @returns {object} verified plan
 */
function compileVerifiedPlan({ fs, authority, authoritySha, repository, facts, requestedClass = null }) {
  const plan = compileGovernancePlan({ fs, authority, authoritySha, repository, facts, requestedClass });
  return verifyPlan(plan, { schema: authority.schema, authoritySha, repository });
}

/**
 * Operator category filter → the plan entries to execute. `null`, empty, or
 * `all` means the whole plan. Anything else may only narrow it (GOV-012).
 * A retired CI category gets its own message, as the seeders always gave it.
 *
 * @param {object} plan
 * @param {string|null|undefined} raw  comma/space separated categories
 * @returns {object[]} materialize entries
 */
function selectPlanFiles(plan, raw) {
  const text = raw == null ? '' : String(raw).trim();
  if (!text || text === 'all') return narrowMaterialization(plan, null);
  const wanted = text.split(/[,\s]+/).map((s) => s.trim()).filter(Boolean);
  const retired = wanted.filter((c) => RETIRED_CATEGORIES.includes(c));
  if (retired.length) {
    throw new GovernanceCompileError(
      'policy_contradiction',
      `seed categor(ies) ${retired.join(', ')} RETIRED: Quantum-L9/.github no longer distributes CI`,
    );
  }
  return narrowMaterialization(plan, wanted);
}

/**
 * @param {object[]} files  plan materialize entries
 * @returns {Record<string, string>} dest → contents, in plan order
 */
function payloadOf(files) {
  const payload = {};
  for (const f of files) payload[f.path] = f.content_utf8;
  return payload;
}

/**
 * One line of plan identity for job summaries (13-observability).
 * @param {object} plan
 * @returns {string}
 */
function planIdentity(plan) {
  return (
    `class \`${plan.repo_class.name}\` (${plan.repo_class.resolved_from}) · ` +
    `authority \`${plan.authority.sha.slice(0, 12)}\` · plan \`${plan.digest.value.slice(0, 12)}\``
  );
}

module.exports = {
  loadAuthority,
  GovernanceCompileError,
  PROBE,
  RemoteProbeError,
  probeContent,
  remoteReader,
  gatherTargetFacts,
  compileVerifiedPlan,
  selectPlanFiles,
  payloadOf,
  planIdentity,
};
