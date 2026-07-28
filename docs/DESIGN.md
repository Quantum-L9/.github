# Design notes

## Problem first

The first section is `## Problem`, with a fenced block prompting the real traceback,
alert, or failing assertion. Reviewers arrive knowing what hurt before they see how
it was fixed. A restatement of the diff is not a problem statement.

## Checkboxes carry weight or they are cut

Most PRs are approved with superficial review, so unenforced checkboxes teach
reflexive ticking. Two kinds survive here:

- **Risk** — exactly one of three levels. Mutually exclusive, and it routes review
  depth rather than acting as a to-do item.
- **Gates** — seven items. Check it, or leave it unchecked *with a reason on the
  same line*. `pr-gates.yml` fails an unchecked box that has no justification.

Mixing "all must be checked" with "pick exactly one" is what breaks naive task-list
validators. Separating them into two sections lets each be enforced correctly.

## Two file lists, on purpose

`## Changes by intent` is written by the author: `path — why`, grouped by
added/modified/deleted. `## Files touched` is written by the bot from
`git diff --name-status base...head`.

The value is the comparison. A file in the diff that nobody declared is usually a
stray debug edit, a committed artifact, or scope creep. `pr-files.yml` marks those
inline with a warning callout and fails the job. Declared-but-absent paths surface
as a note — typically a typo or a dropped change. Lockfiles, snapshots, `dist/`,
and `CHANGELOG.md` are exempt via the `GEN` regex; extend it for your stacks.

Triple-dot diff (`base...head`) is deliberate: it yields the full PR change set
rather than only the latest commit, which is the usual bug in file-listing jobs.

## Evidence, not assertion

The `Evidence` gate requires a fenced block or a link matching `actions/runs/<id>`.
"Tests pass" is unverifiable; pasted output is.

## Idempotent body edits

The bot rewrites the PR body between `<!-- FILES-TOUCHED:START -->` and `:END`
sentinels instead of posting comments, so the description stays current and the
thread stays clean. The template ships the sentinels with a `_pending_` placeholder
so the bot has an anchor on the very first push. It writes only when content
changes, avoiding an edit → `edited` event → edit loop.

## The example is the standard

`PULL_REQUEST_TEMPLATE/EXAMPLE.md` is a complete, realistic PR: measured
before/after table, a named rejected alternative, two gates deliberately unchecked
*with reasons*, an accepted trade-off with a measured cost, and a deferred refactor
linked to its own issue. Link it from `CONTRIBUTING.md` and from onboarding.
Contributors imitate the best precedent they can find; give them one.
