'use strict';

/**
 * Build the consumer-repo seed payload from templates/ plus l9-ci-pack/.
 *
 * Mirrors ops/sync-org-files.sh categories and templates/README.md destinations.
 * Used by seed-governance.yml and auto-seed-new-repo.yml.
 * Health files come from templates/. The Core hub pack (l9-analysis.yml +
 * .github/governance/*.yaml + lint callers) comes from l9-ci-pack/.
 * This repo distributes those callers; l9-ci-core executes CI.
 * Missing-only seed in Actions never overwrites an existing consumer file.
 *
 * @param {object} opts
 * @param {typeof import('fs')} opts.fs
 * @param {string[]} [opts.categories]  subset of ALL_CATEGORIES; default all
 * @param {boolean} [opts.hasRootCodeowners]  skip .github/CODEOWNERS when root CODEOWNERS exists
 * @returns {Record<string, string>} destPath → file contents
 */
const ALL_CATEGORIES = Object.freeze([
  'codeowners',
  'dependabot',
  'governance',
  'labels',
  'community-health',
  'issue-templates',
  'pr-templates',
  'on-org-update',
  'l9-ci-pack',
]);

function parseCategories(raw) {
  if (raw == null || String(raw).trim() === '' || String(raw).trim() === 'all') {
    return [...ALL_CATEGORIES];
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

function addDirFiles(fs, srcDir, destPrefix, payload) {
  if (!fs.existsSync(srcDir) || !fs.statSync(srcDir).isDirectory()) return;
  for (const name of fs.readdirSync(srcDir)) {
    const body = readIfFile(fs, `${srcDir}/${name}`);
    if (body != null) payload[`${destPrefix}/${name}`] = body;
  }
}

function buildSeedPayload({ fs, categories, hasRootCodeowners = false } = {}) {
  if (!fs) throw new Error('buildSeedPayload requires fs');
  const cats = Array.isArray(categories) ? categories : parseCategories(categories);
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
        for (const f of [
          'CODE_OF_CONDUCT.md',
          'CONTRIBUTING.md',
          'SECURITY.md',
          'SUPPORT.md',
          'LICENSE',
        ]) {
          const body = readIfFile(fs, `templates/community-health/${f}`);
          if (body != null) payload[f] = body;
        }
        const funding = readIfFile(fs, 'templates/community-health/FUNDING.yml');
        if (funding != null) payload['.github/FUNDING.yml'] = funding;
        break;
      }
      case 'issue-templates': {
        const dir = 'templates/issue-templates';
        if (!fs.existsSync(dir)) break;
        for (const name of fs.readdirSync(dir)) {
          const body = readIfFile(fs, `${dir}/${name}`);
          if (body != null) payload[`.github/ISSUE_TEMPLATE/${name}`] = body;
        }
        break;
      }
      case 'pr-templates': {
        const body = readIfFile(fs, 'templates/pr-templates/pull_request_template.md');
        if (body != null) payload['.github/pull_request_template.md'] = body;
        break;
      }
      case 'on-org-update': {
        const body = readIfFile(fs, 'templates/on-org-update.yml');
        if (body != null) payload['.github/workflows/on-org-update.yml'] = body;
        break;
      }
      case 'l9-ci-pack': {
        addDirFiles(fs, 'l9-ci-pack/workflows', '.github/workflows', payload);
        addDirFiles(fs, 'l9-ci-pack/governance', '.github/governance', payload);
        break;
      }
      default:
        throw new Error(`unknown seed category: ${cat}`);
    }
  }

  return payload;
}

module.exports = {
  ALL_CATEGORIES,
  parseCategories,
  buildSeedPayload,
};
