'use strict';

/**
 * Render a seed PR body from the canonical PR template with the one PR-body
 * renderer, Cursor-Governance `ops/scripts/compose_pr_body.py`, at the commit
 * `governance-pr.yml` pins. No hand-built body and no manual edit afterwards.
 *
 * The composer measures everything it can from git (Files touched, Changes by
 * intent, Problem, Type of Change, Risk, Evidence, Gates, Semantic change,
 * Protected-root). The two fields it cannot measure are written by the seeder
 * into its copy of the template before composing, so the composer keeps them:
 * Fix and Reviewer focus. The Problem paragraph travels in the seed commit's
 * body, where the composer reads it.
 *
 * Fail closed: a template whose author placeholders moved, a fetched head that
 * is not the seed commit, a composer error, or any field the composer still
 * reports as needing an author stops the PR — an incomplete body never opens.
 */

const os = require('node:os');
const path = require('node:path');

const TEMPLATE_PATH = '.github/pull_request_template.md';
// Author-owned placeholders in the canonical template, replaced verbatim.
const FIX_PLACEHOLDER =
  '<!-- What you changed to make the problem above go away. Note alternatives you rejected and why. -->';
const REVIEWER_PLACEHOLDER =
  '<!-- Where to look hardest. Trade-offs accepted. Deferred follow-ups, with issue links. -->';
const COMPOSER_PATH_IN_CHECKOUT = 'ops/scripts/compose_pr_body.py';

/**
 * The canonical template with the seeder's Fix and Reviewer focus written in.
 * @param {string} template  canonical `.github/pull_request_template.md` text
 * @param {{fix: string, reviewerFocus: string}} fields
 * @returns {string}
 */
function prepareSeedTemplate(template, { fix, reviewerFocus } = {}) {
  if (typeof template !== 'string') throw new TypeError('prepareSeedTemplate: template text is required');
  for (const [name, value] of [['fix', fix], ['reviewerFocus', reviewerFocus]]) {
    if (typeof value !== 'string' || !value.trim()) throw new TypeError(`prepareSeedTemplate: ${name} is required`);
  }
  for (const [name, placeholder] of [['Fix', FIX_PLACEHOLDER], ['Reviewer focus', REVIEWER_PLACEHOLDER]]) {
    if (template.split(placeholder).length !== 2) {
      throw new Error(`${TEMPLATE_PATH}: the ${name} placeholder is missing or repeated — the seeder cannot fill it`);
    }
  }
  return template.replace(FIX_PLACEHOLDER, fix.trim()).replace(REVIEWER_PLACEHOLDER, reviewerFocus.trim());
}

/**
 * The seed commit message: subject, the Problem paragraph the composer reads
 * from the commit body, then trailers.
 * @param {{subject: string, problem: string, trailers?: string[]}} parts
 * @returns {string}
 */
function seedCommitMessage({ subject, problem, trailers = [] } = {}) {
  if (typeof subject !== 'string' || !subject.trim() || subject.includes('\n')) {
    throw new TypeError('seedCommitMessage: a one-line subject is required');
  }
  const para = typeof problem === 'string' ? problem.replace(/\s+/g, ' ').trim() : '';
  if (!para) throw new TypeError('seedCommitMessage: a Problem paragraph is required');
  // The composer skips "Word: value" lines as trailers; a paragraph that starts
  // like one would vanish from Problem.
  if (/^[A-Za-z-]+:\s/.test(para)) throw new Error('seedCommitMessage: the Problem paragraph must not read as a trailer');
  return [subject.trim(), '', para, ...(trailers.length ? ['', ...trailers] : [])].join('\n');
}

const code = (p) => `\`${p}\``;

/**
 * The seed facts in the three author-owned places: the Problem paragraph (seed
 * commit body), Fix and Reviewer focus (prepared template). Deterministic: the
 * same seed renders the same text.
 *
 * @param {object} o
 * @param {string[]} o.added      paths the commit adds
 * @param {string[]} [o.restored] managed paths it restores to the org render
 * @param {{name: string, resolved_from?: string, inherit?: string[]}} o.profile  repo class
 * @param {string} o.branch       seed branch
 * @param {string} o.sourceSha    Quantum-L9/.github commit the payload came from
 * @param {string} o.seeder       workflow file that opened the PR
 * @param {boolean} [o.hasRootCodeowners]
 * @returns {{problem: string, fix: string, reviewerFocus: string}}
 */
function seedNarrative({
  added = [], restored = [], profile, branch, sourceSha, seeder, hasRootCodeowners = false,
} = {}) {
  if (!profile?.name) throw new TypeError('seedNarrative: profile is required');
  if (!added.length && !restored.length) throw new Error('seedNarrative: a seed writes at least one path');
  for (const [name, v] of Object.entries({ branch, sourceSha, seeder })) {
    if (typeof v !== 'string' || !v) throw new TypeError(`seedNarrative: ${name} is required`);
  }
  const cls = `${code(profile.name)}${profile.resolved_from ? ` (${profile.resolved_from})` : ''}`;
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
  const summary = restored.length
    ? `Adds the ${added.length} missing file(s) and restores ${restored.length} managed file(s) to the org render, in one commit on ${code(branch)}. No other existing file was touched.`
    : `Adds only the ${added.length} missing file(s), in one commit on ${code(branch)}. Existing files were left untouched (missing-only seed).`;
  const facts = [
    `- Source: ${code(`Quantum-L9/.github@${sourceSha}`)}, class ${cls}.`,
    hasRootCodeowners ? `- Root ${code('CODEOWNERS')} is present and is not overridden by ${code('.github/CODEOWNERS')}.` : null,
    `- A governance caller, where added, is advisory (${code('strict')} defaults false). CI callers are not distributed from ${code('Quantum-L9/.github')}; see ${code('docs/BOUNDARIES.md')}.`,
    `- While this PR is open the seeder leaves ${code(branch)} alone, so review fixes can be committed onto it.`,
  ].filter(Boolean);
  const origin = `Opened by ${code(`Quantum-L9/.github ${seeder}`)}; this body was rendered from the org PR template by ${code('compose_pr_body.py')}.`;
  const fix = [summary, '', ...facts, '', origin].join('\n');
  const reviewerFocus = [
    `- Each seeded file is listed under Files touched; check it against what this repository already does (routing in ${code('SECURITY.md')} and the issue forms, owners in ${code('.github/CODEOWNERS')}).`,
    restored.length
      ? `- ${restored.map(code).join(', ')} replaces local edits with the org render; opt the repository out of restores with ${code('.l9/no-sync')}.`
      : `- Nothing existing is overwritten; a file you do not want can be deleted from this branch before merge.`,
    "- Consumer CI on this PR is not observed by the seeder; merge only on this repository's own green checks.",
  ].join('\n');
  return { problem, fix, reviewerFocus };
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
 * @returns {{problem: string, fix: string, reviewerFocus: string}}
 */
function syncNarrative({ plan = [], profile, branch, sourceSha, pins = {}, notChanged = [] } = {}) {
  if (!profile?.name) throw new TypeError('syncNarrative: profile is required');
  if (!plan.length) throw new Error('syncNarrative: a sync changes at least one path');
  for (const [name, v] of Object.entries({ branch, sourceSha })) {
    if (typeof v !== 'string' || !v) throw new TypeError(`syncNarrative: ${name} is required`);
  }
  const cls = `${code(profile.name)}${profile.resolved_from ? ` (${profile.resolved_from})` : ''}`;
  const problem = `${plan.length} governance file(s) managed by ${code('Quantum-L9/.github')} drifted from the org standard for this repository's class ${cls} (${code('policies/repo-classes.yml')}).`;
  const detail = (d) => {
    if (d.action === 'delete') return ` — this class inherits it live from ${code('Quantum-L9/.github')}; this local copy is byte-identical to the org file and blocks that`;
    if (d.why === 're-pin') return ` — ${code('uses:')} pins moved to ${Object.entries(pins).map(([k, v]) => code(`governance-${k}.yml@${v}`)).join(' / ')}; the rest of the file is unchanged`;
    return ' — replaced with the org bytes';
  };
  const fix = [
    `Restores ${plan.length} file(s) in one commit on ${code(branch)}:`,
    '',
    ...plan.map((d) => `- **${d.why}** ${code(d.path)}${detail(d)}`),
    ...notChanged.map((t) => `- not changed: ${t}`),
    '',
    `- Source: ${code(`Quantum-L9/.github@${sourceSha}`)}, class ${cls}.`,
    '',
    `Opened by a manual Apply of ${code('Quantum-L9/.github continuous-sync.yml')}; this body was rendered from the org PR template by ${code('compose_pr_body.py')}.`,
  ].join('\n');
  const reviewerFocus = [
    '- Each restored file replaces local edits with the org version; Files touched lists every path.',
    `- To keep a local divergence, close this PR and add ${code('.l9/no-sync')} to opt the repository out of governance sync.`,
    "- Consumer CI on this PR is not observed by Manual Update; merge only on this repository's own green checks.",
  ].join('\n');
  return { problem, fix, reviewerFocus };
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
 * @param {string}   o.template      prepared template text (prepareSeedTemplate)
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

function composeIn({
  exec, fs, workdir, remoteUrl, branch, headSha, baseSha, template, composerRoot, token = '',
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
    Object.assign(env, {
      GIT_CONFIG_COUNT: '1',
      GIT_CONFIG_KEY_0: 'http.extraheader',
      GIT_CONFIG_VALUE_0: `AUTHORIZATION: basic ${basic}`,
    });
  }
  const git = (...args) => String(exec('git', ['-C', workdir, ...args], { encoding: 'utf8', env })).trim();

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
  const body = String(exec('python3', [
    composer, '--workspace', workdir, '--pr-base', baseSha,
    '--template', templateFile, '--remote', '--handoff', handoffFile,
  ], { encoding: 'utf8', env: { ...process.env }, maxBuffer: 16 * 1024 * 1024 }));
  const handoff = JSON.parse(fs.readFileSync(handoffFile, 'utf8'));
  if (!Array.isArray(handoff.needs_completion)) {
    throw new Error('composer handoff carries no needs_completion list — cannot prove the body is complete');
  }
  if (handoff.needs_completion.length) {
    throw new Error(`composed body is incomplete: ${handoff.needs_completion.join('; ')}`);
  }
  if (!body.trim()) throw new Error('composer returned an empty body');
  return { body, handoff };
}

module.exports = {
  TEMPLATE_PATH,
  FIX_PLACEHOLDER,
  REVIEWER_PLACEHOLDER,
  COMPOSER_PATH_IN_CHECKOUT,
  prepareSeedTemplate,
  seedCommitMessage,
  seedNarrative,
  syncNarrative,
  renderSeedPrBody,
};
