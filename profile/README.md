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
| [`l9-ci-core`](https://github.com/Quantum-L9/l9-ci-core) | GitHub Actions CI runtime — SDK-provisioning, governance resolution, publication | [`l9-ci-core` README](https://github.com/Quantum-L9/l9-ci-core) |
| [`l9-assurance`](https://github.com/Quantum-L9/l9-assurance) | 51-package TypeScript governance assurance monorepo | `packages/` |
| [`.github`](https://github.com/Quantum-L9/.github) | Org backbone — health files, org defaults, advisory governance | [`README.md`](https://github.com/Quantum-L9/.github) |

---

## CI

CI execution is owned by [`l9-ci-core`](https://github.com/Quantum-L9/l9-ci-core);
CI targeting, versioning, reconciliation, and enforcement are owned by the
`l9-ci-control-plane`. This repository no longer distributes CI templates,
packs, or starter workflows — it provides the GitHub-native organization
defaults and advisory governance only.

---

## Contributing

1. Read [`CONTRIBUTING.md`](https://github.com/Quantum-L9/.github/blob/main/CONTRIBUTING.md) — governance setup checklist is mandatory.
2. Clone `Cursor-Governance` and run `setup_workspace_symlinks.sh` before committing to any repo.
3. All PRs require CI green + CODEOWNERS approval (2 reviewers for blast-radius files).

See [`SECURITY.md`](https://github.com/Quantum-L9/.github/blob/main/SECURITY.md) to report vulnerabilities.  
Security packages: [`l9-agent-security-testkit`](https://github.com/Quantum-L9/l9-assurance/tree/main/packages/l9-agent-security-testkit), [`l9-security-testkit`](https://github.com/Quantum-L9/l9-assurance/tree/main/packages/l9-security-testkit).
