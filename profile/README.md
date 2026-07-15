<!-- profile/README.md — Quantum-L9 Org Profile -->

# Quantum-L9

**Compliance-grade AI DevOps infrastructure, governed by law.**

[![l9-ci-core CI](https://img.shields.io/badge/CI-l9--ci--core-blue)](https://github.com/Quantum-L9/l9-ci-core)
[![OpenSSF Scorecard](https://img.shields.io/badge/OpenSSF-Scorecard-green)](https://github.com/Quantum-L9)
[![Governance: CANONICAL_LAW](https://img.shields.io/badge/Governance-CANONICAL__LAW-purple)](https://github.com/Quantum-L9/Cursor-Governance/blob/main/CANONICAL_LAW.md)

## Org Architecture
| Repo | Role | Entry Point |
|---|---|---|
| **Cursor-Governance** | GlobalCommands SSOT — AI session lifecycle, canonical law, skills, rules, commands, Graphiti memory layer | `CANONICAL_LAW.md` |
| **l9-ci-core** | CI/security kernel — 8 reusable workflow kernels callable by all org repos via `workflow_call` | `.github/workflows/` |
| **l9-assurance** | 51-package TypeScript compliance platform — CI/CD governance, testkit primitives, release evidence, redteam, frontier trust | `MANIFEST.md` |

## Contributing
All contributors must complete the governance setup checklist before opening a PR. This wires your workspace to the CANONICAL_LAW.md symlink contract (§2 and §8).

CI in every repo runs via l9-ci-core kernels — starter workflows are available in every repo's Actions tab under **New workflow → By Quantum-L9**.

## Security
See `SECURITY.md` for the vulnerability disclosure policy. Security testing is powered by l9-assurance's `l9-agent-security-testkit` and `l9-security-testkit` packages.
