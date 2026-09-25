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

/**
 * Collect the explicit target facts the compiler needs.
 *
 * Existence is probed before content is read, so a failed read of a marker
 * that exists becomes an empty (malformed) declaration — which the compiler
 * rejects — instead of reading as "absent" and falling through to the widest
 * class (AC-ADV-009).
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
  gatherTargetFacts,
  compileVerifiedPlan,
  selectPlanFiles,
  payloadOf,
  planIdentity,
};
