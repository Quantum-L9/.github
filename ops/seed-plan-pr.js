'use strict';

/**
 * Materialize a verified governance plan into one repository as a seed PR.
 *
 * This is the auto-seed materialization step, moved out of
 * auto-seed-new-repo.yml unchanged so the single targeted front door
 * (repo-birth-bootstrap.yml, docs/adr/0004-single-targeted-bootstrap-front-door.md)
 * reuses it instead of re-implementing it. Both run on the same seed branch, so
 * ops/seed-branch-safety.js arbitrates between an hourly sweep and a birth
 * exactly as it arbitrates between two sweeps.
 *
 * Writes only plan.materialize entries, honoring their write mode through
 * selectSeedWrites (GOV-011). Never writes to the default branch: the result is
 * a PR the repository owner merges.
 */

const {
  STOCK_ESLINT_NODE_DEST,
  STOCK_BIOME_DEST,
  selectSeedWrites,
} = require('./build-seed-payload.js');
const { assessSeedBranch, moveSeedBranch } = require('./seed-branch-safety.js');
const { payloadOf, remoteReader } = require('./plan-adapter.js');

const AUTO_SEED_BRANCH = 'chore/auto-seed-governance';

/**
 * @param {object} o
 * @param {object} o.github  octokit (actions/github-script)
 * @param {string} o.owner
 * @param {string} o.repo
 * @param {string} o.base  default branch
 * @param {object} o.plan  verified plan
 * @param {object[]} [o.files]  plan entries to execute; defaults to the whole plan
 * @param {boolean} [o.dry]
 * @returns {Promise<{outcome: 'nothing'|'already'|'skip'|'dry'|'opened', detail: string, prNumber?: number, paths: string[]}>}
 */
async function seedPlanPR({ github, owner, repo, base, plan, files = plan.materialize.files, dry = false }) {
  const o = owner;
  const n = repo;
  const BRANCH = AUTO_SEED_BRANCH;

  // Fail closed: only a 404 is "absent". An unreadable existing file must not
  // look missing (it would be re-seeded over), so any other failure throws
  // before the seed branch is touched.
  const { exists, readText } = remoteReader(github, o, n);

  const payload = payloadOf(files);
  const paths = Object.keys(payload);
  if (!paths.length) return { outcome: 'nothing', detail: 'skipped (nothing safe to seed)', paths: [] };

  const existingByPath = {};
  for (const p of paths) {
    if (!(await exists(p))) {
      existingByPath[p] = null;
      continue;
    }
    existingByPath[p] = p === STOCK_ESLINT_NODE_DEST || p === STOCK_BIOME_DEST ? await readText(p) : true;
  }
  const { writes, replaced } = selectSeedWrites(payload, existingByPath);
  if (!writes.length) return { outcome: 'already', detail: 'already seeded', paths: [] };

  // ── Seed-branch safety gate ────────────────────────────────────────────
  // The rebuild below constructs the branch as "current default branch + one
  // seed commit", so anything else already on that branch would be discarded
  // by construction rather than by conflict. ops/seed-branch-safety.js
  // decides, read-only, before any git write; every seeder shares it.
  const gate = await assessSeedBranch({ github, owner: o, repo: n, base, branch: BRANCH });
  if (gate.action === 'skip') return { outcome: 'skip', detail: gate.reason, paths: [] };
  const branchSha = gate.sha;

  if (dry) {
    const upgrade = replaced.length ? '; replace stock ESLint' : '';
    const preview =
      writes.length <= 6 ? writes.join(', ') : `${writes.slice(0, 6).join(', ')} (+${writes.length - 6} more)`;
    const onto = branchSha ? `; rebuild ${BRANCH}` : '';
    return { outcome: 'dry', detail: `would seed ${writes.length}: ${preview}${upgrade}${onto}`, paths: writes };
  }
  const baseRef = await github.rest.git.getRef({ owner: o, repo: n, ref: `heads/${base}` });
  const baseSha = baseRef.data.object.sha;
  const baseCommit = await github.rest.git.getCommit({ owner: o, repo: n, commit_sha: baseSha });

  const treeItems = [];
  for (const path of writes) {
    if (!replaced.includes(path) && (await exists(path, base))) continue;
    const blob = await github.rest.git.createBlob({
      owner: o,
      repo: n,
      content: Buffer.from(payload[path]).toString('base64'),
      encoding: 'base64',
    });
    treeItems.push({ path, mode: '100644', type: 'blob', sha: blob.data.sha });
  }
  if (!treeItems.length) return { outcome: 'already', detail: 'already seeded', paths: [] };

  const tree = await github.rest.git.createTree({
    owner: o,
    repo: n,
    base_tree: baseCommit.data.tree.sha,
    tree: treeItems,
  });
  const commit = await github.rest.git.createCommit({
    owner: o,
    repo: n,
    message: `chore(governance): auto-seed ${treeItems.length} org template file(s)`,
    tree: tree.data.sha,
    parents: [baseSha],
  });

  const moved = await moveSeedBranch({
    github,
    owner: o,
    repo: n,
    branch: BRANCH,
    expectedSha: branchSha,
    commitSha: commit.data.sha,
  });
  if (!moved.moved) return { outcome: 'skip', detail: moved.reason, paths: [] };

  const pr = await github.rest.pulls.create({
    owner: o,
    repo: n,
    head: BRANCH,
    base,
    title: 'chore(governance): auto-seed org templates from Quantum-L9/.github',
    body: [
      'Automatically seeds the org capabilities applicable to this repository from `Quantum-L9/.github/templates/`. CI is not distributed from this repository.',
      '',
      `**Repo class:** \`${plan.repo_class.name}\` (${plan.repo_class.resolved_from}) — see \`policies/repo-classes.yml\`.`,
      `**Governance plan:** authority \`${plan.authority.sha}\`, digest \`${plan.digest.value}\`.`,
      plan.inherit.paths.length
        ? `Inherited from the org \`.github\` repo and deliberately **not** copied here: ${plan.inherit.paths.map((p) => `\`${p}\``).join(', ')}.`
        : '',
      '',
      '### Files in this PR',
      ...treeItems.map((t) => `- \`${t.path}\``),
      '',
      'Existing files were left untouched (missing-only seed), except a stock ESLint `l9-lint-test-node.yml` which is replaced with the Biome SDK caller.',
      'Governance caller is **advisory** (`strict` defaults false).',
      'Core pack callers are distributed here; `l9-ci-core` executes CI.',
      '',
      'While this PR is open the seeder leaves the branch alone — commit review fixes onto it freely.',
      '',
      '_Opened automatically by Quantum-L9/.github auto-seed._',
    ].join('\n'),
  });
  return {
    outcome: 'opened',
    detail: `PR #${pr.data.number} (${treeItems.length} file(s))`,
    prNumber: pr.data.number,
    paths: treeItems.map((t) => t.path),
  };
}

module.exports = { AUTO_SEED_BRANCH, seedPlanPR };
