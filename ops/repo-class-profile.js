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
 *   - .github/workflows/enforce-policies.yml / preflight-scheduled.yml
 *     (mandatory-file waivers; read-only coverage for the preflight)
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

// ── Read-only mandatory-file coverage (preflight-scheduled.yml) ──────────────
// The monthly preflight used to call a repository "seeded" when it carried
// both .github/CODEOWNERS and .github/dependabot.yml, whatever its class. A
// self_governed repository waives both, and Cursor-Governance is excepted
// outright, so that number was raw presence, not compliance. The functions
// below assess the same policy enforce-policies.yml enforces — class from
// marker > override > default, the class's `mandatory_files_waive`, and the
// policy's repo `exceptions` — without ever turning an unread path into
// "present" or "missing".

const VERDICTS = Object.freeze({
  PRESENT: 'required-present',
  MISSING: 'required-missing',
  WAIVED: 'waived',
  UNOBSERVED: 'unobserved',
});

const statusOf = (e) => e?.status || 'error';

/**
 * Assess one repository's mandatory files against its class.
 *
 * @param {object} o
 * @param {object} o.doc          parsed repo-classes policy (loadRepoClasses)
 * @param {object} o.filesPolicy  parsed policies/mandatory-files.yml
 * @param {string} o.repoName     bare repository name
 * @param {(path: string) => Promise<string|null>} o.readText  file contents;
 *   null ONLY for a 404. Any other failure (403, 5xx, not a file) throws with
 *   `.status`, and the path is unobserved — never present, never missing.
 * @returns {Promise<{repo: string, status: 'exempt'|'unresolved'|'assessed',
 *   className: string|null, reason: string|null,
 *   files: Array<{path: string, verdict: string, detail: string}>}>}
 */
async function assessMandatoryFiles({ doc, filesPolicy, repoName, readText }) {
  const files = Array.isArray(filesPolicy?.files) ? filesPolicy.files : null;
  if (!files?.length || files.some((f) => typeof f?.path !== 'string' || !f.path)) {
    // A policy that names no paths would make every repository vacuously
    // compliant; that is an unreadable policy, not an empty obligation.
    throw new Error('mandatory-files policy declares no readable files list');
  }
  const exception = (filesPolicy.exceptions || []).find((e) => e?.repo === repoName);
  if (exception) {
    return {
      repo: repoName,
      status: 'exempt',
      className: null,
      reason: `mandatory-files exception: ${exception.reason || 'no reason recorded'}`,
      files: files.map((f) => ({ path: f.path, verdict: VERDICTS.WAIVED, detail: 'repo exception' })),
    };
  }
  const unresolved = (reason) => ({
    repo: repoName,
    status: 'unresolved',
    className: null,
    reason,
    files: files.map((f) => ({ path: f.path, verdict: VERDICTS.UNOBSERVED, detail: 'class unresolved' })),
  });
  let markerText;
  try {
    markerText = await readText(doc.marker_path);
  } catch (e) {
    return unresolved(`${doc.marker_path} unreadable (${statusOf(e)})`);
  }
  const decided = classForRepo(doc, repoName, markerText);
  if (decided.error) return unresolved(decided.error);
  const profile = resolveProfile(doc, decided.name);
  const out = [];
  for (const f of files) {
    if (waivesMandatoryFile(profile, f.path)) {
      out.push({ path: f.path, verdict: VERDICTS.WAIVED, detail: `waived by class ${profile.name}` });
      continue;
    }
    try {
      const text = await readText(f.path);
      out.push(text === null
        ? { path: f.path, verdict: VERDICTS.MISSING, detail: '404' }
        : { path: f.path, verdict: VERDICTS.PRESENT, detail: '' });
    } catch (e) {
      out.push({ path: f.path, verdict: VERDICTS.UNOBSERVED, detail: `unreadable (${statusOf(e)})` });
    }
  }
  return { repo: repoName, status: 'assessed', className: profile.name, reason: decided.source, files: out };
}

/**
 * Reduce per-repo assessments to an honest coverage summary.
 *
 * Denominator: repositories that are neither excepted nor without any
 * applicable required path. An unobserved repository stays IN the
 * denominator (it is not demonstrably compliant) and is listed separately.
 * Zero eligible repositories yields `pct: null`, never 100%.
 *
 * @param {Array<Awaited<ReturnType<typeof assessMandatoryFiles>>>} assessments
 */
function summarizeMandatoryCoverage(assessments) {
  const s = {
    total: assessments.length,
    exempt: [],
    notApplicable: [],
    compliant: [],
    noncompliant: [],
    unobserved: [],
    eligible: 0,
    pct: null,
  };
  for (const a of assessments) {
    if (a.status === 'exempt') {
      s.exempt.push({ repo: a.repo, reason: a.reason });
      continue;
    }
    if (a.status === 'unresolved') {
      s.unobserved.push({ repo: a.repo, reasons: [a.reason] });
      continue;
    }
    const required = a.files.filter((f) => f.verdict !== VERDICTS.WAIVED);
    if (!required.length) {
      s.notApplicable.push({ repo: a.repo, reason: `class ${a.className} waives every mandatory path` });
      continue;
    }
    const missing = required.filter((f) => f.verdict === VERDICTS.MISSING).map((f) => f.path);
    const unread = required.filter((f) => f.verdict === VERDICTS.UNOBSERVED);
    if (missing.length) {
      s.noncompliant.push({ repo: a.repo, className: a.className, missing, unobserved: unread.map((f) => f.path) });
    } else if (unread.length) {
      s.unobserved.push({ repo: a.repo, reasons: unread.map((f) => `${f.path} ${f.detail}`) });
    } else {
      s.compliant.push(a.repo);
    }
  }
  s.eligible = s.compliant.length + s.noncompliant.length + s.unobserved.length;
  s.pct = s.eligible ? Math.round((100 * s.compliant.length) / s.eligible) : null;
  return s;
}

/**
 * Render the summary as report findings. `level` is 'info' only when the
 * required coverage is demonstrably high: >= 90% compliant AND nothing
 * unobserved. A policy that could not be read is reported, never scored.
 *
 * @param {ReturnType<typeof summarizeMandatoryCoverage>|null} s
 * @param {{policyError?: string|null}} [opts]
 * @returns {{level: 'info'|'warn', line: string, sections: string[]}}
 */
function describeMandatoryCoverage(s, { policyError = null } = {}) {
  if (policyError || !s) {
    return {
      level: 'warn',
      line: `Mandatory-file compliance: UNOBSERVED — policy unreadable (${policyError || 'no summary'}); no repository counted compliant`,
      sections: [],
    };
  }
  const tail = `${s.noncompliant.length} missing a required file, ${s.unobserved.length} unobserved, ` +
    `${s.exempt.length} exempt, ${s.notApplicable.length} not applicable`;
  const line = s.eligible === 0
    ? `Mandatory-file compliance: no eligible repositories (${s.total} active; ${tail}) — compliance not computed`
    : `Mandatory-file compliance: ${s.compliant.length}/${s.eligible} eligible repos (${s.pct}%) — ${tail}`;
  const level = s.eligible > 0 && s.pct >= 90 && s.unobserved.length === 0 ? 'info' : 'warn';
  const sections = [];
  if (s.noncompliant.length) {
    sections.push(`## Missing required files\n\n${s.noncompliant
      .map((r) => `- \`${r.repo}\` (class \`${r.className}\`): ${r.missing.map((p) => `\`${p}\``).join(', ')}` +
        (r.unobserved.length ? `; unobserved: ${r.unobserved.map((p) => `\`${p}\``).join(', ')}` : ''))
      .join('\n')}`);
  }
  if (s.unobserved.length) {
    sections.push(`## Unobserved — not counted as compliant\n\n${s.unobserved
      .map((r) => `- \`${r.repo}\`: ${r.reasons.join('; ')}`).join('\n')}`);
  }
  if (s.exempt.length || s.notApplicable.length) {
    sections.push(`## Exempt / not applicable — outside the denominator\n\n${[...s.exempt, ...s.notApplicable]
      .map((r) => `- \`${r.repo}\`: ${r.reason}`).join('\n')}`);
  }
  return { level, line, sections };
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
  VERDICTS,
  assessMandatoryFiles,
  summarizeMandatoryCoverage,
  describeMandatoryCoverage,
};
