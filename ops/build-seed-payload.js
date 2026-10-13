'use strict';

const {
  applyProfile,
  classForRepo,
  loadRepoClasses,
  resolveProfile,
} = require('./repo-class-profile.js');

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
 * The payload MATERIALIZES only what needs repository-local bytes.
 * `community-health` is SECURITY.md alone (consumer-specific advisory
 * routing). CODE_OF_CONDUCT.md, CONTRIBUTING.md, SUPPORT.md, FUNDING.yml and
 * VULNERABILITY_REPORT.yml are INHERIT: GitHub serves them org-wide, so they
 * are never in the payload. Modes: docs/REPO_BIRTH_PROFILES.md.
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

// The one community-health file with consumer-specific content: its advisory
// URLs are rewritten per consumer. Every other community-health file is
// INHERIT and must not be listed here.
const COMMUNITY_HEALTH_MATERIALIZED = Object.freeze(['SECURITY.md']);

// Both PR templates a consumer carries locally. `.github/PULL_REQUEST_TEMPLATE/`
// is read by name, never by directory listing, so a template added to this
// repository is not distributed until it is named here.
const PR_TEMPLATES_MATERIALIZED = Object.freeze([
  '.github/pull_request_template.md',
  '.github/PULL_REQUEST_TEMPLATE/release.md',
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
        for (const f of COMMUNITY_HEALTH_MATERIALIZED) {
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
        for (const f of PR_TEMPLATES_MATERIALIZED) {
          const body = readIfFile(fs, f);
          if (body != null) payload[f] = body;
        }
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

/**
 * Plan a seed into a local consumer checkout under the repository's class.
 *
 * This is the one policy path for a manual seed: the same marker > override >
 * default resolution as the Actions seeders, the same payload, the same
 * missing-only selection. ops/sync-org-files.sh calls it and writes nothing
 * on its own, so the shell entrypoint cannot drift from the class contract.
 *
 * @param {object} o
 * @param {typeof import('fs')} o.fs
 * @param {typeof import('path')} o.path
 * @param {string} o.consumerRoot  absolute path of the consumer checkout
 * @param {string} [o.repository]  owner/name; '' when the consumer has no remote
 * @param {string|string[]|null} [o.categories]  explicit categories; null/'all'
 *   lets the class decide. An explicit category the class forbids throws.
 * @returns {{profile: object, writes: string[], kept: string[],
 *   inherited: string[], payload: Record<string,string>}}
 */
function planConsumerSeed({ fs, path, consumerRoot, repository = '', categories = null }) {
  if (!fs || !path) throw new Error('planConsumerSeed requires fs and path');
  const classes = loadRepoClasses(fs);
  const markerFile = path.join(consumerRoot, classes.marker_path);
  // Absent and malformed are different answers: an absent marker resolves
  // through overrides to default; a present but unreadable one fails closed.
  const marker = fs.existsSync(markerFile) ? fs.readFileSync(markerFile, 'utf8') : null;
  const repoName = repository ? repository.split('/').pop() : null;
  const decided = classForRepo(classes, repoName, marker);
  if (decided.error) {
    throw new Error(`refusing to seed ${consumerRoot}: ${decided.error}`);
  }
  const profile = resolveProfile(classes, decided.name);
  if (decided.name) profile.resolved_from = decided.source;

  let explicit = null;
  if (Array.isArray(categories)) {
    explicit = categories;
  } else if (typeof categories === 'string' && !/^\s*(all)?\s*$/.test(categories)) {
    explicit = parseCategories(categories);
  }

  const payload = buildSeedPayload({
    fs,
    categories: explicit ?? profile.seed_categories,
    hasRootCodeowners: fs.existsSync(path.join(consumerRoot, 'CODEOWNERS')),
    hasPython:
      fs.existsSync(path.join(consumerRoot, 'pyproject.toml')) ||
      fs.existsSync(path.join(consumerRoot, 'requirements.txt')),
    hasPackageJson: fs.existsSync(path.join(consumerRoot, 'package.json')),
    repository,
  });
  // Applied here rather than through `profile:` so the inherited list is
  // reportable. FORBID still throws, exactly as it does in the seeders.
  const { inherited } = applyProfile(payload, profile);

  const existingByPath = {};
  for (const dest of Object.keys(payload)) {
    existingByPath[dest] = fs.existsSync(path.join(consumerRoot, dest)) ? true : null;
  }
  const { writes, kept } = selectSeedWrites(payload, existingByPath);
  return { profile, writes, kept, inherited, payload };
}

/**
 * CLI: `node ops/build-seed-payload.js --consumer <dir> [--repository o/n]
 *   [--categories all|a,b,...] [--dry-run]`
 * Writes missing destinations only; an existing file is reported and kept.
 * Exit 2 on a refused target (malformed marker, FORBID hit, retired or
 * unknown category) so a wrapper cannot mistake a refusal for a clean run.
 */
function main(argv) {
  const fs = require('node:fs');
  const path = require('node:path');
  const args = { consumer: '', repository: '', categories: 'all', dryRun: false };
  const valued = { '--consumer': 'consumer', '--repository': 'repository', '--categories': 'categories' };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === '--dry-run') {
      args.dryRun = true;
    } else if (a in valued) {
      i += 1;
      args[valued[a]] = argv[i] ?? '';
    } else {
      throw new Error(`unknown argument: ${a}`);
    }
  }
  if (args.categories === '') args.categories = 'all';
  if (!args.consumer) throw new Error('--consumer <dir> is required');
  const consumerRoot = path.resolve(args.consumer);
  if (!fs.existsSync(consumerRoot) || !fs.statSync(consumerRoot).isDirectory()) {
    throw new Error(`consumer repo path does not exist: ${consumerRoot}`);
  }
  // Templates are read by repo-relative path; the org root is this file's parent.
  process.chdir(path.resolve(__dirname, '..'));

  const plan = planConsumerSeed({
    fs, path, consumerRoot, repository: args.repository, categories: args.categories,
  });
  console.log(`class: ${plan.profile.name} (${plan.profile.resolved_from})`);
  for (const dest of plan.inherited) console.log(`  ~ ${dest} (inherited from the org .github repo; not copied)`);
  for (const dest of plan.kept) console.log(`  = ${dest} (exists; kept)`);
  for (const dest of plan.writes) {
    if (!args.dryRun) {
      const target = path.join(consumerRoot, dest);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, plan.payload[dest]);
    }
    console.log(`  ${args.dryRun ? '+' : '✓'} ${dest}${args.dryRun ? ' (would write)' : ''}`);
  }
  if (!plan.writes.length && !plan.kept.length) console.log('  (nothing to materialize for this class)');
}

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (err) {
    console.error(`❌ ERROR: ${err.message}`);
    process.exit(2);
  }
}

module.exports = {
  ALL_CATEGORIES,
  DEFAULT_CATEGORIES,
  OPT_IN_CATEGORIES,
  RETIRED_CATEGORIES,
  COMMUNITY_HEALTH_MATERIALIZED,
  PR_TEMPLATES_MATERIALIZED,
  SKIP_ISSUE_TEMPLATES,
  PYTHON_LINT_DEST,
  STOCK_BIOME_SCHEMA,
  parseCategories,
  buildSeedPayload,
  selectSeedWrites,
  applyRepoPlaceholders,
  planConsumerSeed,
};
