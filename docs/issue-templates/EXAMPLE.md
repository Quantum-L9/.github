<!-- WORKED EXAMPLE — the standard for a bug report in this org.
     This is the issue body the 🐛 Bug form (.github/ISSUE_TEMPLATE/1-bug.yml)
     renders when it is filled in well: one `### <label>` heading per field, in
     form order. issue-triage.yml parses exactly these headings, and the
     Cursor-Governance issue composer renders the same shape. -->

# bug: token budget aborts runs at ~70% of the real context limit

### Problem

Long agent runs abort well before the context limit. Operators see `BudgetExceeded`
at roughly 122k actual tokens against a 200k limit, so ~40% of usable context is
unreachable.

### Evidence

```shell
agentkit.budget.BudgetExceeded: 198,004 / 200,000 tokens at turn 42
  at agentkit/budget.py:88 in BudgetTracker.check
  (independently measured context via tiktoken: 122,311 tokens)
```

### Reproduction

```shell
git clone git@github.com:acme/agentkit && cd agentkit && git checkout v0.9.3
uv sync
pytest tests/replay/test_long_run.py::test_42_turns   # fails at turn 42
```

### Environment

Production

### Version / commit

v0.9.3 (4f2a1c9e0d7b3a55c21f0e8d9b6a4c3f2e1d0a9b)

### Last known good version

v0.8.7

### Severity

S2 — major function broken, no workaround

### Done when

`test_42_turns` passes, and a 42-turn replay reports within 1% of the tiktoken
measurement.

### Related

related to #902 (closed as fixed; same symptom, different path)

### Anything else

Reported usage is consistently ~1.45x measured, and the ratio tracks the count of
tool-result messages — suggesting those are counted twice. `BudgetTracker.add()`
appears to be called from both `transport.py:212` and `reducer.py:96`. Workaround in
use: `AGENTKIT_BUDGET_LIMIT=290000` on the four affected agents, which is unsafe
because the real ceiling is then unenforced.

---

## Why this is a good report

- The **problem** is the symptom an operator saw, not a theory about the cause.
- The **evidence** is complete, and it includes an **independent measurement** that
  proves the number is wrong rather than merely surprising.
- Reproduction starts from a clean clone at a pinned SHA.
- **Last known good** turns a vague bug into a bisect range (`regression` label).
- **Done when** is a check the fix PR's Evidence section can show verbatim — the
  issue and the PR close on the same fact.
- The theory is present but quarantined in "Anything else", below the facts.
- The workaround is stated **along with why it is unsafe**, which is what makes this
  urgent rather than merely annoying.
