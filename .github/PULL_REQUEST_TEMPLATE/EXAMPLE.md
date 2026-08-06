<!-- WORKED EXAMPLE — the standard, not a template. Reference it; do not copy the content. -->

## Problem

Long agent runs aborted at roughly 70% of the real context limit. Operators saw:

```
agentkit.budget.BudgetExceeded: 198,004 / 200,000 tokens at turn 42
  (actual measured context: 122,311 tokens)
```

Tool-result messages were counted twice, so the tracker reported ~45% high.

Closes #1184

## Fix

`BudgetTracker.add()` was called by both the transport layer and the message
reducer. Removed the transport-side call and made the reducer the single writer,
since it already owns message identity and can dedupe on `message_id`.

Rejected: dedupe inside `add()` by hashing content. That hides the double-call
instead of fixing it, and content hashes are not stable across tool-result
serialization.

## Risk

- [x] Medium — touches shared code, config, or a public interface

Blast radius: all four agents on `agentkit>=0.9`. Budgets now report ~30% lower,
so downstream thresholds tuned to inflated numbers will fire later than before.
Rollback: revert this commit; no state or schema involved. Pin consumers to
`agentkit==0.9.3` if the revert lands after their next deploy.

## Evidence

```
$ pytest -q tests/test_budget.py
....................                                              20 passed in 1.9s

$ pytest -q
1,204 passed, 3 skipped in 48.2s

$ ruff check . && pyright
All checks passed. 0 errors, 0 warnings, 0 informations
```

CI: https://github.com/acme/agentkit/actions/runs/1029384756

Replay of the captured 42-turn production trace:

| Turn | Before | After | Actual (tiktoken) |
| --- | --- | --- | --- |
| 10 | 41,208 | 28,905 | 28,905 |
| 42 | 178,442 | 122,310 | 122,311 |

## Gates

- [x] Regression test added that fails without this fix — `test_add_is_idempotent_per_message_id`
- [x] No secrets, tokens, or customer data — trace fixture scrubbed by `scripts/scrub_trace.py`; only role, message_id, token counts retained
- [x] `semgrep` clean
- [ ] New IAM / workflow permissions — n/a, no infrastructure or workflow changes
- [ ] Third-party actions pinned — n/a, no workflow files touched
- [x] Public interface change documented — `add()` now requires `message_id`; CHANGELOG under Changed, minor bump to 0.10.0
- [x] Observability — `budget.tokens.counted` now tags `source=reducer`, so a regression appears as a second source label

## Reviewer focus

Hardest look at `reducer.py:88-140`, the dedupe boundary. I accepted a
session-bounded in-memory `set` of seen `message_id`s: a small leak on very long
sessions traded for simplicity, measured at 3.2 MB over 10k turns.

Deferred: the transport layer still constructs a `BudgetTracker` it no longer
writes to. Removing it is a wider refactor — #1191.

## Changes by intent

**Added**
- `tests/fixtures/trace_42turn.json` — scrubbed production trace, the regression fixture
- `scripts/scrub_trace.py` — strips content from captured traces so fixtures are safe to commit

**Modified**
- `src/agentkit/budget.py` — `add()` requires `message_id` and dedupes on it
- `src/agentkit/reducer.py` — becomes the single writer to the tracker
- `src/agentkit/transport.py` — removed the duplicate `add()` call
- `tests/test_budget.py` — idempotency and missing-id cases
- `CHANGELOG.md` — 0.10.0 entry

**Deleted**
- none

## Files touched

<!-- FILES-TOUCHED:START -->
**6 files** — 6 files changed, 214 insertions(+), 31 deletions(-)

`src/agentkit/`
- `budget.py` — modified
- `reducer.py` — modified
- `transport.py` — modified

`tests/`
- `test_budget.py` — modified

`tests/fixtures/`
- `trace_42turn.json` — added

`(root)/`
- `CHANGELOG.md` — modified _(generated)_
<!-- FILES-TOUCHED:END -->
