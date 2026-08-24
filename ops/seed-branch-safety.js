'use strict';

/**
 * Decide whether a seeder may rebuild an existing seed branch.
 *
 * Both seed workflows (auto-seed-new-repo.yml, seed-governance.yml) build a
 * fresh commit on top of the consumer's default branch and then move the seed
 * branch onto it. That rebuild is safe only while the branch still holds
 * nothing but the seeder's own commit: every other commit on the branch — a
 * maintainer's fix, a reviewer's suggestion, an agent's remediation — is
 * discarded by construction, not by conflict.
 *
 * This module owns that decision as a pure function over a
 * `GET /repos/{o}/{n}/compare/{base}...{branch}` response so it can be unit
 * tested without network access. It fails closed: anything it cannot prove is
 * seeder-authored is treated as human work and left alone.
 */

// Message written by auto-seed-new-repo.yml ("auto-seed") and
// seed-governance.yml ("seed"). Keep in sync with both workflows.
const SEED_COMMIT_SUBJECT = /^chore\(governance\): (?:auto-)?seed \d+ org template file\(s\)$/;

/**
 * @param {unknown} message  full commit message
 * @returns {boolean} true when the subject line is a seeder-authored subject
 */
function isSeedCommitMessage(message) {
  if (typeof message !== 'string') return false;
  return SEED_COMMIT_SUBJECT.test(message.split('\n')[0].trim());
}

/**
 * Classify an existing seed branch against the consumer's default branch.
 *
 * @param {object} comparison
 * @param {number} comparison.aheadBy   compare `ahead_by` (branch commits not on base)
 * @param {Array<{sha?: string, message?: string}>} comparison.commits
 *   compare `commits`, oldest first, mapped to `{ sha, message }`
 * @returns {{ safeToReplace: boolean, reason: string }}
 */
function classifySeedBranch({ aheadBy, commits } = {}) {
  if (!Number.isInteger(aheadBy) || aheadBy < 0 || !Array.isArray(commits)) {
    return {
      safeToReplace: false,
      reason: 'comparison unavailable — cannot prove the branch is seeder-authored',
    };
  }

  if (aheadBy === 0) {
    return {
      safeToReplace: true,
      reason: 'holds no commit ahead of the default branch',
    };
  }

  if (aheadBy > 1) {
    return {
      safeToReplace: false,
      reason: `holds ${aheadBy} commits ahead of the default branch — not seeder-authored`,
    };
  }

  // aheadBy === 1: the compare payload must actually carry that commit.
  // GitHub truncates `commits` at 250; at ahead_by 1 an empty list means the
  // caller passed something unexpected, so fail closed.
  const only = commits[commits.length - 1];
  if (!only || typeof only.message !== 'string') {
    return {
      safeToReplace: false,
      reason: 'comparison carried no commit detail — cannot prove the branch is seeder-authored',
    };
  }
  if (!isSeedCommitMessage(only.message)) {
    return {
      safeToReplace: false,
      reason: 'holds a commit the seeder did not author',
    };
  }
  return { safeToReplace: true, reason: 'holds only the seeder commit' };
}

/**
 * Resolve what the seeder is allowed to do with `branch` in one consumer repo.
 *
 * Read-only: makes no write call. Callers must honour the returned action —
 * `skip` means the branch carries state this seeder must not overwrite.
 *
 * @param {object} opts
 * @param {object} opts.github  the github-script octokit client
 * @param {string} opts.owner
 * @param {string} opts.repo
 * @param {string} opts.base    the consumer's default branch
 * @param {string} opts.branch  the seed branch
 * @returns {Promise<{action: 'skip'|'create'|'rebuild', sha: string|null, reason: string}>}
 */
async function assessSeedBranch({ github, owner, repo, base, branch }) {
  // An open seed PR is work in flight: the branch may carry review fixes,
  // maintainer commits, or agent remediation. Short-circuit before reading
  // any git state, let alone writing it.
  const openPRs = await github.rest.pulls.list({
    owner, repo, head: `${owner}:${branch}`, state: 'open',
  });
  if (openPRs.data.length) {
    return {
      action: 'skip',
      sha: null,
      reason: `PR #${openPRs.data[0].number} already open — left alone`,
    };
  }

  let sha = null;
  try {
    const ref = await github.rest.git.getRef({ owner, repo, ref: `heads/${branch}` });
    sha = ref.data.object.sha;
  } catch (e) {
    if (e.status !== 404) throw e;
    return { action: 'create', sha: null, reason: 'branch absent' };
  }

  // Raw REST: no dependency on an octokit method alias.
  const cmp = await github.request('GET /repos/{owner}/{repo}/compare/{basehead}', {
    owner, repo, basehead: `${base}...${branch}`,
  });
  const verdict = classifySeedBranch({
    aheadBy: cmp.data.ahead_by,
    commits: (cmp.data.commits || []).map(c => ({
      sha: c.sha, message: c.commit && c.commit.message,
    })),
  });
  if (!verdict.safeToReplace) {
    return { action: 'skip', sha, reason: `branch ${branch} ${verdict.reason} — left alone` };
  }
  return { action: 'rebuild', sha, reason: verdict.reason };
}

/**
 * Point `branch` at `commitSha`, honouring the verdict `assessSeedBranch`
 * returned. This is the only place either seeder moves a seed ref.
 *
 * The update is a compare-and-swap: `expectedSha` is re-read immediately
 * beforehand, because the verdict is only valid for the sha it was computed
 * from. GitHub's updateRef takes no expected-sha, so this is the closest
 * available guard.
 *
 * @param {object} opts
 * @param {object} opts.github
 * @param {string} opts.owner
 * @param {string} opts.repo
 * @param {string} opts.branch
 * @param {string|null} opts.expectedSha  `sha` from assessSeedBranch; null = create
 * @param {string} opts.commitSha         the newly built seed commit
 * @returns {Promise<{moved: boolean, reason: string}>}
 */
async function moveSeedBranch({ github, owner, repo, branch, expectedSha, commitSha }) {
  if (expectedSha === null) {
    try {
      await github.rest.git.createRef({
        owner, repo, ref: `refs/heads/${branch}`, sha: commitSha,
      });
      return { moved: true, reason: 'created' };
    } catch (e) {
      if (e.status !== 422) throw e;
      // Appeared mid-run — it was never covered by a verdict.
      return { moved: false, reason: `branch ${branch} appeared during the run — left alone` };
    }
  }

  const now = await github.rest.git.getRef({ owner, repo, ref: `heads/${branch}` });
  if (now.data.object.sha !== expectedSha) {
    return { moved: false, reason: `branch ${branch} moved during the run — left alone` };
  }
  // Force is required (the rebuild is not a fast-forward) and safe: the branch
  // was proven to hold only the seeder's own commit.
  await github.rest.git.updateRef({
    owner, repo, ref: `heads/${branch}`, sha: commitSha, force: true,
  });
  return { moved: true, reason: 'rebuilt' };
}

module.exports = {
  SEED_COMMIT_SUBJECT,
  isSeedCommitMessage,
  classifySeedBranch,
  assessSeedBranch,
  moveSeedBranch,
};
