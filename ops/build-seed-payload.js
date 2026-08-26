'use strict';

const { applyProfile } = require('./repo-class-profile.js');

/**
 * Build the consumer-repo seed payload from templates/ plus l9-ci-pack/.
 *
 * Mirrors ops/sync-org-files.sh categories and templates/README.md destinations.
 * Used by seed-governance.yml and auto-seed-new-repo.yml.
 *
 * Default `all` is the DEFAULT_CATEGORIES set (stack-aware L9 pack). Opt-in
 * extras (`labels`, `on-org-update`) stay parseable but are not in `all`.
 * Missing-only seed never overwrites an existing consumer file, except two
 * safe upgrades of `.github/workflows/l9-lint-test-node.yml`:
 *   1. a stock ESLint caller (the old pack)
 *   2. the stock Biome caller that ran `tsc` / `Test Suite` with
 *      `cache: ${{ env.PACKAGE_MANAGER }}` (hard-fails without a lockfile)
 * Customized workflows (for example Cursor-Governance's Biome-only file)
 * are kept. A consumer `biome.json` with a different `$schema` is never
 * replaced.
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
  'l9-ci-pack',
]);

const OPT_IN_CATEGORIES = Object.freeze(['labels', 'on-org-update']);

const ALL_CATEGORIES = Object.freeze([...DEFAULT_CATEGORIES, ...OPT_IN_CATEGORIES]);

const COMMUNITY_HEALTH_DEFAULT = Object.freeze([
  'CODE_OF_CONDUCT.md',
  'CONTRIBUTING.md',
  'SECURITY.md',
]);

const SKIP_ISSUE_TEMPLATES = Object.freeze(['bug_report.yml', 'feature_request.yml']);

const PYTHON_LINT_DEST = '.github/workflows/l9-lint-test.yml';
const STOCK_BIOME_DEST = 'biome.json';
const STOCK_ESLINT_NODE_DEST = '.github/workflows/l9-lint-test-node.yml';
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

function isStockEslintNodeWorkflow(text) {
  if (typeof text !== 'string' || !text.trim()) return false;
  if (/l9-biome-scan\.yml/.test(text)) return false;
  const named = /^\s*name:\s*L9 Lint and Test \(Node\)\s*$/m.test(text);
  const eslintJob = /^\s*name:\s*ESLint\s*$/m.test(text);
  const eslintRun = /npx(?:\s+--no-install)?\s+eslint\b/.test(text);
  return named && eslintJob && eslintRun;
}

/**
 * Stock Biome node caller that fails CI on non-Node repos.
 * Matches the pack file shipped before the #276 remediating:
 * workflow name + job named `Test Suite` + setup-node cache on PACKAGE_MANAGER.
 */
function isStockUnsafeNodeWorkflow(text) {
  if (typeof text !== 'string' || !text.trim()) return false;
  if (!/l9-biome-scan\.yml/.test(text)) return false;
  const named = /^\s*name:\s*L9 Lint and Test \(Node\)\s*$/m.test(text);
  const testSuite = /^\s*name:\s*Test Suite\s*$/m.test(text);
  const cachePm = /cache:\s*\$\{\{\s*env\.PACKAGE_MANAGER\s*\}\}/.test(text);
  return named && testSuite && cachePm;
}

function isReplaceableStockNodeWorkflow(text) {
  return isStockEslintNodeWorkflow(text) || isStockUnsafeNodeWorkflow(text);
}

/**
 * `env:` keys l9-ci-pack/README.md §5.4 tells consumers to tune in their copy
 * of `l9-lint-test-node.yml`. Tuning them leaves every stock marker intact, so
 * the replaceable-stock predicates still fire on re-seed. Carry the tuned
 * values into the replacement instead of silently reverting them to defaults.
 */
const TUNABLE_NODE_ENV_KEYS = Object.freeze([
  'NODE_VERSION',
  'PACKAGE_MANAGER',
  'SOURCE_DIR',
  'HAS_TYPESCRIPT',
]);

/**
 * Read the top-level `env:` mapping of a workflow. Only scalar `KEY: value`
 * entries at one indent level are read; the block ends at the first
 * non-indented, non-blank line.
 * @param {string} text
 * @returns {Record<string, string>} key → raw value (quotes preserved)
 */
function readTopLevelEnv(text) {
  const out = {};
  if (typeof text !== 'string') return out;
  const lines = text.split('\n');
  let inEnv = false;
  for (const line of lines) {
    if (!inEnv) {
      if (/^env:\s*$/.test(line)) inEnv = true;
      continue;
    }
    if (!line.trim()) continue;
    if (!/^\s/.test(line)) break;
    const m = line.match(/^\s+([A-Za-z_][A-Za-z0-9_]*):\s*(\S.*?)\s*$/);
    if (m) out[m[1]] = m[2];
  }
  return out;
}

/**
 * Rewrite the tunable `env:` entries of `incoming` with the values the
 * consumer already set in `existing`. Keys absent from either side are left
 * alone, so a replacement never invents configuration.
 * @param {string} incoming  payload contents about to be written
 * @param {string} existing  the consumer file being replaced
 * @returns {string}
 */
function preserveTunedNodeEnv(incoming, existing) {
  if (typeof incoming !== 'string' || typeof existing !== 'string') return incoming;
  const tuned = readTopLevelEnv(existing);
  const shipped = readTopLevelEnv(incoming);
  let out = incoming;
  for (const key of TUNABLE_NODE_ENV_KEYS) {
    if (!(key in tuned) || !(key in shipped)) continue;
    if (tuned[key] === shipped[key]) continue;
    out = out.replace(
      new RegExp(`^(\\s+${key}:\\s*).*$`, 'm'),
      (_m, indent) => `${indent}${tuned[key]}`,
    );
  }
  return out;
}

function biomeSchemaOf(text) {
  if (typeof text !== 'string' || !text.trim()) return null;
  try {
    const parsed = JSON.parse(text);
    return typeof parsed.$schema === 'string' ? parsed.$schema : '';
  } catch {
    return null;
  }
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

function buildExtensionsJson({ hasPython }) {
  const recommendations = ['biomejs.biome'];
  if (hasPython) recommendations.push('charliermarsh.ruff');
  return `${JSON.stringify(
    {
      recommendations,
      unwantedRecommendations: ['dbaeumer.vscode-eslint', 'esbenp.prettier-vscode'],
    },
    null,
    2,
  )}\n`;
}

/**
 * Decide which payload dests to write.
 * @param {Record<string, string>} payload
 * @param {Record<string, string|null|true>} existingByPath
 *   null/absent = missing (write);
 *   true = present, content not fetched (keep);
 *   string = fetched content (replace only if a stock replaceable node caller
 *            or biome.json with the same $schema — different $schema is keep).
 * Replacing a stock node caller rewrites `payload[dest]` in place so the
 * consumer's tuned `env:` values survive the upgrade; callers write
 * `payload[dest]` after this returns.
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
    const existing = existingByPath[dest];
    if (
      dest === STOCK_ESLINT_NODE_DEST &&
      typeof existing === 'string' &&
      isReplaceableStockNodeWorkflow(existing)
    ) {
      // Upgrade the caller, keep the consumer's tuned env: block.
      payload[dest] = preserveTunedNodeEnv(payload[dest], existing);
      writes.push(dest);
      replaced.push(dest);
      continue;
    }
    if (dest === STOCK_BIOME_DEST && typeof existing === 'string') {
      const existingSchema = biomeSchemaOf(existing);
      const incomingSchema = biomeSchemaOf(payload[dest]);
      if (
        existingSchema != null &&
        incomingSchema != null &&
        existingSchema !== incomingSchema
      ) {
        kept.push(dest);
        continue;
      }
    }
    kept.push(dest);
  }
  return { writes, replaced, kept };
}

function addDirFiles(fs, srcDir, destPrefix, payload, { skipNames = [] } = {}) {
  if (!fs.existsSync(srcDir) || !fs.statSync(srcDir).isDirectory()) return;
  const skip = new Set(skipNames);
  for (const name of fs.readdirSync(srcDir)) {
    if (skip.has(name)) continue;
    const body = readIfFile(fs, `${srcDir}/${name}`);
    if (body != null) payload[`${destPrefix}/${name}`] = body;
  }
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
    switch (cat) {
      case 'codeowners': {
        if (hasRootCodeowners) break;
        const body = readIfFile(fs, 'templates/CODEOWNERS.repo');
        if (body != null) payload['.github/CODEOWNERS'] = body;
        break;
      }
      case 'dependabot': {
        const body = readIfFile(fs, 'templates/dependabot.yml');
        if (body != null) payload['.github/dependabot.yml'] = body;
        break;
      }
      case 'governance': {
        const body = readIfFile(fs, 'templates/governance-caller.yml');
        if (body != null) payload['.github/workflows/governance.yml'] = body;
        break;
      }
      case 'labels': {
        const body = readIfFile(fs, 'templates/labels.yml');
        if (body != null) payload['.github/labels.yml'] = body;
        break;
      }
      case 'community-health': {
        for (const f of COMMUNITY_HEALTH_DEFAULT) {
          const body = readIfFile(fs, `templates/community-health/${f}`);
          if (body != null) payload[f] = applyRepoPlaceholders(body, repository);
        }
        break;
      }
      case 'issue-templates': {
        const dir = 'templates/issue-templates';
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
        const human = readIfFile(fs, 'templates/pr-templates/pull_request_template.md');
        if (human != null) payload['.github/pull_request_template.md'] = human;
        const agent = readIfFile(fs, 'templates/pr-templates/agent.md');
        if (agent != null) payload['.github/PULL_REQUEST_TEMPLATE/agent.md'] = agent;
        break;
      }
      case 'on-org-update': {
        const body = readIfFile(fs, 'templates/on-org-update.yml');
        if (body != null) payload['.github/workflows/on-org-update.yml'] = body;
        break;
      }
      case 'l9-ci-pack': {
        addDirFiles(fs, 'l9-ci-pack/workflows', '.github/workflows', payload, {
          skipNames: hasPython ? [] : ['l9-lint-test.yml'],
        });
        addDirFiles(fs, 'l9-ci-pack/governance', '.github/governance', payload);
        const formatterFiles = [
          ['l9-ci-pack/biome.json', STOCK_BIOME_DEST],
          ['l9-ci-pack/.biomeignore', '.biomeignore'],
          ['l9-ci-pack/.editorconfig', '.editorconfig'],
        ];
        for (const [src, dest] of formatterFiles) {
          const body = readIfFile(fs, src);
          if (body != null) payload[dest] = body;
        }
        payload['.vscode/extensions.json'] = buildExtensionsJson({ hasPython });
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
  COMMUNITY_HEALTH_DEFAULT,
  SKIP_ISSUE_TEMPLATES,
  PYTHON_LINT_DEST,
  STOCK_BIOME_DEST,
  STOCK_BIOME_SCHEMA,
  STOCK_ESLINT_NODE_DEST,
  parseCategories,
  buildSeedPayload,
  isStockEslintNodeWorkflow,
  isStockUnsafeNodeWorkflow,
  isReplaceableStockNodeWorkflow,
  preserveTunedNodeEnv,
  readTopLevelEnv,
  TUNABLE_NODE_ENV_KEYS,
  biomeSchemaOf,
  selectSeedWrites,
  applyRepoPlaceholders,
};
