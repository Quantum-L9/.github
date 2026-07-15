# Security Policy — Quantum-L9

## Supported Versions
All active branches of Quantum-L9 repositories are subject to this policy.

## Reporting a Vulnerability
Do not open a public GitHub issue for security vulnerabilities.

Report security issues by emailing: security@quantumaipartners.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected repository and file paths
- Potential impact assessment

You will receive a response within 72 hours. We follow responsible disclosure with a 90-day remediation window before public disclosure.

## Security Scanning Infrastructure
All Quantum-L9 repos are protected by the l9-ci-core security kernel:
- **Secret scanning:** Gitleaks (diff-scoped, blocks on newly introduced secrets)
- **Dependency audit:** pip-audit (strict mode on release gate), Bandit SAST
- **Supply chain:** SPDX-JSON SBOM generated on every main push
- **Scorecard:** OpenSSF Scorecard analysis published weekly

Security testing is powered by l9-assurance packages:
- `l9-agent-security-testkit` — AI agent security testing harness
- `l9-security-testkit` — Core security test primitives
- `l9-redteam-harness` — Red team simulation harness
- `l9-ci-runner-security` — CI runner hardening

## Governance Security
The Cursor-Governance repository is the SSOT for all AI session security posture.
The `governance_sync.sh` script uses a ff-only pull guard on session start.
Hard resets are opt-in only via `GOVERNANCE_SYNC_HARD_RESET=1` and require explicit reviewer sign-off. See CANONICAL_LAW.md §5.
