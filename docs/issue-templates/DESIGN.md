# Design notes

## The issue mirrors the PR

An issue and the PR that closes it should argue about the same facts, so every form
follows the PR template's order:

| PR template | Issue form |
|---|---|
| Problem (the error, pasted) | **Problem** — required, first, the symptom |
| Evidence (a code block or run URL) | **Evidence** — required `render: shell` on bug, incident, CI, seed-CI and governance |
| Risk — pick exactly one | **Severity** (S1–S4) — or **Scope** where nothing is broken yet; one required single-select |
| Gates — checked, or unchecked with a reason | **Done when** — required; the check the fix PR's Evidence must show |
| `Closes #` | **Related** — blocks, blocked by, came from |
| Reviewer focus | **Anything else** — theories and workarounds, last |

`ops/test-issue-forms.js` enforces this shape on every form, so a new form cannot
quietly drop a section.

## Problem first, theory last

Every form opens with a required `Problem` field asking for the observed symptom,
and diagnosis is quarantined in an optional "Anything else" at the bottom. Theories
stated up front anchor triage on the wrong cause; facts first, hypotheses last.

## Forms, not markdown

Markdown issue templates are suggestions — reporters delete the sections they find
inconvenient. Forms with `validations.required: true` cannot be submitted empty, and
each field becomes a stable `### Label` heading in the rendered body, which is what
makes machine parsing viable. That parseability is the entire basis of
`issue-triage.yml`, and it is why no required field carries a pre-filled `value`:
a pre-filled field satisfies `required` without the reporter typing anything.

A field label is an API. `issue-triage.yml` and `governance-issue.yml` key on
`Severity`, `Environment`, `Last known good version`, `Scope`, `Breaking change?`,
`Evidence`, `Version / commit` and `Reproduction`; the test fails if a parser reads a
heading no form renders. Consumers call `governance-issue.yml` at a pinned SHA, so
`Severity` and its `S1`–`S4` tokens must stay stable across forms.

## Severity is the only priority input

Reporters choose `Severity` (S1–S4); the workflow derives `priority:P0–P3`. Asking
for both invites contradiction, and self-assigned priority is always inflated. No
form sets a static `sev:*` or `priority:*` label, and a re-set severity replaces the
old labels instead of stacking beside them.

## Seven forms, one chooser

Bug, Feature, Task, Incident, CI failure, Seed CI failure, Governance violation.
The `bug_report` / `feature_request` pair that duplicated Bug and Feature is gone, so
every repository — seeded or inheriting — sees the same chooser.
`blank_issues_enabled: false` closes the escape hatch, and `contact_links` route
security reports to a private advisory. GitHub Discussions are not enabled for the
org; `SUPPORT.md` says where questions go instead.

`.github/ISSUE_TEMPLATE/` is the source GitHub reads for org defaults. The root
`ISSUE_TEMPLATE/` and the seeded `templates/issue-templates/` are byte-identical
mirrors, enforced by the same test.

## Nudge, do not gate

Triage never closes or rejects an issue for being thin. It posts one comment listing
what would speed things up — Evidence with no traceback, log line or run URL inside
its code fence, `latest` instead of a SHA, a one-line reproduction — and links the
worked example. Gating drives reporters away. The comment fires only on `opened`, so
editing does not spam.

## The one hard failure

A regex scan for GitHub tokens, AWS key ids, `sk-` keys, PEM private keys, and JWTs.
On a hit the issue gets `security:possible-leak` and a `[!CAUTION]` comment telling
the reporter to **rotate**. In this repository the run also fails so it appears in
the Actions log; the consumer workflow `governance-issue.yml` stays advisory (label
and comment, never a red X). Both scan the same patterns — the test holds them in
step. Redacting the body does not help — issue edit history is public.

## Stale, narrowly scoped

Only `needs:info` issues go stale, at 60 days plus 14. Incidents, P0/P1, pinned, and
possible-leak issues are exempt, and PRs are excluded entirely
(`days-before-pr-stale: -1`).

## The example is the standard

`docs/issue-templates/EXAMPLE.md` is the body the Bug form renders when filled in
well: a complete traceback with an independent measurement, a clean-clone
reproduction, a last-known-good version that turns the bug into a bisect range, a
Done when the fix PR can show verbatim, and a workaround stated together with why it
is unsafe. It lives outside `ISSUE_TEMPLATE/` so it is never mistaken for a form,
and the triage comment links it by absolute URL so the link works from any repo.

## Filing from a terminal or an agent

An issue body does not have to come from the web form. Cursor-Governance's
`compose_issue_body.py` — the sibling of `compose_pr_body.py`, which fills this
repo's PR template for `make pr` — renders the same `### Label` body from one of
these forms, so an agent-filed issue is parsed and labelled exactly like a
hand-filed one.
