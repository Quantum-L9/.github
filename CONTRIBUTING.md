# Contributing to Quantum-L9

## Setup

Governance tooling is consumed as a **pinned dependency**, not a sibling clone.
Add to your repo's `package.json` / `pyproject.toml` / `requirements` per its
distribution mechanism (see `docs/AUDIT.md` finding #4 for the migration from the
previous "clone Cursor-Governance alongside your repo" step).

```bash
# one-time bootstrap for a new or existing repo
curl -fsSL https://raw.githubusercontent.com/Quantum-L9/.github/main/scripts/bootstrap.sh | bash
```

`bootstrap.sh` installs governance hooks, PR/issue templates (if locally
overridden), and CI callers — idempotently, safe to re-run.

## Pull requests

Use the default PR template. Every PR requires: a stated Problem, exactly one
checked Risk level, pasted Evidence, and all Gates checked or justified.

## Commits

Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`) — release tooling parses
these to generate changelogs.

## Code of conduct

Standard professional conduct expected across all Quantum-L9 spaces. Report
concerns to governance via a private security advisory if conduct issues intersect
with security, otherwise to org owners directly.
