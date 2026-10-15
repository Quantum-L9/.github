'use strict';

/**
 * Decision and rendering logic for governance-report.yml, the weekly advisory
 * posture issue. The workflow stays a thin caller: it reads metadata through
 * the API and hands it here.
 *
 * Why this exists (#102): the report caught every Actions-permission read
 * failure as `unreadable`, left it out of `blocked`, and then printed "All
 * repos permit cross-repo reusable workflows" whenever `blocked` was empty —
 * an all-clear with no evidence behind it. `selected` allow-lists were
 * counted as fine without reading the list. Here a repository is ALLOWED
 * only when it is demonstrably allowed, BLOCKED only when a blocking policy
 * was observed, and UNKNOWN otherwise; the all-clear sentence is reserved for
 * a report in which every repository was verified allowed.
 *
 * The posture is advisory: nothing here fails a run or gates anything.
 */

const STATES = Object.freeze({ ALLOWED: 'allowed', BLOCKED: 'blocked', UNKNOWN: 'unknown' });

const statusOf = (e) => e?.status || 'error';

/**
 * The reusable-workflow references the distributed governance caller makes,
 * e.g. `Quantum-L9/.github/.github/workflows/governance-pr.yml@<sha>`.
 * These are what a consumer's Actions policy must admit. Every such `uses:`
 * is returned whatever its ref, so one not pinned to a full SHA reaches
 * reusableWorkflowActionRefs() and is refused there instead of being dropped.
 *
 * @param {string} callerText contents of policies/governance-caller.yml
 * @returns {string[]}
 */
function callerRefs(callerText) {
  return [...String(callerText || '').matchAll(/^\s*uses:\s*(Quantum-L9\/\.github\/\.github\/workflows\/[^@\s]+@[^\s#]+)/gm)]
    .map((m) => m[1]);
}

/**
 * Does one `patterns_allowed` entry admit a reference? `*` matches any run
 * of characters (owner and repository names compare case-insensitively).
 * Deliberately literal: a pattern this matcher cannot prove admits the
 * reference does not count as allowing it.
 *
 * @param {string} pattern
 * @param {string} ref
 */
function patternCovers(pattern, ref) {
  if (typeof pattern !== 'string' || !pattern) return false;
  const re = new RegExp(`^${pattern.split('*').map((p) => p.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('.*')}$`, 'i');
  return re.test(ref);
}

/**
 * Remote action and reusable-workflow references in a workflow file
 * (`uses: owner/repo[/path]@ref`). Local (`./`) and `docker://` steps are not
 * governed by the allow-list and are left out.
 *
 * @param {string} workflowText
 * @returns {string[]}
 */
function workflowActionRefs(workflowText) {
  return [...String(workflowText || '').matchAll(/^\s*(?:-\s*)?uses:\s*([A-Za-z0-9_.-]+\/[^@\s#]+@[^\s#]+)/gm)]
    .map((m) => m[1]);
}

// `owner/repo/.github/workflows/<file>.yml@<40-hex sha>`: the only caller
// reference shape whose workflow bytes are fixed, so the only one evaluated.
const PINNED_WORKFLOW_REF = /^(Quantum-L9)\/(\.github)\/(\.github\/workflows\/[^@/]+\.ya?ml)@([0-9a-f]{40})$/;

/**
 * The actions the governance caller's reusable workflows run in turn. A
 * consumer's `selected` policy has to admit these too, or the caller's jobs
 * cannot start. Each workflow is read at the exact commit the caller pins —
 * never at this repository's current checkout, which is a later commit and
 * may run different actions. A reference that is not a Quantum-L9/.github
 * workflow pinned to a full SHA, or a pinned workflow that cannot be read,
 * rejects, so the caller reports UNKNOWN instead of a partial or
 * substituted list.
 *
 * @param {string[]} refs caller references (callerRefs)
 * @param {(o: {owner: string, repo: string, path: string, ref: string}) => Promise<string>} readAt
 *   workflow text at that exact commit; throws when it cannot be read
 * @returns {Promise<string[]>} unique references, caller references excluded
 */
async function reusableWorkflowActionRefs(refs, readAt) {
  const out = new Set();
  for (const ref of refs) {
    const m = PINNED_WORKFLOW_REF.exec(ref);
    if (!m) throw new Error(`not a Quantum-L9/.github reusable workflow pinned to a full SHA: ${ref}`);
    const text = await readAt({ owner: m[1], repo: m[2], path: m[3], ref: m[4] });
    if (typeof text !== 'string') throw new Error(`${m[3]}@${m[4]} returned no workflow text`);
    for (const used of workflowActionRefs(text)) out.add(used);
  }
  return [...out].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

const OWNER = 'quantum-l9';
const GITHUB_OWNED = new Set(['actions', 'github']);

/**
 * Decide one reference under a repository's `selected` policy, following
 * GitHub's documented rules for "Allow OWNER, and select non-OWNER, actions
 * and reusable workflows": a matching `!` pattern blocks; actions and reusable
 * workflows in the same organization are allowed; GitHub-owned actions follow
 * `github_owned_allowed`; anything else needs a positive pattern. Marketplace
 * "verified creator" status is not observable here, so a reference that only
 * `verified_allowed` could admit is UNKNOWN.
 */
function selectedVerdict(ref, selected, positive, negative) {
  if (negative.some((p) => patternCovers(p, ref))) return STATES.BLOCKED;
  const owner = ref.split('/')[0].toLowerCase();
  if (owner === OWNER) return STATES.ALLOWED;
  if (positive.some((p) => patternCovers(p, ref))) return STATES.ALLOWED;
  if (GITHUB_OWNED.has(owner)) {
    if (selected.github_owned_allowed === true) return STATES.ALLOWED;
    return selected.github_owned_allowed === false ? STATES.BLOCKED : STATES.UNKNOWN;
  }
  return selected.verified_allowed === true ? STATES.UNKNOWN : STATES.BLOCKED;
}

/**
 * Classify one repository's Actions policy for the governance caller.
 *
 *   read fails                         -> UNKNOWN  (unreadable, with status)
 *   enabled === false                  -> BLOCKED  (disabled)
 *   allowed_actions === 'local_only'   -> BLOCKED  (local_only)
 *   allowed_actions === 'all'          -> ALLOWED
 *   allowed_actions === 'selected'     -> read the allow-list and decide every
 *                                         caller reference and every action its
 *                                         reusable workflows use (selectedVerdict):
 *       read fails / actions unread    -> UNKNOWN
 *       any reference blocked          -> BLOCKED  (selected-denied)
 *       any reference undecidable      -> UNKNOWN
 *       all allowed                    -> ALLOWED
 *   anything else / no caller refs     -> UNKNOWN
 *
 * @param {object} o
 * @param {() => Promise<{enabled?: boolean, allowed_actions?: string}>} o.readPermissions
 * @param {() => Promise<{patterns_allowed?: string[], github_owned_allowed?: boolean,
 *   verified_allowed?: boolean}>} o.readSelected
 * @param {string[]} o.refs  caller references the policy must admit
 * @param {string[]|null} o.actionRefs  actions the caller's reusable workflows use;
 *   null when they could not be read
 * @returns {Promise<{state: string, detail: string}>}
 */
async function classifyActionsPermission({ readPermissions, readSelected, refs, actionRefs }) {
  let perms;
  try {
    perms = await readPermissions();
  } catch (e) {
    return { state: STATES.UNKNOWN, detail: `permissions unreadable (${statusOf(e)})` };
  }
  if (!perms || typeof perms !== 'object') return { state: STATES.UNKNOWN, detail: 'permissions response empty' };
  if (perms.enabled === false) return { state: STATES.BLOCKED, detail: 'disabled' };
  if (perms.enabled !== true) return { state: STATES.UNKNOWN, detail: `enabled=${perms.enabled}` };
  if (perms.allowed_actions === 'local_only') return { state: STATES.BLOCKED, detail: 'local_only' };
  if (perms.allowed_actions === 'all') return { state: STATES.ALLOWED, detail: 'all' };
  if (perms.allowed_actions !== 'selected') {
    return { state: STATES.UNKNOWN, detail: `allowed_actions=${perms.allowed_actions}` };
  }
  if (!Array.isArray(refs) || !refs.length) {
    return { state: STATES.UNKNOWN, detail: 'selected; no caller reference to verify against' };
  }
  let selected;
  try {
    selected = await readSelected();
  } catch (e) {
    return { state: STATES.UNKNOWN, detail: `selected; allow-list unreadable (${statusOf(e)})` };
  }
  const patterns = selected?.patterns_allowed;
  if (!Array.isArray(patterns)) return { state: STATES.UNKNOWN, detail: 'selected; allow-list has no patterns field' };
  if (!Array.isArray(actionRefs)) {
    return { state: STATES.UNKNOWN, detail: 'selected; actions used by the reusable workflows were not read' };
  }
  const strings = patterns.filter((p) => typeof p === 'string');
  const negative = strings.filter((p) => p.startsWith('!')).map((p) => p.slice(1));
  const positive = strings.filter((p) => !p.startsWith('!'));
  const verdicts = [...refs, ...actionRefs].map((ref) => [ref, selectedVerdict(ref, selected, positive, negative)]);
  const blocked = verdicts.find(([, v]) => v === STATES.BLOCKED);
  if (blocked) return { state: STATES.BLOCKED, detail: `selected-denied (${blocked[0].split('@')[0]})` };
  const unknown = verdicts.find(([, v]) => v === STATES.UNKNOWN);
  if (unknown) return { state: STATES.UNKNOWN, detail: `selected; cannot verify ${unknown[0].split('@')[0]}` };
  return { state: STATES.ALLOWED, detail: 'selected (admits the caller and the actions it runs)' };
}

const PRESENCE = Object.freeze([
  ['co', 'CODEOWNERS'],
  ['caller', 'governance caller'],
  ['dep', 'dependabot'],
]);

/**
 * Raw presence percentage for one key. `true` present, `false` observed
 * absent (404), `null` unobserved. The denominator is every listed repo, so
 * an unobserved file never raises the number.
 */
function presence(rows, key) {
  const present = rows.filter((r) => r[key] === true).length;
  const unobserved = rows.filter((r) => r[key] !== true && r[key] !== false).length;
  return { present, unobserved, pct: Math.round((100 * present) / (rows.length || 1)) };
}

/**
 * @param {Array<{name: string, co: boolean|null, caller: boolean|null,
 *   dep: boolean|null, actions: {state: string, detail: string}}>} rows
 * @param {{date: string}} o
 * @returns {{body: string, refresh: string, counts: {allowed: number, blocked: number, unknown: number}}}
 */
function buildPostureReport(rows, { date }) {
  const by = (state) => rows.filter((r) => r.actions?.state === state);
  const allowed = by(STATES.ALLOWED);
  const blocked = by(STATES.BLOCKED);
  const unknown = rows.filter((r) => r.actions?.state !== STATES.ALLOWED && r.actions?.state !== STATES.BLOCKED);
  const counts = { allowed: allowed.length, blocked: blocked.length, unknown: unknown.length };
  const list = (rs) => rs.map((r) => `\`${r.name}\` (${r.actions?.detail || 'no result'})`).join(', ');

  const pres = PRESENCE.map(([k, label]) => [label, presence(rows, k)]);
  const presenceLine = pres
    .map(([label, p]) => `${label} ${p.pct}%${p.unobserved ? ` (${p.unobserved} unobserved)` : ''}`)
    .join(' · ');

  const notes = [];
  if (!rows.length) {
    notes.push('> [!WARNING]\n> No active repositories were observed; nothing about the Actions policy was verified.');
  }
  if (blocked.length) {
    notes.push(`> [!NOTE]\n> ${blocked.length} repo(s) have an Actions policy that would prevent the governance caller from running: ` +
      `${list(blocked)}. See docs/DISTRIBUTION.md Appendix B.`);
  }
  if (unknown.length) {
    notes.push(`> [!WARNING]\n> ${unknown.length} repo(s) have an Actions policy that could not be verified (UNKNOWN, not counted as allowed): ` +
      `${list(unknown)}.`);
  }
  if (rows.length && allowed.length === rows.length) {
    notes.push('> [!NOTE]\n> All repos permit cross-repo reusable workflows.');
  }

  const tick = (b) => (b === true ? '✅' : b === false ? '⬜' : '❓');
  const cell = (a) => (a?.state === STATES.ALLOWED ? 'allowed'
    : a?.state === STATES.BLOCKED ? `⚠️ blocked: ${a.detail}` : `❓ UNKNOWN: ${a?.detail || 'no result'}`);

  const body = [
    `_Advisory posture report. Nothing here blocks anything. Generated ${date}._`,
    '',
    `**Raw file presence across ${rows.length} active repos** (presence, not class-normalized compliance) — ${presenceLine}`,
    '',
    `**Actions policy for the governance caller** — ${counts.allowed} verified allowed · ${counts.blocked} blocked · ${counts.unknown} UNKNOWN`,
    '',
    ...notes.flatMap((n) => [n, '']),
    '| Repo | CODEOWNERS | Caller | Dependabot | Actions |',
    '| --- | :-: | :-: | :-: | :-: |',
    ...rows.map((r) => `| \`${r.name}\` | ${tick(r.co)} | ${tick(r.caller)} | ${tick(r.dep)} | ${cell(r.actions)} |`),
    '',
    'Presence columns: ✅ present · ⬜ absent (404) · ❓ unobserved. Presence is not compliance: a',
    "repository's class may waive a file (policies/repo-classes.yml); class-aware compliance is the",
    'monthly preflight report.',
    '',
    '### Not measured here, on purpose',
    '',
    'Test results, lint findings, type errors, code scanning, and CI failure',
    'diagnosis are owned by `l9-ci-sdk`, `l9-ci-core`, and `l9-ci-debt-resolver`.',
    'This report deliberately does not recompute them — see `docs/BOUNDARIES.md`.',
    '',
    '### Promotion readiness',
    '',
    'Per `docs/ADVISORY.md`, rung 1 needs 4 consecutive weekly reports plus a',
    'named highest-signal finding. Do not promote a gate without that evidence.',
  ].join('\n');

  const refresh = `Refreshed ${date} — presence: ${pres.map(([label, p]) => `${label} ${p.pct}%`).join(', ')}; ` +
    `Actions: ${counts.allowed} allowed, ${counts.blocked} blocked, ${counts.unknown} UNKNOWN.`;
  return { body, refresh, counts };
}

module.exports = {
  STATES,
  callerRefs,
  patternCovers,
  workflowActionRefs,
  reusableWorkflowActionRefs,
  classifyActionsPermission,
  buildPostureReport,
};
