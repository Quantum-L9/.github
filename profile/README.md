# Quantum-L9

> **Distributed intelligence infrastructure for autonomous AI constellation systems.**

[![CI](https://github.com/Quantum-L9/l9-ci-core/actions/workflows/l9-self-ci.yml/badge.svg)](https://github.com/Quantum-L9/l9-ci-core/actions/workflows/l9-self-ci.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/Quantum-L9/l9-ci-core/badge)](https://securityscorecards.dev/viewer/?uri=github.com/Quantum-L9/l9-ci-core)
[![Governance](https://img.shields.io/badge/governance-CANONICAL__LAW.md-blue)](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)

---

## Architecture

| Repository | Role | Entry Point |
|---|---|---|
| [`Cursor-Governance`](https://github.com/Quantum-L9/Cursor-Governance) | Policy SSOT — CANONICAL_LAW.md §1–§9, symlink wiring, GlobalCommands | `CANONICAL_LAW.md` |
| [`l9-ci-core`](https://github.com/Quantum-L9/l9-ci-core) | Thin GitHub Actions control plane (v2) — SDK-provisioning, governance resolution, publication | `org-ci.yml` via org required-workflow ruleset (current); `l9-ci-pack/` + `pr-pipeline.yml@v1` (retired/frozen) |
| [`l9-assurance`](https://github.com/Quantum-L9/l9-assurance) | 51-package TypeScript governance assurance monorepo | `packages/` |
| [`.github`](https://github.com/Quantum-L9/.github) | Org backbone — health files, starter templates, workflow registry | `workflow-interface-registry.yml` |

---

## CI instantiation

**Current:** canonical CI is
[`l9-ci-core/.github/workflows/org-ci.yml`](https://github.com/Quantum-L9/l9-ci-core/blob/main/.github/workflows/org-ci.yml),
enforced by a GitHub organization required-workflow ruleset. Consumer
repositories copy no workflow and select no Core revision.

**`l9-ci-pack/` (retired):** the copy-first distribution kit, frozen for
reference — see [`l9-ci-pack/README.md`](https://github.com/Quantum-L9/.github/blob/main/l9-ci-pack/README.md).

**`@v1` (legacy, frozen):** All repositories still on legacy `@v1` consume
`l9-ci-core` kernels via thin caller workflows. See
[`workflow-interface-registry.yml`](https://github.com/Quantum-L9/.github/blob/main/workflow-interface-registry.yml)
for the machine-readable CI API contract (`v2:` block for the current pack,
top-level `kernels:` list for the frozen `@v1` set).

| Kernel | Purpose |
|---|---|
| `pr-pipeline.yml@v1` | Lint, type-check, test, security gates on every PR |
| `release-publish.yml@v1` | Versioned release build and publish |
| `nightly.yml@v1` | Scheduled nightly validation |
| `pre-commit-ci.yml@v1` | Pre-commit hook enforcement |
| `trio-governance.yml@v1` | Three-tier separation governance check |
| `security.yml@v1` | Gitleaks, Bandit/Semgrep, pip-audit/npm audit |
| `scorecard.yml@v1` | OpenSSF Scorecard analysis |
| `sbom.yml@v1` | SBOM generation (SPDX-JSON via Syft) |

---

## Contributing

1. Read [`CONTRIBUTING.md`](https://github.com/Quantum-L9/.github/blob/main/CONTRIBUTING.md) — governance setup checklist is mandatory.
2. Clone `Cursor-Governance` and run `setup_workspace_symlinks.sh` before committing to any repo.
3. All PRs require CI green + CODEOWNERS approval (2 reviewers for blast-radius files).

See [`SECURITY.md`](https://github.com/Quantum-L9/.github/blob/main/SECURITY.md) to report vulnerabilities.
Security packages: [`l9-agent-security-testkit`](https://github.com/Quantum-L9/l9-assurance/tree/main/packages/l9-agent-security-testkit), [`l9-security-testkit`](https://github.com/Quantum-L9/l9-assurance/tree/main/packages/l9-security-testkit).
