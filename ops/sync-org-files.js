'use strict';

/**
 * Local plan adapter behind ops/sync-org-files.sh.
 *
 * Compiles the consumer checkout's governance plan and writes its
 * materialize entries into the checkout — the same plan the Actions seeders
 * apply remotely, so a manual sync and an auto-seed of the same repository
 * write the same files (AC-INT-002). It never maps categories to paths itself.
 *
 * Writes honor the plan's write mode (GOV-011): `missing_only` never touches
 * an existing file; `replace_if_stock` replaces only a stock caller, through
 * the same selectSeedWrites() decision the seeders use.
 *
 * Usage (from ops/sync-org-files.sh):
 *   node ops/sync-org-files.js <consumer-path> <owner/name> [category ...]
 * No categories = the whole plan; categories may only narrow it.
 */

const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { selectSeedWrites } = require('./build-seed-payload.js');
const {
  loadAuthority,
  GovernanceCompileError,
  compileVerifiedPlan,
  selectPlanFiles,
  payloadOf,
  planIdentity,
} = require('./plan-adapter.js');

// Absolute paths only (Sonar S4036).
const GIT_CANDIDATES = ['/usr/bin/git', '/usr/local/bin/git', '/opt/homebrew/bin/git'];

function authorityRevision(orgRoot) {
  const git = GIT_CANDIDATES.find((p) => fs.existsSync(p));
  if (!git) throw new GovernanceCompileError('authority_identity', 'git not found; cannot name the authority revision');
  const run = (args) => execFileSync(git, ['-C', orgRoot, ...args], { encoding: 'utf8' });
  const sha = run(['rev-parse', 'HEAD']).trim();
  const dirty = run(['status', '--porcelain', '--', 'policies', '.github/labels.yml', 'templates']).trim();
  return { sha, dirty };
}

function main(argv) {
  const [consumerArg, repository, ...categories] = argv;
  if (!consumerArg) throw new GovernanceCompileError('contract', 'consumer path is required');
  if (!repository) {
    throw new GovernanceCompileError(
      'missing_fact',
      'cannot identify the target repository (no origin remote); pass --repo owner/name',
    );
  }
  const orgRoot = path.resolve(__dirname, '..');
  const consumer = path.resolve(consumerArg);
  process.chdir(orgRoot);

  const authority = loadAuthority(fs);
  const { sha, dirty } = authorityRevision(orgRoot);
  if (dirty) {
    // A local sync writes a local checkout, not a remote; it proceeds, but it
    // does not pretend these bytes are the revision it names.
    process.stderr.write(`⚠️  policy/templates differ from ${sha.slice(0, 12)}; syncing uncommitted org content\n`);
  }

  const inConsumer = (p) => path.join(consumer, p);
  const exists = (p) => fs.existsSync(inConsumer(p));
  const markerPath = authority.classes.marker_path;
  const facts = {
    marker_state: exists(markerPath) ? 'present' : 'absent',
    has_root_codeowners: exists('CODEOWNERS'),
    has_python: exists('pyproject.toml') || exists('requirements.txt'),
    has_package_json: exists('package.json'),
  };
  if (facts.marker_state === 'present') facts.marker_text = fs.readFileSync(inConsumer(markerPath), 'utf8');

  const plan = compileVerifiedPlan({ fs, authority, authoritySha: sha, repository, facts });
  const files = selectPlanFiles(plan, categories.join(','));
  console.log(`Plan: ${planIdentity(plan).replace(/`/g, '')}`);

  const payload = payloadOf(files);
  const existing = {};
  for (const dest of Object.keys(payload)) {
    existing[dest] = exists(dest) ? fs.readFileSync(inConsumer(dest), 'utf8') : null;
  }
  const { writes, replaced, kept } = selectSeedWrites(payload, existing);
  for (const dest of writes) {
    fs.mkdirSync(path.dirname(inConsumer(dest)), { recursive: true });
    fs.writeFileSync(inConsumer(dest), payload[dest]);
    console.log(`  ✓ ${dest}${replaced.includes(dest) ? ' (stock caller replaced)' : ''}`);
  }
  for (const dest of kept) console.log(`  = ${dest} (exists; kept)`);
  if (facts.has_root_codeowners) {
    console.log('  skip .github/CODEOWNERS (root CODEOWNERS present; it stays authoritative)');
  }
  for (const p of plan.inherit.paths) console.log(`  ↑ ${p} (inherited from Quantum-L9/.github; not copied)`);
}

if (require.main === module) {
  try {
    main(process.argv.slice(2));
  } catch (err) {
    process.stderr.write(`❌ ERROR: ${err.message}\n`);
    process.exit(err instanceof GovernanceCompileError ? 2 : 1);
  }
}

module.exports = { main };
