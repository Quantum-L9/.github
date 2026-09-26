'use strict';

/**
 * The governance-plan compiler — the one place organization governance policy
 * is interpreted (docs/adr/0001-one-governance-brain.md,
 * docs/adr/0002-versioned-governance-plan-compiler.md).
 *
 * Input:  explicit target facts + one immutable Quantum-L9/.github revision.
 * Output: an `l9.org-governance-plan/v1` document
 *         (ops/schemas/repo-governance-plan.schema.json) holding the complete
 *         effective answer for that target: class decision, files to
 *         materialize (with content and SHA-256), inherited and forbidden
 *         paths, effective mandatory files, desired labels and repository
 *         settings, attestation expectations, and a deterministic digest.
 *
 * The compiler is pure. It never calls the GitHub API: workflows gather facts,
 * the compiler decides, adapters apply (GOV-025). It reuses the existing
 * primitives — repo-class-profile.js for class resolution, build-seed-payload.js
 * for the category → file mapping, label-taxonomy.js for labels — so there is
 * still exactly one implementation of each rule, now reached through one door.
 *
 * Every failure throws a GovernanceCompileError carrying a `code` naming the
 * failure class, before any plan exists — an adapter never receives a partial
 * or contradictory plan.
 *
 * CLI (production: the checkout must be clean and at the asserted revision):
 *   node ops/compile-repo-governance.js --repo Quantum-L9/example \
 *     --authority-sha HEAD --marker-absent [--has-root-codeowners] \
 *     [--has-python] [--has-package-json] [--class <name>] [--pretty]
 *   node ops/compile-repo-governance.js ... --marker-file path/to/marker.yaml
 */

const crypto = require('node:crypto');
const {
  DEFAULT_CLASSES_PATH,
  parseJsonInYaml,
  loadRepoClasses,
  isKnownClass,
  parseClassMarker,
  classForRepo,
  resolveProfile,
  matchPattern,
  waivesMandatoryFile,
} = require('./repo-class-profile.js');
const {
  ALL_CATEGORIES,
  RETIRED_CATEGORIES,
  STOCK_ESLINT_NODE_DEST,
  parseCategories,
  collectSeedFiles,
} = require('./build-seed-payload.js');
const { parseLabels } = require('./label-taxonomy.js');
const { compileSchema } = require('./json-schema-subset.js');

const COMPILER_NAME = 'ops/compile-repo-governance.js';
const CONTRACT_VERSION = '1.0.0';
const PLAN_SCHEMA = 'l9.org-governance-plan/v1';
const AUTHORITY_REPOSITORY = 'Quantum-L9/.github';
const CANONICALIZATION = 'l9.canonical-json/v1';
const SCHEMA_PATH = 'ops/schemas/repo-governance-plan.schema.json';
const SETTINGS_PATH = 'policies/repo-settings.yml';
const MANDATORY_PATH = 'policies/mandatory-files.yml';
const LABELS_PATH = '.github/labels.yml';

// The code that turns policy into a plan. It is authority exactly as much as
// the policy files are: a modified compiler produces different plan bytes from
// the same policy, so its bytes must be the named revision too (ADR-0003).
// ops/test-compile-repo-governance.js asserts every ops/ module the compiler
// loads is listed here.
const COMPILER_SOURCES = Object.freeze([
  'ops/compile-repo-governance.js',
  'ops/repo-class-profile.js',
  'ops/build-seed-payload.js',
  'ops/label-taxonomy.js',
  'ops/json-schema-subset.js',
]);

// Everything that determines a plan's bytes: policy data, templates, schema,
// and the compiler itself. A production compile asserts all of it is exactly
// the authority revision it names (B-20).
const AUTHORITY_INPUTS = Object.freeze([
  DEFAULT_CLASSES_PATH,
  SETTINGS_PATH,
  MANDATORY_PATH,
  LABELS_PATH,
  'templates',
  SCHEMA_PATH,
  ...COMPILER_SOURCES,
]);

// Settings the existing owners deliberately never auto-change
// (enforce-policies.yml skips it; repo-birth-bootstrap.yml deletes it).
const NEVER_AUTO_APPLIED_SETTINGS = Object.freeze(['default_branch']);

const ERROR_CODES = Object.freeze([
  'contract', // malformed compiler input or schema failure
  'class_resolution', // malformed/unknown marker or operator class
  'policy_contradiction', // FORBID in materialize, retired category, empty taxonomy
  'unsafe_path', // absolute, traversal, backslash, NUL, glob, non-text
  'missing_fact', // a required target fact was not supplied
  'authority_identity', // SHA, repository, or dirty-checkout provenance
  'digest', // canonicalization or digest mismatch
]);

class GovernanceCompileError extends Error {
  /**
   * @param {string} code one of ERROR_CODES
   * @param {string} message
   */
  constructor(code, message) {
    super(`[${code}] ${message}`);
    this.name = 'GovernanceCompileError';
    this.code = code;
  }
}

function fail(code, message) {
  throw new GovernanceCompileError(code, message);
}

// ── canonical JSON + digest (C-03) ──────────────────────────────────────────

/**
 * Canonical JSON: object keys sorted recursively, array order preserved, no
 * insignificant whitespace. Values JSON cannot represent exactly are refused
 * rather than silently coerced — a digest over a lossy encoding is not a
 * digest of the plan.
 * @param {unknown} value
 * @returns {string}
 */
function canonicalJson(value) {
  if (value === null || typeof value === 'boolean' || typeof value === 'string') {
    return JSON.stringify(value);
  }
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) fail('digest', `non-finite number ${value} cannot be canonicalized`);
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(',')}]`;
  if (typeof value === 'object') {
    const keys = Object.keys(value).sort(byCodeUnit);
    const parts = [];
    for (const key of keys) {
      if (value[key] === undefined) fail('digest', `undefined value at key "${key}" cannot be canonicalized`);
      parts.push(`${JSON.stringify(key)}:${canonicalJson(value[key])}`);
    }
    return `{${parts.join(',')}}`;
  }
  return fail('digest', `${typeof value} cannot be canonicalized`);
}

// UTF-16 code-unit order — exactly what a comparator-less sort does, written
// out (Sonar S2871). Never localeCompare: that would make the digest depend on
// the runner's locale.
function byCodeUnit(a, b) {
  if (a < b) return -1;
  return a > b ? 1 : 0;
}

function sha256(text) {
  return crypto.createHash('sha256').update(text, 'utf8').digest('hex');
}

/**
 * Digest of a plan: SHA-256 over canonical JSON of the plan without `digest`.
 * @param {object} plan
 * @returns {string} 64 hex chars
 */
function computePlanDigest(plan) {
  const { digest: _omitted, ...body } = plan;
  return sha256(canonicalJson(body));
}

// ── authority loading ───────────────────────────────────────────────────────

/**
 * Read and parse every policy input from a checkout of Quantum-L9/.github.
 * Returned as data so tests can compile against in-memory fixtures.
 * @param {typeof import('fs')} fs
 * @returns {{classes: object, settings: object, mandatory: object, labels: object[], schema: object}}
 */
function loadAuthority(fs) {
  if (!fs) fail('contract', 'loadAuthority requires fs');
  const read = (path) => {
    if (!fs.existsSync(path)) fail('contract', `authority input missing: ${path}`);
    return fs.readFileSync(path, 'utf8');
  };
  return {
    classes: loadRepoClasses(fs),
    settings: parseJsonInYaml(read(SETTINGS_PATH)),
    mandatory: parseJsonInYaml(read(MANDATORY_PATH)),
    labels: parseLabels(read(LABELS_PATH)),
    schema: JSON.parse(read(SCHEMA_PATH)),
  };
}

// ── validation helpers ──────────────────────────────────────────────────────

const SHA_RE = /^[0-9a-f]{40}$/;
const REPOSITORY_RE = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;

/**
 * A materialized destination must be a plain relative path: no absolute path,
 * no `..` segment, no backslash, no NUL, no glob, no empty segment.
 * @param {string} dest
 */
function assertSafeDest(dest) {
  if (typeof dest !== 'string' || !dest) fail('unsafe_path', 'empty materialize path');
  if (dest.startsWith('/')) fail('unsafe_path', `absolute materialize path: ${dest}`);
  if (dest.includes('\\')) fail('unsafe_path', `backslash in materialize path: ${dest}`);
  if (dest.includes('\u0000')) fail('unsafe_path', `NUL in materialize path: ${JSON.stringify(dest)}`);
  if (dest.includes('*')) fail('unsafe_path', `glob in materialize path: ${dest}`);
  for (const segment of dest.split('/')) {
    if (segment === '..' || segment === '.' || segment === '') {
      fail('unsafe_path', `non-canonical segment in materialize path: ${dest}`);
    }
  }
}

/**
 * Materialized content is text: no NUL byte and no U+FFFD, which is what a
 * utf8 read yields for bytes that are not valid UTF-8.
 * @param {string} dest
 * @param {string} content
 */
function assertTextContent(dest, content) {
  if (typeof content !== 'string') fail('unsafe_path', `non-text content for ${dest}`);
  if (content.includes('\u0000') || content.includes('�')) {
    fail('unsafe_path', `non-text (binary or invalid UTF-8) content for ${dest}`);
  }
}

function normalizeFacts(facts) {
  if (!facts || typeof facts !== 'object') fail('missing_fact', 'target facts are required');
  const out = {};
  if (facts.marker_state !== 'absent' && facts.marker_state !== 'present') {
    fail('missing_fact', 'facts.marker_state must be "absent" or "present"');
  }
  out.marker_state = facts.marker_state;
  if (facts.marker_state === 'present') {
    if (typeof facts.marker_text !== 'string') {
      fail('missing_fact', 'facts.marker_text is required when the marker is present');
    }
    out.marker_text = facts.marker_text;
  } else if (facts.marker_text !== undefined) {
    fail('contract', 'facts.marker_text must be omitted when the marker is absent');
  }
  for (const key of ['has_root_codeowners', 'has_python', 'has_package_json']) {
    if (typeof facts[key] !== 'boolean') fail('missing_fact', `facts.${key} must be a boolean`);
    out[key] = facts[key];
  }
  return out;
}

// ── section compilers ───────────────────────────────────────────────────────

const RESOLVED_FROM = Object.freeze({
  marker: 'marker',
  'org override': 'org_override',
  default: 'default',
});

function decideClass(classes, repoName, facts, requestedClass) {
  if (requestedClass != null && requestedClass !== '') {
    if (!isKnownClass(classes, requestedClass)) {
      fail(
        'class_resolution',
        `operator requested unknown repo class ${requestedClass} ` +
          `(known: ${Object.keys(classes.classes).join(', ')})`,
      );
    }
    // A repository's own declaration is never overruled, and a declaration
    // that cannot be read is never ignored. Either contradiction is decided
    // here, before a plan exists, so no adapter can write first and discover
    // it at attestation.
    if (facts.marker_state === 'present') {
      const declared = parseClassMarker(facts.marker_text);
      if (declared !== requestedClass) {
        fail(
          'class_resolution',
          declared
            ? `operator requested class ${requestedClass} but ${classes.marker_path} declares ${declared}`
            : `operator requested class ${requestedClass} but ${classes.marker_path} is present and declares no parseable profile`,
        );
      }
    }
    return { name: requestedClass, resolved_from: 'operator_request' };
  }
  const markerText = facts.marker_state === 'present' ? facts.marker_text : null;
  const decided = classForRepo(classes, repoName, markerText);
  if (decided.error) fail('class_resolution', decided.error);
  const resolvedFrom = RESOLVED_FROM[decided.source];
  if (!resolvedFrom) fail('class_resolution', `unrecognized class resolution source ${decided.source}`);
  return { name: decided.name || classes.default_class, resolved_from: resolvedFrom };
}

function writeModeFor(dest) {
  // The only existing stock-upgrade predicate (build-seed-payload.js
  // selectSeedWrites). No current category emits this dest; the mode exists so
  // the plan can carry it faithfully if one ever does.
  return dest === STOCK_ESLINT_NODE_DEST ? 'replace_if_stock' : 'missing_only';
}

function compileMaterialize(fs, profile, facts, repository) {
  for (const cat of profile.seed_categories) {
    if (RETIRED_CATEGORIES.includes(cat)) {
      fail('policy_contradiction', `repo class ${profile.name} names retired seed category ${cat}`);
    }
  }
  // Each entry is one category name. Joining and re-parsing would accept `all`
  // (the default set) and whitespace-joined lists that buildSeedPayload
  // refuses, so every entry is checked on its own.
  for (const cat of profile.seed_categories) {
    if (typeof cat !== 'string' || !ALL_CATEGORIES.includes(cat)) {
      fail(
        'policy_contradiction',
        `repo class ${profile.name} names unknown seed category ${JSON.stringify(cat)} ` +
          `(allowed: ${ALL_CATEGORIES.join(', ')})`,
      );
    }
  }
  // An empty category list means "nothing", not "the default set".
  const cats = profile.seed_categories.length ? parseCategories(profile.seed_categories.join(',')) : [];

  const files = [];
  const violations = [];
  for (const entry of collectSeedFiles({
    fs,
    categories: cats,
    hasRootCodeowners: facts.has_root_codeowners,
    repository,
  })) {
    const forbidden = matchPattern(profile.forbid, entry.dest);
    if (forbidden) {
      violations.push(`${entry.dest} (forbid ${forbidden})`);
      continue;
    }
    if (matchPattern(profile.inherit, entry.dest)) continue;
    assertSafeDest(entry.dest);
    assertTemplateSource(entry.dest, entry.source);
    assertTextContent(entry.dest, entry.content);
    files.push({
      path: entry.dest,
      capability: entry.category,
      source: entry.source,
      write_mode: writeModeFor(entry.dest),
      content_utf8: entry.content,
      content_sha256: sha256(entry.content),
    });
  }
  if (violations.length) {
    fail(
      'policy_contradiction',
      `repo class ${profile.name} would materialize forbidden paths: ${violations.join(', ')}`,
    );
  }
  // Path order, not readdir order: identical inputs must give identical bytes
  // on every filesystem.
  files.sort((a, b) => byCodeUnit(a.path, b.path));
  return files;
}

// GitHub reads .github/CODEOWNERS before a root CODEOWNERS, so writing the
// org file into a repository that owns its root file would silently replace
// the repository's ownership rules (B-08). buildSeedPayload already skips it.
const DOT_GITHUB_CODEOWNERS = '.github/CODEOWNERS';

function compileMandatory(mandatory, profile, repoName, facts) {
  const files = Array.isArray(mandatory.files) ? mandatory.files : [];
  const exempt = (mandatory.exceptions || []).some((e) => e && e.repo === repoName);
  const effective = [];
  const waived = [];
  for (const file of files) {
    if (!file || typeof file.path !== 'string' || !file.path) {
      fail('contract', `${MANDATORY_PATH} has an entry without a path`);
    }
    assertSafeDest(file.path);
    const rootCodeowners = file.path === DOT_GITHUB_CODEOWNERS && facts.has_root_codeowners;
    if (exempt || rootCodeowners || waivesMandatoryFile(profile, file.path)) {
      if (!waived.includes(file.path)) waived.push(file.path);
      continue;
    }
    const req = { path: file.path, mode: file.mode };
    if (file.source !== undefined) {
      // Reconciliation reads this path from the authority checkout and writes
      // its bytes into consumer PRs, so it must name an org template — never
      // an arbitrary runner path.
      assertTemplateSource(file.path, file.source);
      req.source = file.source;
    }
    effective.push(req);
  }
  return { effective, waived };
}

function assertTemplateSource(dest, source) {
  if (typeof source !== 'string' || !source.startsWith('templates/')) {
    fail('unsafe_path', `template source for ${dest} must be under templates/, got ${JSON.stringify(source)}`);
  }
  assertSafeDest(source);
}

/**
 * Desired repository settings: defaults, then every override naming the repo
 * in file order. Identical to the inline merge in enforce-policies.yml and
 * repo-birth-bootstrap.yml, minus settings never auto-applied.
 */
function compileRepoSettings(settings, repoName) {
  const defaults = settings.defaults || {};
  const overrides = (settings.overrides || [])
    .filter((o) => o && Array.isArray(o.repos) && o.repos.includes(repoName))
    .reduce((acc, o) => ({ ...acc, ...o, repos: undefined }), {});
  const desired = { ...defaults, ...overrides };
  delete desired.repos;
  for (const key of NEVER_AUTO_APPLIED_SETTINGS) delete desired[key];
  return desired;
}

function compileLabels(labels, enabled) {
  if (!enabled) return { enabled: false, items: [] };
  if (!labels.length) fail('policy_contradiction', `${LABELS_PATH} parses to no labels`);
  return {
    enabled: true,
    items: labels.map((l) => ({ name: l.name, color: l.color, description: l.description })),
  };
}

// ── public API ──────────────────────────────────────────────────────────────

/**
 * Compile the governance plan for one target.
 *
 * @param {object} input
 * @param {typeof import('fs')} input.fs  reads templates/ relative to cwd
 * @param {object} [input.authority]  from loadAuthority(); loaded from fs when omitted
 * @param {string} input.authoritySha  exact 40-hex Quantum-L9/.github revision
 * @param {string} input.repository  owner/name of the target
 * @param {object} input.facts  {marker_state, marker_text?, has_root_codeowners,
 *   has_python, has_package_json}
 * @param {string|null} [input.requestedClass]  explicit operator class request
 * @returns {object} a schema-valid plan with its digest
 */
function compileGovernancePlan({ fs, authority, authoritySha, repository, facts, requestedClass = null } = {}) {
  if (!fs) fail('contract', 'compileGovernancePlan requires fs');
  if (typeof authoritySha !== 'string' || !SHA_RE.test(authoritySha)) {
    fail('authority_identity', `authority SHA must be 40 lowercase hex chars, got ${JSON.stringify(authoritySha)}`);
  }
  if (typeof repository !== 'string' || !REPOSITORY_RE.test(repository)) {
    fail('contract', `target repository must be owner/name, got ${JSON.stringify(repository)}`);
  }
  const auth = authority || loadAuthority(fs);
  const repoName = repository.split('/')[1];
  const normalizedFacts = normalizeFacts(facts);

  const decision = decideClass(auth.classes, repoName, normalizedFacts, requestedClass);
  const profile = resolveProfile(auth.classes, decision.name, { strict: true });

  const materialize = compileMaterialize(fs, profile, normalizedFacts, repository);
  const labelsEnabled = profile.remote_apply.labels === true;
  const settingsEnabled = profile.remote_apply.repo_settings === true;

  const plan = {
    schema: PLAN_SCHEMA,
    compiler: { name: COMPILER_NAME, contract_version: CONTRACT_VERSION },
    authority: { repository: AUTHORITY_REPOSITORY, sha: authoritySha },
    target: { repository, repo_name: repoName, facts: normalizedFacts },
    repo_class: { name: profile.name, resolved_from: decision.resolved_from },
    capabilities: [...profile.seed_categories],
    materialize: { files: materialize },
    inherit: { paths: [...profile.inherit] },
    forbid: { paths: [...profile.forbid] },
    mandatory_files: compileMandatory(auth.mandatory, profile, repoName, normalizedFacts),
    remote_apply: {
      labels: compileLabels(auth.labels, labelsEnabled),
      repo_settings: { enabled: settingsEnabled, desired: compileRepoSettings(auth.settings, repoName) },
    },
    attestation: {
      // What repo-birth-bootstrap.yml reads back from the remote. The org never
      // writes the class marker, so it is required only where it is the source
      // of the class decision; a repository classed by an org override, the
      // default, or an operator request legitimately carries none.
      required_present: [
        'README.md',
        'LICENSE',
        ...(decision.resolved_from === 'marker' ? [auth.classes.marker_path] : []),
      ],
      required_absent: [...profile.forbid],
      verify_class_marker: true,
      verify_remote_apply: labelsEnabled || settingsEnabled,
    },
  };
  plan.digest = { algorithm: 'sha256', canonicalization: CANONICALIZATION, value: computePlanDigest(plan) };

  const errors = compileSchema(auth.schema)(plan);
  if (errors.length) fail('contract', `compiled plan violates ${SCHEMA_PATH}: ${errors.join('; ')}`);
  return plan;
}

/**
 * Everything a mutating adapter must check before it writes (GOV-028):
 * schema, digest, authority, and target identity. Returns the plan when valid.
 *
 * @param {object} plan
 * @param {object} expect
 * @param {object} expect.schema  parsed plan schema
 * @param {string} expect.authoritySha
 * @param {string} expect.repository
 * @param {string} [expect.digest]  expected plan digest, when the caller holds one
 * @returns {object}
 */
function verifyPlan(plan, { schema, authoritySha, repository, digest } = {}) {
  if (!schema) fail('contract', 'verifyPlan requires the plan schema');
  // Identity is not optional: a caller that omits it would otherwise verify a
  // plan compiled for any revision or any repository.
  if (typeof authoritySha !== 'string' || !SHA_RE.test(authoritySha)) {
    fail('contract', 'verifyPlan requires the expected 40-hex authoritySha');
  }
  if (typeof repository !== 'string' || !REPOSITORY_RE.test(repository)) {
    fail('contract', 'verifyPlan requires the expected owner/name repository');
  }
  const errors = compileSchema(schema)(plan);
  if (errors.length) fail('contract', `plan is not schema-valid: ${errors.join('; ')}`);
  const recomputed = computePlanDigest(plan);
  if (recomputed !== plan.digest.value) {
    fail('digest', `plan digest ${plan.digest.value} does not match its content (${recomputed})`);
  }
  if (digest != null && digest !== plan.digest.value) {
    fail('digest', `plan digest ${plan.digest.value} is not the expected ${digest}`);
  }
  if (plan.authority.sha !== authoritySha) {
    fail('authority_identity', `plan compiled at ${plan.authority.sha}, expected ${authoritySha}`);
  }
  if (plan.target.repository !== repository) {
    fail('authority_identity', `plan targets ${plan.target.repository}, invoked for ${repository}`);
  }
  const seen = new Set();
  for (const file of plan.materialize.files) {
    assertSafeDest(file.path);
    if (seen.has(file.path)) fail('contract', `plan materializes ${file.path} more than once`);
    seen.add(file.path);
    if (!plan.capabilities.includes(file.capability)) {
      fail('policy_contradiction', `plan materializes ${file.path} under unauthorized capability ${file.capability}`);
    }
    if (sha256(file.content_utf8) !== file.content_sha256) {
      fail('digest', `content SHA-256 mismatch for ${file.path}`);
    }
    if (matchPattern(plan.forbid.paths, file.path)) {
      fail('policy_contradiction', `plan materializes forbidden path ${file.path}`);
    }
  }
  return plan;
}

/**
 * An operator category filter may only narrow an authorized plan (C-05,
 * GOV-012). Requesting a capability the plan does not authorize is refused,
 * never manufactured from lower-level payload construction (B-10).
 *
 * @param {object} plan
 * @param {string[]|null} requested  capability names; null/empty = the whole plan
 * @returns {object[]} the materialize entries to execute
 */
function narrowMaterialization(plan, requested) {
  if (requested == null || requested.length === 0) return [...plan.materialize.files];
  const unauthorized = requested.filter((c) => !plan.capabilities.includes(c));
  if (unauthorized.length) {
    fail(
      'policy_contradiction',
      `requested capabilities not authorized for ${plan.target.repository} ` +
        `(class ${plan.repo_class.name}): ${unauthorized.join(', ')}`,
    );
  }
  return plan.materialize.files.filter((f) => requested.includes(f.capability));
}

/**
 * Production provenance (B-20): a plan may only name a revision whose bytes
 * are the bytes it compiled. `gitStatus` is `git status --porcelain
 * --ignored=matching --untracked-files=all` over AUTHORITY_INPUTS: modified,
 * untracked, AND git-ignored files all reach the compiler (templates are read
 * with readdir), so any output means the plan is not HEAD's plan. `toplevel`
 * must be this repository's own root: inside an enclosing foreign checkout,
 * HEAD names someone else's commit.
 *
 * @param {{headSha: string, authoritySha: string, gitStatus: string, toplevel: string, root: string}} facts
 */
function assertCleanAuthority({ headSha, authoritySha, gitStatus, toplevel, root }) {
  if (typeof toplevel !== 'string' || typeof root !== 'string' || !toplevel || !root) {
    fail('authority_identity', 'cannot resolve the authority checkout root');
  }
  if (toplevel !== root) {
    fail('authority_identity', `git resolves ${toplevel}, not this authority checkout ${root}`);
  }
  if (!SHA_RE.test(headSha || '')) fail('authority_identity', `cannot resolve checkout HEAD (${headSha})`);
  if (headSha !== authoritySha) {
    fail('authority_identity', `checkout is at ${headSha}, not the asserted authority ${authoritySha}`);
  }
  if ((gitStatus || '').trim()) {
    fail(
      'authority_identity',
      `authority inputs (policy, templates, schema, compiler) differ from ${authoritySha}; ` +
        `commit or remove them before a production compile:\n${gitStatus.trim()}`,
    );
  }
}

// ── CLI ─────────────────────────────────────────────────────────────────────

// Absolute paths only: resolving `git` through PATH would let a writable PATH
// entry substitute it (Sonar S4036).
const GIT_CANDIDATES = Object.freeze(['/usr/bin/git', '/usr/local/bin/git', '/opt/homebrew/bin/git']);

const VALUE_OPTIONS = Object.freeze(['--repo', '--authority-sha', '--marker-file', '--class']);
const FLAG_OPTIONS = Object.freeze([
  '--marker-absent',
  '--has-root-codeowners',
  '--has-python',
  '--has-package-json',
  '--pretty',
]);

function parseArgs(argv) {
  const args = { flags: new Set() };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (VALUE_OPTIONS.includes(a)) {
      if (i + 1 >= argv.length) fail('contract', `${a} needs a value`);
      args[a.slice(2)] = argv[++i];
    } else if (FLAG_OPTIONS.includes(a)) {
      args.flags.add(a.slice(2));
    } else if (a.startsWith('--')) {
      // A mistyped fact flag would otherwise be dropped and silently change
      // the target facts, and with them the plan.
      fail('contract', `unknown option ${a} (known: ${[...VALUE_OPTIONS, ...FLAG_OPTIONS].join(', ')})`);
    } else {
      fail('contract', `unexpected argument ${a}`);
    }
  }
  return args;
}

function main(argv) {
  const fs = require('node:fs');
  const path = require('node:path');
  const { execFileSync } = require('node:child_process');
  const args = parseArgs(argv);
  // Resolve operator paths against the caller's directory before moving to
  // the authority root.
  const markerFile = args['marker-file'] ? path.resolve(args['marker-file']) : null;
  const root = fs.realpathSync(path.resolve(__dirname, '..'));
  process.chdir(root);

  if (!args.repo) fail('contract', '--repo owner/name is required');
  if (!args['authority-sha']) fail('contract', '--authority-sha <40-hex|HEAD> is required');
  const markerAbsent = args.flags.has('marker-absent');
  if (markerAbsent === Boolean(markerFile)) {
    fail('missing_fact', 'pass exactly one of --marker-absent or --marker-file <path>');
  }

  const git = GIT_CANDIDATES.find((p) => fs.existsSync(p));
  if (!git) fail('authority_identity', 'git not found; cannot prove authority provenance');
  const run = (gitArgs) => execFileSync(git, gitArgs, { encoding: 'utf8' });
  const headSha = run(['rev-parse', 'HEAD']).trim();
  const authoritySha = args['authority-sha'] === 'HEAD' ? headSha : args['authority-sha'];
  assertCleanAuthority({
    headSha,
    authoritySha,
    gitStatus: run(['status', '--porcelain', '--ignored=matching', '--untracked-files=all', '--', ...AUTHORITY_INPUTS]),
    toplevel: fs.realpathSync(run(['rev-parse', '--show-toplevel']).trim()),
    root,
  });

  const facts = {
    marker_state: markerAbsent ? 'absent' : 'present',
    has_root_codeowners: args.flags.has('has-root-codeowners'),
    has_python: args.flags.has('has-python'),
    has_package_json: args.flags.has('has-package-json'),
  };
  if (!markerAbsent) {
    try {
      facts.marker_text = fs.readFileSync(markerFile, 'utf8');
    } catch (err) {
      fail('missing_fact', `cannot read --marker-file ${markerFile}: ${err.code || err.message}`);
    }
  }

  const plan = compileGovernancePlan({
    fs,
    authoritySha,
    repository: args.repo,
    facts,
    requestedClass: args.class || null,
  });
  process.stdout.write(
    args.flags.has('pretty') ? `${JSON.stringify(plan, null, 2)}\n` : `${canonicalJson(plan)}\n`,
  );
}

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (err) {
    process.stderr.write(`compile-repo-governance: ${err.message}\n`);
    process.exit(err instanceof GovernanceCompileError ? 2 : 1);
  }
}

module.exports = {
  COMPILER_NAME,
  CONTRACT_VERSION,
  PLAN_SCHEMA,
  AUTHORITY_REPOSITORY,
  AUTHORITY_INPUTS,
  COMPILER_SOURCES,
  SCHEMA_PATH,
  ERROR_CODES,
  NEVER_AUTO_APPLIED_SETTINGS,
  GovernanceCompileError,
  canonicalJson,
  computePlanDigest,
  loadAuthority,
  compileGovernancePlan,
  verifyPlan,
  narrowMaterialization,
  assertCleanAuthority,
  compileRepoSettings,
  parseArgs,
};
