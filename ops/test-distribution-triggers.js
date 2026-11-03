'use strict';

/**
 * Trigger and credential contract of the two manual distribution workflows.
 *
 * continuous-sync.yml (Manual Update) is manual only: no schedule, no push,
 * no other event may start it, and its dispatch defaults to Preview.
 * seed-governance.yml stays a dispatch with its dry-run / seed modes.
 * Both run in the governance-distribution environment, which is where their
 * credentials live (CANONICAL_LAW §14); Manual Update's token step failed with
 * "Input required and not supplied: app-id" on every run while it did not.
 *
 * Read literally, without a YAML dependency, like workflow-script-harness.js:
 * the assertion is about the text the runner reads.
 *
 * Run from the Quantum-L9/.github repo root:
 *   node ops/test-distribution-triggers.js
 */
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

/** Lines of the top-level `on:` block, comments and blanks dropped. */
function onBlock(text) {
  const lines = text.split('\n');
  const start = lines.findIndex((l) => /^on:\s*(#.*)?$/.test(l));
  assert.ok(start !== -1, 'no top-level "on:" block');
  const block = [];
  for (const line of lines.slice(start + 1)) {
    if (/^\S/.test(line) && !line.startsWith('#')) break;
    if (line.trim() === '' || line.trim().startsWith('#')) continue;
    block.push(line);
  }
  return block;
}

/** Event names directly under `on:` (two-space indent). */
const events = (block) => block.flatMap((l) => {
  const m = l.match(/^ {2}([A-Za-z_]+):/);
  return m ? [m[1]] : [];
});

/** The indented body of a dispatch input, e.g. `dry_run:` or `mode:`. */
function input(block, name) {
  const i = block.findIndex((l) => new RegExp(String.raw`^ {6}${name}:\s*$`).test(l));
  assert.ok(i !== -1, `no workflow_dispatch input "${name}"`);
  const body = [];
  for (const l of block.slice(i + 1)) {
    if (l.match(/^\s*/)[0].length <= 6) break;
    body.push(l.trim());
  }
  return body;
}

const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');

// ── continuous-sync.yml: manual only, Preview by default ────────────────────
{
  const label = 'continuous-sync.yml';
  const text = read('.github/workflows/continuous-sync.yml');
  const block = onBlock(text);

  assert.deepStrictEqual(events(block), ['workflow_dispatch'], `${label}: workflow_dispatch must be the only trigger`);
  for (const forbidden of ['schedule', 'push', 'cron', 'pull_request', 'workflow_run', 'repository_dispatch', 'workflow_call']) {
    assert.ok(!block.some((l) => new RegExp(String.raw`^\s*-?\s*${forbidden}:`).test(l)), `${label}: automatic trigger "${forbidden}" present`);
  }
  console.log(`ok: ${label} — workflow_dispatch is the only trigger (no schedule, no push)`);

  const dry = input(block, 'dry_run');
  assert.ok(dry.includes('type: boolean'), `${label}: dry_run must be a boolean`);
  assert.ok(dry.includes('default: true'), `${label}: dispatch must default to Preview`);
  assert.ok(input(block, 'repo_filter').includes('type: string'));
  // Only an explicit false reaches Apply; no fallback may default to writing.
  assert.ok(text.split('\n').some((l) => l.trim() === 'DRY_RUN: ${{ inputs.dry_run }}'), `${label}: DRY_RUN must come from the input alone`);
  assert.doesNotMatch(text, /DRY_RUN:.*\|\|/, `${label}: DRY_RUN must not carry a fallback`);
  assert.match(text, /const DRY = process\.env\.DRY_RUN !== 'false';/, `${label}: Preview unless DRY_RUN is exactly "false"`);
  console.log(`ok: ${label} — Preview is the default and the fail-closed state; Apply needs dry_run=false`);

  assert.match(text, /^ {4}environment: governance-distribution\s*$/m, `${label}: job must run in governance-distribution`);
  assert.match(text, /app-id: \$\{\{ vars\.GOVERNANCE_APP_ID \}\}/);
  assert.match(text, /private-key: \$\{\{ secrets\.GOVERNANCE_APP_PRIVATE_KEY \}\}/);
  // Branch provenance is checked against the App's own bot identity.
  assert.match(text, /APP_SLUG: \$\{\{ steps\.token\.outputs\.app-slug \}\}/);
  assert.match(text, /github-token: \$\{\{ steps\.token\.outputs\.token \}\}/);
  assert.doesNotMatch(text, /secrets\.GH_TOKEN/, `${label}: credential must stay the governance App`);
  console.log(`ok: ${label} — governance App credential read inside governance-distribution; provenance identity unchanged`);

  assert.match(text, /^ {2}group: continuous-sync\s*$/m, `${label}: single fleet writer`);
  assert.match(text, /^ {2}cancel-in-progress: false\s*$/m);
  assert.match(text, /^permissions:\n {2}contents: read\s*$/m, `${label}: GITHUB_TOKEN stays read-only`);
  console.log(`ok: ${label} — one writer at a time; workflow token read-only`);
}

// ── seed-governance.yml: dispatch with dry-run and seed modes ───────────────
{
  const label = 'seed-governance.yml';
  const text = read('.github/workflows/seed-governance.yml');
  const block = onBlock(text);

  assert.deepStrictEqual(events(block), ['workflow_dispatch'], `${label}: workflow_dispatch must be the only trigger`);
  const mode = input(block, 'mode');
  assert.ok(mode.includes('type: choice'));
  assert.ok(mode.includes('options: [dry-run, seed]'), `${label}: modes must be dry-run and seed`);
  assert.ok(mode.includes('default: dry-run'), `${label}: dispatch must default to dry-run`);
  assert.match(text, /^ {4}environment: governance-distribution\s*$/m);
  assert.match(text, /SEED_MODE: \$\{\{ inputs\.mode \}\}/);
  console.log(`ok: ${label} — dispatch only; dry-run (default) and seed modes; governance-distribution`);
}

// ── auto-seed-new-repo.yml: weekly + repo_created + dispatch, dry run default ─
{
  const label = 'auto-seed-new-repo.yml';
  const text = read('.github/workflows/auto-seed-new-repo.yml');
  const block = onBlock(text);
  assert.deepStrictEqual(events(block), ['schedule', 'repository_dispatch', 'workflow_dispatch'], `${label}: trigger set changed`);
  const cronAt = block.findIndex((l) => /^\s+- cron: '0 8 \* \* 1'\s*$/.test(l));
  assert.ok(cronAt >= 0, `${label}: weekly Monday 08:00 sweep must stay`);
  assert.match(block[cronAt + 1] || '', /^\s+timezone: 'America\/New_York'\s*$/, `${label}: the sweep runs in America/New_York`);
  assert.ok(!block.some((l) => /^\s+- cron: '\S+ \* \* \* \*'\s*$/.test(l)), `${label}: hourly sweep is retired`);
  // ADR-0019: the managed dependabot.yml is restored by the sweep, honouring .l9/no-sync.
  assert.match(text, /MANAGED_SEED_PATHS/, `${label}: managed seed paths must be restored`);
  assert.match(text, /'\.l9\/no-sync'/, `${label}: .l9/no-sync must opt out of the restore`);
  assert.match(text, /selectSeedWrites\(payload, existingByPath, \{ managed \}\)/, `${label}: restore goes through the shared planner`);
  assert.ok(block.some((l) => /types: \[repo_created\]/.test(l)), `${label}: repo_created fast path must stay`);
  const dry = input(block, 'dry_run');
  assert.ok(dry.includes('type: boolean') && dry.includes('default: true'), `${label}: operator dispatch defaults to dry run`);
  assert.match(text, /^ {4}environment: governance-distribution\s*$/m);
  assert.match(text, /^ {2}group: auto-seed-new-repo-\$\{\{ github\.event\.client_payload\.repository \|\| inputs\.target_repo \|\| 'sweep' \}\}\s*$/m,
    `${label}: births get a per-repository group (never cancel each other); sweeps share one`);
  console.log(`ok: ${label} — weekly sweep with managed restore, repo_created, dry-run dispatch preserved`);
}

// ── repo-birth-bootstrap.yml: birth chains file seeding (repo_created) ───────
// The auto-seed sweep is weekly; birth must not wait for it (ADR 0019).
{
  const label = 'repo-birth-bootstrap.yml';
  const text = read('.github/workflows/repo-birth-bootstrap.yml');
  assert.match(text, /event_type: 'repo_created'/, `${label}: birth must dispatch repo_created to the seeder`);
  assert.match(text, /createDispatchEvent\(/, `${label}: birth must dispatch, not only describe it`);
  const chain = text.split('\n').find((l) => /^\s+if: .*success\(\)/.test(l)) || '';
  assert.match(chain, /inputs\.dry_run != true\b/, `${label}: dry run must be compared as a boolean, never a string`);
  assert.doesNotMatch(chain, /'true'/, `${label}: a string 'true' never equals the boolean input, so a dry run would chain`);
  // Evaluate the guard the way GitHub does for this one shape: a boolean input,
  // or null for repository_dispatch.
  const chains = (dry) => !(dry === true);
  assert.strictEqual(chains(true), false, `${label}: a dry run must not chain`);
  assert.strictEqual(chains(false), true);
  assert.strictEqual(chains(null), true, `${label}: a repository_dispatch birth (no input) chains`);
  // Reads fail closed: only a 404 is absent (a swallowed 403 once classified a
  // repo `default` and passed FORBID on an unreadable path).
  assert.doesNotMatch(text, /catch \{\s*(?:\/\*[^*]*\*\/\s*)?\}|catch \{\s*return (?:false|null);/,
    `${label}: a read may not swallow every error as "absent"`);
  assert.strictEqual((text.match(/if \(e\.status === 404\) return (?:false|null);/g) || []).length, 2,
    `${label}: pathExists and readText treat only 404 as absent`);
  console.log(`ok: ${label} — birth chains repo_created to auto-seed after attestation; dry run does not`);
}

/**
 * The argument text of every `createDispatchEvent({ … })` call, by index scan
 * (no backtracking regex). A call whose closing `})` is missing fails loudly.
 */
function dispatchCallArgs(text) {
  const out = [];
  const open = 'createDispatchEvent({';
  for (let at = text.indexOf('createDispatchEvent'); at !== -1; at = text.indexOf('createDispatchEvent', at + 1)) {
    assert.ok(text.startsWith(open, at), 'createDispatchEvent must be called with an object literal');
    const close = text.indexOf('})', at + open.length);
    assert.ok(close !== -1, 'unterminated createDispatchEvent call');
    out.push(text.slice(at + open.length, close));
  }
  return out;
}

// ── One PR-body renderer, one pin ────────────────────────────────────────────
// Seed and Manual Update PR bodies are composed by Cursor-Governance
// compose_pr_body.py at the same commit governance-pr.yml's body job runs, and
// the validate suite renders against it too. Every checkout must name it.
{
  const pinOf = (text) => [...text.matchAll(/repository: Quantum-L9\/Cursor-Governance\n\s+ref: ([0-9a-f]{40})/g)].map((m) => m[1]);
  const gov = read('.github/workflows/governance-pr.yml');
  const declared = (gov.match(/COMPOSER: Quantum-L9\/Cursor-Governance@([0-9a-f]{40})/) || [])[1];
  assert.ok(declared, 'governance-pr.yml must declare COMPOSER: Quantum-L9/Cursor-Governance@<sha>');
  assert.deepStrictEqual(pinOf(gov), [declared], 'governance-pr.yml checks the composer out at its declared pin');
  for (const f of ['governance-pr.yml', 'auto-seed-new-repo.yml', 'seed-governance.yml', 'continuous-sync.yml', 'validate-starters.yml']) {
    const text = read(`.github/workflows/${f}`);
    if (f !== 'governance-pr.yml') {
      assert.deepStrictEqual(pinOf(text), [declared], `${f}: the composer checkout must be the governance-pr.yml pin`);
    }
    // The composer imports org_dotgithub at load: a checkout without it fails
    // at the first line, which is how a pin move broke it before.
    const sparse = text.match(/repository: Quantum-L9\/Cursor-Governance[\s\S]*?sparse-checkout: \|\n((?:\s+ops\/scripts\/\S+\n)+)/);
    assert.ok(sparse, `${f}: the composer checkout must list its files`);
    const listed = new Set(sparse[1].trim().split(/\s+/));
    for (const need of ['ops/scripts/compose_pr_body.py', 'ops/scripts/org_dotgithub.py']) {
      assert.ok(listed.has(need), `${f}: the composer checkout misses ${need}`);
    }
  }
  for (const f of ['auto-seed-new-repo.yml', 'seed-governance.yml', 'continuous-sync.yml']) {
    const text = read(`.github/workflows/${f}`);
    assert.match(text, /renderSeedPrBody\(\{/, `${f}: PR bodies are composed, not hand-built`);
    assert.doesNotMatch(text, /'## (Problem|Fix|Risk|Evidence|Gates)'/, `${f}: a hand-built PR body section is back`);
  }
  console.log('ok: seeders, Manual Update and validate compose PR bodies with the governance-pr.yml composer pin');
}

// ── Retired: the push-driven org_template_updated fanout ────────────────────
// dispatch-template-update.yml pushed `repository_dispatch(org_template_updated)`
// to every seeded consumer on a template change. Drift is restored only by a
// dispatched Manual Update now; no workflow here may fan an event out again.
{
  const dir = path.join(root, '.github/workflows');
  assert.ok(!fs.existsSync(path.join(dir, 'dispatch-template-update.yml')), 'dispatch-template-update.yml is retired');
  for (const f of fs.readdirSync(dir).filter((n) => /\.ya?ml$/.test(n))) {
    const text = read(`.github/workflows/${f}`);
    assert.doesNotMatch(text, /org_template_updated/, `${f}: the retired consumer sync event is back`);
    // The only dispatch allowed is to this repository itself (birth chaining
    // repo_created to auto-seed); any other target is a consumer fanout.
    for (const args of dispatchCallArgs(text)) {
      const lines = args.split('\n').map((l) => l.trim());
      assert.ok(lines.includes('repo: context.repo.repo,'), `${f}: a consumer event fanout is back`);
      assert.ok(lines.includes('owner: context.repo.owner,'), `${f}: a consumer event fanout is back`);
      assert.match(args, /event_type: 'repo_created'/, `${f}: only repo_created may be self-dispatched`);
    }
  }
  assert.doesNotMatch(read('Makefile'), /dispatch-template-update/, 'Makefile still runs the retired dispatcher');
  console.log('ok: org_template_updated fanout retired — no workflow emits a consumer dispatch event (self repo_created only)');
}

// ── Canonical governance caller pin ─────────────────────────────────────────
// The pinned commit: the merge of #176 on main, the commit carrying both
// reusable workflows the caller invokes. Choosing a successor is an operator
// decision; it changes this constant, the caller and the record together.
const GOVERNANCE_CALLER_PIN = '02ea092a098563b27970d21416fabc47dd005fb0';

/**
 * The pin record is the one place a re-pin is written; both caller `uses:`
 * lines must name exactly the SHA it records. Returns that SHA, or throws.
 */
function checkCallerPin(caller, recordText) {
  const pins = [...caller.matchAll(/^\s*uses: Quantum-L9\/\.github\/\.github\/workflows\/(governance-(?:pr|issue)\.yml)@(\S+)/gm)]
    .map((m) => [m[1], m[2]]);
  const record = recordText.match(/^caller ([0-9a-f]{40})$/m);
  assert.ok(record, 'ops/governance-v1-pin.txt must record `caller <40-hex sha>`');
  assert.deepStrictEqual(pins, [
    ['governance-pr.yml', record[1]],
    ['governance-issue.yml', record[1]],
  ], 'both caller refs must pin the SHA recorded in ops/governance-v1-pin.txt');
  return record[1];
}

{
  const caller = read('policies/governance-caller.yml');
  const recordText = read('ops/governance-v1-pin.txt');
  const pinned = checkCallerPin(caller, recordText);
  assert.strictEqual(pinned, GOVERNANCE_CALLER_PIN, 'caller and record must pin exactly the merge of #176');
  assert.match(caller, /pull-requests: write/);
  assert.match(caller, /issues: write/);

  // Negative controls: a record and a caller that disagree fail, in either
  // direction and on either `uses:` line; a moving tag is not a pin.
  const other = '1f42b33249310d59a270c05f30cbc75d663185e6';
  const firstUse = (text, sha) => text.replace(`governance-pr.yml@${GOVERNANCE_CALLER_PIN}`, `governance-pr.yml@${sha}`);
  const secondUse = (text, sha) => text.replace(`governance-issue.yml@${GOVERNANCE_CALLER_PIN}`, `governance-issue.yml@${sha}`);
  for (const [what, c, r] of [
    ['record names another sha', caller, recordText.replace(`caller ${GOVERNANCE_CALLER_PIN}`, `caller ${other}`)],
    ['governance-pr.yml pins another sha', firstUse(caller, other), recordText],
    ['governance-issue.yml pins another sha', secondUse(caller, other), recordText],
    ['caller uses the moving v1 tag', secondUse(firstUse(caller, 'v1'), 'v1'), recordText],
    ['record is a moving tag', caller, recordText.replace(`caller ${GOVERNANCE_CALLER_PIN}`, 'v1 7ed3ab8650583f6659a6caf061eae77dbd3ed1be')],
  ]) {
    assert.notStrictEqual(c + r, caller + recordText, `negative control "${what}" did not change its fixture`);
    assert.throws(() => checkCallerPin(c, r), assert.AssertionError, `mismatch not caught: ${what}`);
  }
  // A coordinated re-pin passes the agreement check but is not this pin.
  assert.notStrictEqual(checkCallerPin(firstUse(secondUse(caller, other), other), `caller ${other}\n`), GOVERNANCE_CALLER_PIN);
  console.log(`ok: governance caller and pin record both pin exactly ${GOVERNANCE_CALLER_PIN.slice(0, 8)}; a mismatch or moving tag fails; permissions unchanged`);
}

console.log('\nall distribution trigger scenarios passed');
