'use strict';

/**
 * Render a seed PR body from the canonical PR template with the one PR-body
 * renderer, Cursor-Governance `ops/scripts/compose_pr_body.py`, at the commit
 * `governance-pr.yml` pins. No hand-built body, nothing written into the
 * template, and no edit afterwards.
 *
 * The composer composes every section from git: Problem from the seed commit's
 * first body paragraph, Fix from its subject and later paragraphs, and Files
 * touched, Changes by intent, Type of Change, Risk, Evidence, Gates, Semantic
 * change, Reviewer focus and Protected-root from the measured diff. The seeder
 * only writes the seed commit message (seedCommitMessage).
 *
 * Fail closed: a fetched head that is not the seed commit, a wrong base, a
 * composer error, or any field the composer reports as needing an author stops
 * the PR — an incomplete body never opens.
 */

const os = require('node:os');
const path = require('node:path');

const TEMPLATE_PATH = '.github/pull_request_template.md';
const COMPOSER_PATH_IN_CHECKOUT = 'ops/scripts/compose_pr_body.py';

/**
 * The seed commit message: subject, the Problem paragraph (the composer's
 * Problem), the detail paragraphs (the composer's Fix, after the subject), then
 * trailers.
 * @param {{subject: string, problem: string, details?: string[], trailers?: string[]}} parts
 * @returns {string}
 */
function seedCommitMessage({ subject, problem, details = [], trailers = [] } = {}) {
  if (typeof subject !== 'string' || !subject.trim() || subject.includes('\n')) {
    throw new TypeError('seedCommitMessage: a one-line subject is required');
  }
  const para = typeof problem === 'string' ? problem.replace(/\s+/g, ' ').trim() : '';
  if (!para) throw new TypeError('seedCommitMessage: a Problem paragraph is required');
  // The composer skips "Word: value" lines as trailers; a paragraph that starts
  // like one would vanish from Problem.
  if (/^[A-Za-z-]+:\s/.test(para)) throw new Error('seedCommitMessage: the Problem paragraph must not read as a trailer');
  for (const d of details) {
    if (typeof d !== 'string' || !d.trim()) throw new TypeError('seedCommitMessage: empty detail paragraph');
    if (d.split('\n').every((line) => /^[A-Za-z-]+:\s/.test(line.trim()))) {
      throw new Error('seedCommitMessage: a detail paragraph must not read as trailers');
    }
  }
  const blocks = [subject.trim(), para, ...details.map((d) => d.trim())];
  return [...blocks, ...(trailers.length ? [trailers.join('\n')] : [])].join('\n\n');
}

const code = (p) => `\`${p}\``;

/**
 * The seed facts the commit message carries: the Problem paragraph and the
 * detail paragraphs the composer renders as Fix. Reviewer focus and every other
 * section are the composer's own. Deterministic: the same seed, the same text.
 *
 * @param {object} o
 * @param {string[]} o.added      paths the commit adds
 * @param {string[]} [o.restored] managed paths it restores to the org render
 * @param {{name: string, resolved_from?: string, inherit?: string[]}} o.profile  repo class
 * @param {string} o.branch       seed branch
 * @param {string} o.sourceSha    Quantum-L9/.github commit the payload came from
 * @param {string} o.seeder       workflow file that opened the PR
 * @param {boolean} [o.hasRootCodeowners]
 * @returns {{problem: string, details: string[]}}
 */
/** `name` (resolved_from) — the repo class as the narratives name it. */
function classLabel(profile) {
  const from = profile.resolved_from ? ` (${profile.resolved_from})` : '';
  return code(profile.name) + from;
}

function seedNarrative({
  added = [], restored = [], profile, branch, sourceSha, seeder, hasRootCodeowners = false,
} = {}) {
  if (!profile?.name) throw new TypeError('seedNarrative: profile is required');
  if (!added.length && !restored.length) throw new RangeError('seedNarrative: a seed writes at least one path');
  for (const [name, v] of Object.entries({ branch, sourceSha, seeder })) {
    if (typeof v !== 'string' || !v) throw new TypeError(`seedNarrative: ${name} is required`);
  }
  const cls = classLabel(profile);
  const problem = [
    added.length
      ? `This repository is missing ${added.length} file(s) that its repo class ${cls} materializes from ${code('Quantum-L9/.github')} (${code('policies/repo-classes.yml')}).`
      : '',
    restored.length
      ? `${restored.map(code).join(', ')} drifted from the org render for this repository root (ADR ${code('docs/adr/0019-dependabot-managed-rendered.md')}).`
      : '',
    profile.inherit?.length
      ? `Inherited from the org ${code('.github')} repository and deliberately not copied here: ${profile.inherit.map(code).join(', ')}.`
      : '',
  ].filter(Boolean).join(' ');
  const onBranch = `in one commit on ${code(branch)}`;
  let summary;
  if (!restored.length) {
    summary = `Adds only the ${added.length} missing file(s), ${onBranch}. Existing files were left untouched (missing-only seed).`;
  } else if (!added.length) {
    summary = `Restores ${restored.length} managed file(s) to the org render, ${onBranch}. No file is added and no other existing file was touched.`;
  } else {
    summary = `Adds the ${added.length} missing file(s) and restores ${restored.length} managed file(s) to the org render, ${onBranch}. No other existing file was touched.`;
  }
  const facts = [
    `- Source: ${code('Quantum-L9/.github@' + sourceSha)}, class ${cls}.`,
    hasRootCodeowners ? `- Root ${code('CODEOWNERS')} is present and is not overridden by ${code('.github/CODEOWNERS')}.` : null,
    `- A governance caller, where added, is advisory (${code('strict')} defaults false). CI callers are not distributed from ${code('Quantum-L9/.github')}; see ${code('docs/BOUNDARIES.md')}.`,
    `- While this PR is open the seeder leaves ${code(branch)} alone, so review fixes can be committed onto it.`,
  ].filter(Boolean);
  if (restored.length) {
    facts.push(`- To keep a local divergence instead, opt the repository out of restores with ${code('.l9/no-sync')}.`);
  }
  const origin = `Opened by ${code('Quantum-L9/.github ' + seeder)}; the PR body is the org PR template composed by ${code('compose_pr_body.py')}.`;
  return { problem, details: [summary, facts.join('\n'), origin] };
}

/**
 * The Manual Update (continuous-sync.yml) counterpart of seedNarrative.
 *
 * @param {object} o
 * @param {Array<{path: string, why: string, action: string, existed?: boolean}>} o.plan
 * @param {{name: string, resolved_from?: string}} o.profile
 * @param {string} o.branch
 * @param {string} o.sourceSha
 * @param {Record<string,string>} [o.pins]   governance callee pins, for re-pin rows
 * @param {string[]} [o.notChanged]          paths reported but deliberately left
 * @returns {{problem: string, details: string[]}}
 */
function syncNarrative({ plan = [], profile, branch, sourceSha, pins = {}, notChanged = [] } = {}) {
  if (!profile?.name) throw new TypeError('syncNarrative: profile is required');
  if (!plan.length) throw new RangeError('syncNarrative: a sync changes at least one path');
  for (const [name, v] of Object.entries({ branch, sourceSha })) {
    if (typeof v !== 'string' || !v) throw new TypeError(`syncNarrative: ${name} is required`);
  }
  const cls = classLabel(profile);
  const problem = `${plan.length} governance file(s) managed by ${code('Quantum-L9/.github')} drifted from the org standard for this repository's class ${cls} (${code('policies/repo-classes.yml')}).`;
  const detail = (d) => {
    if (d.action === 'delete') return ` — this class inherits it live from ${code('Quantum-L9/.github')}; this local copy is byte-identical to the org file and blocks that`;
    if (d.why === 're-pin') {
      const moved = Object.entries(pins).map(([k, v]) => code(`governance-${k}.yml@${v}`)).join(' / ');
      return ` — ${code('uses:')} pins moved to ${moved}; the rest of the file is unchanged`;
    }
    return ' — replaced with the org bytes';
  };
  const changes = [
    ...plan.map((d) => `- **${d.why}** ${code(d.path)}${detail(d)}`),
    ...notChanged.map((t) => `- not changed: ${t}`),
    `- Source: ${code('Quantum-L9/.github@' + sourceSha)}, class ${cls}.`,
    `- To keep a local divergence instead, close this PR and add ${code('.l9/no-sync')}.`,
  ].join('\n');
  return {
    problem,
    details: [
      `Restores ${plan.length} file(s) in one commit on ${code(branch)}.`,
      changes,
      `Opened by a manual Apply of ${code('Quantum-L9/.github continuous-sync.yml')}; the PR body is the org PR template composed by ${code('compose_pr_body.py')}.`,
    ],
  };
}

/**
 * Fetch the seed commit and its base into a scratch repository and compose.
 *
 * @param {object} o
 * @param {Function} o.exec          execFileSync-compatible: (cmd, args, opts) => stdout
 * @param {object}   o.fs            node:fs
 * @param {string}   [o.workdir]     empty scratch directory; by default one is created
 *                                   under the OS temp dir and removed afterwards
 * @param {string}   o.remoteUrl     repository URL (no credentials in it)
 * @param {string}   o.branch        seed branch to fetch
 * @param {string}   o.headSha       the seed commit the branch must point at
 * @param {string}   o.baseSha       the default-branch commit it was built on
 * @param {string}   o.template      the canonical PR template text, unchanged
 * @param {string}   o.composerRoot  checkout of Cursor-Governance at the pinned commit
 * @param {string}   [o.token]       GitHub token; sent as an HTTP header via env, never argv
 * @returns {{body: string, handoff: object}}
 */
function renderSeedPrBody({ workdir, fs, ...rest } = {}) {
  if (!fs) throw new TypeError('renderSeedPrBody: fs is required');
  if (workdir) return composeIn({ ...rest, fs, workdir });
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'seed-pr-'));
  try {
    return composeIn({ ...rest, fs, workdir: scratch });
  } finally {
    fs.rmSync(scratch, { recursive: true, force: true });
  }
}

/**
 * The composer's environment, built from an allowlist rather than by removing
 * known secrets. The composer runs the target repository's own
 * validate_root_file_protection.py from the fetched branch, so it must not
 * inherit SEED_GIT_TOKEN, the GIT_CONFIG_* auth header, actions/github-script's
 * INPUT_* (which carries its github-token) or the runner's ACTIONS_* tokens.
 * Only the git fetch above needs a credential.
 *
 * @param {Record<string, string|undefined>} source  usually process.env
 * @returns {Record<string, string>}
 */
function composerEnv(source) {
  const keep = (k) => COMPOSER_ENV_KEYS.has(k) || k.startsWith('LC_');
  const env = Object.fromEntries(
    Object.entries(source).filter(([k, v]) => keep(k) && typeof v === 'string'),
  );
  return { ...env, GIT_TERMINAL_PROMPT: '0' };
}

const COMPOSER_ENV_KEYS = new Set([
  'PATH', 'HOME', 'LANG', 'TMPDIR', 'TEMP', 'TMP', 'LD_LIBRARY_PATH', 'pythonLocation',
]);

function composeIn({
  // `exec` is execFileSync-compatible (argv array, no shell); bound as execFile.
  exec: execFile, fs, workdir, remoteUrl, branch, headSha, baseSha, template, composerRoot, token = '',
}) {
  for (const [name, v] of Object.entries({ workdir, remoteUrl, branch, headSha, baseSha, template, composerRoot })) {
    if (typeof v !== 'string' || !v) throw new TypeError(`renderSeedPrBody: ${name} is required`);
  }
  if (/:\/\/[^/]*@/.test(remoteUrl)) throw new Error('renderSeedPrBody: remoteUrl must not carry credentials');
  const composer = path.join(composerRoot, COMPOSER_PATH_IN_CHECKOUT);
  if (!fs.existsSync(composer)) throw new Error(`composer not found at ${composer} — check out Cursor-Governance at the pin first`);

  // Credentials travel as git config from the environment (GIT_CONFIG_*), so
  // they are in neither argv nor the scratch repository's config file.
  const env = { ...process.env, GIT_TERMINAL_PROMPT: '0' };
  if (token) {
    const basic = Buffer.from(`x-access-token:${token}`).toString('base64');
    env.GIT_CONFIG_COUNT = '1';
    env.GIT_CONFIG_KEY_0 = 'http.extraheader';
    env.GIT_CONFIG_VALUE_0 = `AUTHORIZATION: basic ${basic}`;
  }
  const git = (...args) => String(execFile('git', ['-C', workdir, ...args], { encoding: 'utf8', env })).trim();

  git('init', '-q');
  // Depth 2 is the seed commit and its parent (the base): all the range needs.
  git('fetch', '-q', '--no-tags', '--depth=2', remoteUrl, `+refs/heads/${branch}:refs/remotes/seed/${branch}`);
  const fetched = git('rev-parse', `refs/remotes/seed/${branch}`);
  if (fetched !== headSha) {
    throw new Error(`${branch} points at ${fetched.slice(0, 7)}, not the seed commit ${headSha.slice(0, 7)} — not composing a body for another head`);
  }
  git('checkout', '-q', '--detach', headSha);
  const parent = git('rev-parse', 'HEAD^');
  if (parent !== baseSha) {
    throw new Error(`seed commit ${headSha.slice(0, 7)} is not built on ${baseSha.slice(0, 7)} (parent ${parent.slice(0, 7)})`);
  }

  const templateFile = path.join(workdir, '.seed-pr-template.md');
  const handoffFile = path.join(workdir, '.seed-pr-handoff.json');
  fs.writeFileSync(templateFile, template);
  // --remote: no local receipts exist on a seeder runner, so nothing is claimed
  // as measured that was not; the additive_only range is measured with the
  // repository's own validator or reported unmeasured.
  const body = String(execFile('python3', [
    composer, '--workspace', workdir, '--pr-base', baseSha,
    '--template', templateFile, '--remote', '--handoff', handoffFile,
  ], { encoding: 'utf8', env: composerEnv(process.env), maxBuffer: 16 * 1024 * 1024 }));
  const handoff = JSON.parse(fs.readFileSync(handoffFile, 'utf8'));
  if (!Array.isArray(handoff.needs_completion)) {
    throw new TypeError('composer handoff carries no needs_completion list — cannot prove the body is complete');
  }
  if (handoff.needs_completion.length) {
    throw new Error(`composed body is incomplete: ${handoff.needs_completion.join('; ')}`);
  }
  if (!body.trim()) throw new Error('composer returned an empty body');
  return { body, handoff };
}

module.exports = {
  TEMPLATE_PATH,
  COMPOSER_PATH_IN_CHECKOUT,
  seedCommitMessage,
  seedNarrative,
  syncNarrative,
  renderSeedPrBody,
  composerEnv,
};
