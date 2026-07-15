# Security Policy — Quantum-L9

## Supported Versions
All active branches of Quantum-L9 repositories are subject to this policy.

## Reporting a Vulnerability
**Do not open a public GitHub issue for security vulnerabilities.**
Report security issues by emailing: security@quantumaipartners.com

We follow responsible disclosure with a 90-day remediation window before public disclosure.

## Security Scanning Infrastructure
All Quantum-L9 repos are protected by the l9-ci-core security kernel:
- **Secret scanning:** Gitleaks (diff-scoped, blocks on newly introduced secrets)
- **Dependency audit:** pip-audit (strict mode on release gate), Bandit SAST
- **Supply chain:** SPDX-JSON SBOM generated on every main push
- **Scorecard:** OpenSSF Scorecard analysis published weekly
