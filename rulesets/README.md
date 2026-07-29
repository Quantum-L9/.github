# Rulesets — evaluate mode only

Every ruleset here ships with `"enforcement": "evaluate"`. In evaluate mode a rule
runs and reports to Insights **without blocking anyone**. Nothing in this directory
can fail a merge until a human changes one word.

`evaluate` requires GitHub Enterprise Cloud. On lower plans, `apply-rulesets.sh`
detects this and skips rather than silently falling back to `active` — never trade
advisory posture for availability.

## Files

| File | Targets | Rules |
| --- | --- | --- |
| `org-advisory-pr.json` | default branch, all non-archived repos | PR required, governance check reported |
| `org-advisory-hygiene.json` | all branches | deletion + force-push observed |

## Promotion is a deliberate, dated decision

```bash
# observe for at least 4 weeks, then review Insights before touching this
jq '.enforcement = "active"' rulesets/org-advisory-pr.json > /tmp/r.json
```

Do not promote a ruleset that has not produced 4 weeks of clean evaluate data.
See `docs/ADVISORY.md`.

## Warning

Never add `required_status_checks` to a ruleset that targets branch **creation** —
an org-wide rule doing so can block repository creation entirely.
