'use strict';

const { applyProfile } = require('./repo-class-profile.js');

/**
 * Build the consumer-repo seed payload from the canonical files in this repo.
 *
 * Mirrors ops/sync-org-files.sh. Consumer-only files live in policies/.
 * Used by seed-governance.yml and auto-seed-new-repo.yml.
 *
 * Default `all` is the DEFAULT_CATEGORIES set. Opt-in extras (`labels`)
 * stay parseable but are not in `all`. Missing-only: an existing consumer
 * file is left untouched. CI workflows are not in the payload. Canonical CI
 * is Quantum-L9/l9-ci-core `.github/workflows/org-ci.yml`.
 *
 * @param {object} opts
 * @param {typeof import('fs')} opts.fs
 * @param {string[]} [opts.categories]  subset of ALL_CATEGORIES; default DEFAULT
 * @param {boolean} [opts.hasRootCodeowners]  skip .github/CODEOWNERS when root CODEOWNERS exists
 * @param {boolean} [opts.hasPython]  seed Python lint caller only when true
 * @param {boolean} [opts.hasPackageJson]  add Ruff to extensions.json when Python
 * @param {string} [opts.repository]  owner/name — rewrite SECURITY / contact_links
 * @param {object} [opts.profile]  resolved repo-class profile (ops/repo-class-profile.js).
 *   When given and `categories` is not explicitly passed, the profile's
 *   `seed_categories` decide the category set. INHERIT dests are dropped
 *   (GitHub supplies them org-wide); a FORBID dest throws.
 * @returns {Record<string, string>} destPath → file contents
 */

const DEFAULT_CATEGORIES = Object.freeze([
  'codeowners',
  'dependabot',
  'governance',
  'community-health',
  'issue-templates',
  'pr-templates',
]);

const OPT_IN_CATEGORIES = Object.freeze(['labels']);

// RETIRED — `on-org-update` only ran `scripts/sync_ci_from_pack.py`, the
// consumer half of the old copy-first CI loop. `l9-ci-pack` was the pack
// those files came from. The names stay so a request fails closed.
// Canonical CI is `l9-ci-core/.github/workflows/org-ci.yml`.
const RETIRED_CATEGORIES = Object.freeze(['on-org-update', 'l9-ci-pack']);

const ALL_CATEGORIES = Object.freeze([...DEFAULT_CATEGORIES, ...OPT_IN_CATEGORIES]);

const COMMUNITY_HEALTH_DEFAULT = Object.freeze([
  'CODE_OF_CONDUCT.md',
  'CONTRIBUTING.md',
  'SECURITY.md',
]);

const SKIP_ISSUE_TEMPLATES = Object.freeze([
  'bug_report.yml',
  'feature_request.yml',
  'EXAMPLE.md',
]);

const PYTHON_LINT_DEST = '.github/workflows/l9-lint-test.yml';
const STOCK_BIOME_SCHEMA = 'https://biomejs.dev/schemas/2.5.8/schema.json';

const ADVISORY_INBOX_STOCK = 'https://github.com/Quantum-L9/.github/security/advisories/new';
const ADVISORY_POLICY_STOCK = 'https://github.com/Quantum-L9/.github/security/policy';

function parseCategories(raw) {
  if (raw == null || String(raw).trim() === '' || String(raw).trim() === 'all') {
    return [...DEFAULT_CATEGORIES];
  }
  const wanted = String(raw)
    .split(/[,\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const unknown = wanted.filter((c) => !ALL_CATEGORIES.includes(c));
  if (unknown.length) {
    throw new Error(
      `unknown seed categor(ies): ${unknown.join(', ')} (allowed: ${ALL_CATEGORIES.join(', ')}, all)`,
    );
  }
  return wanted;
}

function readIfFile(fs, path) {
  if (!fs.existsSync(path) || !fs.statSync(path).isFile()) return null;
  return fs.readFileSync(path, 'utf8');
}

function assertJsonInYaml(text, dest) {
  try {
    JSON.parse(text);
  } catch (err) {
    throw new Error(`governance pack ${dest} is not JSON-in-YAML: ${err.message}`);
  }
}

function applyRepoPlaceholders(text, repository) {
  if (!repository || typeof text !== 'string') return text;
  const advisory = `https://github.com/${repository}/security/advisories/new`;
  return text.split(ADVISORY_INBOX_STOCK).join(advisory).split(ADVISORY_POLICY_STOCK).join(advisory);
}


/**
 * Decide which payload dests to write.
 * @param {Record<string, string>} payload
 * @param {Record<string, string|null|true>} existingByPath
 *   null/absent = missing (write);
 *   anything else = present (keep).
 * CI callers are never overwritten. Canonical CI is
 * Quantum-L9/l9-ci-core `.github/workflows/org-ci.yml`.
 * @returns {{ writes: string[], replaced: string[], kept: string[] }}
 */
function selectSeedWrites(payload, existingByPath = {}) {
  const writes = [];
  const replaced = [];
  const kept = [];
  for (const dest of Object.keys(payload)) {
    if (!(dest in existingByPath) || existingByPath[dest] === null) {
      writes.push(dest);
      continue;
    }
    kept.push(dest);
  }
  return { writes, replaced, kept };
}

function buildSeedPayload({
  fs,
  categories,
  hasRootCodeowners = false,
  hasPython = false,
  hasPackageJson = false,
  repository = '',
  profile = null,
} = {}) {
  if (!fs) throw new Error('buildSeedPayload requires fs');
  // An explicit `categories` argument always wins, so a caller can still ask
  // for a specific category set and get a loud FORBID error if that set
  // contradicts the class. With no explicit argument the class decides.
  const requested =
    categories == null && profile ? profile.seed_categories : categories;
  const cats = Array.isArray(requested) ? requested : parseCategories(requested);
  const payload = {};

  for (const cat of cats) {
    // Fail closed, loudly. A retired category silently producing an empty
    // payload would read as "seeded, nothing to do" — the same false green the
    // whole distribution model was retired for.
    if (RETIRED_CATEGORIES.includes(cat)) {
      throw new Error(
        `seed category '${cat}' is RETIRED: Quantum-L9/.github no longer distributes CI. ` +
          'Canonical CI is Quantum-L9/l9-ci-core/.github/workflows/org-ci.yml, ' +
          'enforced by a GitHub organization required-workflow ruleset.',
      );
    }
    switch (cat) {
      case 'codeowners': {
        if (hasRootCodeowners) break;
        const body = readIfFile(fs, 'policies/CODEOWNERS');
        if (body != null) payload['.github/CODEOWNERS'] = body;
        break;
      }
      case 'dependabot': {
        const body = readIfFile(fs, '.github/dependabot.yml');
        if (body != null) payload['.github/dependabot.yml'] = body;
        break;
      }
      case 'governance': {
        const body = readIfFile(fs, 'policies/governance-caller.yml');
        if (body != null) payload['.github/workflows/governance.yml'] = body;
        break;
      }
      case 'labels': {
        const body = readIfFile(fs, '.github/labels.yml');
        if (body != null) payload['.github/labels.yml'] = body;
        break;
      }
      case 'community-health': {
        for (const f of COMMUNITY_HEALTH_DEFAULT) {
          const body = readIfFile(fs, f);
          if (body != null) payload[f] = applyRepoPlaceholders(body, repository);
        }
        break;
      }
      case 'issue-templates': {
        const dir = '.github/ISSUE_TEMPLATE';
        if (!fs.existsSync(dir)) break;
        for (const name of fs.readdirSync(dir)) {
          if (SKIP_ISSUE_TEMPLATES.includes(name)) continue;
          const body = readIfFile(fs, `${dir}/${name}`);
          if (body != null) {
            payload[`.github/ISSUE_TEMPLATE/${name}`] = applyRepoPlaceholders(body, repository);
          }
        }
        break;
      }
      case 'pr-templates': {
        const human = readIfFile(fs, '.github/pull_request_template.md');
        if (human != null) payload['.github/pull_request_template.md'] = human;
        break;
      }
      default:
        throw new Error(`unknown seed category: ${cat}`);
    }
  }

  for (const dest of Object.keys(payload)) {
    if (dest.startsWith('.github/governance/') && dest.endsWith('.yaml')) {
      assertJsonInYaml(payload[dest], dest);
    }
  }

  if (profile) applyProfile(payload, profile);

  return payload;
}

module.exports = {
  ALL_CATEGORIES,
  DEFAULT_CATEGORIES,
  OPT_IN_CATEGORIES,
  RETIRED_CATEGORIES,
  COMMUNITY_HEALTH_DEFAULT,
  SKIP_ISSUE_TEMPLATES,
  PYTHON_LINT_DEST,
  STOCK_BIOME_SCHEMA,
  parseCategories,
  buildSeedPayload,
  selectSeedWrites,
  applyRepoPlaceholders,
};
