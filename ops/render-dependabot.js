'use strict';

const crypto = require('node:crypto');

/**
 * Render a consumer's `.github/dependabot.yml` from this repository's
 * fragments, the consumer's root shape, and the vendored Core list of
 * Core-owned tools. ADR: docs/adr/0019-dependabot-managed-rendered.md.
 *
 * Pure: `fs` is injected (as in buildSeedPayload) and every path is
 * repository-relative, so the seeders, continuous-sync and the local CLI all
 * compare against and write the same bytes for the same shape.
 *
 * The shape is never guessed. A missing or malformed shape throws instead of
 * falling back to the github-actions-only render, which would wipe a
 * consumer's legitimate uv / pip / pre-commit entries on the next restore.
 */

const FRAGMENT_DIR = 'policies/dependabot';
const SOURCE_RECORD = `${FRAGMENT_DIR}/core-owned-tools.source.json`;
const CORE_OWNED_SCHEMA = 'l9.core-owned-tools/v1';
const IGNORE_TOKEN = '{{ignore}}';

// Root files that decide the rendered ecosystems. Only the root `/` is in
// scope: nested manifests are neither probed nor rendered.
const UV_LOCK = 'uv.lock';
const PYPROJECT = 'pyproject.toml';
const PRE_COMMIT_CONFIG = '.pre-commit-config.yaml';
const REQUIREMENTS_RE = /^requirements.*\.txt$/;
const PEP621_RE = /^\[project\]\s*$/m;

const SHAPE_BOOLEANS = Object.freeze(['uvLock', 'pep621', 'preCommit']);

function readRequired(fs, path) {
  try {
    return fs.readFileSync(path);
  } catch (err) {
    throw new Error(`seed source ${path} is missing or not a file (${err.code || err.message}) — refusing to render dependabot.yml`);
  }
}

/**
 * Derive the shape from the names of the files at a repository root.
 * @param {object} o
 * @param {string[]} o.names  root file names (directories excluded)
 * @param {string|null} [o.pyprojectText]  required when names lists pyproject.toml
 * @returns {{uvLock: boolean, requirements: string[], pep621: boolean, preCommit: boolean}}
 */
function shapeFromRoot({ names, pyprojectText = null } = {}) {
  if (!Array.isArray(names) || names.some((n) => typeof n !== 'string')) {
    throw new Error('shapeFromRoot requires names: string[] (the repository root file names)');
  }
  const hasPyproject = names.includes(PYPROJECT);
  if (hasPyproject && typeof pyprojectText !== 'string') {
    throw new Error(`${PYPROJECT} is listed at the root but its text was not read`);
  }
  return Object.freeze({
    uvLock: names.includes(UV_LOCK),
    requirements: Object.freeze([...new Set(names.filter((n) => REQUIREMENTS_RE.test(n)))].sort()),
    pep621: hasPyproject && PEP621_RE.test(pyprojectText),
    preCommit: names.includes(PRE_COMMIT_CONFIG),
  });
}

/**
 * Probe a repository root through caller-supplied readers and derive its shape.
 * Shared by every remote entrypoint so none renders on its own.
 * @param {object} o
 * @param {() => Promise<{name: string, type: string}[]>} o.listRoot
 *   the root listing; must throw on anything but a readable directory
 * @param {(path: string) => Promise<string|null>} o.readText
 *   a root file's text; null only when the file is absent (404)
 */
async function probeRepoShape({ listRoot, readText }) {
  const entries = await listRoot();
  if (!Array.isArray(entries)) {
    throw new Error('repository root listing is not a directory listing');
  }
  const names = entries.filter((e) => e && e.type === 'file').map((e) => e.name);
  let pyprojectText = null;
  if (names.includes(PYPROJECT)) {
    pyprojectText = await readText(PYPROJECT);
    if (typeof pyprojectText !== 'string') {
      throw new Error(`${PYPROJECT} is listed at the root but could not be read`);
    }
  }
  return shapeFromRoot({ names, pyprojectText });
}

function assertShape(shape) {
  if (!shape || typeof shape !== 'object') {
    throw new Error('renderDependabot requires a repository shape (ops/render-dependabot.js shapeFromRoot); refusing to render without one');
  }
  for (const key of SHAPE_BOOLEANS) {
    if (typeof shape[key] !== 'boolean') {
      throw new Error(`repository shape.${key} must be a boolean (got ${typeof shape[key]})`);
    }
  }
  if (!Array.isArray(shape.requirements) || shape.requirements.some((n) => typeof n !== 'string')) {
    throw new Error('repository shape.requirements must be a string[]');
  }
}

/**
 * Read the vendored Core list, verify its bytes against the recorded digest,
 * and return the Core-owned dependency names per Dependabot ecosystem.
 * Names come from `tools[].ecosystems` verbatim; there is no alias table.
 * `non_dependency_lock_keys` (pip, python) are not dependency names.
 * @returns {Record<string, string[]>} ecosystem -> sorted, de-duplicated names
 */
function loadCoreOwnedNames(fs) {
  const record = JSON.parse(readRequired(fs, SOURCE_RECORD).toString('utf8'));
  for (const key of ['repository', 'path', 'commit', 'sha256', 'vendored_at']) {
    if (typeof record[key] !== 'string' || !record[key]) {
      throw new Error(`${SOURCE_RECORD} is missing ${key}`);
    }
  }
  if (!/^[0-9a-f]{40}$/.test(record.commit)) throw new Error(`${SOURCE_RECORD} commit is not a full sha`);
  const bytes = readRequired(fs, record.vendored_at);
  const digest = crypto.createHash('sha256').update(bytes).digest('hex');
  if (digest !== record.sha256) {
    throw new Error(
      `${record.vendored_at} sha256 ${digest} does not match ${SOURCE_RECORD} (${record.sha256}); ` +
        'the vendored Core bytes, commit and digest move together',
    );
  }
  const list = JSON.parse(bytes.toString('utf8'));
  if (list.schema !== CORE_OWNED_SCHEMA || !Array.isArray(list.tools)) {
    throw new Error(`${record.vendored_at} is not ${CORE_OWNED_SCHEMA}`);
  }
  const byEcosystem = {};
  for (const tool of list.tools) {
    for (const [ecosystem, names] of Object.entries(tool.ecosystems || {})) {
      if (!Array.isArray(names) || names.some((n) => typeof n !== 'string' || !n)) {
        throw new Error(`${record.vendored_at}: tool ${tool.name} ecosystem ${ecosystem} names must be non-empty strings`);
      }
      byEcosystem[ecosystem] = [...(byEcosystem[ecosystem] || []), ...names];
    }
  }
  for (const ecosystem of Object.keys(byEcosystem)) {
    byEcosystem[ecosystem] = [...new Set(byEcosystem[ecosystem])].sort();
  }
  return byEcosystem;
}

function fragment(fs, name, ignoreNames = []) {
  const text = readRequired(fs, `${FRAGMENT_DIR}/${name}.yml.tpl`).toString('utf8').replace(/\r\n/g, '\n');
  const lines = text.replace(/\n+$/, '').split('\n');
  const tokens = lines.filter((l) => l.includes(IGNORE_TOKEN));
  if (tokens.length > 1) throw new Error(`fragment ${name} carries more than one ${IGNORE_TOKEN}`);
  if (!tokens.length) return lines;
  if (tokens[0].trim() !== IGNORE_TOKEN) throw new Error(`fragment ${name}: ${IGNORE_TOKEN} must stand alone on its line`);
  const block = ignoreNames.length
    ? ['    ignore:', ...ignoreNames.map((n) => `      - dependency-name: ${JSON.stringify(n)}`)]
    : [];
  return lines.flatMap((l) => (l === tokens[0] ? block : [l]));
}

/**
 * @param {object} o
 * @param {typeof import('fs')} o.fs
 * @param {ReturnType<typeof shapeFromRoot>} o.shape
 * @returns {string} dependabot.yml bytes: LF, exactly one trailing newline
 */
function renderDependabot({ fs, shape } = {}) {
  if (!fs) throw new Error('renderDependabot requires fs');
  assertShape(shape);
  const owned = loadCoreOwnedNames(fs);
  const lines = [...fragment(fs, 'header'), ...fragment(fs, 'base-actions')];
  if (shape.uvLock) {
    lines.push(...fragment(fs, 'uv', owned.uv || []));
  } else if (shape.requirements.length || shape.pep621) {
    lines.push(...fragment(fs, 'pip', owned.pip || []));
  }
  if (shape.preCommit) lines.push(...fragment(fs, 'pre-commit', owned['pre-commit'] || []));
  return `${lines.join('\n')}\n`;
}

/** The ecosystems a shape renders, in render order. */
function renderedEcosystems(shape) {
  assertShape(shape);
  const out = ['github-actions'];
  if (shape.uvLock) out.push('uv');
  else if (shape.requirements.length || shape.pep621) out.push('pip');
  if (shape.preCommit) out.push('pre-commit');
  return out;
}

/** Shape of a local checkout: its root files, plus pyproject.toml when present. */
function shapeOfDirectory({ fs, path, dir }) {
  const names = fs.readdirSync(dir, { withFileTypes: true }).filter((d) => d.isFile()).map((d) => d.name);
  const pyprojectText = names.includes(PYPROJECT) ? fs.readFileSync(path.join(dir, PYPROJECT), 'utf8') : null;
  return shapeFromRoot({ names, pyprojectText });
}

/**
 * CLI: `node ops/render-dependabot.js [--root <dir>]` prints the render for
 * <dir> (default: this repository, whose own .github/dependabot.yml is it).
 */
if (require.main === module) {
  const fs = require('node:fs');
  const path = require('node:path');
  const args = process.argv.slice(2);
  const at = args.indexOf('--root');
  const dir = path.resolve(at === -1 ? path.resolve(__dirname, '..') : args[at + 1] || '');
  try {
    const shape = shapeOfDirectory({ fs, path, dir });
    process.chdir(path.resolve(__dirname, '..'));
    process.stdout.write(renderDependabot({ fs, shape }));
  } catch (err) {
    console.error(`❌ ERROR: ${err.message}`);
    process.exit(2);
  }
}

module.exports = {
  FRAGMENT_DIR,
  SOURCE_RECORD,
  CORE_OWNED_SCHEMA,
  shapeFromRoot,
  shapeOfDirectory,
  probeRepoShape,
  loadCoreOwnedNames,
  renderDependabot,
  renderedEcosystems,
};
