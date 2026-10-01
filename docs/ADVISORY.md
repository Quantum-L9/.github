# Advisory posture

Everything in this repo reports. Nothing blocks a merge or a push until that
control is promoted. A governance system that blocks before it is trusted gets
bypassed, and a bypassed control is worse than an absent one because it
manufactures false confidence.

## Current state of every control

| Control | Mode | Can it block a merge or push? |
| --- | --- | --- |
| `governance-pr.yml` gates | `strict: false` default | No — `core.notice` + job summary |
| `governance-issue.yml` triage | advisory | No — labels and comments only |
| Issue form validations | required *fields*, not required checkboxes | No — only shapes new issues |
| Org rulesets | `evaluate` | No — reports to Insights |
| Secret scanning | alerts only | No |
| Push protection | **not enabled** | No |
| Dependabot | opens PRs | No — no auto-merge |
| Weekly governance report | read-only issue | No |

Hard failures here fail closed toward advisory, not toward blocking a push:

- `scripts/apply-rulesets.sh` refuses a ruleset whose `enforcement` is not `evaluate`.
- `ops/build-seed-payload.js` throws if asked for `on-org-update`.
- An unparseable or unknown `.l9/org-birth-profile.yaml` is an error. It does not
  fall back to `default`.

## Promotion ladder

Each rung requires evidence from the rung below. No rung is skipped, and no rung is
climbed because it feels overdue.

**Rung 0 — observe.** Blocking controls stay off. The weekly report runs. Seeding,
label sync, and drift repair may already run; they do not block a merge.

**Rung 1 — promote one gate, one repo.** Requires four consecutive weekly reports
plus one named highest-signal finding from those reports. Set `with: {strict: true}`
in *one* repo's caller. Leave it a fortnight. If contributors route around it, the
gate is wrong, not the contributors.

**Rung 2 — promote that gate org-wide.** Only after rung 1 produced zero
justified complaints.

**Rung 3 — rulesets to active.** Requires 4+ weeks of clean evaluate data in
Insights. Change `enforcement` in the JSON, not in the UI, so the change is
reviewable in a PR.

**Rung 4 — push protection.** The last rung because it is the only control that can
block a `git push` outright. Requires that secret-scanning alerts have been *acted
on*, not merely received.

## Reversal is cheaper than caution

Every rung is one word or one flag. Going back down costs the same as going up, so
prefer trying a rung and reverting over deferring indefinitely.

## What advisory does NOT mean

It does not mean silent. A finding nobody sees is not advisory, it is absent. The
weekly report exists so that advisory findings accumulate visibly, which is what
eventually justifies promotion.
