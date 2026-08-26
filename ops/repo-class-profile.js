'use strict';

/**
 * Resolve the organization birth profile for a repository class.
 *
 * The organization does not seed "every file into every repository". It applies
 * every capability that is *applicable* to that repository's class. This module
 * is the resolver for `policies/repo-classes.yml`, shared by:
 *
 *   - ops/build-seed-payload.js        (payload filtering)
 *   - .github/workflows/auto-seed-new-repo.yml
 *   - .github/workflows/repo-birth-bootstrap.yml
 *   - Quantum-L9/l9-repo-template scripts/birth-runner/new_repo.py (via the
 *     same JSON-in-YAML file, read with json.loads)
 *
 * Why this exists: `l9-repo-template` fails closed on repo-local organization
 * CI distribution (scripts/inventory_check.py DENY_CI_DISTRIBUTION). Seeding
 * the historic default categories into a template-born repository writes
 * `.github/workflows/governance.yml`, `l9-analysis.yml`, `l9-lint-test.yml`
 * and `.github/governance/*` — every one of which makes `make verify` fail in
 * the newborn. Automating that seed without a class contract would only
 * automate the contradiction faster.
 */

const DEFAULT_CLASSES_PATH = 'policies/repo-classes.yml';
const MODES = Object.freeze(['inherit', 'materialize', 'remote_apply']);

/**
 * Parse the JSON-in-YAML class file.
 *
 * Full-line `#` comments are stripped before JSON.parse so the policy file can
 * document itself. Only lines whose first non-space character is `#` are
 * removed, so a `#` inside a JSON string value is preserved. A JSON string must
 * therefore never be the first thing on a line after a `#`; the policy file is
 * validated by ops/test-repo-class-profile.js.
 *
 * @param {string} text
 * @returns {object}
 */
function parseJsonInYaml(text) {
  if (typeof text !== 'string' || !text.trim()) {
    throw new Error('repo-classes policy is empty');
  }
  const stripped = text.replace(/^[ \t]*#.*$/gm, '');
  try {
    return JSON.parse(stripped);
  } catch (err) {
    throw new Error(`repo-classes policy is not JSON-in-YAML: ${err.message}`);
  }
}

/**
 * @param {typeof import('fs')} fs
 * @param {string} [path]
 * @returns {object} the parsed policy document
 */
function loadRepoClasses(fs, path = DEFAULT_CLASSES_PATH) {
  if (!fs) throw new Error('loadRepoClasses requires fs');
  if (!fs.existsSync(path)) throw new Error(`repo-classes policy not found: ${path}`);
  const doc = parseJsonInYaml(fs.readFileSync(path, 'utf8'));
  if (!doc || typeof doc !== 'object' || !doc.classes || typeof doc.classes !== 'object') {
    throw new Error(`${path} has no classes map`);
  }
  if (!doc.classes[doc.default_class]) {
    throw new Error(`${path} default_class ${doc.default_class} is not defined`);
  }
  for (const [repo, cls] of Object.entries(doc.overrides || {})) {
    if (!doc.classes[cls]) {
      throw new Error(`${path} override ${repo} names undefined class ${cls}`);
    }
  }
  return doc;
}

/**
 * Read the class name a repository declares in its marker file.
 *
 * The marker is deliberately flat so it parses with one regex on the Node side
 * and with yaml.safe_load on the Python side. Anything unparseable resolves to
 * null, and the caller falls back to the default class — an unreadable marker
 * must never widen what a repository receives.
 *
 * @param {string|null} markerText contents of `.l9/org-birth-profile.yaml`
 * @returns {string|null}
 */
function parseClassMarker(markerText) {
  if (typeof markerText !== 'string' || !markerText.trim()) return null;
  const m = markerText.match(/^profile:[ \t]*["']?([A-Za-z0-9_-]+)["']?[ \t]*$/m);
  return m ? m[1] : null;
}

/**
 * Match a destination path against a class pattern list.
 *
 * Patterns are exact paths or a single trailing `/**` directory prefix. Full
 * glob syntax is deliberately not supported: a birth contract that needs a
 * regex to explain what a repository receives is not a contract.
 *
 * @param {string[]} patterns
 * @param {string} dest
 * @returns {string|null} the matching pattern, or null
 */
function matchPattern(patterns, dest) {
  if (!Array.isArray(patterns)) return null;
  for (const pattern of patterns) {
    if (typeof pattern !== 'string' || !pattern) continue;
    if (pattern === dest) return pattern;
    if (pattern.endsWith('/**')) {
      const prefix = pattern.slice(0, -2); // keep the trailing slash
      if (dest.startsWith(prefix)) return pattern;
    }
  }
  return null;
}

/**
 * Decide which class a repository belongs to.
 *
 * Precedence is marker > overrides > default_class, with one hard rule:
 *
 *   marker absent                 -> override, else default_class
 *   marker present + known class  -> that class
 *   marker present + unparseable  -> ERROR. Never default.
 *   marker present + unknown class-> ERROR. Never default.
 *
 * The last two matter more than they look. `default` is the WIDEST payload
 * there is, so silently falling back to it on a malformed marker turns a typo
 * (`profile: non_constelation_python`) into a broad-seeding candidate — which
 * is precisely the class of pull request this contract exists to stop. An
 * explicit declaration that cannot be honored must fail closed and be
 * reported, not quietly widened.
 *
 * Absence is different from malformation: a repository that never declared a
 * class has not made a statement to contradict, so the override map and then
 * the default apply as before.
 *
 * @param {object} doc  parsed policy document
 * @param {string} repoName  bare repository name (no owner)
 * @param {string|null} markerText  marker file contents, or null when ABSENT.
 *   An empty/whitespace string means the file exists but says nothing, which
 *   is a malformed declaration, not an absent one.
 * @returns {{name: string|null, source: string, error: string|null}}
 *   `error` non-null means the caller must skip (sweep) or fail (birth); it
 *   must never be treated as "use the default".
 */
function classForRepo(doc, repoName, markerText) {
  const hasMarker = typeof markerText === 'string';
  if (hasMarker) {
    const declared = parseClassMarker(markerText);
    if (!declared) {
      return {
        name: null,
        source: 'marker',
        error: `${doc.marker_path || 'class marker'} is present but declares no parseable profile`,
      };
    }
    if (!doc.classes[declared]) {
      return {
        name: null,
        source: 'marker',
        error:
          `${doc.marker_path || 'class marker'} declares unknown class ${declared} ` +
          `(known: ${Object.keys(doc.classes).join(', ')})`,
      };
    }
    return { name: declared, source: 'marker', error: null };
  }
  const overrides = doc.overrides || {};
  if (repoName && Object.prototype.hasOwnProperty.call(overrides, repoName)) {
    return { name: overrides[repoName], source: 'org override', error: null };
  }
  return { name: null, source: 'default', error: null };
}

/**
 * Resolve one class into a fully-defaulted profile.
 *
 * @param {object} doc  parsed policy document
 * @param {string|null|undefined} className  null/absent resolves to default_class
 * @param {{strict?: boolean}} [opts] strict throws on an unknown class instead
 *   of falling back. Birth is strict (a typo must not silently widen the
 *   payload); an org-wide sweep is not (an unreadable marker on one repo must
 *   not stop the sweep).
 * @returns {{name: string, description: string, seed_categories: string[],
 *   inherit: string[], forbid: string[], remote_apply: object,
 *   mandatory_files_waive: string[], resolved_from: string}}
 */
function resolveProfile(doc, className, { strict = false } = {}) {
  const fallback = doc.default_class;
  let name = className;
  let resolvedFrom = 'marker';
  if (!name) {
    name = fallback;
    resolvedFrom = 'default (no marker)';
  } else if (!doc.classes[name]) {
    if (strict) {
      throw new Error(
        `unknown repo class ${className} (known: ${Object.keys(doc.classes).join(', ')})`,
      );
    }
    name = fallback;
    resolvedFrom = `default (unknown class ${className})`;
  }
  const cls = doc.classes[name];
  return {
    name,
    description: cls.description || '',
    seed_categories: Array.isArray(cls.seed_categories) ? [...cls.seed_categories] : [],
    inherit: Array.isArray(cls.inherit) ? [...cls.inherit] : [],
    forbid: Array.isArray(cls.forbid) ? [...cls.forbid] : [],
    remote_apply: { ...(cls.remote_apply || {}) },
    mandatory_files_waive: Array.isArray(cls.mandatory_files_waive)
      ? [...cls.mandatory_files_waive]
      : [],
    resolved_from: resolvedFrom,
  };
}

/**
 * Apply a profile to an already-built payload.
 *
 * INHERIT dests are dropped silently — GitHub supplies them, so a copy in the
 * repository is duplication the org would then need a second synchronizer to
 * clean up. FORBID dests throw: reaching one means the category set and the
 * prohibition list disagree, which is a configuration bug, and a birth engine
 * that quietly drops a forbidden file hides the bug instead of fixing it.
 *
 * @param {Record<string,string>} payload  mutated in place
 * @param {object} profile  from resolveProfile
 * @returns {{payload: Record<string,string>, inherited: string[]}}
 */
function applyProfile(payload, profile) {
  const inherited = [];
  const violations = [];
  for (const dest of Object.keys(payload)) {
    const forbidden = matchPattern(profile.forbid, dest);
    if (forbidden) {
      violations.push(`${dest} (forbid ${forbidden})`);
      continue;
    }
    if (matchPattern(profile.inherit, dest)) {
      inherited.push(dest);
      delete payload[dest];
    }
  }
  if (violations.length) {
    throw new Error(
      `seed payload violates repo class ${profile.name}: ${violations.join(', ')} — ` +
        'organization CI targeting is not distributed into the repository',
    );
  }
  return { payload, inherited };
}

/**
 * Mandatory-file paths this class is not held to.
 * @param {object} profile
 * @param {string} path
 * @returns {boolean}
 */
function waivesMandatoryFile(profile, path) {
  return matchPattern(profile.mandatory_files_waive, path) != null;
}

module.exports = {
  DEFAULT_CLASSES_PATH,
  MODES,
  parseJsonInYaml,
  loadRepoClasses,
  parseClassMarker,
  classForRepo,
  matchPattern,
  resolveProfile,
  applyProfile,
  waivesMandatoryFile,
};
