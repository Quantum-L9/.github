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

const crypto = require('node:crypto');

const STATES = Object.freeze({ ALLOWED: 'allowed', BLOCKED: 'blocked', UNKNOWN: 'unknown' });

const statusOf = (e) => e?.status || 'error';

/*
 * Which repositories the report covers is an admission decision, and that
 * decision is owned by semantics/repository_registry.yaml (classes resolved
 * through semantics/repository_classes.yaml). The report used to take
 * whatever repos.listForOrg returned, minus archived repositories and forks:
 * a second, implicit list of governed repositories that drifted from the
 * registry by construction. Here the registry is the only membership source.
 * GitHub discovery is an independent observation, reconciled against it.
 *
 * The census below is a generated, non-authoritative view. It preserves the
 * four fields the registry's downstream_obligations require (id, coordinate,
 * lifecycle, class_ref) plus the source revision and content digest. The one
 * admitted derived view over the registry today (the l9 memory namespace in
 * repository_classes.yaml) selects every lifecycle for a different consumer,
 * so it is not reused for this one.
 */
const REGISTRY_SOURCE = Object.freeze({
  path: 'semantics/repository_registry.yaml',
  schema: 'l9.repository-registry/v1',
  artifact_id: 'l9.repository-registry/global@1',
});
const CLASSES_SOURCE = Object.freeze({
  path: 'semantics/repository_classes.yaml',
  schema: 'l9.repository-classes/v1',
  artifact_id: 'l9.repository-classes/global@1',
});
// Only a `current` registry entry is an operational member of the census.
// `superseded` and `retired` entries are kept and listed, never dropped.
const CENSUS_LIFECYCLE = 'current';

// The same pinned PyYAML (6.0.2) scripts/validate-semantics.py validates these
// files with; the bytes arrive on stdin so the digest and the parse cover the
// same read.
const YAML_TO_JSON = 'import json, sys, yaml; json.dump(yaml.safe_load(sys.stdin.buffer.read()), sys.stdout)';

/**
 * @param {Function} execFileSync child_process.execFileSync
 * @returns {(bytes: Buffer) => unknown}
 */
const pythonYamlParser = (execFileSync) => (bytes) =>
  JSON.parse(execFileSync('python3', ['-I', '-c', YAML_TO_JSON], { input: bytes, encoding: 'utf8', maxBuffer: 16 << 20 }));

const isText = (v) => typeof v === 'string' && v.length > 0;
// Code-unit order: deterministic, independent of the runner's locale.
const byCodeUnit = (a, b) => (a < b ? -1 : Number(a > b));
const isMap = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);

/**
 * Read one canonical source and record where it came from.
 *
 * @param {{path: string, schema: string, artifact_id: string}} source
 * @param {{readBytes: (p: string) => Buffer, parseYaml: (b: Buffer) => unknown, revision: string}} o
 * @returns {{doc: object, provenance: {path: string, artifact_id: string, revision: string, sha256: string}}}
 */
function loadCanonicalSource(source, { readBytes, parseYaml, revision }) {
  if (!/^[0-9a-f]{40}$/.test(String(revision))) throw new Error(`source revision is not a full commit SHA: ${revision}`);
  let bytes;
  try {
    bytes = readBytes(source.path);
  } catch (e) {
    throw new Error(`${source.path} unreadable: ${e.message}`);
  }
  if (!Buffer.isBuffer(bytes) || !bytes.length) throw new Error(`${source.path} is empty`);
  let doc;
  try {
    doc = parseYaml(bytes);
  } catch (e) {
    throw new Error(`${source.path} is not parseable YAML: ${e.message}`);
  }
  if (!isMap(doc)) throw new Error(`${source.path} is not a mapping`);
  if (doc.schema !== source.schema) throw new Error(`${source.path} schema is ${doc.schema}, expected ${source.schema}`);
  if (doc.artifact_id !== source.artifact_id) {
    throw new Error(`${source.path} artifact_id is ${doc.artifact_id}, expected ${source.artifact_id}`);
  }
  if (doc.canonical !== true) throw new Error(`${source.path} is not marked canonical`);
  const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
  return { doc, provenance: { path: source.path, artifact_id: source.artifact_id, revision, sha256 } };
}

/**
 * Project the governed census from the registry and the class catalog.
 * Every violation throws: a census that cannot be derived exactly is no
 * census, never a partial one.
 *
 * @param {{registry: object, classes: object, provenance: {registry: object, classes: object}}} o
 * @returns {{members: object[], historical: object[], aliases: unknown[], provenance: object}}
 */
function projectGovernedCensus({ registry, classes, provenance }) {
  if (!isMap(registry) || !isMap(classes)) throw new Error('registry and class catalog must be mappings');
  if (registry.class_catalog_ref !== classes.artifact_id) {
    throw new Error(`registry class_catalog_ref ${registry.class_catalog_ref} does not name ${classes.artifact_id}`);
  }
  const lifecycles = isMap(registry.repository_lifecycle) ? Object.keys(registry.repository_lifecycle) : [];
  if (!lifecycles.includes(CENSUS_LIFECYCLE)) throw new Error('registry defines no `current` lifecycle');
  const admitted = classes.catalog_status?.admitted_classes;
  if (!Array.isArray(admitted) || !admitted.length) throw new Error('class catalog admits no class');
  const classIds = new Set(Object.values(isMap(classes.classes) ? classes.classes : {}).map((c) => c?.id).filter(isText));
  const repositories = registry.repositories;
  if (!Array.isArray(repositories) || !repositories.length) throw new Error('registry lists no repositories');
  if (registry.aliases !== undefined && !Array.isArray(registry.aliases)) throw new Error('registry aliases is not a list');

  const ids = new Set();
  const coordinates = new Map();
  const entries = repositories.map((entry, index) => {
    const at = `repositories[${index}]`;
    if (!isMap(entry)) throw new Error(`${at} is not a mapping`);
    const { id, coordinate, lifecycle, class_ref: classRef } = entry;
    if (!isText(id)) throw new Error(`${at}.id is missing`);
    if (ids.has(id)) throw new Error(`duplicate registry id ${id}`);
    ids.add(id);
    if (!isMap(coordinate) || coordinate.provider !== 'github' || !isText(coordinate.organization) || !isText(coordinate.repository)) {
      throw new Error(`${id}: coordinate is not a complete github coordinate`);
    }
    const fullName = `${coordinate.organization}/${coordinate.repository}`;
    // GitHub resolves owner/name case-insensitively, so two entries that
    // differ only by case name one repository twice.
    const key = fullName.toLowerCase();
    if (coordinates.has(key)) throw new Error(`${id} and ${coordinates.get(key)} claim the same coordinate ${fullName}`);
    coordinates.set(key, id);
    if (!lifecycles.includes(lifecycle)) throw new Error(`${id}: lifecycle ${lifecycle} is not defined by the registry`);
    if (!isText(classRef) || !classIds.has(classRef)) throw new Error(`${id}: class_ref ${classRef} does not resolve in the class catalog`);
    if (!admitted.includes(classRef)) throw new Error(`${id}: class_ref ${classRef} is not an admitted class`);
    return {
      id,
      coordinate: { provider: coordinate.provider, organization: coordinate.organization, repository: coordinate.repository },
      full_name: fullName,
      lifecycle,
      class_ref: classRef,
    };
  });
  return {
    members: entries.filter((e) => e.lifecycle === CENSUS_LIFECYCLE),
    historical: entries.filter((e) => e.lifecycle !== CENSUS_LIFECYCLE),
    aliases: registry.aliases || [],
    provenance,
  };
}

/**
 * Read both canonical sources at one revision and project the census.
 *
 * @param {{readBytes: (p: string) => Buffer, parseYaml: (b: Buffer) => unknown, revision: string}} io
 */
function loadGovernedCensus(io) {
  const registry = loadCanonicalSource(REGISTRY_SOURCE, io);
  const classes = loadCanonicalSource(CLASSES_SOURCE, io);
  return projectGovernedCensus({
    registry: registry.doc,
    classes: classes.doc,
    provenance: { registry: registry.provenance, classes: classes.provenance },
  });
}

/**
 * Reconcile the census with what GitHub discovery returned. Discovery never
 * admits or removes a member: a member it did not return stays in the census
 * with nothing observed, and a repository it returned that the registry does
 * not list is a registry discrepancy outside the denominator.
 *
 * @param {{members: object[], historical: object[]}} census
 * @param {Array<{name: string, full_name?: string, archived?: boolean, fork?: boolean}>|null} discovered
 *   listForOrg results, or null when discovery failed
 * @param {string} org the organization discovery listed
 * @returns {{members: Array<{member: object, repo: object|null, reason: string|null}>,
 *   unregistered: string[], caseDrift: Array<{registered: string, discovered: string}>}}
 */
function reconcileDiscovery(census, discovered, org) {
  const listed = Array.isArray(discovered)
    ? discovered.map((r) => ({ ...r, full_name: r.full_name || `${org}/${r.name}` }))
    : null;
  const exact = new Map((listed || []).map((r) => [r.full_name, r]));
  const folded = new Map((listed || []).map((r) => [r.full_name.toLowerCase(), r]));
  const caseDrift = [];
  const members = census.members.map((member) => {
    if (!listed) return { member, repo: null, reason: 'GitHub discovery unavailable' };
    if (member.coordinate.organization !== org) return { member, repo: null, reason: `not discoverable under ${org}` };
    const repo = exact.get(member.full_name);
    if (repo) return { member, repo, reason: null };
    const near = folded.get(member.full_name.toLowerCase());
    if (near) {
      caseDrift.push({ registered: member.full_name, discovered: near.full_name });
      return { member, repo: null, reason: `GitHub reports ${near.full_name}, not the registered coordinate` };
    }
    return { member, repo: null, reason: 'not returned by GitHub discovery' };
  });
  const known = new Set([...census.members, ...census.historical].map((e) => e.full_name.toLowerCase()));
  const unregistered = (listed || [])
    .map((r) => r.full_name)
    .filter((n) => !known.has(n.toLowerCase()))
    .sort(byCodeUnit);
  return { members, unregistered, caseDrift };
}

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

const short = (sha) => String(sha).slice(0, 12);

/**
 * Census provenance and reconciliation lines, and the notes they force.
 * `census` absent means the caller did not derive one; that is reported, not
 * assumed fine.
 */
function censusSection(census, rows) {
  const notes = [];
  if (!census || census.error) {
    notes.push(`> [!WARNING]\n> The governed census could not be derived from \`${REGISTRY_SOURCE.path}\`` +
      `${census?.error ? ` (${census.error})` : ''}. No repository was assessed and nothing here is an all-clear.`);
    return { lines: [], notes };
  }
  const { registry, classes } = census.provenance;
  const byClass = {};
  for (const r of rows) byClass[r.class_ref] = (byClass[r.class_ref] || 0) + 1;
  const classLine = Object.keys(byClass).sort(byCodeUnit).map((c) => `\`${c}\` ×${byClass[c]}`).join(', ') || 'none';
  const lines = [
    `**Governed census** — ${rows.length} repositories: registry lifecycle \`${CENSUS_LIFECYCLE}\` with an admitted class (${classLine}). ` +
      `Source \`${registry.path}\` (\`${registry.artifact_id}\`) sha256 \`${short(registry.sha256)}\`, ` +
      `classes \`${classes.path}\` sha256 \`${short(classes.sha256)}\`, both at \`${short(registry.revision)}\`. ` +
      'Membership is the registry\'s admission decision; GitHub discovery is an observation only.',
  ];
  if (census.historical?.length) {
    lines.push(`Registered but not \`${CENSUS_LIFECYCLE}\` (kept, outside the census): ` +
      census.historical.map((e) => `\`${e.full_name}\` (${e.lifecycle})`).join(', ') + '.');
  }
  if (census.discoveryError) {
    notes.push(`> [!WARNING]\n> GitHub discovery failed (${census.discoveryError}): every member is UNKNOWN and unregistered repositories were not checked.`);
  }
  const unseen = rows.filter((r) => r.reason);
  if (unseen.length && !census.discoveryError) {
    notes.push(`> [!WARNING]\n> ${unseen.length} registered repo(s) were not observed, so every column is UNKNOWN: ` +
      `${unseen.map((r) => `\`${r.full_name}\` (${r.reason})`).join(', ')}.`);
  }
  if (census.caseDrift?.length) {
    notes.push(`> [!WARNING]\n> Registry coordinate case differs from GitHub: ` +
      `${census.caseDrift.map((d) => `\`${d.registered}\` → \`${d.discovered}\``).join(', ')}.`);
  }
  if (census.unregistered?.length) {
    notes.push(`> [!NOTE]\n> Registry discrepancy: ${census.unregistered.length} repo(s) returned by GitHub discovery are not in the registry ` +
      `and are not counted: ${census.unregistered.map((n) => `\`${n}\``).join(', ')}.`);
  }
  if (census.aliases?.length) {
    notes.push(`> [!WARNING]\n> The registry carries ${census.aliases.length} alias entr(ies) this report does not interpret; ` +
      'a historical coordinate may appear above as unregistered.');
  }
  return { lines, notes };
}

/**
 * @param {Array<{name: string, co: boolean|null, caller: boolean|null,
 *   dep: boolean|null, actions: {state: string, detail: string}}>} rows
 * @param {{date: string, census?: object}} o  `census` is the projected
 *   census plus reconciliation (discoveryError, unregistered, caseDrift), or
 *   `{error}` when it could not be derived
 * @returns {{body: string, refresh: string, counts: {allowed: number, blocked: number, unknown: number}}}
 */
function buildPostureReport(rows, { date, census }) {
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

  const section = census === undefined ? { lines: [], notes: [] } : censusSection(census, rows);
  const censusOk = census === undefined || !census.error;
  const notes = [...section.notes];
  if (!rows.length && censusOk) {
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
  if (censusOk && rows.length && allowed.length === rows.length) {
    notes.push('> [!NOTE]\n> All repos permit cross-repo reusable workflows.');
  }

  const tick = (b) => (b === true ? '✅' : b === false ? '⬜' : '❓');
  const cell = (a) => (a?.state === STATES.ALLOWED ? 'allowed'
    : a?.state === STATES.BLOCKED ? `⚠️ blocked: ${a.detail}` : `❓ UNKNOWN: ${a?.detail || 'no result'}`);
  // Archived and forked members stay in the census; GitHub's flags are shown.
  const flags = (r) => [r.archived === true && 'archived', r.fork === true && 'fork'].filter(Boolean);
  const repoCell = (r) => `\`${r.name}\`${flags(r).length ? ` (${flags(r).join(', ')})` : ''}`;
  const withCensus = census !== undefined;

  const body = [
    `_Advisory posture report. Nothing here blocks anything. Generated ${date}._`,
    '',
    ...section.lines.flatMap((l) => [l, '']),
    `**Raw file presence across ${rows.length} ${withCensus ? 'governed' : 'active'} repos** (presence, not class-normalized compliance) — ${presenceLine}`,
    '',
    `**Actions policy for the governance caller** — ${counts.allowed} verified allowed · ${counts.blocked} blocked · ${counts.unknown} UNKNOWN`,
    '',
    ...notes.flatMap((n) => [n, '']),
    `| Repo | CODEOWNERS | Caller | Dependabot | Actions |${withCensus ? ' Registry id |' : ''}`,
    `| --- | :-: | :-: | :-: | :-: |${withCensus ? ' --- |' : ''}`,
    ...rows.map((r) => `| ${repoCell(r)} | ${tick(r.co)} | ${tick(r.caller)} | ${tick(r.dep)} | ${cell(r.actions)} |` +
      (withCensus ? ` \`${r.id}\` |` : '')),
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

  const censusNote = withCensus && censusOk ? `census ${rows.length} @ ${short(census.provenance.registry.sha256)}; ` : '';
  const refresh = `Refreshed ${date} — ${censusNote}presence: ${pres.map(([label, p]) => `${label} ${p.pct}%`).join(', ')}; ` +
    `Actions: ${counts.allowed} allowed, ${counts.blocked} blocked, ${counts.unknown} UNKNOWN.`;
  return { body, refresh, counts };
}

module.exports = {
  STATES,
  REGISTRY_SOURCE,
  CLASSES_SOURCE,
  pythonYamlParser,
  loadCanonicalSource,
  projectGovernedCensus,
  loadGovernedCensus,
  reconcileDiscovery,
  callerRefs,
  patternCovers,
  workflowActionRefs,
  reusableWorkflowActionRefs,
  classifyActionsPermission,
  buildPostureReport,
};
