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

module.exports = {
  SEED_COMMIT_SUBJECT,
  isSeedCommitMessage,
  classifySeedBranch,
};
