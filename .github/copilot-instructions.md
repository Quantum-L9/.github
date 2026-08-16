# Quantum-L9 Organization — Copilot Instructions

## Architecture

This organization uses a governed CI constellation. All CI pipelines are owned by
`l9-ci-core` (runtime) and `l9-ci-sdk` (execution engine), with policy owned by
the `l9-ci-control-plane`. Never write CI workflows from scratch — template
distribution from `Quantum-L9/.github` was retired; follow the CI control-plane
guidance instead.

The policy source of truth is `CANONICAL_LAW.md` in `Quantum-L9/Cursor-Governance`.

## Language & Tooling

### Python
- **Formatter/linter:** ruff (format + check). Never use Black or isort.
- **Type checker:** mypy (strict, blocking). Never use Pyright.
- **Test framework:** pytest with pytest-cov. Never use unittest directly.
- **Package manager:** uv preferred, pip acceptable. Never use Poetry or Pipenv.
- **Build system:** setuptools with `pyproject.toml`. Never use hatchling or flit.
- **Dependency pins:** exact versions (`==`) in `requirements-consumer-ci.txt`.

### TypeScript / JavaScript
- **Formatter/linter:** Biome (format + lint + import organization). Never use Prettier.
- **Supplemental linting:** ESLint only for framework-specific plugins Biome lacks.
  Never use ESLint for formatting.
- **Type checker:** `tsc --noEmit`.
- **Test framework:** vitest.

## CI Conventions

- All GitHub Actions MUST be pinned to full 40-character commit SHAs. Never use
  floating refs like `@main`, `@v1`, or `@latest`.
- Workflow permissions MUST be least-privilege (`contents: read` default). Only
  grant `write` scopes on the specific job that needs them.
- Immutable checkout: use raw `git fetch --depth=1` of `github.sha`, not
  `actions/checkout` with default settings.
- CI tool versions are pinned in `requirements-consumer-ci.txt` (Dependabot-tracked).

## Repository Standards

- Every repo MUST have `.github/CODEOWNERS` with `@Quantum-L9/platform` as default owner.
- Every repo MUST have `.github/dependabot.yml` for automated dependency updates.
- Type checking is required and blocking. No global `--ignore-missing-imports`.
- Coverage threshold is advisory (`0`) unless explicitly raised per-repo.

## Forbidden Patterns

- Never suggest auto-merge for Dependabot PRs.
- Never generate CI that duplicates `l9-ci-core`'s analysis pipeline (semgrep,
  normalize, publish).
- Never use `workflow-templates/` v1 starters for new work.
- Never add Sonar, Prettier, Poetry, or PacketEnvelope to any repo.
- Never reference `cryptoxdog/golden-repo` — it is superseded.

## Security

- Secret scanning is enabled org-wide (alerts only, advisory).
- Push protection is NOT enabled — do not assume secrets are blocked at push time.
- Never commit secrets, tokens, or credentials. Use GitHub Secrets or environment
  variables.
- Report vulnerabilities via SECURITY.md (coordinated disclosure, not public issues).

## Code Style

- Prefer explicit over implicit.
- Prefer composition over inheritance.
- All public functions must have type annotations (Python) or TypeScript types.
- Docstrings on all public APIs (Google style for Python).
- Error messages must include the actual value that failed validation.
