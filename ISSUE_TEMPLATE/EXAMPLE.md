<!-- WORKED EXAMPLE — the standard for a bug report in this org.
     This is what the 🐛 Bug form looks like when filled in well. Reference it. -->

# bug: token budget aborts runs at ~70% of the real context limit

**Problem**
Long agent runs abort well before the context limit. Operators see `BudgetExceeded`
at roughly 122k actual tokens against a 200k limit, so ~40% of usable context is
unreachable.

**Error output**
```
agentkit.budget.BudgetExceeded: 198,004 / 200,000 tokens at turn 42
  at agentkit/budget.py:88 in BudgetTracker.check
  (independently measured context via tiktoken: 122,311 tokens)
```

**Reproduction**
```
1. git clone git@github.com:acme/agentkit && cd agentkit && git checkout v0.9.3
2. uv sync
3. pytest tests/replay/test_long_run.py::test_42_turns  -> fails at turn 42
```

**Expected behavior**
The tracker reports the actual measured token count, so runs continue to the real limit.

**Version / commit** — v0.9.3 (`4f2a1c9`)
**Severity** — S2 — major function broken, no workaround
**Environment** — local (macOS), CI (GitHub Actions), prod
**Last known good version** — v0.8.7, so the regression is in the 0.9.0 reducer rewrite

**Anything else**
Reported usage is consistently ~1.45x measured, and the ratio tracks the count of
tool-result messages — suggesting those are counted twice. `BudgetTracker.add()`
appears to be called from both `transport.py:212` and `reducer.py:96`. Workaround in
use: `AGENTKIT_BUDGET_LIMIT=290000` on the four affected agents, which is unsafe
because the real ceiling is then unenforced.

**Before submitting** — searched (#902 is related but closed as fixed), reproduced on
main at `4f2a1c9`, trace excerpts scrubbed by `scripts/scrub_trace.py`.

---

## Why this is a good report

- The **problem** is the symptom an operator saw, not a theory about the cause.
- The traceback is complete, and it includes an **independent measurement** that
  proves the number is wrong rather than merely surprising.
- Reproduction starts from a clean clone at a pinned SHA.
- **Last known good** turns a vague bug into a bisect range.
- The theory is present but quarantined in "anything else", below the facts.
- The workaround is stated **along with why it is unsafe**, which is what makes this
  urgent rather than merely annoying.
