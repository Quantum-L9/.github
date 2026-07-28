# Design notes

## Problem first, theory last

Every form opens with a required `Problem` field asking for the observed symptom,
and the bug form quarantines the reporter's diagnosis in an optional "Anything else"
at the bottom. Theories stated up front anchor triage on the wrong cause; facts
first, hypotheses last.

## Forms, not markdown

Markdown issue templates are suggestions — reporters delete the sections they find
inconvenient. Forms with `validations.required: true` cannot be submitted empty, and
each field becomes a stable `### Label` heading in the rendered body, which is what
makes machine parsing viable. That parseability is the entire basis of
`issue-triage.yml`.

## Severity is the only priority input

Reporters choose `Severity` (S1–S4); the workflow derives `priority:P0–P3`. Asking
for both invites contradiction, and self-assigned priority is always inflated.
Severity is at least anchored to observable impact, and the dropdown text says
inflation gets ignored.

## Four forms, and the fifth path

Bug, Feature, Task, Incident. `blank_issues_enabled: false` closes the escape hatch,
and `contact_links` routes the two things that must never be public issues: security
reports go to a private advisory, and open-ended questions go to Discussions. Most
issue-tracker rot is questions filed as bugs.

## Nudge, do not gate

Triage never closes or rejects an issue for being thin. It posts one comment listing
what would speed things up — a missing traceback, `latest` instead of a SHA, a
one-line reproduction — and links the worked example. Gating drives reporters away;
they are doing you a favor by filing at all. The comment fires only on `opened`, so
editing does not spam.

## The one hard failure

A regex scan for GitHub tokens, AWS key ids, `sk-` keys, PEM private keys, and JWTs.
On a hit the issue gets `security:possible-leak`, a `[!CAUTION]` comment telling the
reporter to **rotate**, and the run fails so it appears in the Actions log. Redacting
the body does not help — issue edit history is public. Rotation is the only remedy,
and saying so immediately is worth the occasional false positive.

## Stale, narrowly scoped

Only `needs:info` issues go stale, at 60 days plus 14. Incidents, P0/P1, pinned, and
possible-leak issues are exempt, and PRs are excluded entirely
(`days-before-pr-stale: -1`). Blanket stale bots close real bugs and teach
contributors that filing is pointless; this one only closes threads genuinely
blocked on a reporter who has gone quiet.

## The example is the standard

`ISSUE_TEMPLATE/EXAMPLE.md` is a filled-in bug report with a complete traceback, an
independent measurement proving the number is wrong, a clean-clone reproduction, a
last-known-good version that turns the bug into a bisect range, and a workaround
stated together with why it is unsafe. It ends with a short "why this is good"
section, so the example teaches rather than merely demonstrating.
