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
// Message written by continuous-sync.yml, which rebuilds its own branch
// through the same guarded path with this subject in place of the seed one.
const SYNC_COMMIT_SUBJECT = /^chore\(governance\): sync \d+ org-managed file\(s\)$/;

/**
 * @param {unknown} message  full commit message
 * @param {RegExp} [subject] the subject the writing workflow uses
 * @returns {boolean} true when the subject line is that workflow's subject
 */
function isSeedCommitMessage(message, subject = SEED_COMMIT_SUBJECT) {
  if (typeof message !== 'string') return false;
  return subject.test(message.split('\n')[0].trim());
}

/**
 * Classify an existing seed branch against the consumer's default branch.
 *
 * Provenance is proven, not assumed: the single ahead commit must carry the
 * seeder subject, must be committed by the identity the seeder itself runs
 * as, and must be GitHub-verified (seeder commits are created through the
 * API, so GitHub signs them). A commit amended or rebased locally loses the
 * verified signature even when the subject line is preserved.
 *
 * @param {object} comparison
 * @param {number} comparison.aheadBy   compare `ahead_by` (branch commits not on base)
 * @param {Array<{sha?: string, message?: string, committerLogin?: string|null,
 *   verified?: boolean}>} comparison.commits
 *   compare `commits`, oldest first
 * @param {string|null} comparison.seederLogin  login the seeder authenticates as
 * @returns {{ safeToReplace: boolean, reason: string }}
 */
function classifySeedBranch({ aheadBy, commits, seederLogin, subject = SEED_COMMIT_SUBJECT } = {}) {
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
  const only = commits.at(-1);
  if (!only || typeof only.message !== 'string') {
    return {
      safeToReplace: false,
      reason: 'comparison carried no commit detail — cannot prove the branch is seeder-authored',
    };
  }
  if (!isSeedCommitMessage(only.message, subject)) {
    return {
      safeToReplace: false,
      reason: 'holds a commit the seeder did not author',
    };
  }
  if (typeof seederLogin !== 'string' || !seederLogin) {
    return {
      safeToReplace: false,
      reason: 'cannot resolve the seeder identity — cannot prove the branch is seeder-authored',
    };
  }
  if (only.committerLogin !== seederLogin) {
    return {
      safeToReplace: false,
      reason: `holds a commit committed by ${only.committerLogin || 'an unknown identity'}, not the seeder`,
    };
  }
  if (only.verified !== true) {
    return {
      safeToReplace: false,
      reason: 'holds a seed-subject commit without a verified signature — possibly amended',
    };
  }
  return { safeToReplace: true, reason: 'holds only the seeder\'s own verified commit' };
}

// The login a client authenticates as, resolved once per client. A seeder
// sweep calls assessSeedBranch per consumer repo with the same octokit.
const seederLoginCache = new WeakMap();
async function resolveSeederLogin(github) {
  if (seederLoginCache.has(github)) return seederLoginCache.get(github);
  let login = null;
  try {
    const me = await github.rest.users.getAuthenticated();
    login = (me.data && typeof me.data.login === 'string' && me.data.login) || null;
  } catch {
    login = null; // classifySeedBranch fails closed on a null login
  }
  seederLoginCache.set(github, login);
  return login;
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
 * @param {RegExp} [opts.subject]       commit subject the writing workflow uses
 * @param {string} [opts.seederLogin]   committer login, when the client cannot
 *   resolve its own (a GitHub App installation token cannot call /user; pass
 *   `<app-slug>[bot]`)
 * @returns {Promise<{action: 'skip'|'create'|'rebuild', sha: string|null, reason: string}>}
 */
async function assessSeedBranch({
  github, owner, repo, base, branch, subject = SEED_COMMIT_SUBJECT, seederLogin,
}) {
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
      sha: c.sha,
      message: c.commit?.message,
      committerLogin: c.committer?.login ?? null,
      verified: c.commit?.verification?.verified === true,
    })),
    seederLogin: seederLogin || (await resolveSeederLogin(github)),
    subject,
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
 * The update is a true compare-and-swap: GraphQL `updateRefs` enforces
 * `beforeOid` server-side and atomically rejects the move when the branch no
 * longer points at `expectedSha` — there is no window between check and
 * write. (REST `updateRef` takes no expected sha, which is why it is not
 * used here.)
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

  let repositoryId;
  try {
    const res = await github.graphql(
      'query($owner: String!, $repo: String!) { repository(owner: $owner, name: $repo) { id } }',
      { owner, repo },
    );
    repositoryId = res.repository.id;
  } catch {
    return {
      moved: false,
      reason: `could not resolve ${owner}/${repo} for a guarded ref move — left alone`,
    };
  }

  try {
    // The rebuild is not a fast-forward, so the update is forced — but only
    // through this guarded mutation, whose beforeOid pins the exact sha the
    // safety verdict was computed from.
    await github.graphql(
      `mutation($repositoryId: ID!, $name: String!, $afterOid: GitObjectID!, $beforeOid: GitObjectID!) {
        updateRefs(input: {
          repositoryId: $repositoryId,
          refUpdates: [{ name: $name, afterOid: $afterOid, beforeOid: $beforeOid, force: true }]
        }) { clientMutationId }
      }`,
      {
        repositoryId,
        name: `refs/heads/${branch}`,
        afterOid: commitSha,
        beforeOid: expectedSha,
      },
    );
  } catch {
    // beforeOid mismatch (branch moved since the verdict) or any other
    // rejection: the ref was not touched. Fail closed either way.
    return { moved: false, reason: `branch ${branch} moved during the run — left alone` };
  }
  return { moved: true, reason: 'rebuilt' };
}

/**
 * Refuse a write whose destination paths another open PR already changes.
 *
 * The seeders and Manual Update add files on a branch of their own; a second
 * pending PR that touches the same path would turn their PR into a merge
 * conflict on the consumer. Read-only. Every open PR is listed and its files
 * (with the previous name of a rename) intersected with `paths`. Only the
 * caller's own PR, `branch` in this repository, is excluded: assessSeedBranch
 * already guards it.
 *
 * Fail closed: when the PRs or their files cannot be read, the answer is a
 * named blocker, never "no overlap". This narrows a race; it does not close
 * one — a PR opened after this read is not seen.
 *
 * @param {object} opts
 * @param {object} opts.github
 * @param {string} opts.owner
 * @param {string} opts.repo
 * @param {string} opts.branch  the caller's own head branch
 * @param {string[]} opts.paths candidate destination paths
 * @returns {Promise<{action: 'proceed'|'block', status: string|null, reason: string}>}
 */
async function assessOpenPrOverlap({ github, owner, repo, branch, paths }) {
  const wanted = new Set(paths);
  const blocked = (e, what) => ({
    action: 'block',
    status: e.status === 403 || e.status === 401 ? 'BLOCKED_PERMISSION' : 'UNREACHABLE',
    reason: `${what} unreadable (${e.status || 'error'}): ${String(e.message || e).slice(0, 80)} — nothing written`,
  });
  let prs;
  try {
    prs = await github.paginate(github.rest.pulls.list, { owner, repo, state: 'open', per_page: 100 });
  } catch (e) {
    return blocked(e, 'open pull requests');
  }
  for (const pr of prs) {
    const own = pr.head && pr.head.ref === branch && pr.head.repo && pr.head.repo.full_name === `${owner}/${repo}`;
    if (own) continue;
    let files;
    try {
      files = await github.paginate(github.rest.pulls.listFiles, { owner, repo, pull_number: pr.number, per_page: 100 });
    } catch (e) {
      return blocked(e, `files of PR #${pr.number}`);
    }
    // The files endpoint stops at 3000 entries; past that the list is not proof.
    if (files.length >= 3000) {
      return { action: 'block', status: 'UNREACHABLE', reason: `PR #${pr.number} lists 3000+ files — overlap unprovable, nothing written` };
    }
    const hits = [...new Set(files.flatMap((f) => [f.filename, f.previous_filename]).filter((p) => wanted.has(p)))];
    if (hits.length) {
      return {
        action: 'block',
        status: 'BLOCKED_CONFLICT',
        reason: `open PR #${pr.number} (${pr.head ? pr.head.ref : '?'}) also changes ${hits.join(', ')} — nothing written`,
      };
    }
  }
  return { action: 'proceed', status: null, reason: 'no other open PR changes these paths' };
}

module.exports = {
  assessOpenPrOverlap,
  SYNC_COMMIT_SUBJECT,
  SEED_COMMIT_SUBJECT,
  isSeedCommitMessage,
  classifySeedBranch,
  assessSeedBranch,
  moveSeedBranch,
};
