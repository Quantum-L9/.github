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

Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`, `docs/<scope>`.
PRs targeting `main` require CODEOWNERS approvals for blast-radius paths.

## Code of conduct

Standard professional conduct expected across all Quantum-L9 spaces. Report
concerns to governance via a private security advisory if conduct issues intersect
with security, otherwise to org owners directly.

## Instantiating l9-ci-core v2 (current)

For any new repo, start here:

1. Copy the six governance files from
   [`l9-ci-pack/governance/`](https://github.com/Quantum-L9/.github/tree/main/l9-ci-pack/governance) → `.github/governance/`.
2. Copy [`l9-ci-pack/workflows/l9-analysis.yml`](https://github.com/Quantum-L9/.github/blob/main/l9-ci-pack/workflows/l9-analysis.yml) → `.github/workflows/l9-analysis.yml`.
3. Optionally copy the matching lint/test template for your language.
4. Full steps, profile matrix, and rollout guidance:
   [`l9-ci-pack/README.md`](https://github.com/Quantum-L9/.github/blob/main/l9-ci-pack/README.md).

Ownership and pinning rules live in
[`l9-ci-core/AGENTS.md`](https://github.com/Quantum-L9/l9-ci-core/blob/main/AGENTS.md).

## CI Gate Requirements (Legacy `@v1`)

> **New repos: skip this table.** Instantiate `l9-ci-core` **v2** from
> [`l9-ci-pack/README.md`](https://github.com/Quantum-L9/.github/blob/main/l9-ci-pack/README.md)
> instead. The kernels below are frozen at the historical `@v1` commit and
> kept only so already-imported repos keep resolving.

All pull requests on repos still using legacy `@v1` kernels must pass:

| Gate | Tool | Kernel |
|---|---|---|
| Lint + type-check | ruff, mypy (Python) / tsc (TypeScript) | `pr-pipeline.yml@v1` |
| Unit tests | pytest (Python) / Jest (TypeScript) | `pr-pipeline.yml@v1` |
| Secret scan | gitleaks | `security.yml@v1` |
| SAST | Bandit + Semgrep (Python) | `security.yml@v1` |
| Dependency audit | pip-audit / npm audit | `security.yml@v1` |
| Pre-commit hooks | pre-commit framework | `pre-commit-ci.yml@v1` |
| Governance trio | Three-tier separation | `trio-governance.yml@v1` |

> Never duplicate logic across kernels. Never add business logic to thin callers.
> Never reference `@main` from thin callers — always use `@v1`.

## Kernel Authoring (l9-ci-core contributors only)

- Kernels must use `on: workflow_call` only
- `l9-self-ci.yml` must remain `on: pull_request/push` — **never convert to workflow_call** (circular dependency)
- `@v1` moving tag discipline: force-update `v1` for backward-compatible changes; cut `v2` for breaking changes
- See [workflow-interface-registry.yml](https://github.com/Quantum-L9/.github/blob/main/workflow-interface-registry.yml) for the full kernel API contract (see the `v2:` block for the current pack; the top-level `kernels:` list is the frozen `@v1` set)
